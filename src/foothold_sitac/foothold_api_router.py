from datetime import datetime
from typing import Annotated, Any
from fastapi import APIRouter, Depends
from foothold_sitac.cache import get_checked_at, get_status_mtime
from foothold_sitac.config import get_config
from foothold_sitac.dependencies import get_active_sitac
from foothold_sitac.foothold import Sitac, list_servers, parse_coordinates_from_text
from foothold_sitac.veaf_campaign import split_campaign_key
from foothold_sitac.schemas import (
    MapConnection,
    MapConvoy,
    MapData,
    MapEjectedPilot,
    MapFarp,
    MapMission,
    MapPlayer,
    MapZone,
    Server,
    UnitGroup,
)

router = APIRouter()

SIDE_COLORS = {"red": "red", "blue": "blue"}


@router.get("", response_model=list[Server], description="List foothold servers")
async def foothold_list_servers() -> Any:
    return [
        Server.model_validate({"name": server, "kind": "veaf" if split_campaign_key(server) else "foothold"})
        for server in list_servers()
    ]


@router.get("/{server}/sitac", response_model=Sitac)
async def foothold_get_sitac(sitac: Annotated[Sitac, Depends(get_active_sitac)]) -> Any:
    return sitac


@router.get("/{server}/map.json", response_model=MapData)
async def foothold_get_map_data(
    server: str,
    sitac: Annotated[Sitac, Depends(get_active_sitac)],
) -> Any:
    show_forces = get_config().features.show_zone_forces

    zones = [
        MapZone.model_validate(
            {
                "name": zone_name,
                "lat": zone.position.latitude,
                "lon": zone.position.longitude,
                "side": zone.side_str,
                "color": zone.side_color,
                "units": zone.total_units,
                "level": zone.level,
                "flavor_text": zone.flavor_text,
                "upgrades_used": zone.upgrades_used,
                "unit_groups": [UnitGroup(group_id=g["group_id"], units=g["units"]) for g in zone.unit_groups]
                if show_forces
                else None,
                **(
                    zone.veaf.model_dump(exclude={"garrison_alive"}) if zone.veaf else {}
                ),  # VEAF campaign details; the alive count is already `units`
            }
        )
        for zone_name, zone in sitac.zones.items()
        if zone.position and not zone.hidden
    ]

    # Build connections with resolved coordinates
    connections = []
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
            connections.append(
                MapConnection(
                    from_zone=conn.from_zone,
                    to_zone=conn.to_zone,
                    from_lat=from_zone.position.latitude,
                    from_lon=from_zone.position.longitude,
                    to_lat=to_zone.position.latitude,
                    to_lon=to_zone.position.longitude,
                    color=from_zone.side_color,
                )
            )

    status_mtime = get_status_mtime(server)
    reference_time = status_mtime if status_mtime else sitac.updated_at
    age_seconds = (datetime.now() - reference_time).total_seconds()
    is_fresh = get_checked_at(server) is not None and age_seconds < 130

    # Build players list
    players = [
        MapPlayer(
            player_name=player.player_name,
            lat=player.latitude,
            lon=player.longitude,
            coalition=player.coalition,
            unit_type=player.unit_type,
            color=player.side_color,
        )
        for player in sitac.players
    ]

    # Build ejected pilots list (exclude "Unknown" pilots)
    ejected_pilots = [
        MapEjectedPilot(
            player_name=pilot.player_name,
            lat=pilot.latitude,
            lon=pilot.longitude,
            altitude=pilot.altitude,
            lost_credits=pilot.lost_credits,
        )
        for pilot in sitac.ejected_pilots
        # if pilot.player_name != "Unknown" # don't hide Unknown pilots, real pilots have this name
    ]

    # Build missions with coordinates
    missions_with_coords = []
    for mission in sitac.missions:
        pos = parse_coordinates_from_text(mission.description)
        if pos:
            missions_with_coords.append(
                MapMission(
                    title=mission.title,
                    lat=pos.latitude,
                    lon=pos.longitude,
                    is_running=mission.is_running,
                    is_escort_mission=mission.is_escort_mission,
                )
            )

    # Build FARPs list
    farps = [MapFarp(name=farp.name, lat=farp.latitude, lon=farp.longitude) for farp in sitac.farps]

    # VEAF campaign assault convoys, drawn from their zone of departure to their target
    convoys = []
    for convoy in sitac.convoys:
        origin = sitac.zones.get(convoy.from_zone)
        target = sitac.zones.get(convoy.to_zone)
        if origin and target:
            convoys.append(
                MapConvoy(
                    side=convoy.side,
                    color=SIDE_COLORS.get(convoy.side, "gray"),
                    from_zone=convoy.from_zone,
                    to_zone=convoy.to_zone,
                    from_lat=origin.position.latitude,
                    from_lon=origin.position.longitude,
                    to_lat=target.position.latitude,
                    to_lon=target.position.longitude,
                    units=convoy.units,
                )
            )

    return MapData(
        updated_at=sitac.updated_at,
        age_seconds=age_seconds,
        is_fresh=is_fresh,
        zones=zones,
        connections=connections,
        players=players,
        ejected_pilots=ejected_pilots,
        missions=missions_with_coords,
        farps=farps,
        progress=sitac.campaign_progress,
        missions_count=len(sitac.missions),
        ejected_pilots_count=len(ejected_pilots),
        red_credits=sitac.accounts.red,
        blue_credits=sitac.accounts.blue,
        show_zone_forces=show_forces,
        source=sitac.source,
        convoys=convoys,
        red_resources=sitac.resources.red if sitac.resources else None,
        blue_resources=sitac.resources.blue if sitac.resources else None,
    )
