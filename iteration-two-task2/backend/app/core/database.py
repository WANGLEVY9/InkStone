from collections.abc import Generator
from typing import Any

from pymongo import MongoClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

database_url = settings.database_url or settings.mysql_dsn
engine_options: dict[str, Any] = {"pool_pre_ping": True}
if database_url.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(database_url, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class _InMemoryCollection:
    def __init__(self) -> None:
        self._rows: list[dict] = []

    def _matches(self, row: dict, query: dict) -> bool:
        return all(row.get(k) == v for k, v in query.items())

    def find(self, *_args, **_kwargs):
        return self._rows

    def find_one(self, query: dict, *args, **kwargs) -> dict | None:
        rows = self._rows
        # Basic sort support — if sorting by a field descending, reverse the list.
        sort = kwargs.get("sort")
        if sort and all(d == -1 for _, d in sort):
            rows = list(reversed(rows))
        for row in rows:
            if self._matches(row, query):
                return row
        return None

    def update_one(self, query: dict, update: dict, upsert: bool = False) -> None:
        name = query.get("name")
        payload = update.get("$set", {})
        for idx, row in enumerate(self._rows):
            if row.get("name") == name:
                self._rows[idx] = {**row, **payload}
                return
        if upsert:
            self._rows.append(payload)

    def insert_one(self, payload: dict) -> None:
        self._rows.append(payload)

    def delete_many(self, query: dict) -> None:
        self._rows = [row for row in self._rows if not self._matches(row, query)]


class _InMemoryMongoDB:
    def __init__(self) -> None:
        self._collections: dict[str, _InMemoryCollection] = {}

    def __getitem__(self, name: str) -> _InMemoryCollection:
        if name not in self._collections:
            self._collections[name] = _InMemoryCollection()
        return self._collections[name]


try:
    mongo_client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=1500)  # type: ignore
    mongo_client.admin.command("ping")
    mongo_db = mongo_client[settings.mongo_db]
except Exception:
    mongo_db = _InMemoryMongoDB()  # type: ignore


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
