import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.database import engine
from app.core.exceptions import AppException

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "detail": exc.detail,
            "request_id": request_id,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": "HTTP_ERROR",
            "message": str(exc.detail),
            "detail": {},
            "request_id": request_id,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "request validation failed",
            "detail": {"errors": exc.errors()},
            "request_id": request_id,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "internal server error",
            "detail": {"error": str(exc)},
            "request_id": request_id,
        },
    )


app.include_router(v1_router, prefix=settings.api_prefix)

# ── 数据库 schema 自动迁移 ──────────────────────────────────────────────
# 确保所有模型表存在，并为已有表补齐缺失列
try:
    from app.models import Base
    import sqlalchemy as sa

    Base.metadata.create_all(bind=engine)

    inspector = sa.inspect(engine)
    if inspector.has_table("evaluation_strategies"):
        cols = {c["name"] for c in inspector.get_columns("evaluation_strategies")}
        if "dimension_weights" not in cols:
            with engine.begin() as conn:
                conn.execute(
                    sa.text(
                        "ALTER TABLE evaluation_strategies "
                        "ADD COLUMN dimension_weights JSON NULL"
                    )
                )
except Exception:
    pass  # 非致命：首次启动时部分表可能尚未就绪

