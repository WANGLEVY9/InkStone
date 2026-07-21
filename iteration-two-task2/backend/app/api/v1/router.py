from fastapi import APIRouter

from app.api.v1.endpoints import (
	agents,
	datasets,
	health,
	llm_judge,
	metric_templates,
	metrics,
	mode_batch,
	mode_offline,
	mode_realtime,
	results,
	seed,
	strategies,
	tasks,
)

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(agents.router, prefix="/agents", tags=["agents"])
router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
router.include_router(metric_templates.router, prefix="/metrics/templates", tags=["metric-templates"])
router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
router.include_router(results.router, prefix="/results", tags=["results"])
router.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
router.include_router(mode_realtime.router, prefix="/mode-realtime", tags=["mode-realtime"])
router.include_router(mode_offline.router, prefix="/mode-offline", tags=["mode-offline"])
router.include_router(mode_batch.router, prefix="/mode-batch", tags=["mode-batch"])
router.include_router(llm_judge.router, prefix="/llm-judge", tags=["llm-judge"])
router.include_router(seed.router, prefix="/demo", tags=["demo"])
