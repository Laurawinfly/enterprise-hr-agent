from fastapi.testclient import TestClient
from app.main import app

def test_health_and_chat():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        r = client.post("/api/chat", json={"message": "我还有多少年假？", "employee_id": "E001"})
        assert r.status_code == 200
        assert "5 天" in r.json()["answer"]
