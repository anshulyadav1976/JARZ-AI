"""
TTL cache for tool/API results.
Lives in memory and persists to a JSON file in the backend directory
so cache survives backend restarts (e.g. demo on a teammate's laptop).
"""
import json
import time
from pathlib import Path
from threading import Lock
from typing import Any, Optional

# Default TTL: 1 hour for demo
DEFAULT_TTL_SECONDS = 3600

# Persist to backend/cache.json (survives restarts)
_CACHE_FILE = Path(__file__).resolve().parent.parent / "cache.json"

_lock = Lock()
_store: dict[str, tuple[str, float]] = {}  # key -> (json_value, expiry_ts)


def _load_from_disk() -> None:
    """Load cache from JSON file; skip expired entries."""
    if not _CACHE_FILE.exists():
        return
    try:
        with open(_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return
    now = time.time()
    with _lock:
        for key, item in data.items():
            if not isinstance(item, dict):
                continue
            v = item.get("v")
            e = item.get("e")
            if v is None or e is None:
                continue
            if e <= now:
                continue
            _store[key] = (v, e)


def _save_to_disk() -> None:
    """Write in-memory cache to JSON file."""
    with _lock:
        data = {k: {"v": v, "e": e} for k, (v, e) in _store.items()}
    try:
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=0, default=str)
    except OSError:
        pass


# Load persisted cache on first import (so restarts get cache back)
_load_from_disk()


def _make_key(prefix: str, *parts: Any) -> str:
    """Build a cache key from prefix and JSON-serializable parts."""
    try:
        payload = json.dumps(parts, sort_keys=True, default=str)
    except (TypeError, ValueError):
        payload = str(parts)
    return f"{prefix}:{payload}"


def get(key: str) -> Optional[dict[str, Any]]:
    """Return cached value if present and not expired. Otherwise None."""
    with _lock:
        entry = _store.get(key)
        if not entry:
            return None
        json_val, expiry = entry
        if time.time() > expiry:
            del _store[key]
            return None
        try:
            return json.loads(json_val)
        except (json.JSONDecodeError, TypeError):
            return None


def set_(key: str, value: dict[str, Any], ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
    """Store value in cache and persist to disk. Value must be JSON-serializable."""
    with _lock:
        try:
            json_val = json.dumps(value, default=str)
        except (TypeError, ValueError):
            return
        expiry = time.time() + ttl_seconds
        _store[key] = (json_val, expiry)
    _save_to_disk()


def clear() -> None:
    """Clear all cached entries (memory and file)."""
    with _lock:
        _store.clear()
    _save_to_disk()
