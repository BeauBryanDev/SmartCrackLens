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


def _normalize_user_id(user_id: ObjectId | str) -> ObjectId:
    
    if isinstance(user_id, ObjectId):
        
        return user_id
    
    return ObjectId(user_id)


def _empty_summary_stats() -> SummaryStats:
    
    return SummaryStats(
        
        total_images_analyzed=0,
        total_cracks_detected=0,
        average_confidence=0.0,
        average_inference_ms=0.0,
        most_cracked_image=None,
    )


def _empty_severity_distribution() -> SeverityDistribution:
    
    return SeverityDistribution(data=[], total_instances=0)


def _empty_surface_distribution() -> SurfaceDistribution:
    
    return SurfaceDistribution(data=[])


def _empty_orientation_distribution() -> OrientationDistribution:
    
    order = ["horizontal", "diagonal", "vertical", "forked", "irregular"]
    
    return OrientationDistribution(
        
        data=[OrientationPoint(orientation=orientation, count=0) for orientation in order]
    )


def _empty_timeline(days: int) -> DetectionsTimeline:
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    since = today - timedelta(days=max(days - 1, 0))
    
    data = [
        
        TimelinePoint(
            date=(since + timedelta(days=i)).strftime("%Y-%m-%d"),
            total_cracks=0,
            total_images=0,
        )
        for i in range(days)
    ]
    return DetectionsTimeline(data=data, period_days=days)


def _empty_top_locations() -> TopLocations:
    
    return TopLocations(data=[])


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
    
    user_id = _normalize_user_id(current_user["_id"])
    logger.info(f"Building dashboard for user: {user_id}")

    metrics = await asyncio.gather(
        
        _get_summary_stats(user_id, db),
        _get_severity_distribution(user_id, db),
        _get_surface_distribution(user_id, db),
        _get_orientation_distribution(user_id, db),
        _get_detections_timeline(user_id, db, timeline_days),
        _get_top_locations(user_id, db),
        return_exceptions=True,
    )

    fallbacks = (
        
        _empty_summary_stats(),
        _empty_severity_distribution(),
        _empty_surface_distribution(),
        _empty_orientation_distribution(),
        _empty_timeline(timeline_days),
        _empty_top_locations(),
    )
    metric_names = ("summary", "severity", "surface", "orientation", "timeline", "locations")
    resolved_metrics = []

    for name, result, fallback in zip(metric_names, metrics, fallbacks):
        if isinstance(result, Exception):
            logger.exception("Dashboard metric '%s' failed", name, exc_info=result)
            resolved_metrics.append(fallback)
            continue
        resolved_metrics.append(result)

    summary, severity, surface, orientation, timeline, locations = resolved_metrics

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
    user_id = _normalize_user_id(user_id)

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
        
        return _empty_summary_stats()

    stats = result[0]
    
    # Average confidence
    
    conf_pipeline = [
        
    {"$match": { "user_id": user_id }},
    { "$unwind": "$detections"},
    { "$group": {
        "_id": None,
        "avg_confidence": { "$avg": "$detections.confidence" }
    }}
    ]
    
    conf_cursor = db["detections"].aggregate(conf_pipeline)
    conf_result = await conf_cursor.to_list(length=1)
    avg_conf = round(conf_result[0]["avg_confidence"], 4) if conf_result else 0.0

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
        average_inference_ms=round(stats["avg_inference_ms"] or 0.0, 2),
        most_cracked_image=most_cracked,
    )


# Severity Distribution

async def _get_severity_distribution(
    user_id: ObjectId,
    db: AsyncIOMotorDatabase,
    limit: int = 8,
) -> SeverityDistribution:
    """
    Counts crack instances grouped by severity level.
    Unknown severity values are grouped under 'unknown'.
    """
    user_id = _normalize_user_id(user_id)

    pipeline = [
        
        {"$match": {"user_id": user_id}},
        {"$unwind": "$detections"},
        
        {"$unwind": {"path": "$detections", "preserveNullAndEmpty": False}},
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
        
        raw = r["_id"]

        if raw is None :

            continue 

        key = raw.value if hasattr( raw ,"value") else str( raw).lower()
        
        if key in counts:
            
            counts[key] += r["count"]
        else:
            
            counts["unknown"] += counts.get("unknown", 0) + r["count"] 
        
    total =  sum( counts.values() )

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
    Normalizes surface_type to lowercase string before grouping
    for mongomock compatibility.
    """
    
    user_id = _normalize_user_id(user_id)

    pipeline = [
        
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$surface_type",
            "cracks": {"$sum": "$total_cracks"},
            "images": {"$sum": 1},
        }},
        {"$sort": {"cracks": -1}}
    ]

    cursor = db["detections"].aggregate(pipeline)
    results = await cursor.to_list(length=None)

    # Normalize unknown surface types to 'other'
    normalized: dict[str, dict] = {}

    for r in results:

        raw = r["_id"]

        if raw is None:

            key = "others"

        else:
            
            # Normalize surface_type to lowercase string before grouping
            raw_str = raw.value if hasattr(raw, "value") else str(raw).lower().strip()
            key = raw_str if raw_str in KNOWN_SURFACES else "others"    

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
    user_id = _normalize_user_id(user_id)

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
    user_id = _normalize_user_id(user_id)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    since = today - timedelta(days=(days - 1))

    cursor = db["detections"].find(
        {
            "user_id":     user_id,
            "detected_at": {"$gte": since},
        },
        {"detected_at": 1, "total_cracks": 1, "_id": 0},
    )
    documents = await cursor.to_list(length=None)

    # Build a dict keyed by date string
    by_date: dict[str, dict[str, int]] = {}
    
    for doc in documents:
        
        date_str = doc["detected_at"].strftime("%Y-%m-%d")
        
        if date_str not in by_date:
            
            by_date[date_str] = {"total_cracks": 0, "total_images": 0}
            
        by_date[date_str]["total_cracks"] += doc["total_cracks"]
        by_date[date_str]["total_images"] += 1

    # Fill all days in the range — no gaps in AreaChart
    data = []
    for i in range(days):
        
        day = (since + timedelta(days=i)).strftime("%Y-%m-%d")
        entry = by_date.get(day, {"total_cracks": 0, "total_images": 0})
        
        data.append(TimelinePoint(
            date=day,
            total_cracks=entry["total_cracks"],
            total_images=entry["total_images"],
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
    user_id = _normalize_user_id(user_id)
    
    pipeline = [
        {
            "$match": {
                "user_id": user_id,
                "location_id": {"$exists": True, "$ne": None},
            }
        },
        {
            "$group": {
                "_id": "$location_id",
                "total_cracks": {
                    "$sum": {
                        "$cond": [
                            {"$isNumber": "$total_cracks_detected"},
                            "$total_cracks_detected",
                            0,
                        ]
                    }
                },
                "total_images": {"$sum": 1},
            }
        },
        {"$sort": {"total_cracks": -1}},
        {"$limit": limit},
        {
            "$lookup": {
                "from": "locations",
                "localField": "_id",
                "foreignField": "_id",
                "as": "location_doc",
            }
        },
        {"$unwind": {"path": "$location_doc", "preserveNullAndEmptyArrays": False}},
        {
            "$project": {
                "_id": 1,
                "total_cracks": 1,
                "total_images": 1,
                "name": "$location_doc.name",
                "city": "$location_doc.city",
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


# latency inference time ms

async def _get_latency_history(user_id: ObjectId, db: AsyncIOMotorDatabase, limit: int = 20):
    """
    Returns the last 'n' inference times for latency tracking.
    """
    user_id = _normalize_user_id(user_id)
    cursor = db["images"].find(
        {"user_id": user_id, "inference_status": "completed", "inference_ms": {"$ne": None}},
        {"_id": 1, "original_filename": 1, "inference_ms": 1, "uploaded_at": 1}
    ).sort("uploaded_at", -1).limit(limit)

    images = await cursor.to_list(length=limit)
    
    # Inverted list in order to show time data crom past to present 
    latency_data = [
        {
            "id": str(img["_id"]),
            "filename": img["original_filename"],
            "latency": round(img["inference_ms"], 2),
            "timestamp": img["uploaded_at"].isoformat()
        }
        for img in reversed(images)
    ]

    return {"data": latency_data}
