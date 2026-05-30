import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.prometheus.router import router as prometheus_router
from app.core.config import settings
from app.incidents.router import router as incidents_router
from app.metrics.router import router as metrics_router
from app.notifications.router import router as notifications_router
from app.reports.router import router as reports_router
from app.services.router import router as services_router
from app.status.router import router as status_router
from app.users.router import router as users_router
from app.websocket.router import router as ws_router

logging.basicConfig(level=settings.log_level)

app = FastAPI(title="StatusForge API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/api/v1"

app.include_router(auth_router, prefix=PREFIX)
app.include_router(users_router, prefix=PREFIX)
app.include_router(services_router, prefix=PREFIX)
app.include_router(incidents_router, prefix=PREFIX)
app.include_router(notifications_router, prefix=PREFIX)
app.include_router(metrics_router, prefix=PREFIX)
app.include_router(reports_router, prefix=PREFIX)
app.include_router(status_router, prefix=PREFIX)
app.include_router(ws_router)
app.include_router(prometheus_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
