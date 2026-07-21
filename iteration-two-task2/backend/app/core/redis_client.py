from __future__ import annotations

import json
import threading
from typing import Any

from app.core.config import get_settings

settings = get_settings()


class _MemoryStore:
    """Fallback in-memory store when Redis is unavailable."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            return self._data.get(key)

    def set(self, key: str, value: Any, ex: int | None = None) -> None:
        with self._lock:
            self._data[key] = value

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def exists(self, key: str) -> bool:
        with self._lock:
            return key in self._data

    def keys(self, pattern: str) -> list[str]:
        with self._lock:
            prefix = pattern.replace("*", "")
            return [k for k in self._data if k.startswith(prefix)]

    def expire(self, key: str, seconds: int) -> None:
        pass  # not implemented for in-memory fallback

    def lpush(self, key: str, value: Any) -> None:
        with self._lock:
            if key not in self._data:
                self._data[key] = []
            self._data[key].insert(0, value)

    def rpush(self, key: str, value: Any) -> None:
        with self._lock:
            if key not in self._data:
                self._data[key] = []
            self._data[key].append(value)

    def lrange(self, key: str, start: int, stop: int) -> list[Any]:
        with self._lock:
            items = self._data.get(key, [])
            return items[start:stop] if stop >= 0 else items[start:]

    def llen(self, key: str) -> int:
        with self._lock:
            return len(self._data.get(key, []))

    def ltrim(self, key: str, start: int, stop: int) -> None:
        with self._lock:
            items = self._data.get(key, [])
            self._data[key] = items[start:stop]

    def sadd(self, key: str, member: str) -> None:
        with self._lock:
            if key not in self._data:
                self._data[key] = set()
            self._data[key].add(member)

    def srem(self, key: str, member: str) -> None:
        with self._lock:
            s = self._data.get(key)
            if s and member in s:
                s.remove(member)

    def smembers(self, key: str) -> set[str]:
        with self._lock:
            return set(self._data.get(key, []))


class RedisClient:
    """Redis client wrapper. Falls back to in-memory store when unavailable."""

    def __init__(self) -> None:
        self._redis = None
        self._mem = _MemoryStore()
        self._use_memory = False
        self._connect()

    def _connect(self) -> None:
        try:
            import redis as redis_mod

            self._redis = redis_mod.from_url(
                settings.redis_url, decode_responses=True, socket_timeout=2
            )
            self._redis.ping()
            self._use_memory = False
        except Exception:
            self._use_memory = True
            self._redis = None

    @property
    def _store(self) -> _MemoryStore | Any:
        if self._use_memory or self._redis is None:
            return self._mem
        return self._redis

    # --- String ops ---
    def get(self, key: str) -> Any | None:
        if self._use_memory or self._redis is None:
            return self._mem.get(key)
        try:
            val = self._redis.get(key)
            return val
        except Exception:
            return self._mem.get(key)

    def set(self, key: str, value: Any, ex: int | None = None) -> None:
        if self._use_memory or self._redis is None:
            self._mem.set(key, value, ex=ex)
            return
        try:
            self._redis.set(key, value, ex=ex)
        except Exception:
            self._mem.set(key, value, ex=ex)

    def delete(self, key: str) -> None:
        if self._use_memory or self._redis is None:
            self._mem.delete(key)
            return
        try:
            self._redis.delete(key)
        except Exception:
            self._mem.delete(key)

    def exists(self, key: str) -> bool:
        if self._use_memory or self._redis is None:
            return self._mem.exists(key)
        try:
            return bool(self._redis.exists(key))
        except Exception:
            return self._mem.exists(key)

    def expire(self, key: str, seconds: int) -> None:
        if self._use_memory or self._redis is None:
            self._mem.expire(key, seconds)
            return
        try:
            self._redis.expire(key, seconds)
        except Exception:
            pass

    def keys(self, pattern: str) -> list[str]:
        if self._use_memory or self._redis is None:
            return self._mem.keys(pattern)
        try:
            return list(self._redis.keys(pattern))
        except Exception:
            return self._mem.keys(pattern)

    # --- List ops (for events / alerts) ---
    def rpush(self, key: str, value: Any) -> int | None:
        if self._use_memory or self._redis is None:
            self._mem.rpush(key, value)
            return None
        try:
            return self._redis.rpush(key, value)
        except Exception:
            self._mem.rpush(key, value)
            return None

    def lrange(self, key: str, start: int, stop: int) -> list[Any]:
        if self._use_memory or self._redis is None:
            return self._mem.lrange(key, start, stop)
        try:
            return self._redis.lrange(key, start, stop)
        except Exception:
            return self._mem.lrange(key, start, stop)

    def llen(self, key: str) -> int:
        if self._use_memory or self._redis is None:
            return self._mem.llen(key)
        try:
            return self._redis.llen(key)
        except Exception:
            return self._mem.llen(key)

    def ltrim(self, key: str, start: int, stop: int) -> None:
        if self._use_memory or self._redis is None:
            self._mem.ltrim(key, start, stop)
            return
        try:
            self._redis.ltrim(key, start, stop)
        except Exception:
            self._mem.ltrim(key, start, stop)

    # --- Set ops (for indexes) ---
    def sadd(self, key: str, member: str) -> None:
        if self._use_memory or self._redis is None:
            self._mem.sadd(key, member)
            return
        try:
            self._redis.sadd(key, member)
        except Exception:
            self._mem.sadd(key, member)

    def srem(self, key: str, member: str) -> None:
        if self._use_memory or self._redis is None:
            self._mem.srem(key, member)
            return
        try:
            self._redis.srem(key, member)
        except Exception:
            self._mem.srem(key, member)

    def smembers(self, key: str) -> set[str]:
        if self._use_memory or self._redis is None:
            return self._mem.smembers(key)
        try:
            return self._redis.smembers(key)
        except Exception:
            return self._mem.smembers(key)

    # --- JSON convenience ---
    def set_json(self, key: str, value: dict, ex: int | None = None) -> None:
        self.set(key, json.dumps(value, default=str), ex=ex)

    def get_json(self, key: str) -> dict | None:
        raw = self.get(key)
        if raw is None:
            return None
        if isinstance(raw, dict):
            return raw
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    def is_available(self) -> bool:
        return not self._use_memory


redis_client = RedisClient()
