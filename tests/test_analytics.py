"""
Group 6 - Analytics routes (T35-T42)
"""
from datetime import datetime, timedelta, timezone

from bson import ObjectId


async def _seed_analytics_dataset(test_db, registered_user):
    
    user_id = ObjectId(registered_user["id"])
    now = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)

    loc1_id = ObjectId()
    loc2_id = ObjectId()

    await test_db["locations"].insert_many(
        [
            {
                "_id": loc1_id,
                "user_id": user_id,
                "name": "Bridge North",
                "city": "Bogota",
                "country": "Colombia",
                "created_at": now,
                "updated_at": now,
            },
            {
                "_id": loc2_id,
                "user_id": user_id,
                "name": "Tunnel South",
                "city": "Medellin",
                "country": "Colombia",
                "created_at": now,
                "updated_at": now,
            },
        ]
    )

    image1_id = ObjectId()
    image2_id = ObjectId()
    image3_id = ObjectId()

    await test_db["images"].insert_many(
        [
            {
                "_id": image1_id,
                "user_id": user_id,
                "location_id": loc1_id,
                "original_filename": "bridge-a.jpg",
                "stored_filename": "bridge-a-stored.jpg",
                "stored_path": "/tmp/bridge-a-stored.jpg",
                "mime_type": "image/jpeg",
                "size_bytes": 2048,
                "width_px": 100,
                "height_px": 100,
                "total_cracks_detected": 3,
                "inference_status": "completed",
                "inference_ms": 10.0,
                "uploaded_at": now,
                "updated_at": now,
            },
            {
                "_id": image2_id,
                "user_id": user_id,
                "location_id": loc2_id,
                "original_filename": "tunnel-b.jpg",
                "stored_filename": "tunnel-b-stored.jpg",
                "stored_path": "/tmp/tunnel-b-stored.jpg",
                "mime_type": "image/jpeg",
                "size_bytes": 2048,
                "width_px": 100,
                "height_px": 100,
                "total_cracks_detected": 1,
                "inference_status": "completed",
                "inference_ms": 20.0,
                "uploaded_at": now - timedelta(days=1),
                "updated_at": now - timedelta(days=1),
            },
            {
                "_id": image3_id,
                "user_id": user_id,
                "location_id": loc1_id,
                "original_filename": "bridge-c.jpg",
                "stored_filename": "bridge-c-stored.jpg",
                "stored_path": "/tmp/bridge-c-stored.jpg",
                "mime_type": "image/jpeg",
                "size_bytes": 2048,
                "width_px": 100,
                "height_px": 100,
                "total_cracks_detected": 0,
                "inference_status": "completed",
                "inference_ms": 30.0,
                "uploaded_at": now - timedelta(days=2),
                "updated_at": now - timedelta(days=2),
            },
        ]
    )

    await test_db["detections"].insert_many(
        [
            {
                "_id": ObjectId(),
                "image_id": image1_id,
                "user_id": user_id,
                "filename": "bridge-a.jpg",
                "surface_type": "stone",
                "image_width": 100,
                "image_height": 100,
                "inference_ms": 10.0,
                "total_cracks": 3,
                "detections": [
                    {
                        "crack_index": 0,
                        "confidence": 0.9,
                        "bbox": [0, 0, 10, 10],
                        "mask_polygon": [[0.0, 0.0], [1.0, 1.0]],
                        "mask_area_px": 100,
                        "max_width_px": 10,
                        "max_length_px": 50,
                        "orientation": "diagonal",
                        "severity": "high",
                    },
                    {
                        "crack_index": 1,
                        "confidence": 0.5,
                        "bbox": [0, 0, 10, 10],
                        "mask_polygon": [[0.0, 0.0], [1.0, 1.0]],
                        "mask_area_px": 80,
                        "max_width_px": 5,
                        "max_length_px": 30,
                        "orientation": "horizontal",
                        "severity": "low",
                    },
                    {
                        "crack_index": 2,
                        "confidence": 0.7,
                        "bbox": [0, 0, 10, 10],
                        "mask_polygon": [[0.0, 0.0], [1.0, 1.0]],
                        "mask_area_px": 90,
                        "max_width_px": 7,
                        "max_length_px": 40,
                        "orientation": "vertical",
                        "severity": "medium",
                    },
                ],
                "detected_at": now,
            },
            {
                "_id": ObjectId(),
                "image_id": image2_id,
                "user_id": user_id,
                "filename": "tunnel-b.jpg",
                "surface_type": "asphalt",
                "image_width": 100,
                "image_height": 100,
                "inference_ms": 20.0,
                "total_cracks": 1,
                "detections": [
                    {
                        "crack_index": 0,
                        "confidence": 0.8,
                        "bbox": [0, 0, 10, 10],
                        "mask_polygon": [[0.0, 0.0], [1.0, 1.0]],
                        "mask_area_px": 110,
                        "max_width_px": 11,
                        "max_length_px": 60,
                        "orientation": "diagonal",
                        "severity": "high",
                    }
                ],
                "detected_at": now - timedelta(days=1),
            },
            {
                "_id": ObjectId(),
                "image_id": image3_id,
                "user_id": user_id,
                "filename": "bridge-c.jpg",
                "surface_type": "stone",
                "image_width": 100,
                "image_height": 100,
                "inference_ms": 30.0,
                "total_cracks": 0,
                "detections": [],
                "detected_at": now - timedelta(days=2),
            },
        ]
    )


async def test_get_analytics_summary_returns_expected_totals(
    app_client, auth_headers, test_db, registered_user
):
    await _seed_analytics_dataset(test_db, registered_user)

    r = await app_client.get("/api/v1/analytics/summary", headers=auth_headers)
    assert r.status_code == 200

    body = r.json()
    assert body["total_images_analyzed"] == 3
    assert body["total_cracks_detected"] == 4
    assert body["average_confidence"] == 0.725
    assert body["average_inference_ms"] == 20.0
    assert body["most_cracked_image"]["filename"] == "bridge-a.jpg"
    assert body["most_cracked_image"]["total_cracks"] == 3


async def test_get_analytics_severity_returns_instance_counts(
    app_client, auth_headers, test_db, registered_user
):
    await _seed_analytics_dataset(test_db, registered_user)

    r = await app_client.get("/api/v1/analytics/severity", headers=auth_headers)
    assert r.status_code == 200

    body = r.json()
    counts = {item["name"]: item["value"] for item in body["data"]}
    assert body["total_instances"] == 4
    assert counts == {"low": 1, "medium": 1, "high": 2}


async def test_get_analytics_surface_uses_detection_document_surface_type(
    app_client, auth_headers, test_db, registered_user
):
    await _seed_analytics_dataset(test_db, registered_user)

    r = await app_client.get("/api/v1/analytics/surface", headers=auth_headers)
    assert r.status_code == 200

    body = r.json()
    rows = {item["surface"]: item for item in body["data"]}
    assert rows["stone"]["cracks"] == 3
    assert rows["stone"]["images"] == 2
    assert rows["asphalt"]["cracks"] == 1
    assert rows["asphalt"]["images"] == 1


async def test_get_analytics_orientation_returns_all_axes(
    app_client, auth_headers, test_db, registered_user
):
    await _seed_analytics_dataset(test_db, registered_user)

    r = await app_client.get("/api/v1/analytics/orientation", headers=auth_headers)
    assert r.status_code == 200

    body = r.json()
    counts = {item["orientation"]: item["count"] for item in body["data"]}
    assert counts == {
        "horizontal": 1,
        "diagonal": 2,
        "vertical": 1,
        "forked": 0,
        "irregular": 0,
    }


async def test_get_analytics_timeline_returns_calendar_day_buckets(
    app_client, auth_headers, test_db, registered_user
):
    await _seed_analytics_dataset(test_db, registered_user)

    r = await app_client.get("/api/v1/analytics/timeline?days=3", headers=auth_headers)
    assert r.status_code == 200

    body = r.json()
    assert body["period_days"] == 3
    assert len(body["data"]) == 3
    assert [item["total_cracks"] for item in body["data"]] == [0, 1, 3]
    assert [item["total_images"] for item in body["data"]] == [1, 1, 1]


async def test_get_analytics_locations_aggregates_from_images_by_location(
    app_client, auth_headers, test_db, registered_user
):
    await _seed_analytics_dataset(test_db, registered_user)

    r = await app_client.get("/api/v1/analytics/locations", headers=auth_headers)
    assert r.status_code == 200

    body = r.json()
    assert len(body["data"]) == 2
    assert body["data"][0]["name"] == "Bridge North"
    assert body["data"][0]["total_cracks"] == 3
    assert body["data"][0]["total_images"] == 2
    assert body["data"][1]["name"] == "Tunnel South"
    assert body["data"][1]["total_cracks"] == 1
    assert body["data"][1]["total_images"] == 1


async def test_get_analytics_latency_returns_oldest_to_newest_order(
    app_client, auth_headers, test_db, registered_user
):
    await _seed_analytics_dataset(test_db, registered_user)

    r = await app_client.get("/api/v1/analytics/latency?limit=3", headers=auth_headers)
    assert r.status_code == 200

    body = r.json()
    assert [item["filename"] for item in body["data"]] == [
        "bridge-c.jpg",
        "tunnel-b.jpg",
        "bridge-a.jpg",
    ]
    assert [item["latency"] for item in body["data"]] == [30.0, 20.0, 10.0]


async def test_get_analytics_dashboard_combines_all_metric_sections(
    app_client, auth_headers, test_db, registered_user
):
    await _seed_analytics_dataset(test_db, registered_user)

    r = await app_client.get(
        "/api/v1/analytics/dashboard?timeline_days=3",
        headers=auth_headers,
    )
    assert r.status_code == 200

    body = r.json()
    assert body["summary"]["total_cracks_detected"] == 4
    assert body["severity"]["total_instances"] == 4
    assert body["surface"]["data"][0]["surface"] == "stone"
    assert body["orientation"]["data"][1]["count"] == 2
    assert len(body["timeline"]["data"]) == 3
    assert body["locations"]["data"][0]["name"] == "Bridge North"
