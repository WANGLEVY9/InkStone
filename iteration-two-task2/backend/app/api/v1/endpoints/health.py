from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import engine, mongo_db

router = APIRouter()


@router.get("/")
def health_check() -> dict:
    mysql_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        mysql_ok = True
    except Exception:
        mysql_ok = False

    mongo_ok = True
    try:
        # in-memory fallback object has no command method
        if hasattr(mongo_db, "command"):
            mongo_db.command("ping")
    except Exception:
        mongo_ok = False

    return {
        "status": "ok" if mysql_ok else "degraded",
        "database": {
            "mysql": "up" if mysql_ok else "down",
            "mongo": "up" if mongo_ok else "fallback",
        },
    }
