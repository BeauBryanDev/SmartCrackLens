"""
Group 9 — Detections routes (T50–T54)
"""
from unittest.mock import patch

import numpy as np
import pytest
from bson import ObjectId


# ---------------------------------------------------------------------------
# Helper — upload an image and return (image_id, detection_id)
# ---------------------------------------------------------------------------

async def _upload_image(app_client, auth_headers, sample_image_bytes) -> tuple[str, str | None]:
    with (
        patch("app.services.images_service.save_raw_image") as mock_save,
        patch("app.services.images_service.load_image_for_inference") as mock_load,
        patch("app.services.images_service.save_output_image"),
        patch("app.services.images_service.delete_image_files"),
    ):
        mock_save.return_value = {
            "stored_filename": "det-uuid.jpg",
            "stored_path": "/tmp/det-uuid.jpg",
            "size_bytes": len(sample_image_bytes),
            "width_px": 100,
            "height_px": 100,
        }
        mock_load.return_value = np.zeros((100, 100, 3), dtype=np.uint8)

        files = {"file": ("wall.jpg", sample_image_bytes, "image/jpeg")}
        r = await app_client.post(
            "/api/v1/images/upload",
            files=files,
            data={"surface_type": "stone"},
            headers=auth_headers,
        )
    assert r.status_code == 201
    body = r.json()
    image_id = body["image"]["id"]
    detection_id = body["detection"].get("_id")
    return image_id, detection_id


# ---------------------------------------------------------------------------
# T50 — DELETE detection resets image inference_status to "pending"
# ---------------------------------------------------------------------------

async def test_delete_detection_resets_image_to_pending(
    app_client, auth_headers, test_db, sample_image_bytes
):
    image_id, detection_id = await _upload_image(app_client, auth_headers, sample_image_bytes)
    assert detection_id is not None, "No detection was created"

    r = await app_client.delete(
        f"/api/v1/detections/{detection_id}", headers=auth_headers
    )
    assert r.status_code == 410

    img_doc = await test_db["images"].find_one({"_id": ObjectId(image_id)})
    assert img_doc is not None
    assert img_doc["inference_status"] == "pending"


# ---------------------------------------------------------------------------
# T51 — GET /detections?severity=high filters correctly
# ---------------------------------------------------------------------------

async def test_get_detections_filter_by_severity(
    app_client, auth_headers, test_db, registered_user, sample_image_bytes
):
    # Inject a detection with highest_severity-relevant data directly into DB
    from datetime import datetime, timezone
    user_id = ObjectId(registered_user["id"])

    # Insert a fake image doc
    img_result = await test_db["images"].insert_one({
        "user_id": user_id,
        "original_filename": "sev_test.jpg",
        "stored_filename": "sev-uuid.jpg",
        "stored_path": "/tmp/sev-uuid.jpg",
        "mime_type": "image/jpeg",
        "size_bytes": 1024,
        "width_px": 100,
        "height_px": 100,
        "total_cracks_detected": 1,
        "inference_status": "completed",
        "inference_ms": 10.0,
        "uploaded_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })
    img_id = img_result.inserted_id

    # Insert a detection doc with a HIGH-severity crack
    await test_db["detections"].insert_one({
        "image_id": img_id,
        "user_id": user_id,
        "filename": "sev_test.jpg",
        "surface_type": "stone",
        "image_width": 100,
        "image_height": 100,
        "inference_ms": 10.0,
        "total_cracks": 1,
        "detections": [{
            "crack_index": 1,
            "confidence": 0.90,
            "bbox": [0, 0, 100, 100],
            "mask_polygon": [[0.0, 0.0], [1.0, 1.0]],
            "mask_area_px": 20000,
            "max_width_px": 80,
            "max_length_px": 200,
            "orientation": "diagonal",
            "severity": "high",
        }],
        "detected_at": datetime.now(timezone.utc),
    })

    r = await app_client.get(
        "/api/v1/detections?severity=high", headers=auth_headers
    )
    assert r.status_code == 200
    results = r.json()["results"]
    assert len(results) >= 1
    for det in results:
        assert det["highest_severity"] == "high"


# ---------------------------------------------------------------------------
# T52 — GET /detections/image/{image_id} returns the right detection
# ---------------------------------------------------------------------------

async def test_get_detection_by_image_id(
    app_client, auth_headers, sample_image_bytes
):
    image_id, _ = await _upload_image(app_client, auth_headers, sample_image_bytes)

    r = await app_client.get(
        f"/api/v1/detections/image/{image_id}", headers=auth_headers
    )
    assert r.status_code == 200
    body = r.json()
    # The detection links back to this image
    assert body["image_id"] == image_id


# ---------------------------------------------------------------------------
# T53 — GET /detections/surface-types is public and returns known types
# ---------------------------------------------------------------------------

async def test_get_surface_types_public_200(app_client):
    r = await app_client.get("/api/v1/detections/surface-types")
    assert r.status_code == 200
    types = r.json()["surface_types"]
    assert "stone" in types
    assert "brickwall" in types


# ---------------------------------------------------------------------------
# T54 — GET /detections/location/{id} returns results list
# ---------------------------------------------------------------------------

async def test_get_detections_by_location(
    app_client, auth_headers, created_location
):
    location_id = created_location["id"]
    r = await app_client.get(
        f"/api/v1/detections/location/{location_id}", headers=auth_headers
    )
    assert r.status_code == 200
    assert "results" in r.json()
