def test_upload_dataset_and_analysis(client) -> None:
    payload = '{"samples": [{"question": "q1", "answer": "a1", "latency_ms": 120, "token_usage": 64, "success": true}]}'

    upload_resp = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("agent_eval.json", payload, "application/json")},
    )
    assert upload_resp.status_code == 200, upload_resp.text
    data = upload_resp.json()

    dataset_id = data["dataset"]["dataset_id"]
    assert dataset_id
    assert "latency_ms" in data["parsed_metrics"] or isinstance(data["parsed_metrics"], list)

    list_resp = client.get("/api/v1/datasets/")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    analysis_resp = client.get(f"/api/v1/datasets/{dataset_id}/analysis")
    assert analysis_resp.status_code == 200
    analysis = analysis_resp.json()
    assert analysis["dataset_id"] == dataset_id
    assert "live_metrics" in analysis

    preview_resp = client.get(f"/api/v1/datasets/{dataset_id}/preview?limit=5")
    assert preview_resp.status_code == 200
    preview = preview_resp.json()
    assert preview["dataset_id"] == dataset_id
    assert preview["total"] >= 1
    assert isinstance(preview["items"], list)

    delete_resp = client.delete(f"/api/v1/datasets/{dataset_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["message"] == "deleted"
