# tests/test_health.py


def test_health_check(client):
    response = client.get("/api/v1/health")
    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "SUCCESS"
    assert data["code"] == 200
    assert "uptime" in data["meta"]


def test_health_ping(client):
    response = client.get("/api/v1/health/me")
    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "OK"


def test_unknown_route_returns_json_404(client):
    response = client.get("/api/v1/does-not-exist")
    data = response.get_json()

    assert response.status_code == 404
    assert data["status"] == "ERROR"
    assert data["code"] == 404
