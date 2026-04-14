import json
from unittest.mock import patch

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@patch('app.api.endpoints.process_transaction.delay')
def test_inject_event_valid(mock_delay, client):
    payload = {
        "transaction_id": "tx-123456",
        "user_id": "user-A",
        "amount": 100.0,
        "currency": "USD"
    }
    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["transaction_id"] == "tx-123456"
    assert data["status"] == "Accepted"
    mock_delay.assert_called_once()

def test_inject_event_invalid_currency(client):
    payload = {
        "transaction_id": "tx-123457",
        "user_id": "user-A",
        "amount": 100.0,
        "currency": "XXX" # 不支援的幣別
    }
    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 422 # Pydantic Validation Error

def test_inject_event_invalid_amount(client):
    payload = {
        "transaction_id": "tx-123458",
        "user_id": "user-A",
        "amount": -50.0,
        "currency": "USD"
    }
    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 422
