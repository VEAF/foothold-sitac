from fastapi import HTTPException, status
from foothold_sitac.foothold import (
    Sitac,
    detect_foothold_mission_path,
    get_server_path_by_name,
    load_sitac,
)


def get_sitac_or_none(server: str) -> Sitac | None:
    """Load sitac for a server, return None if not available"""
    server_path = get_server_path_by_name(server)

    if not server_path.is_dir():
        return None

    mission_path = detect_foothold_mission_path(server)

    if not mission_path:
        return None

    return load_sitac(mission_path)


def get_active_sitac(server: str) -> Sitac:
    """Dependency injection of sitac by server name"""

    server_path = get_server_path_by_name(server)

    if not server_path.is_dir():
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"server {server} not found")

    mission_path = detect_foothold_mission_path(server)

    if not mission_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"mission not found for server {server}")

    return load_sitac(mission_path)
