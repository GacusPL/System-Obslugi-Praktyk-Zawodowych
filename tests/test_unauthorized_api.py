import pytest

def test_unauthorized_api_endpoints(client):
    endpoints = [
        ('/api/v1/praktyki', 'GET'),
        ('/api/v1/praktyki', 'POST'),
        ('/api/v1/praktyki/1', 'GET'),
        ('/api/v1/praktyki/1', 'PATCH'),
        ('/api/v1/harmonogramy', 'POST'),
        ('/api/v1/harmonogramy/1', 'PATCH'),
        ('/api/v1/harmonogramy/1', 'PUT'),
        ('/api/v1/dziennik/wpisy', 'POST'),
        ('/api/v1/dziennik/wpisy/1', 'PATCH'),
        ('/api/v1/efekty/potwierdzenie', 'POST'),
        ('/api/v1/efekty/potwierdzenie/1', 'GET'),
        ('/api/v1/efekty/potwierdzenie/1', 'PATCH'),
    ]
    
    for url, method in endpoints:
        if method == 'GET':
            response = client.get(url)
        elif method == 'POST':
            response = client.post(url, json={})
        elif method == 'PATCH':
            response = client.patch(url, json={})
        elif method == 'PUT':
            response = client.put(url, json={})
            
        assert response.status_code == 401
        res_json = response.get_json()
        assert "error" in res_json
        assert res_json["error"]["code"] == "UNAUTHORIZED"
