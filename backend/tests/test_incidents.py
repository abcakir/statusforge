import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.incidents.models import IncidentSeverity, IncidentStatus
from app.incidents.service import create_incident


async def _create_service(client) -> str:
    r = await client.post("/api/v1/services", json={"name": "Test Service", "url": "https://test.com"})
    assert r.status_code == 201
    return r.json()["id"]


async def test_list_incidents_empty(client):
    r = await client.get("/api/v1/incidents")
    assert r.status_code == 200
    assert r.json() == []


async def test_get_incident_not_found(client):
    r = await client.get(f"/api/v1/incidents/{uuid.uuid4()}")
    assert r.status_code == 404


async def test_create_and_list_incident(client, db: AsyncSession):
    svc_id = await _create_service(client)
    incident = await create_incident(db, uuid.UUID(svc_id), "Service is DOWN", IncidentSeverity.CRITICAL)

    r = await client.get("/api/v1/incidents")
    assert r.status_code == 200
    ids = [i["id"] for i in r.json()]
    assert str(incident.id) in ids


async def test_get_incident(client, db: AsyncSession):
    svc_id = await _create_service(client)
    incident = await create_incident(db, uuid.UUID(svc_id), "Service is DOWN", IncidentSeverity.HIGH)

    r = await client.get(f"/api/v1/incidents/{incident.id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == str(incident.id)
    assert data["status"] == IncidentStatus.OPEN
    assert data["severity"] == IncidentSeverity.HIGH


async def test_acknowledge_incident(client, db: AsyncSession):
    svc_id = await _create_service(client)
    incident = await create_incident(db, uuid.UUID(svc_id), "Service is DOWN", IncidentSeverity.CRITICAL)

    r = await client.post(f"/api/v1/incidents/{incident.id}/acknowledge")
    assert r.status_code == 200
    assert r.json()["status"] == IncidentStatus.ACKNOWLEDGED


async def test_resolve_incident(client, db: AsyncSession):
    svc_id = await _create_service(client)
    incident = await create_incident(db, uuid.UUID(svc_id), "Service is DOWN", IncidentSeverity.CRITICAL)

    r = await client.post(f"/api/v1/incidents/{incident.id}/resolve")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == IncidentStatus.RESOLVED
    assert data["resolved_at"] is not None


async def test_resolve_sets_resolved_at(client, db: AsyncSession):
    svc_id = await _create_service(client)
    incident = await create_incident(db, uuid.UUID(svc_id), "Service is DOWN", IncidentSeverity.LOW)

    assert incident.resolved_at is None
    r = await client.post(f"/api/v1/incidents/{incident.id}/resolve")
    assert r.json()["resolved_at"] is not None


async def test_add_comment(client, db: AsyncSession):
    svc_id = await _create_service(client)
    incident = await create_incident(db, uuid.UUID(svc_id), "Service is DOWN", IncidentSeverity.CRITICAL)

    r = await client.post(
        f"/api/v1/incidents/{incident.id}/comment",
        json={"message": "Looking into it"},
    )
    assert r.status_code == 201
    assert r.json()["message"] == "Looking into it"
    assert r.json()["event_type"] == "COMMENT"


async def test_get_incident_events(client, db: AsyncSession):
    svc_id = await _create_service(client)
    incident = await create_incident(db, uuid.UUID(svc_id), "Service is DOWN", IncidentSeverity.CRITICAL)

    r = await client.get(f"/api/v1/incidents/{incident.id}/events")
    assert r.status_code == 200
    events = r.json()
    assert len(events) == 1
    assert events[0]["event_type"] == "CREATED"


async def test_viewer_cannot_acknowledge(viewer_client, db: AsyncSession):
    from app.services.models import MonitoredService

    svc = MonitoredService(name="Test", url="https://test.com")
    db.add(svc)
    await db.commit()
    await db.refresh(svc)
    incident = await create_incident(db, svc.id, "Service is DOWN", IncidentSeverity.CRITICAL)

    r = await viewer_client.post(f"/api/v1/incidents/{incident.id}/acknowledge")
    assert r.status_code == 403


async def test_acknowledge_not_found(client):
    r = await client.post(f"/api/v1/incidents/{uuid.uuid4()}/acknowledge")
    assert r.status_code == 404
