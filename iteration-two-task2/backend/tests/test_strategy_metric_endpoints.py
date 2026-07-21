def test_metric_crud_contract(client) -> None:
    payload = {
        "name": "custom_latency_score",
        "metric_type": "explicit",
        "logic_type": "builtin",
        "ragas_config": {"source_key": "latency"},
        "description": "custom metric for ci",
    }

    create_resp = client.post("/api/v1/metrics/", json=payload)
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["name"] == payload["name"]

    list_resp = client.get("/api/v1/metrics/")
    assert list_resp.status_code == 200
    names = [item["name"] for item in list_resp.json()]
    assert payload["name"] in names

    delete_resp = client.delete(f"/api/v1/metrics/{created['id']}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["message"] == "deleted"


def test_strategy_create_update_contract(client) -> None:
    payload = {
        "name": "ci-strategy",
        "weights": {"task_success": 0.7, "response_time": 0.3},
        "metrics": ["task_success", "response_time"],
        "description": "created by ci",
    }

    create_resp = client.post("/api/v1/strategies/", json=payload)
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["name"] == payload["name"]
    assert created["weights"]["task_success"] == 0.7

    update_payload = {
        **payload,
        "weights": {"task_success": 0.5, "response_time": 0.5},
        "description": "updated by ci",
    }
    update_resp = client.post("/api/v1/strategies/", json=update_payload)
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["description"] == "updated by ci"
    assert updated["weights"]["response_time"] == 0.5

    list_resp = client.get("/api/v1/strategies/")
    assert list_resp.status_code == 200
    strategy = next(item for item in list_resp.json() if item["name"] == payload["name"])
    assert strategy["weights"]["task_success"] == 0.5
