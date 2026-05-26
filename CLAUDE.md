# StatusForge — Claude Code Context

## What is this project?

StatusForge is a monitoring and incident management platform. It monitors registered services (APIs, websites, databases), detects failures automatically, creates incidents, tracks recovery, and updates dashboards in real time.

## Tech stack

### Backend
- Python 3.12
- FastAPI (async)
- Pydantic v2 + pydantic-settings
- SQLAlchemy 2.0 (async, mapped_column style)
- Alembic for migrations
- WebSockets (native FastAPI)
- Celery + Celery Beat
- httpx for outbound HTTP checks

### Auth
- Keycloak (runs in Docker)
- OAuth2 / OIDC / JWT
- JWKS-based token validation (no python-keycloak library, raw httpx calls)
- Role-based access control: ADMIN, OPERATOR, VIEWER

### Database
- PostgreSQL 16

### Cache / Realtime
- Redis 7
- DB 0: Celery broker + result backend
- DB 1: WebSocket Pub/Sub (Celery → FastAPI → Browser)
- DB 2: Cache (service status, JWKS, metrics summary)

### Frontend
- React 18 + TypeScript
- Vite
- Tailwind CSS
- TanStack Query v5
- Axios
- Recharts
- keycloak-js

### Infrastructure
- Docker Compose only (local dev)
- No Kubernetes, no cloud

## Project structure

```
statusforge/
├── backend/
│   ├── app/
│   │   ├── auth/           # JWT validation, RBAC, Keycloak client
│   │   ├── users/          # User model, router, service
│   │   ├── services/       # MonitoredService CRUD
│   │   ├── monitoring/     # HealthCheck model, HTTP probe logic
│   │   ├── incidents/      # Incident model, router, auto-create logic
│   │   ├── notifications/  # In-app notifications (bell icon, unread count)
│   │   ├── websocket/      # ConnectionManager, Redis Pub/Sub bridge
│   │   ├── metrics/        # Dashboard summary, latency series
│   │   ├── tasks/          # Celery app, beat schedule, health_check task
│   │   ├── core/           # config.py, database.py, redis.py
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/            # axios instance, typed API calls
│   │   ├── auth/           # keycloak.ts, AuthProvider
│   │   ├── components/     # StatusBadge, IncidentCard, ServiceCard, LatencyChart, NotificationBell
│   │   ├── pages/          # Dashboard, Services, Incidents, ServiceDetail, Settings
│   │   ├── hooks/          # useWebSocket, useServices, useIncidents
│   │   ├── stores/         # realtimeStore (Zustand)
│   │   └── types/          # index.ts (shared TypeScript types)
│   ├── Dockerfile
│   ├── vite.config.ts
│   └── tailwind.config.ts
├── keycloak/
│   └── realm-export.json   # Pre-configured realm, clients, roles
├── docker-compose.yml
├── .env                    # Never commit this
├── .env.example            # Commit this (no real values)
└── CLAUDE.md               # This file
```

## Environment variables

Always read from `.env` via `pydantic-settings`. Never hardcode secrets.

```env
# PostgreSQL
POSTGRES_DB=statusforge
POSTGRES_USER=statusforge
POSTGRES_PASSWORD=supersecret
DATABASE_URL=postgresql+asyncpg://statusforge:supersecret@postgres:5432/statusforge

# Redis
REDIS_URL=redis://redis:6379

# Keycloak
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_REALM=statusforge
KEYCLOAK_CLIENT_ID=statusforge-backend
KEYCLOAK_CLIENT_SECRET=change-me
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin

# Backend
SECRET_KEY=dev-secret-key-change-in-prod
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Database schema (key tables)

| Table | Purpose |
|---|---|
| `users` | Local mirror of Keycloak users. UUID = Keycloak user ID. |
| `monitored_services` | Registered services to monitor. |
| `health_checks` | Every probe result (status, latency, error). Timeseries. |
| `incidents` | Auto-created on failure, auto-resolved on recovery. |
| `incident_events` | Audit log: CREATED, ACKNOWLEDGED, RESOLVED, COMMENT. |
| `notifications` | Per-user in-app notifications. Created on incident events. |

All primary keys are UUID. All timestamps are TIMESTAMPTZ.

## Auth & RBAC pattern

```python
# Protect a route:
@router.post("/services")
async def create_service(
    data: ServiceCreate,
    user: User = Depends(require_role(Role.ADMIN, Role.OPERATOR))
):
    ...

# require_role is in app/auth/rbac.py
# get_current_user validates JWT, auto-provisions user in DB
# JWKS is cached in Redis DB 2 with 1h TTL
```

### Role permissions
| Action | ADMIN | OPERATOR | VIEWER |
|---|---|---|---|
| View dashboard / incidents / metrics | ✓ | ✓ | ✓ |
| Create / edit services | ✓ | ✓ | — |
| Acknowledge / resolve incidents | ✓ | ✓ | — |
| Delete services | ✓ | — | — |
| Manage users | ✓ | — | — |
| System config | ✓ | — | — |

## API structure

Base URL: `http://localhost:8000/api/v1`

```
GET    /auth/me
POST   /auth/refresh

GET    /services
POST   /services
GET    /services/{id}
PATCH  /services/{id}
DELETE /services/{id}
GET    /services/{id}/health-history
POST   /services/{id}/check-now

GET    /incidents
GET    /incidents/{id}
POST   /incidents/{id}/acknowledge
POST   /incidents/{id}/resolve
POST   /incidents/{id}/comment

GET    /metrics/overview
GET    /metrics/services/{id}/latency
GET    /metrics/services/{id}/uptime

WS     ws://localhost:8000/ws
WS     ws://localhost:8000/ws/services/{id}

GET    /notifications
PATCH  /notifications/{id}/read
PATCH  /notifications/read-all

GET    /users                  (ADMIN)
PATCH  /users/{id}/role        (ADMIN)
DELETE /users/{id}             (ADMIN)
```

## WebSocket message format

```json
{ "type": "service_update", "service_id": "uuid", "status": "DOWN", "latency_ms": null, "checked_at": "..." }
{ "type": "incident_created", "incident_id": "uuid", "service_id": "uuid", "severity": "CRITICAL", "title": "..." }
{ "type": "incident_updated", "incident_id": "uuid", "status": "ACKNOWLEDGED" }
{ "type": "notification", "notification_id": "uuid", "message": "...", "severity": "CRITICAL" }
```

Celery workers publish to Redis channel `ws:global` and `ws:service:{uuid}`.
FastAPI subscribes via `aioredis` pubsub and forwards to all connected WebSocket clients.

## In-app notifications

Notifications are created server-side whenever an incident is opened, acknowledged, or resolved. They appear as a bell icon in the navbar with an unread badge count.

### DB table: `notifications`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | UUID FK → users | One notification per ADMIN/OPERATOR user |
| `incident_id` | UUID FK → incidents | Which incident triggered this |
| `message` | VARCHAR | e.g. "Payment API is DOWN" |
| `severity` | ENUM | CRITICAL / HIGH / MEDIUM / LOW |
| `is_read` | BOOLEAN | default false |
| `created_at` | TIMESTAMPTZ | |

### How it works
1. Celery creates incident → `notifications` rows inserted for all ADMIN + OPERATOR users
2. WebSocket broadcasts `notification` event → frontend bell shows unread badge instantly
3. User opens bell → `GET /notifications` fetches list
4. User clicks notification → `PATCH /notifications/{id}/read` marks as read
5. "Mark all read" → `PATCH /notifications/read-all`

### Frontend: `NotificationBell` component
- Lives in the navbar
- Shows unread count badge (red dot if > 0)
- Dropdown list on click: message, severity color, timestamp, link to incident
- Realtime update via `useWebSocket` hook — no polling needed

## Celery architecture

- **Beat** runs every 10 seconds, calls `run_all_checks`
- `run_all_checks` dispatches one `check_service(service_id)` task per active service
- `check_service` respects per-service `check_interval` (skips if checked recently)
- Status transitions:
  - 2 consecutive failures → DOWN, create incident
  - Recovery → UP, auto-resolve open incident
  - Latency > 2000ms → DEGRADED

## SQLAlchemy conventions

- Use `async` sessions everywhere (`AsyncSession`)
- Use `mapped_column` and `Mapped` type hints (SQLAlchemy 2.0 style)
- Base class: `app.core.database.Base`
- All models import from their own `models.py` file inside the module

```python
# Example model style
class MonitoredService(Base):
    __tablename__ = "monitored_services"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ServiceStatus] = mapped_column(
        SQLAlchemyEnum(ServiceStatus), default=ServiceStatus.UNKNOWN
    )
```

## Docker services and ports

| Service | Port | Notes |
|---|---|---|
| frontend | 3000 | Vite dev server |
| backend | 8000 | FastAPI + uvicorn --reload |
| keycloak | 8080 | Admin console at /admin |
| postgres | 5432 | |
| redis | 6379 | |
| celery-worker | — | No exposed port |
| celery-beat | — | No exposed port |

## Development conventions

- All backend code is async (use `async def`, `await`, `AsyncSession`)
- Pydantic v2 syntax (`model_config = ConfigDict(...)`, not `class Config`)
- Routers use `APIRouter` with prefix and tags
- Services layer handles business logic (routers only parse/validate/return)
- Errors: raise `HTTPException` with appropriate status codes
- Logging: use Python `logging` module, structured where possible
- Tests go in `backend/tests/`, use `pytest` + `pytest-asyncio`

## What does NOT exist yet

- Email notifications (future phase — in-app notifications are the MVP solution)
- Prometheus /metrics endpoint (future phase)
- Grafana dashboards (future phase)
- Retry logic with backoff (future phase)
- SLA reports (future phase)
- Alert rules engine (future phase)

## Implementation phases

1. **Infrastructure** — Docker Compose, Keycloak realm, FastAPI skeleton, Alembic init
2. **Auth & Users** — JWT validation, RBAC, get_current_user, /auth/me
3. **Services CRUD** — MonitoredService model, router, schemas
4. **Monitoring Engine** — Celery tasks, HTTP probe, incident auto-creation, WebSocket
5. **Frontend** — Keycloak-js, Dashboard, Incidents, WebSocket hook, Charts, NotificationBell

Always implement phases in order. Do not start phase N+1 before phase N is working and tested.
