"""VEAF dynamic campaigns: discovery and reading of their `persistent.state`.

A VEAF persistent campaign (VEAF Mission Creation Tools) saves itself to
``{saved_games}/{server}/Missions/Saves/{campaign}/persistent.state``, a Lua literal
``return { ... }``. Since VMCT's FEAT-CAMPAIGN-SITAC-STATE, that file carries a ``sitac``
block written for this map: zones in lat/lon, kinds, connections, convoys, credits and
resources. See docs/veaf-campaign-format.md.

A campaign is served under the key ``{server}@{campaign}``, next to the Foothold servers.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from lupa import LuaRuntime  # type: ignore[import-untyped]

from foothold_sitac.foothold import (
    Accounts,
    Convoy,
    Sitac,
    get_foothold_server_saves_path,
    is_plain_server_name,
    lua_to_dict,
)

CAMPAIGN_SEPARATOR = "@"
STATE_FILE_NAME = "persistent.state"
SITAC_MARKER = '["sitac"]='

SIDES = {"red": 1, "blue": 2}

# Run the state file with no environment at all: it is a data literal and can call nothing.
_EVAL_DATA = """
function(code)
  local chunk, err = load(code, "persistent.state", "t", {})
  if not chunk then error(err) end
  return chunk()
end
"""

# (mtime, has a sitac block) by state file, so that listing the servers does not reread unchanged files
_sitac_check_cache: dict[Path, tuple[float, bool]] = {}


def campaign_key(server: str, campaign: str) -> str:
    """The key a campaign is listed and served under."""
    return f"{server}{CAMPAIGN_SEPARATOR}{campaign}"


def split_campaign_key(key: str) -> tuple[str, str] | None:
    """The (server, campaign folder) of a campaign key, or None when the key is not one."""
    parts = key.split(CAMPAIGN_SEPARATOR)
    if len(parts) != 2 or not all(is_plain_server_name(part) for part in parts):
        return None
    return parts[0], parts[1]


def get_campaign_state_path(key: str) -> Path | None:
    """The state file of a campaign key, or None when the key is not one."""
    split = split_campaign_key(key)
    if split is None:
        return None
    server, campaign = split
    return get_foothold_server_saves_path(server) / campaign / STATE_FILE_NAME


def has_sitac_block(path: Path) -> bool:
    """Whether a state file carries the `sitac` block (VMCT builds before it do not)."""
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return False
    cached = _sitac_check_cache.get(path)
    if cached is not None and cached[0] == mtime:
        return cached[1]
    try:
        found = SITAC_MARKER in path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    _sitac_check_cache[path] = (mtime, found)
    return found


def list_campaigns(server: str) -> list[str]:
    """The keys of the server's VEAF campaigns whose state file carries a `sitac` block."""
    if CAMPAIGN_SEPARATOR in server:
        return []
    saves = get_foothold_server_saves_path(server)
    if not saves.is_dir():
        return []
    return sorted(
        campaign_key(server, folder.name)
        for folder in saves.iterdir()
        # a folder whose key would not split back is left out rather than listed and never served
        if folder.is_dir()
        and split_campaign_key(campaign_key(server, folder.name)) is not None
        and has_sitac_block(folder / STATE_FILE_NAME)
    )


def _lua_list(value: Any) -> list[Any]:
    """A Lua sequence (a dict keyed 1..n once converted) as a list, in order."""
    if isinstance(value, dict):
        return [value[key] for key in sorted(key for key in value if isinstance(key, int))]
    return []


def _table(value: Any) -> dict[Any, Any]:
    """A Lua table as a dict, or an empty one for anything else."""
    return value if isinstance(value, dict) else {}


def _number(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _integer(value: Any) -> int | None:
    number = _number(value)
    return int(number) if number is not None else None


def _zone(raw: dict[str, Any]) -> dict[str, Any]:
    """A `sitac` zone mapped onto the Foothold Zone model, the VEAF details under `veaf`."""
    garrison = _table(raw.get("garrison"))
    capture = _table(raw.get("capture"))
    structures = _table(raw.get("structures"))
    capture_side = capture.get("side")
    return {
        "upgradesUsed": 0,
        "side": SIDES.get(str(raw.get("owner")), 0),
        "active": True,
        "destroyed": {},
        "extraUpgrade": {},
        "remainingUnits": {},
        "firstCaptureByRed": False,
        "level": 0,
        "triggers": {},
        "lat_long": {"latitude": raw["lat"], "longitude": raw["lon"]},
        "veaf": {
            "kind": str(raw.get("kind") or "outpost"),
            "waypoint": _integer(raw.get("waypoint")),
            "garrison_alive": _integer(garrison.get("alive")),
            "garrison_total": _integer(garrison.get("total")),
            "capture_side": capture_side if isinstance(capture_side, str) else None,
            "capture_seconds": _number(capture.get("seconds")),
            "structures_standing": _integer(structures.get("standing")),
            "structures_total": _integer(structures.get("total")),
            "awake": raw.get("awake") is not False,
        },
    }


def sitac_from_block(block: dict[str, Any], updated_at: datetime) -> Sitac:
    """Map a `sitac` block onto the Sitac model."""
    zones: dict[str, Any] = {}
    for raw in _lua_list(block.get("zones")):
        if isinstance(raw, dict) and isinstance(raw.get("name"), str) and "lat" in raw and "lon" in raw:
            zones[raw["name"]] = _zone(raw)

    connections = [
        {"from": pair[1], "to": pair[2]}
        for pair in _lua_list(block.get("connections"))
        if isinstance(pair, dict) and isinstance(pair.get(1), str) and isinstance(pair.get(2), str)
    ]

    convoys = [
        Convoy(
            side=str(raw.get("side")),
            from_zone=str(raw.get("from")),
            to_zone=str(raw.get("to")),
            units=_integer(raw.get("units")) or 0,
        )
        for raw in _lua_list(block.get("convoys"))
        if isinstance(raw, dict)
    ]

    sides = _table(block.get("sides"))
    red = _table(sides.get("red"))
    blue = _table(sides.get("blue"))
    resources = None
    if "resources" in red or "resources" in blue:
        resources = Accounts(red=_number(red.get("resources")) or 0, blue=_number(blue.get("resources")) or 0)

    return Sitac.model_validate(
        {
            "updated_at": updated_at,
            "zones": zones,
            "playerStats": {},
            "connections": connections,
            "accounts": {1: _number(red.get("credits")) or 0, 2: _number(blue.get("credits")) or 0},
            "source": "veaf",
            "campaign_name": block.get("campaign") if isinstance(block.get("campaign"), str) else None,
            "theatre": block.get("theatre") if isinstance(block.get("theatre"), str) else None,
            "convoys": convoys,
            "resources": resources,
        }
    )


def load_campaign_sitac(path: Path) -> Sitac:
    """Read a campaign's state file into a Sitac.

    Raises:
        ValueError: the file is not a readable state, or carries no `sitac` block.
    """
    code = path.read_text(encoding="utf-8")
    lua = LuaRuntime(unpack_returned_tuples=True)
    try:
        state = lua_to_dict(lua.eval(_EVAL_DATA)(code))
    except Exception as error:  # lupa raises LuaError, or a TypeError on a value that is not a table
        raise ValueError(f"unreadable campaign state {path.name}: {error}") from error
    block = state.get("sitac") if isinstance(state, dict) else None
    if not isinstance(block, dict):
        raise ValueError(f"campaign state {path.name} carries no sitac block")
    return sitac_from_block(block, datetime.fromtimestamp(path.stat().st_mtime))
