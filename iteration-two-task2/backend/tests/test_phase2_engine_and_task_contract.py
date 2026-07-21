def test_task_batch_samples_and_export(client) -> None:
    payload = {
        "name": "phase2-batch",
        "agent_version": "v1",
        "dataset_id": "ds_batch",
        "mode": "result",
        "method": "explicit",
        "dimension": "effectiveness",
        "config": {
            "metrics": ["task_success", "response_time"],
            "strategy": "default",
            "enable_process_trace": False,
        },
        "input_payload": {
            "samples": [
                {
                    "id": "s1",
                    "question": "q1",
                    "answer": "a1",
                    "ground_truth": "a1",
                    "response_time_ms": 120,
                    "task_success": True,
                },
                {
                    "id": "s2",
                    "question": "q2",
                    "answer": "a2",
                    "ground_truth": "a2",
                    "response_time_ms": 150,
                    "task_success": False,
                },
            ]
        },
    }

    create_resp = client.post("/api/v1/tasks/", json=payload)
    assert create_resp.status_code == 200
    task_id = create_resp.json()["id"]

    run_resp = client.post(f"/api/v1/tasks/{task_id}/run")
    assert run_resp.status_code == 200

    stats_resp = client.get(f"/api/v1/tasks/{task_id}/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["result_count"] >= 2

    export_resp = client.get(f"/api/v1/tasks/{task_id}/results/export?format=csv")
    assert export_resp.status_code == 200
    assert "text/csv" in export_resp.headers["content-type"]
    assert "result_id,task_id,sample_id" in export_resp.text


def test_task_compare_endpoint(client) -> None:
    base = {
        "agent_version": "v1",
        "dataset_id": "ds_cmp",
        "mode": "result",
        "method": "explicit",
        "dimension": "effectiveness",
        "config": {
            "metrics": ["task_success", "response_time"],
            "strategy": "default",
            "enable_process_trace": False,
        },
    }
    t1 = client.post(
        "/api/v1/tasks/",
        json={
            **base,
            "name": "cmp-1",
            "input_payload": {"question": "q1", "answer": "a1", "task_success": True, "response_time_ms": 100},
        },
    ).json()
    t2 = client.post(
        "/api/v1/tasks/",
        json={
            **base,
            "name": "cmp-2",
            "input_payload": {"question": "q2", "answer": "a2", "task_success": False, "response_time_ms": 300},
        },
    ).json()

    client.post(f"/api/v1/tasks/{t1['id']}/run")
    client.post(f"/api/v1/tasks/{t2['id']}/run")

    compare_resp = client.post("/api/v1/tasks/compare", json={"task_ids": [t1["id"], t2["id"]]})
    assert compare_resp.status_code == 200
    payload = compare_resp.json()
    assert "summary" in payload
    assert "by_metric" in payload
