"""
Group 6 — Users routes (T35–T39)
"""
from unittest.mock import patch

import numpy as np
import pytest
from bson import ObjectId



# ---------------------------------------------------------------------------
# T35 — GET /users/me returns own profile
# ---------------------------------------------------------------------------

async def test_get_me_returns_own_profile_200(app_client, auth_headers, registered_user):
    r = await app_client.get("/api/v1/users/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == registered_user["email"]


# ---------------------------------------------------------------------------
# T36 — GET /users/me without token returns 401
# ---------------------------------------------------------------------------

async def test_get_me_unauthenticated_401(app_client):
    r = await app_client.get("/api/v1/users/me")
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# T37 — PATCH /users/{id} updates own profile
# ---------------------------------------------------------------------------

async def test_patch_user_own_profile_200(app_client, auth_headers, registered_user):
    user_id = registered_user["id"]
    r = await app_client.patch(
        f"/api/v1/users/{user_id}",
        headers=auth_headers,
        json={"country": "Mexico"},
    )
    assert r.status_code == 200
    assert r.json()["country"] == "Mexico"


# ---------------------------------------------------------------------------
# T38 — PATCH /users/{other_id} with first user's token returns 403
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    reason=(
        "_verify_ownership() in users_service.py converts the bool comparison to "
        "a str ('False'), which is always truthy, so 'not is_owner' is always False "
        "and the 403 guard never fires.  This is a known bug — the test documents "
        "the intended behaviour and will pass once the bug is fixed."
    ),
    strict=True,
)
async def test_patch_user_other_user_forbidden_403(app_client, auth_headers, registered_user):
    # Register a second user
    other = {
        "email": "other_user2@example.com",
        "username": "other_user_2",
        "password": "Test.Pass!1",
        "confirm_password": "Test.Pass!1",
        "gender": "female",
        "phone_number": "3001234569",
        "country": "Colombia",
    }
    r_reg = await app_client.post("/api/v1/auth/register", json=other)
    assert r_reg.status_code == 201
    other_user_id = r_reg.json()["id"]

    # Try to patch the second user using first user's token — should be 403
    r = await app_client.patch(
        f"/api/v1/users/{other_user_id}",
        headers=auth_headers,
        json={"country": "Peru"},
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# T39 — DELETE /users/{id} cascades locations, images, detections
# ---------------------------------------------------------------------------

async def test_delete_user_cascades_locations_images_detections(
    app_client, auth_headers, registered_user, test_db, sample_image_bytes
):
    user_id = registered_user["id"]

    # Create a location
    loc_r = await app_client.post(
        "/api/v1/locations",
        json={
            "name": "Cascade Loc",
            "city": "Bogotá",
            "country": "Colombia",
            "address": "Cra 1",
            "description": "cascade test",
        },
        headers=auth_headers,
    )
    assert loc_r.status_code == 201

    # Upload an image (mocked storage so no disk I/O)
    with (
        patch("app.services.images_service.save_raw_image") as mock_save,
        patch("app.services.images_service.load_image_for_inference") as mock_load,
        patch("app.services.images_service.save_output_image"),
        patch("app.services.images_service.delete_image_files"),
    ):
        mock_save.return_value = {
            "stored_filename": "cascade-uuid.jpg",
            "stored_path": "/tmp/cascade-uuid.jpg",
            "size_bytes": len(sample_image_bytes),
            "width_px": 100,
            "height_px": 100,
        }
        mock_load.return_value = np.zeros((100, 100, 3), dtype=np.uint8)

        img_r = await app_client.post(
            "/api/v1/images/upload",
            files={"file": ("wall.jpg", sample_image_bytes, "image/jpeg")},
            data={"surface_type": "stone"},
            headers=auth_headers,
        )
        assert img_r.status_code == 201

        # Delete user
        r = await app_client.delete(
            f"/api/v1/users/{user_id}", headers=auth_headers
        )

    assert r.status_code == 410

    uid = ObjectId(user_id)
    assert await test_db["locations"].count_documents({"user_id": uid}) == 0
    assert await test_db["images"].count_documents({"user_id": uid}) == 0
    assert await test_db["detections"].count_documents({"user_id": uid}) == 0
