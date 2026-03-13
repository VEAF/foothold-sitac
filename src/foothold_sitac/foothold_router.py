from dataclasses import dataclass
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from foothold_sitac.foothold import PlayerStats, Sitac, get_sitac_center, list_servers
from foothold_sitac.templater import env
from foothold_sitac.dependencies import get_active_sitac, get_sitac_or_none


@dataclass
class SuccessCategory:
    title: str
    field: str
    icon: str
    description: str
    reverse: bool = False  # True = lowest wins (e.g. deaths)


SUCCESS_CATEGORIES: list[SuccessCategory] = [
    SuccessCategory("Top Scorer", "points", "fa-star", "Most points earned"),
    SuccessCategory("Top Spender", "points_spent", "fa-coins", "Most points invested"),
    SuccessCategory("Ace Pilot", "air", "fa-jet-fighter", "Most air-to-air kills"),
    SuccessCategory("Helo Hunter", "helo", "fa-helicopter", "Most helicopter kills"),
    SuccessCategory("SAM Slayer", "SAM", "fa-explosion", "Most SAM kills"),
    SuccessCategory("Ground Pounder", "ground_units", "fa-crosshairs", "Most ground unit kills"),
    SuccessCategory("Infantry Expert", "infantry", "fa-person-rifle", "Most infantry kills"),
    SuccessCategory("Demolisher", "structure", "fa-building", "Most structures destroyed"),
    SuccessCategory("CAS Specialist", "CAS_mission", "fa-bullseye", "Most CAS missions completed"),
    SuccessCategory("CAP Guardian", "CAP_mission", "fa-shield-halved", "Most CAP missions flown"),
    SuccessCategory("Scout", "recon_mission", "fa-binoculars", "Most recon missions"),
    SuccessCategory("Rescuer", "pilot_rescue", "fa-parachute-box", "Most pilots rescued"),
    SuccessCategory(
        "Cargo Interceptor", "intercept_cargo_plane", "fa-plane-circle-xmark", "Most cargo planes intercepted"
    ),
    SuccessCategory("Trucker", "warehouse_delivery", "fa-warehouse", "Most warehouse deliveries"),
    SuccessCategory("Zone Conqueror", "zone_capture", "fa-flag", "Most zones captured"),
    SuccessCategory("Zone Builder", "zone_upgrade", "fa-arrow-up", "Most zone upgrades"),
    SuccessCategory("Runway Striker", "bomb_runway", "fa-road", "Most runways bombed"),
    SuccessCategory("Logistic Flight", "flight_time", "fa-clock", "Most flight time"),
    SuccessCategory("Survivor", "deaths", "fa-heart", "Fewest deaths among active players", reverse=True),
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


@router.get("", response_class=HTMLResponse)
async def foothold_servers(request: Request) -> str:
    servers_data: list[ServerInfo] = []
    for server_name in list_servers():
        sitac = get_sitac_or_none(server_name)
        servers_data.append(
            ServerInfo(
                name=server_name,
                updated_at=sitac.updated_at if sitac else None,
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
                "title": category.title,
                "description": category.description,
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
