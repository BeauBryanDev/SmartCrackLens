from pydantic import BaseModel, Field
from typing import Optional


# Summary stats — top stat cards

class SummaryStats(BaseModel):
    """
    Global summary counters for the current user.
    Displayed as stat cards at the top of the dashboard.
    """
    total_images_analyzed: int = Field(..., description="Total images uploaded and analyzed")
    total_cracks_detected: int = Field(..., description="Sum of all crack instances across all detections")
    average_confidence:    float = Field(..., description="Average confidence score across all crack instances")
    average_inference_ms:  float = Field(..., description="Average model inference time in milliseconds")
    most_cracked_image: Optional[dict] = Field(
        default=None,
        description="Image document with the highest total_cracks_detected"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_images_analyzed": 42,
                "total_cracks_detected": 187,
                "average_confidence":    0.812,
                "average_inference_ms":  118.4,
                "most_cracked_image": {
                    "image_id":        "661f1e2b3f4a5c6d7e8f9a0b",
                    "filename":        "wall_photo.jpg",
                    "total_cracks":    9,
                    "uploaded_at":     "2026-04-02T01:03:52Z",
                }
            }
        }
    }


# Severity distribution — PieChart

class SeveritySlice(BaseModel):
    """Single slice of the severity PieChart."""
    name:  str = Field(..., description="Severity label: low | medium | high")
    value: int = Field(..., description="Total crack instances with this severity")
    fill:  str = Field(..., description="Hex color for Recharts fill prop")


class SeverityDistribution(BaseModel):
    """
    Severity distribution data ready for Recharts PieChart.

    Frontend usage:
        <PieChart>
          <Pie data={severity.data} dataKey="value" nameKey="name" />
        </PieChart>
    """
    data: list[SeveritySlice]
    total_instances: int = Field(..., description="Total crack instances counted")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_instances": 187,
                "data": [
                    {"name": "low",    "value": 54,  "fill": "#00FF9C"},
                    {"name": "medium", "value": 89,  "fill": "#FFB800"},
                    {"name": "high",   "value": 44,  "fill": "#FF3A3A"},
                ]
            }
        }
    }
    
    
# Surface type distribution — BarChart

class SurfaceBar(BaseModel):
    """Single bar of the surface type BarChart."""
    surface: str = Field(..., description="Surface type label")
    cracks:  int = Field(..., description="Total crack instances detected on this surface")
    images:  int = Field(..., description="Total images analyzed for this surface")


class SurfaceDistribution(BaseModel):
    """
    Surface type distribution ready for Recharts BarChart.

    Frontend usage:
        <BarChart data={surface.data}>
          <Bar dataKey="cracks" />
          <Bar dataKey="images" />
        </BarChart>
    """
    data: list[SurfaceBar]

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {"surface": "asphalt",   "cracks": 72, "images": 14},
                    {"surface": "brickwall", "cracks": 45, "images": 9},
                    {"surface": "other",     "cracks": 12, "images": 3},
                ]
            }
        }
    }
    
# Orientation distribution — RadarChart

class OrientationPoint(BaseModel):
    """Single point of the orientation RadarChart."""
    orientation: str = Field(..., description="Orientation label")
    count:       int = Field(..., description="Total crack instances with this orientation")


class OrientationDistribution(BaseModel):
    """
    Orientation distribution ready for Recharts RadarChart.

    Frontend usage:
        <RadarChart data={orientation.data}>
          <Radar dataKey="count" />
        </RadarChart>
    """
    data: list[OrientationPoint]

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {"orientation": "diagonal",   "count": 89},
                    {"orientation": "horizontal", "count": 34},
                    {"orientation": "vertical",   "count": 28},
                    {"orientation": "forked",     "count": 21},
                    {"orientation": "irregular",  "count": 15},
                ]
            }
        }
    }


# Detections timeline — AreaChart

class TimelinePoint(BaseModel):
    """Single point on the timeline AreaChart."""
    date:         str = Field(..., description="ISO date string YYYY-MM-DD")
    total_cracks: int = Field(..., description="Total crack instances detected on this date")
    total_images: int = Field(..., description="Total images analyzed on this date")


class DetectionsTimeline(BaseModel):
    """
    Daily timeline of detections ready for Recharts AreaChart.

    Frontend usage:
        <AreaChart data={timeline.data}>
          <Area dataKey="total_cracks" />
          <Area dataKey="total_images" />
        </AreaChart>
    """
    data:       list[TimelinePoint]
    period_days: int = Field(..., description="Number of days covered by this timeline")

    model_config = {
        "json_schema_extra": {
            "example": {
                "period_days": 30,
                "data": [
                    {"date": "2026-03-01", "total_cracks": 12, "total_images": 3},
                    {"date": "2026-03-02", "total_cracks": 8,  "total_images": 2},
                ]
            }
        }
    }


# Top locations — horizontal BarChart

class LocationBar(BaseModel):
    """Single bar of the top locations BarChart."""
    location_id:   str = Field(..., description="MongoDB ObjectId as string")
    name:          str = Field(..., description="Location name")
    city:          str = Field(..., description="Location city")
    total_cracks:  int = Field(..., description="Total crack instances detected at this location")
    total_images:  int = Field(..., description="Total images analyzed at this location")


class TopLocations(BaseModel):
    """
    Top locations ranked by total cracks detected.
    Ready for Recharts horizontal BarChart.

    Frontend usage:
        <BarChart data={locations.data} layout="vertical">
          <Bar dataKey="total_cracks" />
        </BarChart>
    """
    data: list[LocationBar]

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": [
                    {"location_id": "661f...", "name": "Edificio D1",  "city": "Bogota",   "total_cracks": 45, "total_images": 8},
                    {"location_id": "661f...", "name": "Puente Norte", "city": "Medellin", "total_cracks": 32, "total_images": 5},
                ]
            }
        }
    }
    

# Full dashboard response — single endpoint returns everything

class DashboardResponse(BaseModel):
    """
    Complete dashboard payload returned by GET /api/v1/analytics/dashboard
    One single request loads all the data the frontend needs.
    """
    summary:     SummaryStats
    severity:    SeverityDistribution
    surface:     SurfaceDistribution
    orientation: OrientationDistribution
    timeline:    DetectionsTimeline
    locations:   TopLocations