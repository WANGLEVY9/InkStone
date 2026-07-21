def _build_task_payload(name: str) -> dict:
    return {
        "name": name,
        "agent_version": "v1",
        "dataset_id": "demo_ds",
        "mode": "result",
        "method": "fuzzy",
        "dimension": "effectiveness",
        "config": {
            "metrics": [
                "response_time",
                "token_usage",
                "tool_accuracy",
                "task_success",
            ],
            "strategy": "default",
            "enable_process_trace": True,
        },
        "input_payload": {
            "question": "RAG是什么？",
            "answer": "RAG是检索增强生成。",
            "ground_truth": "RAG即Retrieval-Augmented Generation。",
            "contexts": ["RAG combines retrieval and generation."],
            "response_time_ms": 321,
            "token_usage": 888,
            "tool_calls_total": 9,
            "tool_calls_success": 8,
            "task_success": True,
            "trace": ["retrieve", "reason", "answer"],
        },
        "note": "pytest",
    }


def test_task_create_execute_and_result_contract(client) -> None:
    create_resp = client.post(
        "/api/v1/tasks/", json=_build_task_payload("pytest-task-1")
    )
    assert create_resp.status_code == 200
    task = create_resp.json()
    assert task["name"] == "pytest-task-1"
    assert task["method"] == "fuzzy"

    execute_resp = client.post(f"/api/v1/tasks/{task['id']}/execute")
    assert execute_resp.status_code == 200
    assert execute_resp.json()["message"] == "completed"

    result_resp = client.get(f"/api/v1/results/task/{task['id']}")
    assert result_resp.status_code == 200
    result_items = result_resp.json()
    assert len(result_items) >= 1
    first = result_items[0]
    assert "scores" in first
    assert "raw_data" in first
    assert "engine_details" in first["raw_data"]


def test_compare_results_contract(client) -> None:
    t1 = client.post(
        "/api/v1/tasks/", json=_build_task_payload("pytest-compare-1")
    ).json()
    t2 = client.post(
        "/api/v1/tasks/", json=_build_task_payload("pytest-compare-2")
    ).json()

    client.post(f"/api/v1/tasks/{t1['id']}/execute")
    client.post(f"/api/v1/tasks/{t2['id']}/execute")

    compare_resp = client.post(
        "/api/v1/results/compare", json={"task_ids": [t1["id"], t2["id"]]}
    )
    assert compare_resp.status_code == 200
    payload = compare_resp.json()
    assert "summary" in payload
    assert "by_metric" in payload


def test_error_response_contract(client) -> None:
    not_found_resp = client.get("/api/v1/tasks/999999")
    assert not_found_resp.status_code == 404
    payload = not_found_resp.json()
    assert payload["code"] == "HTTP_ERROR"
    assert payload["message"] == "task not found"
    assert "request_id" in payload


def test_validation_error_contract(client) -> None:
    invalid_payload = _build_task_payload("x")
    invalid_payload["mode"] = "invalid_mode"
    resp = client.post("/api/v1/tasks/", json=invalid_payload)
    assert resp.status_code == 422
    payload = resp.json()
    assert payload["code"] == "VALIDATION_ERROR"
    assert "errors" in payload["detail"]
