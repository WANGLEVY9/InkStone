from app.models.result import EvaluationResult
from app.services.analysis_service import AnalysisService


def test_compare_results_generates_summary_and_best_task() -> None:
    items = [
        EvaluationResult(task_id=101, scores={"task_success": 1.0, "response_time": 420.0}),
        EvaluationResult(task_id=102, scores={"task_success": 0.0, "response_time": 220.0}),
        EvaluationResult(task_id=103, scores={"task_success": 1.0, "response_time": 180.0}),
    ]

    result = AnalysisService.compare_results(items)

    assert "task_success" in result["summary"]
    assert "response_time" in result["by_metric"]
    assert result["by_metric"]["task_success"]["best_task"] in [101, 103]
    assert len(result["by_metric"]["response_time"]["values"]) == 3


def test_compare_results_empty_input() -> None:
    result = AnalysisService.compare_results([])
    assert result == {"summary": {}, "by_metric": {}}
