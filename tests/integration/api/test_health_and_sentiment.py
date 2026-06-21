from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.integration

def test_health_endpoint(api_client: TestClient):
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_sentiment_classify_endpoint_labels_negative_text(api_client: TestClient):
    response = api_client.post("/sentiment/classify", json={"text": "BIONS error"})

    assert response.status_code == 200
    assert response.json()["label"] == "negative"
