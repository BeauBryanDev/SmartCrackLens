
import io
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

import app.core.database as db_module
import app.core.session as session_module
from app.core.database import get_database
from app.main import app
from app.routers.dependencies import get_db, get_session


# Low-level fixtures

@pytest.fixture
def mock_onnx_session():
    """ONNX InferenceSession mock.

    Returns all-zeros for output0 [1,37,8400] and output1 [1,32,160,160]
    so the confidence filter discards every candidate → no detections.
    The mock also exposes get_inputs()[0].name / .shape for health checks
    and for the inference input-name look-up.
    """
    session = MagicMock()

    session.run.return_value = [
        np.zeros((1, 37, 8400), dtype=np.float32),
        np.zeros((1, 32, 160, 160), dtype=np.float32),
    ]
    mock_input = MagicMock()
    mock_input.name = "images"
    mock_input.shape = [1, 3, 640, 640]
    session.get_inputs.return_value = [mock_input]
    return session


@pytest_asyncio.fixture
async def test_db():
    """Isolated in-memory MongoDB database (function-scoped → fresh per test)."""
    client = AsyncMongoMockClient()
    db = client["crackdb_test"]
    yield db
    for coll in await db.list_collection_names():

        await db.drop_collection(coll)


@pytest.fixture
def sample_image_bytes():
    """100×100 white JPEG bytes — valid image for upload tests."""
    img = np.full((100, 100, 3), 255, dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)

    return buf.tobytes()


# App client

@pytest_asyncio.fixture
async def app_client(test_db, mock_onnx_session):
    """
    Async HTTP client wired directly to the FastAPI ASGI app.

    Sets module-level singletons so that code paths that call
    get_database() / get_onnx_session() as plain functions (e.g. health.py)
    also work without a real MongoDB or ONNX file.

    FastAPI dependency overrides cover the DI paths.
    """
    # Keep originals so we can restore after the test
    _orig_client  = db_module._client
    _orig_session = session_module._onnx_session

    # Build a mongomock client and point the module singleton at it so
    # get_database() (called directly in health.py) doesn't raise.
    mock_mongo_client = AsyncMongoMockClient()
    db_module._client  = mock_mongo_client
    session_module._onnx_session = mock_onnx_session

    # Override FastAPI DI so all routers use the *same* test_db instance
    app.dependency_overrides[get_database] = lambda: test_db
    app.dependency_overrides[get_db]       = lambda: test_db
    app.dependency_overrides[get_session]  = lambda: mock_onnx_session

    # Patch lifespan callees so startup doesn't hit real ONNX / MongoDB
    with patch("app.core.session.load_model", return_value=mock_onnx_session), \
         patch("app.core.database.connect_db", return_value=None), \
         patch("app.core.database.disconnect_db", return_value=None):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            yield client

    # Teardown
    app.dependency_overrides.clear()
    db_module._client            = _orig_client
    session_module._onnx_session = _orig_session


# Auth helpers

_REGISTER_PAYLOAD = {
    "email": "testuser@example.com",
    "username": "test_user",
    "password": "Test.Pass!1",
    "confirm_password": "Test.Pass!1",
    "gender": "male",
    "phone_number": "3001234567",
    "country": "Colombia",
}


@pytest_asyncio.fixture
async def registered_user(app_client):
    """Registers a user and returns the JSON response enriched with plain password."""
    r = await app_client.post("/api/v1/auth/register", json=_REGISTER_PAYLOAD)
    assert r.status_code == 201, r.text
    return {**r.json(), "_plain_password": _REGISTER_PAYLOAD["password"]}


@pytest_asyncio.fixture
async def auth_headers(app_client, registered_user):
    """Bearer token headers for the registered_user."""
    r = await app_client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_user["email"],
            "password": registered_user["_plain_password"],
        },
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# Location / image helpers

_LOCATION_PAYLOAD = {
    "name": "Test Bridge",
    "city": "Bogotá",
    "country": "Colombia",
    "address": "Calle 10",
    "description": "Test location",
}


@pytest_asyncio.fixture
async def created_location(app_client, auth_headers):
    """Creates a location and returns its JSON doc."""
    r = await app_client.post(
        "/api/v1/locations",
        json=_LOCATION_PAYLOAD,
        headers=auth_headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest_asyncio.fixture
async def uploaded_image(app_client, auth_headers, sample_image_bytes):
    """
    Uploads a valid image with storage functions mocked (no disk I/O).
    Returns the ImageResponse JSON dict.
    """
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
        assert r.status_code == 201, r.text
        yield r.json()["image"]
