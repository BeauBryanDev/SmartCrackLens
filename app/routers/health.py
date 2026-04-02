import time

from fastapi import APIRouter, status
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import get_settings
from app.core.database import get_database
from app.core.session import get_onnx_session
from app.core.logging import logger


settings = get_settings()
router   = APIRouter(prefix="/health", tags=["health"])

_START_TIME = time.time()


# GET /health

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Basic health check",
)
async def health() -> dict:
    """
    Basic liveness check.
    Returns HTTP 200 if the application process is running.
    Does not check dependencies — use /health/full for that.

    Used by Docker HEALTHCHECK and basic uptime monitors.
    """
    
    return {
        "status":  "ok",
        "app":     settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
    
    
# GET /health/full

@router.get(
    "/full",
    status_code=status.HTTP_200_OK,
    summary="Full health check — verifies all dependencies",
)
async def health_full() -> dict:
    """
    Full readiness check.
    Verifies that all critical dependencies are reachable:
        - MongoDB connection
        - ONNX model loaded in memory

    Returns HTTP 200 if everything is healthy.
    Returns HTTP 503 if any dependency is unavailable.

    Used by Docker depends_on healthcheck and monitoring dashboards.
    """
    checks   = {}
    healthy  = True
    uptime_s = round(time.time() - _START_TIME, 1)

    #  Check for MongoDB 
    try:
        
        db = get_database()
        
        await db.command("ping")
        
        checks["mongodb"] = {
            
            "status":   "ok",
            "database": settings.DB_NAME,
        }
        
        logger.debug("Health check: MongoDB OK")
        
    except Exception as e:
        
        healthy = False
        
        checks["mongodb"] = {
            
            "status": "unreachable",
            "detail": str(e),
        }
        
        logger.warning(f"Health check: MongoDB FAILED — {e}")

    #  Check for ONNX model 
    try:
        
        session = get_onnx_session()
        
        input_shape = session.get_inputs()[0].shape
        
        checks["onnx_model"] = {
            
            "status":      "ok",
            "model_path":  settings.MODEL_PATH,
            "input_shape": input_shape,
        }
        
        logger.debug("Health check: ONNX model OK")
        
    except Exception as e:
        
        healthy = False
        
        checks["onnx_model"] = {
            "status": "not_loaded",
            "detail": str(e),
        }
        
        logger.warning(f"Health check: ONNX model FAILED — {e}")

    response_status = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        
        "status":    "ok" if healthy else "degraded",
        "app":       settings.APP_NAME,
        "version":   settings.APP_VERSION,
        "uptime_s":  uptime_s,
        "checks":    checks,
        "http response" : response_status ,
        
    }