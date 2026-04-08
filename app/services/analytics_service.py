from datetime import datetime, timezone, timedelta

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.logging import logger
from app.models.detections import Orientation, Severity, SurfaceType
from app.schemas.analytics import (
    DashboardResponse,
    DetectionsTimeline,
    LocationBar,
    OrientationDistribution,
    OrientationPoint,
    SeverityDistribution,
    SeveritySlice,
    SummaryStats,
    SurfaceBar,
    SurfaceDistribution,
    TimelinePoint,
    TopLocations,
)

SEVERITY_COLORS = {
    "low":    "#00FF9C",   # neon green
    "medium": "#FFB800",   # neon amber
    "high":   "#FF3A3A",   # neon red
}

# Known surface types from enum
KNOWN_SURFACES = {s.value for s in SurfaceType}


async def get_dashboard(
    current_user: dict,
    db: AsyncIOMotorDatabase,
    timeline_days: int = 30,
) -> DashboardResponse:
    """
    Fetches all dashboard metrics in parallel using asyncio.gather.
    Returns a DashboardResponse ready for the frontend.
    """
    import asyncio
    
    user_id = current_user["_id"]
    logger.info(f"Building dashboard for user: {user_id}")

    (
        summary,
        severity,
        surface,
        orientation,
        timeline,
        locations,
    ) = await asyncio.gather(
        _get_summary_stats(user_id, db),
        _get_severity_distribution(user_id, db),
        _get_surface_distribution(user_id, db),
        _get_orientation_distribution(user_id, db),
        _get_detections_timeline(user_id, db, timeline_days),
        _get_top_locations(user_id, db),
    )

    return DashboardResponse(
        summary=summary,
        severity=severity,
        surface=surface,
        orientation=orientation,
        timeline=timeline,
        locations=locations,
    )


# Summary Stats 

async def _get_summary_stats(
    user_id: ObjectId,
    db: AsyncIOMotorDatabase,
) -> SummaryStats:
    """
    Computes global counters for the user:
    total images, total cracks, avg confidence, avg inference_ms,
    and the image with the most cracks detected.
    """
    pipeline = [
        
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                
                "_id":                  None,
                "total_images":         {"$sum": 1},
                "total_cracks":         {"$sum": "$total_cracks"},
                "avg_inference_ms":     {"$avg": "$inference_ms"},
                "max_cracks":           {"$max": "$total_cracks"},
            }
        }
    ]

    cursor = db["detections"].aggregate(pipeline)
    result = await cursor.to_list(length=1)

    if not result:
        
        return SummaryStats(
            
            total_images_analyzed=0,
            total_cracks_detected=0,
            average_confidence=0.0,
            average_inference_ms=0.0,
            most_cracked_image=None,
        )

    stats = result[0]
    
    # Average confidence
    
    conf_pipeline = [
        
    {"$match": { "user_id": user_id  , "confidence": { "$gt": 0 }}},
    { "$unwind": "$detections"},
    { "$group": {
        "_id": None,
        "avg_confidence": { "$avg": "$detections.confidence" }
    }}
    ]
    
    conf_cursor = db["detections"].aggregate(conf_pipeline)
    conf_result = await conf_cursor.to_list(length=1)
    avg_conf = round(conf_result[0]["avg_conf"], 4) if conf_result else 0.0

    # Image with most cracks
    most_cracked_doc = await db["images"].find_one(
        {"user_id": user_id, "total_cracks_detected": stats["max_cracks"]},
        sort=[("uploaded_at", -1)],
    )

    most_cracked = None
    
    if most_cracked_doc:
        
        most_cracked = {
            "image_id":    str(most_cracked_doc["_id"]),
            "filename":    most_cracked_doc["original_filename"],
            "total_cracks": most_cracked_doc["total_cracks_detected"],
            "uploaded_at": most_cracked_doc["uploaded_at"].isoformat(),
        }

    return SummaryStats(
        
        total_images_analyzed=stats["total_images"],
        total_cracks_detected=stats["total_cracks"],
        average_confidence=avg_conf,
        average_inference_ms=round(stats["avg_inference_ms"], 2),
        most_cracked_image=most_cracked,
    )


# Severity Distribution

async def _get_severity_distribution(
    user_id: ObjectId,
    db: AsyncIOMotorDatabase,
) -> SeverityDistribution:
    """
    Counts crack instances grouped by severity level.
    Unknown severity values are grouped under 'unknown'.
    """
    pipeline = [
        
        {"$match": {"user_id": user_id}},
        {"$unwind": "$detections"},
        {
            "$group": {
                "_id":   "$detections.severity",
                "count": {"$sum": 1},
            }
        }
    ]

    cursor  = db["detections"].aggregate(pipeline)
    results = await cursor.to_list(length=None)

    # Initialize all severity levels at 0
    counts = {s.value: 0 for s in Severity}
    
    for r in results:
        
        key = r["_id"] if r["_id"] in counts else "unknown"
        
        counts[key] = counts.get(key, 0) + r["count"]

    total = sum(counts.values())

    data = [
        SeveritySlice(
            
            name=severity,
            value=count,
            fill=SEVERITY_COLORS.get(severity, "#888888"),
        )
        
        for severity, count in counts.items()
        
        if count > 0
    ]

    return SeverityDistribution(data=data, total_instances=total)


# Surface type distribution

async def _get_surface_distribution(
    user_id: ObjectId,
    db: AsyncIOMotorDatabase,
) -> SurfaceDistribution:
    """
    Groups detections by surface_type.
    Surface types not in the enum are grouped as 'other'.
    """
    
    pipeline = [
        
        {"$match": {"user_id": user_id}},
        {"$unwind": "$detections"},
        
        {"$group": {
            "_id": "$detections.surface_type",
            "cracks": {"$sum": "$detections.total_cracks"},
            "images": {"$sum": 1},
        }},
        {"$sort": {"cracks": -1}}
    ]

    cursor = db["detections"].aggregate(pipeline)
    results = await cursor.to_list(length=None)

    # Initialize all surface types at 0
    counts = {s.value: 0 for s in SurfaceType}
    total_cracks = 0
    total_images = 0
    
    # Normalize unknown surface types to 'other'
    normalized: dict[str, dict] = {}
    for r in results:
        key = r["_id"] if r["_id"] in KNOWN_SURFACES else "other"
        if key not in normalized:
            normalized[key] = {"cracks": 0, "images": 0}
        normalized[key]["cracks"] += r["cracks"]
        normalized[key]["images"] += r["images"]

    data = [
        SurfaceBar(surface=surface, cracks=v["cracks"], images=v["images"])
        for surface, v in sorted(
            normalized.items(), key=lambda x: x[1]["cracks"], reverse=True
        )
    ]

    return SurfaceDistribution(data=data)
 
 
 # Orientation distribution
 
async def _get_orientation_distribution(
    user_id: ObjectId,
    db: AsyncIOMotorDatabase,
) -> OrientationDistribution:
    """
    Counts crack instances grouped by orientation.
    Used for the RadarChart — all 5 orientations always present.
    """
    pipeline = [
        
        {"$match": {"user_id": user_id}},
        {"$unwind": "$detections"},
        {
            "$group": {
                "_id":   "$detections.orientation",
                "count": {"$sum": 1},
            }
        }
    ]

    cursor  = db["detections"].aggregate(pipeline)
    results = await cursor.to_list(length=None)

    # Initialize all orientations at 0 — RadarChart needs all axes
    counts = {o.value: 0 for o in Orientation}
    total_count = 0
    
    for r in results:
        
        key = r["_id"] if r["_id"] in counts else "irregular"
        counts[key] = counts.get(key, 0) + r["count"]

    # Fixed order for RadarChart consistency
    order = ["horizontal", "diagonal", "vertical", "forked", "irregular"]
    
    data  = [
        OrientationPoint(orientation=o, count=counts.get(o, 0))
        for o in order
    ]

    return OrientationDistribution(data=data)


# Detections timeline

async def _get_detections_timeline(
    user_id: ObjectId,
    db: AsyncIOMotorDatabase,
    days: int = 30,
) -> DetectionsTimeline:
    """
    Groups detections by day for the last N days.
    Missing days are filled with zeros so the AreaChart has no gaps.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    pipeline = [
        {
            "$match": {
                "user_id":      user_id,
                "detected_at":  {"$gte": since},
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date":   "$detected_at",
                    }
                },
                "total_cracks": {"$sum": "$total_cracks"},
                "total_images": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    cursor  = db["detections"].aggregate(pipeline)
    results = await cursor.to_list(length=None)

    # Build a dict keyed by date string
    by_date = {
        r["_id"]: {
            "total_cracks": r["total_cracks"],
            "total_images": r["total_images"],
        }
        for r in results
    }

    # Fill all days in the range — no gaps in AreaChart
    data = []
    total_count = 0
    
    for i in range(days):
        
        day = (since + timedelta(days=i)).strftime("%Y-%m-%d")
        entry = by_date.get(day, {"total_cracks": 0, "total_images": 0})
        total_cracks = entry["total_cracks"]
        #total_images = entry["total_images"]
        total_count += total_cracks
        
        data.append(TimelinePoint(
            date=day,
            total_cracks=entry["total_cracks"],
            total_images=entry["total_images"],
            total_count=total_count,

        ))

    return DetectionsTimeline(data=data, period_days=days)


# Top locations

async def _get_top_locations(
    user_id: ObjectId,
    db: AsyncIOMotorDatabase,
    limit: int = 8,
) -> TopLocations:
    """
    Returns the top N locations ranked by total cracks detected.
    Joins detections -> images -> locations by image_id in aggregation pipeline.
    Locations with no images are excluded.
    """
    pipeline = [
        # Start from images — they have both user_id and location_id
        {
            "$match": {
                "user_id":     user_id,
                "location_id": {"$exists": True, "$ne": None},
            }
        },
        # Join with detections on image_id
        {
            "$lookup": {
                "from":         "detections",
                "localField":   "_id",
                "foreignField": "image_id",
                "as":           "detection",
            }
        },
        {"$unwind": {"path": "$detection", "preserveNullAndEmpty": False}},
        # Group by location_id
        {
            "$group": {
                "_id":          "$location_id",
                "total_cracks": {"$sum": "$detection.total_cracks"},
                "total_images": {"$sum": 1},
            }
        },
        {"$sort":  {"total_cracks": -1}},
        {"$limit": limit},
        # Join with locations to get name and city
        {
            "$lookup": {
                "from":         "locations",
                "localField":   "_id",
                "foreignField": "_id",
                "as":           "location_doc",
            }
        },
        {"$unwind": "$location_doc"},
        {
            "$project": {
                "_id":          1,
                "total_cracks": 1,
                "total_images": 1,
                "name":         "$location_doc.name",
                "city":         "$location_doc.city",
            }
        },
    ]

    cursor  = db["images"].aggregate(pipeline)
    results = await cursor.to_list(length=None)

    data = [
        
        LocationBar(
            
            location_id=str(r["_id"]),
            name=r["name"],
            city=r["city"],
            total_cracks=r["total_cracks"],
            total_images=r["total_images"],
        )
        for r in results
    ]

    return TopLocations(data=data)

