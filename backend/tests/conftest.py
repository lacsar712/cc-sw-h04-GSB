import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

import pgserver  # noqa: E402


@pytest.fixture(scope="session")
def database_url():
    srv = pgserver.get_server(tempfile.mkdtemp(prefix="spectrum-pg-"))
    uri = srv.get_uri()
    os.environ["DATABASE_URL"] = uri
    yield uri
    srv.cleanup()


@pytest.fixture(scope="session")
def client(database_url):
    from litestar.testing import TestClient

    import api

    with TestClient(app=api.app) as c:
        yield c


def _token(client, username, password):
    r = client.post("/api/login", json={"username": username, "password": password})
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def writer_headers(client):
    return _token(client, "calibrator", "calib123456")


@pytest.fixture(scope="session")
def reader_headers(client):
    return _token(client, "inspector", "insp123456")
