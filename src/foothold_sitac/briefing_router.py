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
        edit_token=token,
        is_edit_mode=True,
    )
