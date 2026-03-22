import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from foothold_sitac.foothold import (
    Sitac,
    detect_foothold_mission_path,
    get_foothold_server_status_path,
    load_sitac,
)

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    status_mtime: float
    mission_path: Path
    sitac: Sitac
    checked_at: datetime = field(default_factory=datetime.now)


_cache: dict[str, CacheEntry] = {}


def get_cached_sitac(server_name: str) -> Sitac | None:
    """Return a cached Sitac if the status file hasn't changed, or reload it.

    Returns None if the server has no valid foothold data.
    """
    status_path = get_foothold_server_status_path(server_name)

    if not status_path.is_file():
        _cache.pop(server_name, None)
        return None

    current_mtime = status_path.stat().st_mtime
    cached = _cache.get(server_name)

    if cached is not None and cached.status_mtime == current_mtime:
        logger.debug("Cache hit for server '%s'", server_name)
        cached.checked_at = datetime.now()
        return cached.sitac

    logger.info("Cache miss for server '%s', reloading sitac", server_name)
    mission_path = detect_foothold_mission_path(server_name)
    if mission_path is None:
        _cache.pop(server_name, None)
        return None

    sitac = load_sitac(mission_path)
    _cache[server_name] = CacheEntry(
        status_mtime=current_mtime,
        mission_path=mission_path,
        sitac=sitac,
        checked_at=datetime.now(),
    )
    return sitac


def get_checked_at(server_name: str) -> datetime | None:
    """Return when the cache was last checked for this server."""
    cached = _cache.get(server_name)
    return cached.checked_at if cached else None


def get_status_mtime(server_name: str) -> datetime | None:
    """Return the status file mtime for this server's cached entry."""
    cached = _cache.get(server_name)
    if cached is None:
        return None
    return datetime.fromtimestamp(cached.status_mtime)


def clear_cache() -> None:
    """Clear all cached entries."""
    _cache.clear()
