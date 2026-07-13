"""Shared API test fixtures."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

TEST_ENCRYPTION_KEY = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="


@pytest.fixture
def client() -> Iterator[TestClient]:
    settings = Settings(
        environment="test",
        log_level="CRITICAL",
        database_url="sqlite+aiosqlite://",
        data_encryption_key=TEST_ENCRYPTION_KEY,
        session_cookie_secure=False,
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client
