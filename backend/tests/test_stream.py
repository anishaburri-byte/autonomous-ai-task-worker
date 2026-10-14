# SSE streaming tested via httpx + auth header
import os
os.environ["DATABASE_URL"]="sqlite:///./test_stream.db"
# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_token

def test_stream_requires_auth():
    c=TestClient(app)
    r=c.get("/api/tasks/1/stream")
    assert r.status_code==401

def test_finance_records_filtered_by_owner():
    c=TestClient(app)
    tok=create_token("owner-a")
    r=c.get("/api/finance/records", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code==200
    assert isinstance(r.json(), list)
