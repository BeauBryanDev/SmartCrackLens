from fastapi import APIRouter, Depends, status

from app.routers.dependencies import DBUserAndSession
from app.services import images_service


router = APIRouter(prefix="/api/v1/inference", tags=["inference"])


# POST /api/v1/inference/reanalyze/{image_id}

@router.post(
    "/reanalyze/{image_id}",
    status_code=status.HTTP_200_OK,
    summary="Re-run crack detection on an existing image",
) # R-running inference on an existing image
async def reanalyze_image(
    image_id: str,
    deps: DBUserAndSession = Depends(DBUserAndSession),
) -> dict:
    """
    Re-runs the ONNX inference pipeline on an image that was
    previously uploaded but whose inference status is pending or failed.

    Use cases:
        - Inference failed on the original upload due to a server error.
        - The user deleted the detection record and wants to re-analyze.
        - A new model version was deployed and the user wants fresh results.

    - Requires a valid JWT.
    - Users can only re-analyze their own images.
    - Returns the full updated detection result.
    - Replaces the existing DetectionDocument if one exists.
    """
    return await images_service.reanalyze_image(
        
        image_id=image_id,
        current_user=deps.current_user,
        db=deps.db,
        session=deps.session,
    )
    
    