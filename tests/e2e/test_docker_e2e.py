import pytest

def test_docker_e2e_proxy_headers(client):
    # Verify that the application correctly handles forwarded proxy headers from Nginx
    response = client.get('/api/v1/health', headers={
        'X-Forwarded-For': '127.0.0.1',
        'X-Forwarded-Proto': 'https',
        'X-Real-IP': '127.0.0.1'
    })
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "ok"
