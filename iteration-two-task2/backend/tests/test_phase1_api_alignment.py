def _build_task_payload(name: str) -> dict:
    return {
        "name": name,
        "description": "phase1 api alignment test",
        "agent_version": "v1",
        "dataset_id": "demo_ds",
        "mode": "result",
        "method": "explicit",
        "dimension": "effectiveness",
        "metrics": ["task_success", "response_time"],
        "run_config": {"concurrency": 2},
        "judge_config": {"model": "gpt-4o-mini"},
        "config": {
            "metrics": ["task_success", "response_time"],
            "strategy": "default",
            "enable_process_trace": False,
        },
        "input_payload": {
            "question": "hello",
            "answer": "world",
            "response_time_ms": 100,
            "task_success": True,
        },
    }


def test_agents_and_metric_templates_crud(client) -> None:
    agent_payload = {
        "name": "agent-phase1",
        "endpoint": "http://example.com/agent",
        "auth_type": "none",
    }
    create_agent = client.post("/api/v1/agents/", json=agent_payload)
    assert create_agent.status_code == 200
    agent = create_agent.json()
    assert agent["name"] == "agent-phase1"

    list_agent = client.get("/api/v1/agents/")
    assert list_agent.status_code == 200
    assert any(item["id"] == agent["id"] for item in list_agent.json())

    tmpl_payload = {
        "name": "tmpl-phase1",
        "template_type": "llm_judge",
        "prompt_template": "score this: {agent_output}",
    }
    create_tmpl = client.post("/api/v1/metrics/templates/", json=tmpl_payload)
    assert create_tmpl.status_code == 200
    tmpl = create_tmpl.json()
    assert tmpl["name"] == "tmpl-phase1"


def test_task_run_clone_cancel_and_stats(client) -> None:
    create_resp = client.post("/api/v1/tasks/", json=_build_task_payload("phase1-task"))
    assert create_resp.status_code == 200
    task = create_resp.json()

    run_resp = client.post(f"/api/v1/tasks/{task['id']}/run")
    assert run_resp.status_code == 200

    stats_resp = client.get(f"/api/v1/tasks/{task['id']}/stats")
    assert stats_resp.status_code == 200
    assert "avg_scores" in stats_resp.json()

    clone_resp = client.post(f"/api/v1/tasks/{task['id']}/clone")
    assert clone_resp.status_code == 200
    cloned = clone_resp.json()
    assert cloned["name"].endswith("(copy)")

    cancel_resp = client.post(f"/api/v1/tasks/{cloned['id']}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["message"] == "cancelled"


def test_result_label_update(client) -> None:
    create_resp = client.post("/api/v1/tasks/", json=_build_task_payload("phase1-label"))
    assert create_resp.status_code == 200
    task = create_resp.json()
    client.post(f"/api/v1/tasks/{task['id']}/run")

    list_result = client.get(f"/api/v1/results/task/{task['id']}")
    assert list_result.status_code == 200
    result_id = list_result.json()[0]["id"]

    patch_resp = client.patch(
        f"/api/v1/results/{result_id}/label",
        json={"human_label": {"passed": True, "note": "manual review"}},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["human_label"]["passed"] is True
