import pytest
import httpx
from app.main import app

BASE_URL = "http://localhost:3001/api/v1"

@pytest.mark.asyncio
async def test_health_check():
    async with httpx.AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.get("/sports")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_sports():
    async with httpx.AsyncClient(app=app, base_url=BASE_URL) as client:
        response = await client.get("/sports")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0






