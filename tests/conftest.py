from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_session
from app.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    engine = create_async_engine(
        "sqlite+aiosqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    fabrica = async_sessionmaker(engine, expire_on_commit=False)

    async def sessao_teste() -> AsyncIterator[AsyncSession]:
        async with fabrica() as sessao:
            yield sessao

    app.dependency_overrides[get_session] = sessao_teste
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()


async def autenticar(client: AsyncClient, email: str = "ana@exemplo.com") -> dict[str, str]:
    await client.post(
        "/auth/registro", json={"nome": "Ana", "email": email, "senha": "senha-forte-123"}
    )
    resp = await client.post("/auth/token", data={"username": email, "password": "senha-forte-123"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def auth(client: AsyncClient) -> dict[str, str]:
    return await autenticar(client)
