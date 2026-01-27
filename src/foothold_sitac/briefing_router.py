"""Briefing HTML router - pages for viewing and editing briefings."""

import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse

from foothold_sitac.briefing_storage import list_briefings, load_briefing
from foothold_sitac.dependencies import get_sitac_or_none
from foothold_sitac.foothold import Sitac, list_servers
from foothold_sitac.templater import env


def zones_to_json(sitac: Sitac | None) -> str:
    """Convert sitac zones to JSON string for JavaScript."""
    if not sitac:
        return "{}"
    zones_dict: dict[str, Any] = {name: zone.model_dump(mode="json") for name, zone in sitac.zones.items()}
    return json.dumps(zones_dict)


def connections_to_json(sitac: Sitac | None) -> str:
    """Convert sitac connections to JSON string for JavaScript with resolved coordinates."""
    if not sitac:
        return "[]"
    connections_list: list[dict[str, Any]] = []
    for conn in sitac.connections:
        from_zone = sitac.zones.get(conn.from_zone)
        to_zone = sitac.zones.get(conn.to_zone)
        # Only include connection if both zones exist, have positions, and are not hidden
        if (
            from_zone
            and to_zone
            and from_zone.position
            and to_zone.position
            and not from_zone.hidden
            and not to_zone.hidden
        ):
            connections_list.append(
                {
                    "from_zone": conn.from_zone,
                    "to_zone": conn.to_zone,
                    "from_lat": from_zone.position.latitude,
                    "from_lon": from_zone.position.longitude,
                    "to_lat": to_zone.position.latitude,
                    "to_lon": to_zone.position.longitude,
                    "color": from_zone.side_color,
                }
            )
    return json.dumps(connections_list)


router = APIRouter()


@router.get("", response_class=HTMLResponse)
async def briefing_list(request: Request, server: str | None = None) -> str:
    """List all briefings."""
    briefings = list_briefings(server)
    servers = list_servers()
    template = env.get_template("briefing/list.html")
    return template.render(
        request=request,
        briefings=briefings,
        servers=servers,
        server_filter=server,
    )


@router.get("/new", response_class=HTMLResponse)
async def briefing_new(request: Request, server: str | None = None) -> str:
    """Create new briefing form."""
    servers = list_servers()
    template = env.get_template("briefing/new.html")
    return template.render(
        request=request,
        servers=servers,
        preselected_server=server,
    )


@router.get("/{briefing_id}", response_class=HTMLResponse)
async def briefing_view(request: Request, briefing_id: UUID) -> str:
    """View a briefing (read-only)."""
    briefing = load_briefing(briefing_id)
    if not briefing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Briefing not found")

    sitac = get_sitac_or_none(briefing.server_name)

    template = env.get_template("briefing/view.html")
    return template.render(
        request=request,
        briefing=briefing,
        sitac=sitac,
        zones_json=zones_to_json(sitac),
        connections_json=connections_to_json(sitac),
        is_edit_mode=False,
    )


@router.get("/{briefing_id}/edit", response_class=HTMLResponse)
async def briefing_edit(
    request: Request,
    briefing_id: UUID,
    token: UUID = Query(...),
) -> str:
    """Edit a briefing (requires token)."""
    briefing = load_briefing(briefing_id)
    if not briefing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Briefing not found")

    if briefing.edit_token != token:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid edit token")

    sitac = get_sitac_or_none(briefing.server_name)

    template = env.get_template("briefing/edit.html")
    return template.render(
        request=request,
        briefing=briefing,
        sitac=sitac,
        zones_json=zones_to_json(sitac),
        connections_json=connections_to_json(sitac),
        edit_token=token,
        is_edit_mode=True,
    )
