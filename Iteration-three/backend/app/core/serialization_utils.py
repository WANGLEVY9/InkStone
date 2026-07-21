"""Utilities for safely serializing LangChain and Pydantic objects to JSON."""

from __future__ import annotations

from typing import Any


def safe_json_value(obj: Any) -> Any:
    """Recursively convert any object to JSON-serializable Python types.

    Uses langchain_core.load.dumpd for LangChain Serializable objects (messages,
    Commands, runnables, etc.) and handles Pydantic models, exceptions, and
    other non-serializable types.

    This function is safe to call on any data structure that may contain
    LangChain objects, Pydantic models, or standard Python types.
    """
    # Fast path: already a primitive
    if isinstance(obj, str | int | float | bool | type(None)):
        return obj

    # LangChain Serializable objects (messages, Commands, runnables, etc.)
    # Use dumpd to recursively serialize LangChain objects, then re-apply
    # safe_json_value in case the dump contains non-LangChain nested objects.
    # Silently skip if langchain_core is unavailable or the object is not
    # serializable by dumpd (TypeError/ValueError can occur on edge cases).
    try:
        from langchain_core.load import dumpd
        from langchain_core.runnables import Runnable

        if isinstance(obj, Runnable) or getattr(obj, "__lc_serializable__", False):
            return safe_json_value(dumpd(obj))
    except (ImportError, TypeError, ValueError):
        pass

    # Pydantic v2 BaseModel — model_dump(mode='json') converts to JSON-compatible
    # primitives. Silently skip if pydantic is not installed.
    try:
        from pydantic import BaseModel

        if isinstance(obj, BaseModel):
            return safe_json_value(obj.model_dump(mode="json"))
    except ImportError:
        pass

    # Standard dict / list / tuple
    if isinstance(obj, dict):
        return {k: safe_json_value(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [safe_json_value(i) for i in obj]

    # Fallback for any remaining non-serializable object
    return str(obj)
