import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.users.models import User

TEST_DB_URL = settings.database_url.rsplit("/", 1)[0] + "/statusforge_test"

engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
TestSession = async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def truncate_tables():
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield


async def _make_user(role: str) -> User:
    async with TestSession() as session:
        user = User(
            id=uuid.uuid4(),
            email=f"{role.lower()}@test.com",
            username=role.lower(),
            role=role,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


def _override(user: User):
    async def _get_db():
        async with TestSession() as session:
            yield session

    async def _auth():
        return user

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_current_user] = _auth


@pytest_asyncio.fixture
async def admin_user() -> User:
    return await _make_user("ADMIN")


@pytest_asyncio.fixture
async def client(admin_user: User):
    _override(admin_user)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def viewer_client():
    viewer = await _make_user("VIEWER")
    _override(viewer)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    session = TestSession()
    yield session
    try:
        await session.close()
    except Exception:
        pass
