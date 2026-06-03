import pytest

def test_api_health(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data == {"data": {"status": "ok"}}
