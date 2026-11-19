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
    -- since VMCT's FIX-CAMPAIGN-THIRD-SERVER-FLIGHT: Foothold's own lists, by Foothold's field names
    players = { { coalition = "blue", unitType = "A-10C_2", playerName = "Zip", latitude = 36.5, longitude = 36.9, altitude = 3048 } },
    playerStats = { Zip = { Points = 420, Air = 1, SAM = 2, ["Ground Units"] = 7, Infantry = 3, Structure = 1, Deaths = 1 } },
    ejectedPilots = { { playerName = "Paluche", latitude = 36.45, longitude = 36.95, altitude = 412, lostCredits = 15 } },
    missions = {
      { title = "Prendre Tal Rifaat (300 cr.)", description = "", isRunning = true, isEscortMission = false,
        kind = "capture", zone = "Tal Rifaat", reward = 300 },
    },
    support = {
      { name = "Arco", kind = "tanker_boom", side = "blue", latitude = 36.2, longitude = 36.6, altitude = 7620,
        frequency = 252.5, tacan = "51Y", alive = true },
      { name = "Texaco", alive = false },
    },
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
| `players` | the players in a slot, Foothold's shape | the player markers, as for Foothold |
| `playerStats` | the ranking by pilot name, Foothold's legacy layout: `Points` the credits earned, kills by category, `Deaths`, `Warehouse delivery` | the ranking, player and success pages |
| `ejectedPilots` | the players' side's pilots waiting for the CSAR; `lostCredits` lost at the ejection | the ejected pilots markers and list |
| `missions` | the task board, titles as the F10 menu gives them; `kind`, `zone`, `reward` on top of Foothold's | the missions list; a task is drawn on its `zone` |
| `support` | the players' side's AWACS and tankers: `kind` (`awacs`, `tanker_boom`, `tanker_basket`, `tanker_both`, `tanker`), position, `frequency` (MHz), `tacan`; one destroyed has its name and `alive = false` only | a dish or pump icon with name, frequency and TACAN; a destroyed one is not drawn |

The garrison's composition is never written: the campaign hides it until the zone is reconnoitred, and the map is public.
A convoy's position is not saved either: its truck is drawn two thirds of the way to its target.

## How it maps onto the models

`veaf_campaign.load_campaign_sitac()` builds a `Sitac` with `source = "veaf"`, so every page and endpoint works unchanged.
Each zone is a Foothold `Zone` (side 2 blue, 1 red, 0 neutral; level 0; no Foothold upgrades) with the VEAF details in `Zone.veaf`; `Zone.total_units` is the garrison's alive count.
`Sitac.convoys`, `Sitac.resources` and `Sitac.support` exist only for VEAF campaigns, as `Mission.kind`, `zone` and `reward`.
`players`, `playerStats`, `ejectedPilots` and `missions` are validated by Foothold's own models, so the ranking, success, ejected pilots and missions pages read them unchanged; a state file written before them has none, and those pages stay empty.
These lists are as fresh as the save: the campaign writes it every 60 s of simulation, and not while the server is paused (Foothold writes its own on its own rhythm).

The state file's mtime is the cache key and the data's age.
At every save the campaign writes a complete `persistent.state.tmp` first, then the file itself: while the file is missing or half-written, the sitac reads the temporary, as the campaign does when it reloads.
When neither can be read, the map keeps the last data read until the next save.
