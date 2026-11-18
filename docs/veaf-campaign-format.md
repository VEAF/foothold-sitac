# VEAF dynamic campaign format

Besides Foothold missions, the sitac draws the **VEAF dynamic campaigns** built with [VEAF Mission Creation Tools](https://github.com/VEAF/VEAF-Mission-Creation-Tools) (VMCT), such as "Bouclier de l'Oronte".

## Where the file is

A VEAF persistent campaign saves itself every minute, and at mission end, to:

```text
{saved_games}/{server}/Missions/Saves/{campaign}/persistent.state
```

`{campaign}` is the campaign's name with every character other than letters, digits, `-`, `_` and space replaced by `_` ("Bouclier de l'Oronte" → `Bouclier de l_Oronte`).

The sitac scans every server folder for such files and lists those that carry a `sitac` block (VMCT builds from FEAT-CAMPAIGN-SITAC-STATE on).
A campaign is listed and served under the key `{server}@{campaign}`, next to the Foothold servers, for example `/foothold/map/foothold2@Bouclier de l_Oronte`.
A server folder can hold a Foothold mission and VEAF campaigns at the same time: each gets its own entry.

## The file

The file is a Lua literal, `return { ... }`, written on one line.
The sitac runs it with no environment at all (`load(code, name, "t", {})`), so it cannot call anything.
Most of it is what the next mission needs to reload the campaign (garrisons unit by unit, warehouses…): the sitac reads only the `sitac` block, made for it.

```lua
return {
  -- ... the campaign's own state, ignored by the sitac ...
  sitac = {
    theatre = "Syria",
    campaign = "Bouclier de l'Oronte",
    updated = 5432.5, -- mission simulation time, in seconds
    zones = {
      { name = "Minakh", waypoint = 2, kind = "airfield", lat = 36.5225, lon = 36.8778, owner = "blue",
        garrison = { alive = 9, total = 12 }, awake = false },
      { name = "Tal Rifaat", waypoint = 3, kind = "outpost", lat = 36.4505, lon = 36.9333, owner = "neutral",
        capture = { side = "blue", seconds = 42.5 }, awake = true },
      { name = "Kafr Naya", waypoint = 4, kind = "factory", lat = 36.3784, lon = 36.8444, owner = "red",
        garrison = { alive = 5, total = 6 }, structures = { standing = 2, total = 3 }, awake = false },
    },
    connections = { { "Minakh", "Tal Rifaat" }, { "Tal Rifaat", "Kafr Naya" } },
    convoys = { { side = "blue", from = "Minakh", to = "Tal Rifaat", units = 3 } },
    sides = { blue = { credits = 1915, resources = 600 }, red = { resources = 250 } },
  },
}
```

| Field | Meaning | Shown as |
|---|---|---|
| `theatre`, `campaign` | DCS map and campaign name | the campaign name names the map page and its card |
| `zones[].owner` | `blue`, `red` or `neutral` | the zone's colour; progress counts blue against red |
| `zones[].kind` | `airfield`, `outpost`, `factory`, `depot` | an icon on the label, the circle's size |
| `zones[].lat`, `lon` | the zone's centre, decimal degrees | the circle's centre |
| `zones[].waypoint` | the zone's steerpoint in the players' flight plan | `WP n` under the label, in the zone window |
| `zones[].garrison` | units alive and in total, **counts only** | the truck count, "Garrison 5 / 6" |
| `zones[].capture` | side capturing the zone and for how long | a dashed ring in that side's colour |
| `zones[].structures` | a factory's or depot's buildings standing and in total | "Buildings standing 2 / 3" |
| `zones[].awake` | false for a sleeping zone (no units spawned) | a paler circle, "Activity asleep" |
| `connections` | pairs of zone names | dashed lines |
| `convoys` | assault convoys on the road | a line from their zone to their target, a truck with a tooltip |
| `sides.*.credits` | the players' side's credits | the Credits badges (red has none: 0) |
| `sides.*.resources` | each side's stock, when the campaign counts it | the Stock badges |

The garrison's composition is never written: the campaign hides it until the zone is reconnoitred, and the map is public.
A convoy's position is not saved either: its truck is drawn two thirds of the way to its target.

## How it maps onto the models

`veaf_campaign.load_campaign_sitac()` builds a `Sitac` with `source = "veaf"`, so every page and endpoint works unchanged.
Each zone is a Foothold `Zone` (side 2 blue, 1 red, 0 neutral; level 0; no Foothold upgrades) with the VEAF details in `Zone.veaf`; `Zone.total_units` is the garrison's alive count.
`Sitac.convoys` and `Sitac.resources` exist only for VEAF campaigns; `Sitac.player_stats` is empty, so the ranking and success pages are empty for them.

The state file's mtime is the cache key and the data's age.
A file that cannot be read (caught half-written) keeps the last data read until the next save.
