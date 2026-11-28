from unittest.mock import patch

import redis


def test_live(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_when_dependencies_up(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["checks"] == {"postgres": "ok", "redis": "ok"}


def test_ready_returns_503_when_redis_down(client):
    with patch("src.api.routes.health.redis_client.ping", side_effect=redis.ConnectionError):
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["redis"] == "unavailable"


def test_every_response_has_a_request_id(client):
    response = client.get("/health/live")
    assert len(response.headers["X-Request-ID"]) == 32

    echoed = client.get("/health/live", headers={"X-Request-ID": "abc-123"})
    assert echoed.headers["X-Request-ID"] == "abc-123"

    # Unsafe values are replaced, not copied into logs.
    unsafe = client.get("/health/live", headers={"X-Request-ID": "bad value\nINJECTED"})
    assert unsafe.headers["X-Request-ID"] != "bad value\nINJECTED"
