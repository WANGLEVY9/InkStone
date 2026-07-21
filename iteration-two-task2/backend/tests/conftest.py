import os

import pytest
from fastapi.testclient import TestClient

# 测试环境优先使用SQLite，避免依赖外部MySQL。
os.environ["DATABASE_URL"] = "sqlite:///./test_backend.db"
os.environ["USE_CELERY"] = "false"
os.environ["RAGAS_ENABLED"] = "false"

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.core.database import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
