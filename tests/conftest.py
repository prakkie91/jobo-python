"""Shared fixtures for integration tests."""

from __future__ import annotations

import os

import pytest

from jobo_enterprise.client import AsyncJoboClient, JoboClient

API_KEY = os.environ.get("JOBO_API_KEY", "")
BASE_URL = os.environ.get("JOBO_BASE_URL", "https://connect.jobo.world")


@pytest.fixture
def client():
    with JoboClient(api_key=API_KEY, base_url=BASE_URL) as c:
        yield c


@pytest.fixture
async def async_client():
    c = AsyncJoboClient(api_key=API_KEY, base_url=BASE_URL)
    yield c
    await c.close()
