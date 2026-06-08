import pytest
from unittest.mock import patch

def test_health_success(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    assert response.get_json() == {"data": {"status": "ok"}}

def test_health_db_failure(client):
    with patch('app.db.session.execute') as mock_execute:
        mock_execute.side_effect = Exception("Database connection failed")
        response = client.get('/api/v1/health')
        assert response.status_code == 503
        assert response.get_json()["error"]["code"] == "DATABASE_UNAVAILABLE"
