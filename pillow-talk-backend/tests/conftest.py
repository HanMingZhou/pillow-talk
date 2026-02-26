"""Pytest 配置和共享 fixtures"""
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from pillow_talk.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
