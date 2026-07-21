def _task_payload() -> dict:
    return {
        "name": "ws-task",
        "agent_version": "v1",
        "dataset_id": "ds_ws",
        "mode": "result",
        "method": "explicit",
        "dimension": "effectiveness",
        "config": {
            "metrics": ["task_success", "response_time"],
            "strategy": "default",
            "enable_process_trace": False,
        },
        "input_payload": {
            "question": "q",
            "answer": "a",
            "task_success": True,
            "response_time_ms": 111,
        },
    }


def test_task_websocket_init_and_ping(client) -> None:
    task = client.post("/api/v1/tasks/", json=_task_payload()).json()
    task_id = task["id"]

    with client.websocket_connect(f"/api/v1/tasks/{task_id}/ws") as ws:
        init_msg = ws.receive_json()
        assert init_msg["event"] == "task_init"
        assert init_msg["data"]["task"]["id"] == task_id

        ws.send_json({"type": "ping"})
        pong = ws.receive_json()
        assert pong["event"] == "pong"
