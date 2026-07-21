def test_health(client) -> None:
    resp = client.get("/api/v1/health/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
