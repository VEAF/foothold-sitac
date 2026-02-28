from datetime import datetime
from typing import Annotated, Any
from fastapi import APIRouter, Depends
from foothold_sitac.dependencies import get_active_sitac
from foothold_sitac.foothold import Sitac, list_servers
from foothold_sitac.schemas import (
    MapConnection,
    MapData,
    MapEjectedPilot,
    MapPlayer,
    MapZone,
    MapZoneGroupStatusEntry,
    Server,
)

router = APIRouter()


@router.get("", response_model=list[Server], description="List foothold servers")
async def foothold_list_servers() -> Any:
    return [Server.model_validate({"name": server}) for server in list_servers()]


@router.get("/{server}/sitac", response_model=Sitac)
async def foothold_get_sitac(sitac: Annotated[Sitac, Depends(get_active_sitac)]) -> Any:
    return sitac


@router.get("/{server}/map.json", response_model=MapData)
async def foothold_get_map_data(
    sitac: Annotated[Sitac, Depends(get_active_sitac)],
) -> Any:
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
                "group_status_max": zone.group_status_max,
                "group_status": [
                    MapZoneGroupStatusEntry.model_validate(
                        {
                            "name": entry.name,
                            "kind": entry.kind,
                            **({"damaged": True} if entry.damaged else {}),
                        }
                    )
                    for entry in (zone.group_status or [])
                ],
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

    age_seconds = (datetime.now() - sitac.updated_at).total_seconds()

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

    return MapData(
        updated_at=sitac.updated_at,
        age_seconds=age_seconds,
        zones=zones,
        connections=connections,
        players=players,
        ejected_pilots=ejected_pilots,
        progress=sitac.campaign_progress,
        missions_count=len(sitac.missions),
        ejected_pilots_count=len(ejected_pilots),
        red_credits=sitac.accounts.red,
        blue_credits=sitac.accounts.blue,
    )
