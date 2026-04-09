"""
Groups 1, 4, 5, 7, 8, 10:
  T01–T07  : Security / core utilities
  T22–T26  : Storage service unit tests
  T27–T34  : Auth routes
  T40–T44  : Locations routes
  T45–T49  : Images routes
  T55–T56  : Health endpoints
"""
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import cv2
import numpy as np
import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.services.storage import get_image_urls, validate_upload


# ===========================================================================
# Group 1 — Security / core (T01–T07)
# ===========================================================================

def test_hash_password_returns_bcrypt_hash():
    h = hash_password("MyPass!1")
    assert h.startswith("$2b$")
    assert len(h) == 60


def test_verify_password_correct_password():
    h = hash_password("MyPass!1")
    assert verify_password("MyPass!1", h) is True


def test_verify_password_wrong_password():
    h = hash_password("MyPass!1")
    assert verify_password("WrongPass!2", h) is False


def test_create_access_token_contains_sub():
    token = create_access_token({"sub": "abc123"})
    payload = decode_access_token(token)
    assert payload["sub"] == "abc123"


def test_decode_access_token_expired_raises_401():
    token = create_access_token({"sub": "x"}, expires_delta=timedelta(seconds=-1))
    with pytest.raises(HTTPException) as exc:
        decode_access_token(token)
    assert exc.value.status_code == 401


def test_decode_access_token_invalid_signature_raises_401():
    with pytest.raises(HTTPException) as exc:
        decode_access_token("not.a.valid.token")
    assert exc.value.status_code == 401


def test_hash_and_verify_long_password():
    # Passwords longer than 72 bytes must not crash because we SHA-256 the input
    long_pw = "A" * 200 + "!1"
    h = hash_password(long_pw)
    assert verify_password(long_pw, h) is True
    assert verify_password("A" * 199 + "!1", h) is False


# ===========================================================================
# Group 4 — Storage service unit tests (T22–T26)
# ===========================================================================

@pytest.mark.asyncio
async def test_validate_upload_rejects_oversized_file():
    mock_file = AsyncMock()
    mock_file.content_type = "image/jpeg"
    mock_file.filename = "img.jpg"
    mock_file.read = AsyncMock(return_value=b"x" * (10 * 1024 * 1024 + 1))
    with pytest.raises(HTTPException) as exc:
        await validate_upload(mock_file)
    assert exc.value.status_code == 413


@pytest.mark.asyncio
async def test_validate_upload_rejects_unsupported_mime():
    mock_file = AsyncMock()
    mock_file.content_type = "application/pdf"
    mock_file.filename = "doc.pdf"
    mock_file.read = AsyncMock(return_value=b"fake pdf content")
    with pytest.raises(HTTPException) as exc:
        await validate_upload(mock_file)
    assert exc.value.status_code == 415


@pytest.mark.asyncio
async def test_validate_upload_rejects_empty_file():
    mock_file = AsyncMock()
    mock_file.content_type = "image/jpeg"
    mock_file.filename = "empty.jpg"
    mock_file.read = AsyncMock(return_value=b"")
    with pytest.raises(HTTPException) as exc:
        await validate_upload(mock_file)
    assert exc.value.status_code == 400


def test_save_raw_image_creates_file_and_returns_metadata(sample_image_bytes):
    from app.services import storage as st

    img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    jpg_bytes = buf.tobytes()

    with tempfile.TemporaryDirectory() as tmp:
        original_dir = st.RAW_IMGS_DIR
        st.RAW_IMGS_DIR = Path(tmp)
        try:
            meta = st.save_raw_image(jpg_bytes, "test.jpg")
            assert meta["width_px"] == 100
            assert meta["height_px"] == 100
            assert Path(meta["stored_path"]).exists()
        finally:
            st.RAW_IMGS_DIR = original_dir


def test_get_image_urls_returns_static_paths():
    urls = get_image_urls("abc123.jpg")
    assert "/static/rawImgs/abc123.jpg" in urls["raw_url"]
    assert "/static/outputs/abc123_output.jpg" in urls["output_url"]


# ===========================================================================
# Group 5 — Auth routes (T27–T34)
# ===========================================================================

_REG = {
    "email": "auth_test@example.com",
    "username": "auth_user",
    "password": "Test.Pass!1",
    "confirm_password": "Test.Pass!1",
    "gender": "male",
    "phone_number": "3001234567",
    "country": "Colombia",
}


async def test_register_user_success_201(app_client):
    r = await app_client.post("/api/v1/auth/register", json=_REG)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == _REG["email"]
    assert "hashed_password" not in body


async def test_register_duplicate_email_409(app_client):
    await app_client.post("/api/v1/auth/register", json=_REG)
    r = await app_client.post("/api/v1/auth/register", json=_REG)
    assert r.status_code == 409


async def test_register_duplicate_username_409(app_client):
    payload2 = {**_REG, "email": "other_auth@example.com"}
    await app_client.post("/api/v1/auth/register", json=_REG)
    r = await app_client.post("/api/v1/auth/register", json=payload2)
    assert r.status_code == 409


async def test_register_weak_password_422(app_client):
    weak = {**_REG, "password": "password", "confirm_password": "password"}
    r = await app_client.post("/api/v1/auth/register", json=weak)
    assert r.status_code == 422


async def test_register_password_mismatch_422(app_client):
    mismatch = {**_REG, "confirm_password": "Different!1"}
    r = await app_client.post("/api/v1/auth/register", json=mismatch)
    assert r.status_code == 422


async def test_login_success_returns_token_200(app_client):
    await app_client.post("/api/v1/auth/register", json=_REG)
    r = await app_client.post(
        "/api/v1/auth/login",
        data={"username": _REG["email"], "password": _REG["password"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


async def test_login_wrong_password_401(app_client):
    await app_client.post("/api/v1/auth/register", json=_REG)
    r = await app_client.post(
        "/api/v1/auth/login",
        data={"username": _REG["email"], "password": "BadPass!99"},
    )
    assert r.status_code == 401


async def test_login_inactive_user_403(app_client, test_db):
    await app_client.post("/api/v1/auth/register", json=_REG)
    await test_db["users"].update_one(
        {"email": _REG["email"]},
        {"$set": {"is_active": False}},
    )
    r = await app_client.post(
        "/api/v1/auth/login",
        data={"username": _REG["email"], "password": _REG["password"]},
    )
    assert r.status_code == 403


# ===========================================================================
# Group 7 — Locations routes (T40–T44)
# ===========================================================================

_LOC = {
    "name": "Bridge 1",
    "city": "Bogotá",
    "country": "Colombia",
    "address": "Calle 10",
    "description": "test",
}


async def test_create_location_success_201(app_client, auth_headers):
    r = await app_client.post("/api/v1/locations", json=_LOC, headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["name"] == "Bridge 1"


async def test_get_user_locations_paginated_200(app_client, auth_headers):
    # Create 3 locations
    for i in range(3):
        await app_client.post(
            "/api/v1/locations",
            json={**_LOC, "name": f"Bridge {i}"},
            headers=auth_headers,
        )
    r = await app_client.get(
        "/api/v1/locations?page=1&page_size=2", headers=auth_headers
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    assert len(body["results"]) == 2


async def test_full_update_location_success_200(app_client, auth_headers, created_location):
    location_id = created_location["id"]
    r = await app_client.put(
        f"/api/v1/locations/{location_id}",
        headers=auth_headers,
        json={
            "name": "Bridge Updated",
            "city": "Medellín",
            "country": "Colombia",
            "address": "Cra 5",
            "description": "updated",
        },
    )
    assert r.status_code == 200
    assert r.json()["city"] == "Medellín"


async def test_update_location_other_user_forbidden_403(app_client, auth_headers, created_location, test_db):
    location_id = created_location["id"]

    # Register a second user and get their token
    other_payload = {
        "email": "other_loc@example.com",
        "username": "other_loc_user",
        "password": "Test.Pass!1",
        "confirm_password": "Test.Pass!1",
        "gender": "female",
        "phone_number": "3001234568",
        "country": "Colombia",
    }
    await app_client.post("/api/v1/auth/register", json=other_payload)
    login_r = await app_client.post(
        "/api/v1/auth/login",
        data={"username": other_payload["email"], "password": other_payload["password"]},
    )
    other_token = login_r.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    r = await app_client.put(
        f"/api/v1/locations/{location_id}",
        headers=other_headers,
        json={
            "name": "Hijack",
            "city": "Lima",
            "country": "Peru",
            "address": "Av. 1",
            "description": "unauthorized",
        },
    )
    # Service returns 404 to avoid revealing resource existence (security through obscurity)
    assert r.status_code in (403, 404)


async def test_delete_location_success_410(app_client, auth_headers, created_location):
    location_id = created_location["id"]
    r = await app_client.delete(
        f"/api/v1/locations/{location_id}", headers=auth_headers
    )
    assert r.status_code == 410
    r2 = await app_client.get(
        f"/api/v1/locations/{location_id}", headers=auth_headers
    )
    assert r2.status_code == 404


# ===========================================================================
# Group 8 — Images routes (T45–T49)
# ===========================================================================

async def test_upload_image_unsupported_format_415(app_client, auth_headers):
    files = {"file": ("doc.pdf", b"%PDF-1.4 fake", "application/pdf")}
    r = await app_client.post(
        "/api/v1/images/upload",
        files=files,
        data={"surface_type": "stone"},
        headers=auth_headers,
    )
    assert r.status_code == 415


async def test_upload_image_too_large_413(app_client, auth_headers):
    big = b"\xff\xd8\xff" + b"0" * (10 * 1024 * 1024 + 1)
    files = {"file": ("big.jpg", big, "image/jpeg")}
    r = await app_client.post(
        "/api/v1/images/upload",
        files=files,
        data={"surface_type": "stone"},
        headers=auth_headers,
    )
    assert r.status_code == 413


async def test_upload_valid_image_returns_201(app_client, auth_headers, sample_image_bytes):
    with (
        patch("app.services.images_service.save_raw_image") as mock_save,
        patch("app.services.images_service.load_image_for_inference") as mock_load,
        patch("app.services.images_service.save_output_image"),
        patch("app.services.images_service.delete_image_files"),
    ):
        mock_save.return_value = {
            "stored_filename": "test-uuid.jpg",
            "stored_path": "/tmp/test-uuid.jpg",
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
    assert "image" in body
    assert body["image"]["inference_status"] == "completed"


async def test_get_images_filter_by_inference_status(app_client, auth_headers, uploaded_image):
    r = await app_client.get(
        "/api/v1/images?inference_status=completed", headers=auth_headers
    )
    assert r.status_code == 200
    for img in r.json()["results"]:
        assert img["inference_status"] == "completed"


async def test_delete_image_removes_detection_and_file(
    app_client, auth_headers, uploaded_image, test_db
):
    image_id = uploaded_image["id"]
    with patch("app.services.images_service.delete_image_files"):
        r = await app_client.delete(
            f"/api/v1/images/{image_id}", headers=auth_headers
        )
    assert r.status_code == 410
    # Detection record should be gone
    det = await test_db["detections"].find_one({"image_id": ObjectId(image_id)})
    assert det is None


# ===========================================================================
# Group 10 — Health endpoints (T55–T56)
# ===========================================================================

async def test_health_liveness_200(app_client):
    r = await app_client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_health_full_200_when_dependencies_up(app_client):
    r = await app_client.get("/health/full")
    assert r.status_code == 200
    body = r.json()
    # status is "ok" when all checks pass
    assert body["status"] == "ok"
    assert body["checks"]["mongodb"]["status"] == "ok"
    assert body["checks"]["onnx_model"]["status"] == "ok"
