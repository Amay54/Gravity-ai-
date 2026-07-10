import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """
    Standard test client fixture wrapping the FastAPI application.
    """
    with TestClient(app) as test_client:
        yield test_client
