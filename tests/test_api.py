from fastapi.testclient import TestClient
from apps.api.app.main import app


def test_health():
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}


def test_sentiment_classify_endpoint():
    client = TestClient(app)
    res = client.post("/sentiment/classify", json={"text": "BIONS error"})
    assert res.status_code == 200
    assert res.json()["label"] == "negative"
