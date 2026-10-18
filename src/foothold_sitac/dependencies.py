from fastapi import HTTPException, status

from foothold_sitac.cache import get_cached_sitac
from foothold_sitac.foothold import Sitac, list_servers

SERVER_NOT_FOUND = "server not found"


def is_known_server(server: str) -> bool:
    """Only servers discovered under dcs.saved_games are served; the URL value never builds a path by itself."""
    return server in list_servers()


def get_sitac_or_none(server: str) -> Sitac | None:
    """Load sitac for a server, return None if not available (uses cache)."""
    if not is_known_server(server):
        return None

    return get_cached_sitac(server)


def get_active_sitac(server: str) -> Sitac:
    """Dependency injection of sitac by server name (uses cache)."""
    # Same response whether the server is unknown or has no mission loaded, without echoing the value.
    if not is_known_server(server):
        raise HTTPException(status.HTTP_404_NOT_FOUND, SERVER_NOT_FOUND)

    sitac = get_cached_sitac(server)

    if sitac is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, SERVER_NOT_FOUND)

    return sitac
