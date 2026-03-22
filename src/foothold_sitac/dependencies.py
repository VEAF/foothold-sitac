from fastapi import HTTPException, status

from foothold_sitac.cache import get_cached_sitac
from foothold_sitac.foothold import Sitac, get_server_path_by_name


def get_sitac_or_none(server: str) -> Sitac | None:
    """Load sitac for a server, return None if not available (uses cache)."""
    server_path = get_server_path_by_name(server)

    if not server_path.is_dir():
        return None

    return get_cached_sitac(server)


def get_active_sitac(server: str) -> Sitac:
    """Dependency injection of sitac by server name (uses cache)."""

    server_path = get_server_path_by_name(server)

    if not server_path.is_dir():
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"server {server} not found")

    sitac = get_cached_sitac(server)

    if sitac is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"mission not found for server {server}")

    return sitac
