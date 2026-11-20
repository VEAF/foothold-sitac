from dataclasses import dataclass
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from foothold_sitac.foothold import PlayerStats, Sitac, get_sitac_center, list_servers
from foothold_sitac.templater import env
from foothold_sitac.dependencies import get_active_sitac, get_sitac_or_none
from foothold_sitac.veaf_campaign import split_campaign_key


@dataclass
class SuccessCategory:
    """A success board award; its title and description are the i18n keys award.<field>.title/description."""

    field: str
    icon: str
    reverse: bool = False  # True = lowest wins (e.g. deaths)


SUCCESS_CATEGORIES: list[SuccessCategory] = [
    SuccessCategory("points", "fa-star"),
    SuccessCategory("points_spent", "fa-coins"),
    SuccessCategory("air", "fa-jet-fighter"),
    SuccessCategory("helo", "fa-helicopter"),
    SuccessCategory("SAM", "fa-explosion"),
    SuccessCategory("ground_units", "fa-crosshairs"),
    SuccessCategory("infantry", "fa-person-rifle"),
    SuccessCategory("structure", "fa-building"),
    SuccessCategory("CAS_mission", "fa-bullseye"),
    SuccessCategory("CAP_mission", "fa-shield-halved"),
    SuccessCategory("recon_mission", "fa-binoculars"),
    SuccessCategory("pilot_rescue", "fa-parachute-box"),
    SuccessCategory("intercept_cargo_plane", "fa-plane-circle-xmark"),
    SuccessCategory("warehouse_delivery", "fa-warehouse"),
    SuccessCategory("zone_capture", "fa-flag"),
    SuccessCategory("zone_upgrade", "fa-arrow-up"),
    SuccessCategory("bomb_runway", "fa-road"),
    SuccessCategory("flight_time", "fa-clock"),
    SuccessCategory("deaths", "fa-heart", reverse=True),  # fewest deaths among active players
]


def _find_best_player(player_stats: dict[str, PlayerStats], category: SuccessCategory) -> tuple[str, float] | None:
    """Return (player_name, value) for the best player in a category, or None."""
    if not player_stats:
        return None

    if category.reverse:
        # Only consider active players (points >= 1)
        active = [(n, s) for n, s in player_stats.items() if s.points >= 1]
        if not active:
            return None
        best_name, best_stats = min(active, key=lambda x: getattr(x[1], category.field))
        value: float = getattr(best_stats, category.field)
        return best_name, value

    best_name, best_stats = max(player_stats.items(), key=lambda x: getattr(x[1], category.field))
    value = getattr(best_stats, category.field)
    if value == 0:
        return None
    return best_name, value


router = APIRouter()


class ServerInfo(BaseModel):
    name: str
    updated_at: datetime | None
    kind: str = "foothold"
    label: str = ""
    host: str | None = None


def server_label(server: str, sitac: Sitac | None) -> str:
    """How a server is named on the pages: a VEAF campaign by its name, else the server folder."""
    split = split_campaign_key(server)
    if split is None:
        return server
    if sitac is not None and sitac.campaign_name:
        return sitac.campaign_name
    return split[1]


@router.get("", response_class=HTMLResponse)
async def foothold_servers(request: Request) -> str:
    servers_data: list[ServerInfo] = []
    for server_name in list_servers():
        sitac = get_sitac_or_none(server_name)
        split = split_campaign_key(server_name)
        servers_data.append(
            ServerInfo(
                name=server_name,
                updated_at=sitac.updated_at if sitac else None,
                kind="veaf" if split else "foothold",
                label=server_label(server_name, sitac),
                host=split[0] if split else None,
            )
        )

    template = env.get_template("foothold/servers.html")
    return template.render(
        {
            "request": request,
            "servers": servers_data,
            "now": datetime.now(),
        }
    )


@router.get("/sitac/{server}", response_class=HTMLResponse)
async def foothold_sitac(request: Request, server: str, sitac: Annotated[Sitac, Depends(get_active_sitac)]) -> str:
    template = env.get_template("foothold/sitac.html")
    return template.render(
        {
            "request": request,
            "sitac": sitac,
            "server": server,
        }
    )


@router.get("/map/{server}", response_class=HTMLResponse)
async def foothold_map(request: Request, server: str, sitac: Annotated[Sitac, Depends(get_active_sitac)]) -> str:
    template = env.get_template("foothold/map.html")
    map_center = get_sitac_center(sitac)

    return template.render(
        {
            "request": request,
            "sitac": sitac,
            "server": server,
            "server_label": server_label(server, sitac),
            "center": [map_center.latitude, map_center.longitude],
            "progress": sitac.campaign_progress,
        }
    )


@router.get("/map/{server}/players", response_class=HTMLResponse)
async def foothold_players_modal(
    request: Request, server: str, sitac: Annotated[Sitac, Depends(get_active_sitac)]
) -> str:
    template = env.get_template("foothold/partials/players.html")
    return template.render({"request": request, "sitac": sitac, "server": server})


@router.get("/map/{server}/zones", response_class=HTMLResponse)
async def foothold_zones_modal(sitac: Annotated[Sitac, Depends(get_active_sitac)]) -> str:
    template = env.get_template("foothold/partials/zones.html")
    return template.render({"sitac": sitac, "progress": sitac.campaign_progress})


@router.get("/map/{server}/missions", response_class=HTMLResponse)
async def foothold_missions_modal(sitac: Annotated[Sitac, Depends(get_active_sitac)]) -> str:
    template = env.get_template("foothold/partials/missions.html")
    return template.render({"missions": sitac.missions})


@router.get("/map/{server}/ejected", response_class=HTMLResponse)
async def foothold_ejected_modal(sitac: Annotated[Sitac, Depends(get_active_sitac)]) -> str:
    template = env.get_template("foothold/partials/ejected.html")
    # Filter out "Unknown" pilots
    # ejected_pilots = [p for p in sitac.ejected_pilots if p.player_name != "Unknown"]
    # return template.render({"ejected_pilots": ejected_pilots})
    return template.render({"ejected_pilots": sitac.ejected_pilots})


@router.get("/player/{server}/{player_name}", response_class=HTMLResponse)
async def foothold_player(
    request: Request,
    server: str,
    player_name: str,
    sitac: Annotated[Sitac, Depends(get_active_sitac)],
) -> str:
    if player_name not in sitac.player_stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Player '{player_name}' not found")

    stats = sitac.player_stats[player_name]

    sorted_players = sorted(
        sitac.player_stats.items(),
        key=lambda x: x[1].points,
        reverse=True,
    )
    rank = next(i + 1 for i, (name, _) in enumerate(sorted_players) if name == player_name)

    template = env.get_template("foothold/player.html")
    return template.render(
        {
            "request": request,
            "server": server,
            "player_name": player_name,
            "stats": stats,
            "rank": rank,
            "total_players": len(sitac.player_stats),
        }
    )


@router.get("/success/{server}", response_class=HTMLResponse)
async def foothold_success_board(
    request: Request,
    server: str,
    sitac: Annotated[Sitac, Depends(get_active_sitac)],
) -> str:
    awards: list[dict[str, object]] = []
    for category in SUCCESS_CATEGORIES:
        result = _find_best_player(sitac.player_stats, category)
        if result is None:
            continue
        player_name, value = result
        awards.append(
            {
                "key": category.field,
                "icon": category.icon,
                "player_name": player_name,
                "value": int(value) if isinstance(value, float) and value == int(value) else value,
            }
        )

    template = env.get_template("foothold/success.html")
    return template.render(
        {
            "request": request,
            "server": server,
            "awards": awards,
        }
    )
