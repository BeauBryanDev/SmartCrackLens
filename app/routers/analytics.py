from fastapi import APIRouter, Depends, status
from bson import ObjectId

from app.routers.dependencies import DBAndUser
from app.schemas.analytics import (
    DashboardResponse,
    DetectionsTimeline,
    OrientationDistribution,
    SeverityDistribution,
    SummaryStats,
    SurfaceDistribution,
    TopLocations,
)
from app.services import analytics_service


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


# GET /api/v1/analytics/dashboard

@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Full dashboard payload — all metrics in one request",
)
async def get_dashboard(
    timeline_days: int = 30,
    deps: DBAndUser = Depends(DBAndUser),
) -> DashboardResponse:
    """
    Returns all dashboard metrics in a single response.

    - Requires a valid JWT.
    - All queries run in parallel via asyncio.gather.
    - timeline_days controls the AreaChart window: ?timeline_days=30
    - Scoped to the authenticated user — never returns other users data.
    """
    return await analytics_service.get_dashboard(
        
        current_user=deps.current_user,
        db=deps.db,
        timeline_days=timeline_days,
    )
    
    
# GET /api/v1/analytics/summary-stats

@router.get(
    "/summary",
    response_model=SummaryStats,
    status_code=status.HTTP_200_OK,
    summary="Summary stat cards",
)
async def get_summary(
    deps: DBAndUser = Depends(DBAndUser),
) -> SummaryStats:
    """Returns global summary counters for the stat cards."""
    
    from app.services.analytics_service import _get_summary_stats
    
    return await _get_summary_stats(deps.current_user["_id"], deps.db)



# GET /api/v1/analytics/severity-distribution

@router.get(
    "/severity",
    response_model=SeverityDistribution,
    status_code=status.HTTP_200_OK,
    summary="Severity distribution — PieChart data",
)
async def get_severity(
    limit: int = 8,
    deps: DBAndUser = Depends(DBAndUser),
) -> SeverityDistribution:
    """Returns crack instance counts grouped by severity for PieChart."""
    
    from app.services.analytics_service import _get_severity_distribution
    
    return await _get_severity_distribution(deps.current_user["_id"], deps.db, limit)


# GET /api/v1/analytics/surface-distribution

@router.get(
    "/surface",
    response_model=SurfaceDistribution,
    status_code=status.HTTP_200_OK,
    summary="Surface type distribution — BarChart data",
)
async def get_surface(
    deps: DBAndUser = Depends(DBAndUser),
) -> SurfaceDistribution:
    
    """Returns crack counts grouped by surface type for BarChart."""
    
    from app.services.analytics_service import _get_surface_distribution
    
    return await _get_surface_distribution(deps.current_user["_id"], deps.db)


# GET /api/v1/analytics/orientation-distribution

@router.get(
    "/orientation",
    response_model=OrientationDistribution,
    status_code=status.HTTP_200_OK,
    summary="Orientation distribution — RadarChart data",
)
async def get_orientation(
    deps: DBAndUser = Depends(DBAndUser),
) -> OrientationDistribution:
    
    """Returns crack counts grouped by orientation for RadarChart."""
    from app.services.analytics_service import _get_orientation_distribution
    
    return await _get_orientation_distribution(deps.current_user["_id"], deps.db)


# GET /api/v1/analytics/detections-timeline

@router.get(
    "/timeline",
    response_model=DetectionsTimeline,
    status_code=status.HTTP_200_OK,
    summary="Detections timeline — AreaChart data",
)
async def get_timeline(
    days: int = 30,
    deps: DBAndUser = Depends(DBAndUser),
) -> DetectionsTimeline:
    """
    Returns daily detection counts for the AreaChart.
    Adjust the window with ?days=7 or ?days=90.
    """
    from app.services.analytics_service import _get_detections_timeline
    
    return await _get_detections_timeline(deps.current_user["_id"], deps.db, days)


# GET /api/v1/analytics/top-locations

@router.get(
    "/locations",
    response_model=TopLocations,
    status_code=status.HTTP_200_OK,
    summary="Top locations — BarChart data",
)
async def get_top_locations(
    limit: int = 8,
    deps: DBAndUser = Depends(DBAndUser),
) -> TopLocations:
    """Returns top locations ranked by total cracks for horizontal BarChart."""
    
    from app.services.analytics_service import _get_top_locations
    
    return await _get_top_locations(ObjectId(deps.current_user["_id"] ), deps.db, limit) 


# GET /api/v1/analytics/latency

@router.get(
    "/latency",
    response_model=dict, 
    status_code=status.HTTP_200_OK,
    summary="Model latency history — LineChart data",
)
async def get_latency(
    limit: int = 20,
    deps: DBAndUser = Depends(DBAndUser),
) -> dict:
    """
    Returns the last inference times (ms) to plot a latency/performance chart.
    Useful to monitor ONNX model speed on the current hardware.
    """
    from app.services.analytics_service import _get_latency_history
    
    return await _get_latency_history(deps.current_user["_id"], deps.db, limit)
