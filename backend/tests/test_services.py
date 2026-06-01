import uuid


async def test_list_services_empty(client):
    r = await client.get("/api/v1/services")
    assert r.status_code == 200
    assert r.json() == []


async def test_create_service(client):
    r = await client.post("/api/v1/services", json={"name": "My API", "url": "https://example.com"})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "My API"
    assert data["url"] == "https://example.com"
    assert data["status"] == "UNKNOWN"
    assert data["is_active"] is True


async def test_create_service_defaults(client):
    r = await client.post("/api/v1/services", json={"name": "X", "url": "https://x.com"})
    assert r.status_code == 201
    data = r.json()
    assert data["check_interval"] == 60
    assert data["timeout"] == 10
    assert data["failure_threshold"] == 2
    assert data["latency_threshold_ms"] == 2000
    assert data["incident_severity"] == "CRITICAL"


async def test_viewer_cannot_create_service(viewer_client):
    r = await viewer_client.post("/api/v1/services", json={"name": "X", "url": "https://x.com"})
    assert r.status_code == 403


async def test_list_services_returns_created(client):
    await client.post("/api/v1/services", json={"name": "A", "url": "https://a.com"})
    await client.post("/api/v1/services", json={"name": "B", "url": "https://b.com"})
    r = await client.get("/api/v1/services")
    assert r.status_code == 200
    assert len(r.json()) == 2


async def test_get_service(client):
    create_r = await client.post("/api/v1/services", json={"name": "Test", "url": "https://test.com"})
    svc_id = create_r.json()["id"]
    r = await client.get(f"/api/v1/services/{svc_id}")
    assert r.status_code == 200
    assert r.json()["id"] == svc_id


async def test_get_service_not_found(client):
    r = await client.get(f"/api/v1/services/{uuid.uuid4()}")
    assert r.status_code == 404


async def test_update_service_name(client):
    create_r = await client.post("/api/v1/services", json={"name": "Old", "url": "https://old.com"})
    svc_id = create_r.json()["id"]
    r = await client.patch(f"/api/v1/services/{svc_id}", json={"name": "New"})
    assert r.status_code == 200
    assert r.json()["name"] == "New"
    assert r.json()["url"] == "https://old.com"


async def test_update_service_not_found(client):
    r = await client.patch(f"/api/v1/services/{uuid.uuid4()}", json={"name": "X"})
    assert r.status_code == 404


async def test_viewer_cannot_update_service(viewer_client, db):
    from app.services.models import MonitoredService

    svc = MonitoredService(name="Test", url="https://test.com")
    db.add(svc)
    await db.commit()
    r = await viewer_client.patch(f"/api/v1/services/{svc.id}", json={"name": "Hacked"})
    assert r.status_code == 403


async def test_delete_service(client):
    create_r = await client.post("/api/v1/services", json={"name": "ToDelete", "url": "https://del.com"})
    svc_id = create_r.json()["id"]
    r = await client.delete(f"/api/v1/services/{svc_id}")
    assert r.status_code == 204
    r = await client.get(f"/api/v1/services/{svc_id}")
    assert r.status_code == 404


async def test_delete_service_not_found(client):
    r = await client.delete(f"/api/v1/services/{uuid.uuid4()}")
    assert r.status_code == 404


async def test_viewer_cannot_delete_service(viewer_client, db):
    from app.services.models import MonitoredService

    svc = MonitoredService(name="Test", url="https://test.com")
    db.add(svc)
    await db.commit()
    r = await viewer_client.delete(f"/api/v1/services/{svc.id}")
    assert r.status_code == 403
