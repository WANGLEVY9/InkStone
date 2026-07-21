import pytest

from app.plugins.dimension_scoring import (
    effectiveness_plugin,
    performance_plugin,
    safety_plugin,
)


def test_effectiveness_plugin_weighted_score() -> None:
    scores = {
        "task_success": 1.0,
        "answer_relevancy": 0.8,
        "faithfulness": 0.6,
        "context_recall": 0.4,
    }

    result, meta = effectiveness_plugin({}, scores)

    assert result["dimension_effectiveness"] == 0.82
    assert meta["dimension"] == "effectiveness"


def test_effectiveness_plugin_custom_weights() -> None:
    scores = {
        "task_success": 1.0,
        "answer_relevancy": 0.8,
        "faithfulness": 0.6,
        "context_recall": 0.4,
    }
    custom_weights = {
        "task_success_weight": 10.0,
        "relevancy_weight": 1.0,
        "faithfulness_weight": 1.0,
        "recall_weight": 0.0,
        "divisor": 12.0,
    }

    result, meta = effectiveness_plugin({}, scores, custom_weights)

    assert meta["weights_applied"] is True
    assert result["dimension_effectiveness"] == pytest.approx((10.0 + 0.8 + 0.6) / 12.0, 0.01)


def test_safety_plugin_returns_sub_scores() -> None:
    payload = {
        "harmful_content_ratio": 1.4,
        "privacy_risk": 0.2,
        "prompt_injection_risk": 0.1,
        "toxicity_risk": 0.0,
    }
    scores = {"llm_judge_safety": 6.0}

    result, meta = safety_plugin(payload, scores)

    assert result["dimension_safety_alignment"] == 5.0
    assert result["dimension_safety_content"] == 0.0
    assert result["dimension_safety_privacy"] == 4.0
    assert result["dimension_safety_injection"] == 4.5
    assert result["dimension_safety_toxicity"] == 5.0
    assert result["dimension_safety"] == 3.475
    assert set(meta["sub_scores"].keys()) == {
        "alignment",
        "content",
        "privacy",
        "injection",
        "toxicity",
    }


def test_performance_plugin_uses_payload_fallbacks() -> None:
    payload = {
        "response_time_ms": 800,
        "token_usage": 600,
        "process_success_ratio": 0.8,
        "retry_count": 2,
        "timeout_ratio": 0.2,
        "stability_hint": 0.9,
    }

    result, meta = performance_plugin(payload, {})

    assert result["dimension_performance_latency"] == 3.0
    assert result["dimension_performance_efficiency"] == 4.0
    assert result["dimension_performance_success"] == 4.0
    assert result["dimension_performance_stability"] == 3.0
    assert result["dimension_performance"] == 3.5
    assert meta["dimension"] == "performance"
