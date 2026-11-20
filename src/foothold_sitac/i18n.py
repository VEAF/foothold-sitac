"""Translations of the web UI (English and French) and the choice of the language per request.

English is the reference text. Each language is a flat dictionary ``key -> text``; a text may hold
``{name}`` placeholders filled by ``t(key, name=value)``. The keys starting with ``js.`` are the ones
the map's JavaScript needs: they are passed to the page as one JSON object (``js_messages()``).

The language of a request comes from the ``lang`` cookie set by the language selector, else from the
browser's ``Accept-Language`` header, else English. ``LanguageMiddleware`` stores it for the request so
that the ``t()`` Jinja global needs no argument.
"""

from contextvars import ContextVar
from urllib.parse import quote

from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

DEFAULT_LANGUAGE = "en"
LANGUAGE_COOKIE = "lang"
LANGUAGE_NAMES: dict[str, str] = {"en": "English", "fr": "Français"}
JS_PREFIX = "js."

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        # common
        "common.yes": "Yes",
        "common.no": "No",
        "common.back_home": "Back to home",
        "common.back_map": "Back to map",
        "common.back_servers": "Back to server list",
        "lang.choose": "Language",
        # home
        "home.title": "Home",
        "home.welcome": "Welcome",
        "home.intro": "Access to Foothold Sitac.",
        "home.go": "Go to Foothold",
        # servers
        "servers.title": "Servers",
        "servers.heading": "Servers and campaigns",
        "servers.veaf_campaign": "VEAF dynamic campaign",
        "servers.updated_min": "Updated {n} min ago",
        "servers.updated_hours": "Updated {n}h ago",
        "servers.updated_days": "Updated {n}d ago",
        "servers.no_data": "No data available",
        "servers.empty": "No Foothold server nor VEAF campaign found.",
        # map page and navbar
        "map.title": "Map",
        "nav.ranking": "Ranking",
        "nav.ranking_tip": "View player statistics and rankings",
        "nav.success": "Success",
        "nav.success_tip": "Best players in each category",
        "nav.missions": "Missions",
        "nav.missions_tip": "Active missions on the server",
        "nav.ejected": "Ejected",
        "nav.ejected_tip": "Ejected pilots awaiting rescue",
        "nav.credits": "Credits",
        "nav.credits_tip": "Coalition credits (Blue / Red)",
        "nav.stock": "Stock",
        "nav.stock_tip": "Resource stock of each side (Blue / Red)",
        "nav.objectives": "Objectives",
        "nav.objectives_tip": "Campaign progress and zone status",
        "nav.ruler": "Ruler",
        "nav.ruler_tip": "Measure distance between two points",
        "nav.markpoint": "Markpoint",
        "nav.markpoint_tip": "Add a marker at coordinates",
        "nav.settings": "Settings",
        "nav.settings_tip": "Display settings",
        "ruler.measure": "Measure",
        "ruler.clear": "Clear measurement",
        "ruler.distance": "Distance",
        "ruler.bearing": "Bearing",
        "ruler.flight_time": "Flight time",
        # sides and zones
        "side.red": "Red",
        "side.blue": "Blue",
        "side.neutral": "Neutral",
        "zone.name": "Name",
        "zone.side": "Side",
        "zone.level": "Level",
        "zone.upgrades_used": "Upgrades Used",
        "zone.active": "Active",
        "zone.first_capture_red": "First Capture by Red",
        "zones.heading": "Objectives",
        "zones.progress": "Campaign Progress",
        "zones.none_blue": "No blue zones",
        "zones.none_neutral": "No neutral zones",
        "zones.none_red": "No red zones",
        # sitac page
        "sitac.player_stats": "Player Stats",
        # rankings
        "rank.heading": "Player Rankings",
        "rank.general": "General",
        "rank.air": "Air to Air",
        "rank.sead": "SEAD",
        "rank.cas": "CAS",
        "rank.strike": "Strike",
        "rank.logistic": "Logistic",
        "rank.csar": "CSAR",
        "rank.recon": "Recon",
        "rank.player": "Player",
        "rank.no_data": "No player data available",
        # player statistics
        "stat.points": "Points",
        "stat.points_spent": "Points Spent",
        "stat.deaths": "Deaths",
        "stat.points_per_life": "Points per Life",
        "stat.points_per_life_short": "Points / Life",
        "stat.air_kills": "Air Kills (A/A)",
        "stat.helo_kills": "Helicopter Kills",
        "stat.intercept_cargo": "Intercept Cargo Plane",
        "stat.cap_missions": "CAP Missions",
        "stat.air_kl": "Air K/L Ratio",
        "stat.sam_kills": "SAM/Air Defense Kills",
        "stat.ground_kills": "Ground Unit Kills",
        "stat.infantry_kills": "Infantry Kills",
        "stat.cas_missions": "CAS Missions",
        "stat.ground_kl": "Ground K/L Ratio",
        "stat.structure_kills": "Structure Kills",
        "stat.bomb_runway": "Bomb Runway",
        "stat.flight_time": "Flight Time (min)",
        "stat.warehouse": "Warehouse Deliveries",
        "stat.zone_captures": "Zone Captures",
        "stat.zone_upgrades": "Zone Upgrades",
        "stat.pilot_rescues": "Pilot Rescues",
        "stat.recon_missions": "Recon Missions",
        # player page
        "player.og_title": "{name} - Foothold Stats",
        "player.og_description": (
            "Rank #{rank}/{total} | {points} pts | {air} air kills | {ground} ground kills | {deaths} deaths"
        ),
        "player.air_combat": "Air Combat",
        "player.ground_combat": "Ground Combat",
        "player.logistics": "Logistics & Support",
        "player.air_kills": "Air Kills",
        "player.helo_kills": "Helo Kills",
        "player.intercept_cargo": "Intercept Cargo",
        "player.air_kl": "Air K/L",
        "player.ground_units": "Ground Units",
        "player.infantry": "Infantry",
        "player.sam_kills": "SAM Kills",
        "player.structures": "Structures",
        "player.ground_kl": "Ground K/L",
        # success board
        "success.title": "Success Board",
        "success.no_awards": "No player stats available yet.",
        "award.points.title": "Top Scorer",
        "award.points.description": "Most points earned",
        "award.points_spent.title": "Top Spender",
        "award.points_spent.description": "Most points invested",
        "award.air.title": "Ace Pilot",
        "award.air.description": "Most air-to-air kills",
        "award.helo.title": "Helo Hunter",
        "award.helo.description": "Most helicopter kills",
        "award.SAM.title": "SAM Slayer",
        "award.SAM.description": "Most SAM kills",
        "award.ground_units.title": "Ground Pounder",
        "award.ground_units.description": "Most ground unit kills",
        "award.infantry.title": "Infantry Expert",
        "award.infantry.description": "Most infantry kills",
        "award.structure.title": "Demolisher",
        "award.structure.description": "Most structures destroyed",
        "award.CAS_mission.title": "CAS Specialist",
        "award.CAS_mission.description": "Most CAS missions completed",
        "award.CAP_mission.title": "CAP Guardian",
        "award.CAP_mission.description": "Most CAP missions flown",
        "award.recon_mission.title": "Scout",
        "award.recon_mission.description": "Most recon missions",
        "award.pilot_rescue.title": "Rescuer",
        "award.pilot_rescue.description": "Most pilots rescued",
        "award.intercept_cargo_plane.title": "Cargo Interceptor",
        "award.intercept_cargo_plane.description": "Most cargo planes intercepted",
        "award.warehouse_delivery.title": "Trucker",
        "award.warehouse_delivery.description": "Most warehouse deliveries",
        "award.zone_capture.title": "Zone Conqueror",
        "award.zone_capture.description": "Most zones captured",
        "award.zone_upgrade.title": "Zone Builder",
        "award.zone_upgrade.description": "Most zone upgrades",
        "award.bomb_runway.title": "Runway Striker",
        "award.bomb_runway.description": "Most runways bombed",
        "award.flight_time.title": "Logistic Flight",
        "award.flight_time.description": "Most flight time",
        "award.deaths.title": "Survivor",
        "award.deaths.description": "Fewest deaths among active players",
        # ejected pilots
        "ejected.heading": "Ejected Pilots",
        "ejected.pilot": "Pilot",
        "ejected.altitude": "Altitude",
        "ejected.credits": "Credits",
        "ejected.none": "No ejected pilots",
        # missions
        "missions.heading": "Active Missions",
        "missions.title": "Title",
        "missions.description": "Description",
        "missions.type": "Type",
        "missions.status": "Status",
        "missions.escort": "Escort",
        "missions.attack": "Attack",
        "missions.running": "Running",
        "missions.stopped": "Stopped",
        "missions.none": "No active missions",
        # JavaScript (map page)
        "js.map.default_layer": "Default",
        "js.modal.loading": "Loading...",
        "js.modal.error": "Error loading data",
        "js.coord.latitude": "Latitude",
        "js.coord.longitude": "Longitude",
        "js.coord.latlon": "Lat / Lon",
        "js.coord.decimal": "Decimal",
        "js.side.red": "red",
        "js.side.blue": "blue",
        "js.side.neutral": "neutral",
        "js.side.disabled": "disabled",
        "js.zone.unknown": "Unknown zone",
        "js.zone.coalition": "Coalition",
        "js.zone.detected_units": "Detected units",
        "js.zone.level": "Level",
        "js.zone.forces": "Forces",
        "js.zone.group": "Group {id}",
        "js.zone.kind": "Kind",
        "js.zone.waypoint": "Waypoint",
        "js.zone.garrison": "Garrison",
        "js.zone.buildings": "Buildings standing",
        "js.zone.capture": "Capture",
        "js.zone.capture_for": "{side} for {time}",
        "js.zone.capture_in_progress": "capture in progress",
        "js.zone.activity": "Activity",
        "js.zone.awake": "awake",
        "js.zone.asleep": "asleep",
        "js.kind.airfield": "airfield",
        "js.kind.outpost": "outpost",
        "js.kind.factory": "factory",
        "js.kind.depot": "depot",
        "js.ejected.altitude": "Alt: {altitude}m",
        "js.convoy.tooltip": "Assault convoy ({side})",
        "js.convoy.vehicles": "{n} vehicle(s)",
        "js.support.awacs": "AWACS",
        "js.support.tanker_boom": "Tanker (boom)",
        "js.support.tanker_basket": "Tanker (basket)",
        "js.support.tanker_both": "Tanker (boom and basket)",
        "js.support.tanker": "Tanker",
        "js.support.other": "Support",
        "js.freshness.offline": "Offline",
        "js.freshness.connection_lost": "Connection to server lost",
        "js.freshness.fresh": "Data up to date ({age}s) • Refresh in {n}s",
        "js.freshness.stale": "Stale data ({minutes}min) • Refresh in {n}s",
        "js.freshness.refresh_in": "Refresh in {n}s",
        "js.ruler.point_a": "Point A",
        "js.ruler.point_b": "Point B",
        "js.ruler.click_to_set": "Click to set",
        "js.settings.heading": "Settings",
        "js.settings.coord_format": "Coordinate format",
        "js.settings.cruise_speed": "Cruise speed (ruler)",
        "js.settings.save": "Save",
        "js.pilot.decimal_degrees": "Decimal Degrees",
        "js.pilot.ddm": "Degrees Decimal Minutes (DDM)",
        "js.pilot.dms": "Degrees Minutes Seconds (DMS)",
        "js.pilot.other": "Other Info",
        "js.pilot.altitude": "Altitude",
        "js.pilot.lost_credits": "Lost Credits",
        "js.markpoint.default": "Markpoint",
        "js.markpoint.add_title": "Add Markpoint",
        "js.markpoint.paste": "Paste coordinates",
        "js.markpoint.label_optional": "Label (optional)",
        "js.markpoint.label_placeholder": "Target",
        "js.markpoint.add": "Add",
        "js.markpoint.invalid": "Invalid coordinates",
        "js.markpoint.invalid_alert": "Invalid coordinates. Please enter valid DMS, DDM, or decimal coordinates.",
        "js.markpoint.delete": "Delete",
    },
    "fr": {
        # common
        "common.yes": "Oui",
        "common.no": "Non",
        "common.back_home": "Retour à l'accueil",
        "common.back_map": "Retour à la carte",
        "common.back_servers": "Retour à la liste des serveurs",
        "lang.choose": "Langue",
        # home
        "home.title": "Accueil",
        "home.welcome": "Bienvenue",
        "home.intro": "Accès à la sitac Foothold.",
        "home.go": "Aller sur Foothold",
        # servers
        "servers.title": "Serveurs",
        "servers.heading": "Serveurs et campagnes",
        "servers.veaf_campaign": "Campagne dynamique VEAF",
        "servers.updated_min": "Mis à jour il y a {n} min",
        "servers.updated_hours": "Mis à jour il y a {n} h",
        "servers.updated_days": "Mis à jour il y a {n} j",
        "servers.no_data": "Aucune donnée disponible",
        "servers.empty": "Aucun serveur Foothold ni campagne VEAF trouvé.",
        # map page and navbar
        "map.title": "Carte",
        "nav.ranking": "Classement",
        "nav.ranking_tip": "Statistiques et classement des joueurs",
        "nav.success": "Palmarès",
        "nav.success_tip": "Meilleurs joueurs de chaque catégorie",
        "nav.missions": "Missions",
        "nav.missions_tip": "Missions actives sur le serveur",
        "nav.ejected": "Éjectés",
        "nav.ejected_tip": "Pilotes éjectés en attente de récupération",
        "nav.credits": "Crédits",
        "nav.credits_tip": "Crédits des coalitions (bleu / rouge)",
        "nav.stock": "Stock",
        "nav.stock_tip": "Stock de ressources de chaque camp (bleu / rouge)",
        "nav.objectives": "Objectifs",
        "nav.objectives_tip": "Avancement de la campagne et état des zones",
        "nav.ruler": "Règle",
        "nav.ruler_tip": "Mesurer la distance entre deux points",
        "nav.markpoint": "Markpoint",
        "nav.markpoint_tip": "Ajouter un marqueur à des coordonnées",
        "nav.settings": "Réglages",
        "nav.settings_tip": "Réglages d'affichage",
        "ruler.measure": "Mesure",
        "ruler.clear": "Effacer la mesure",
        "ruler.distance": "Distance",
        "ruler.bearing": "Cap",
        "ruler.flight_time": "Temps de vol",
        # sides and zones
        "side.red": "Rouge",
        "side.blue": "Bleu",
        "side.neutral": "Neutre",
        "zone.name": "Nom",
        "zone.side": "Camp",
        "zone.level": "Niveau",
        "zone.upgrades_used": "Améliorations utilisées",
        "zone.active": "Active",
        "zone.first_capture_red": "Première capture par les rouges",
        "zones.heading": "Objectifs",
        "zones.progress": "Avancement de la campagne",
        "zones.none_blue": "Aucune zone bleue",
        "zones.none_neutral": "Aucune zone neutre",
        "zones.none_red": "Aucune zone rouge",
        # sitac page
        "sitac.player_stats": "Statistiques des joueurs",
        # rankings
        "rank.heading": "Classement des joueurs",
        "rank.general": "Général",
        "rank.air": "Air-air",
        "rank.sead": "SEAD",
        "rank.cas": "CAS",
        "rank.strike": "Strike",
        "rank.logistic": "Logistique",
        "rank.csar": "CSAR",
        "rank.recon": "Reco",
        "rank.player": "Joueur",
        "rank.no_data": "Aucune donnée joueur disponible",
        # player statistics
        "stat.points": "Points",
        "stat.points_spent": "Points dépensés",
        "stat.deaths": "Morts",
        "stat.points_per_life": "Points par vie",
        "stat.points_per_life_short": "Points / vie",
        "stat.air_kills": "Kills air-air",
        "stat.helo_kills": "Kills hélicoptères",
        "stat.intercept_cargo": "Avions cargo interceptés",
        "stat.cap_missions": "Missions CAP",
        "stat.air_kl": "Ratio K/L air",
        "stat.sam_kills": "Kills SAM / défense aérienne",
        "stat.ground_kills": "Kills unités au sol",
        "stat.infantry_kills": "Kills infanterie",
        "stat.cas_missions": "Missions CAS",
        "stat.ground_kl": "Ratio K/L sol",
        "stat.structure_kills": "Bâtiments détruits",
        "stat.bomb_runway": "Pistes bombardées",
        "stat.flight_time": "Temps de vol (min)",
        "stat.warehouse": "Livraisons d'entrepôt",
        "stat.zone_captures": "Captures de zones",
        "stat.zone_upgrades": "Améliorations de zones",
        "stat.pilot_rescues": "Pilotes récupérés",
        "stat.recon_missions": "Missions de reco",
        # player page
        "player.og_title": "{name} - Stats Foothold",
        "player.og_description": (
            "Rang {rank}/{total} | {points} pts | {air} kills air | {ground} kills sol | {deaths} morts"
        ),
        "player.air_combat": "Combat aérien",
        "player.ground_combat": "Combat au sol",
        "player.logistics": "Logistique et soutien",
        "player.air_kills": "Kills air",
        "player.helo_kills": "Kills hélicos",
        "player.intercept_cargo": "Cargos interceptés",
        "player.air_kl": "K/L air",
        "player.ground_units": "Unités au sol",
        "player.infantry": "Infanterie",
        "player.sam_kills": "Kills SAM",
        "player.structures": "Bâtiments",
        "player.ground_kl": "K/L sol",
        # success board
        "success.title": "Palmarès",
        "success.no_awards": "Pas encore de statistiques des joueurs.",
        "award.points.title": "Meilleur marqueur",
        "award.points.description": "Le plus de points gagnés",
        "award.points_spent.title": "Gros investisseur",
        "award.points_spent.description": "Le plus de points investis",
        "award.air.title": "As de la chasse",
        "award.air.description": "Le plus de kills air-air",
        "award.helo.title": "Chasseur d'hélicos",
        "award.helo.description": "Le plus de kills hélicoptères",
        "award.SAM.title": "Tueur de SAM",
        "award.SAM.description": "Le plus de SAM détruits",
        "award.ground_units.title": "Briseur de blindés",
        "award.ground_units.description": "Le plus d'unités au sol détruites",
        "award.infantry.title": "Expert anti-infanterie",
        "award.infantry.description": "Le plus de kills infanterie",
        "award.structure.title": "Démolisseur",
        "award.structure.description": "Le plus de bâtiments détruits",
        "award.CAS_mission.title": "Spécialiste CAS",
        "award.CAS_mission.description": "Le plus de missions CAS accomplies",
        "award.CAP_mission.title": "Gardien CAP",
        "award.CAP_mission.description": "Le plus de missions CAP volées",
        "award.recon_mission.title": "Éclaireur",
        "award.recon_mission.description": "Le plus de missions de reco",
        "award.pilot_rescue.title": "Sauveteur",
        "award.pilot_rescue.description": "Le plus de pilotes récupérés",
        "award.intercept_cargo_plane.title": "Intercepteur de cargos",
        "award.intercept_cargo_plane.description": "Le plus d'avions cargo interceptés",
        "award.warehouse_delivery.title": "Routier",
        "award.warehouse_delivery.description": "Le plus de livraisons d'entrepôt",
        "award.zone_capture.title": "Conquérant",
        "award.zone_capture.description": "Le plus de zones capturées",
        "award.zone_upgrade.title": "Bâtisseur",
        "award.zone_upgrade.description": "Le plus d'améliorations de zones",
        "award.bomb_runway.title": "Casseur de pistes",
        "award.bomb_runway.description": "Le plus de pistes bombardées",
        "award.flight_time.title": "Pilote infatigable",
        "award.flight_time.description": "Le plus de temps de vol",
        "award.deaths.title": "Survivant",
        "award.deaths.description": "Le moins de morts parmi les joueurs actifs",
        # ejected pilots
        "ejected.heading": "Pilotes éjectés",
        "ejected.pilot": "Pilote",
        "ejected.altitude": "Altitude",
        "ejected.credits": "Crédits",
        "ejected.none": "Aucun pilote éjecté",
        # missions
        "missions.heading": "Missions actives",
        "missions.title": "Titre",
        "missions.description": "Description",
        "missions.type": "Type",
        "missions.status": "Statut",
        "missions.escort": "Escorte",
        "missions.attack": "Attaque",
        "missions.running": "En cours",
        "missions.stopped": "En pause",
        "missions.none": "Aucune mission active",
        # JavaScript (map page)
        "js.map.default_layer": "Par défaut",
        "js.modal.loading": "Chargement…",
        "js.modal.error": "Erreur au chargement des données",
        "js.coord.latitude": "Latitude",
        "js.coord.longitude": "Longitude",
        "js.coord.latlon": "Lat / Lon",
        "js.coord.decimal": "Décimal",
        "js.side.red": "rouge",
        "js.side.blue": "bleu",
        "js.side.neutral": "neutre",
        "js.side.disabled": "désactivée",
        "js.zone.unknown": "Zone inconnue",
        "js.zone.coalition": "Coalition",
        "js.zone.detected_units": "Unités détectées",
        "js.zone.level": "Niveau",
        "js.zone.forces": "Forces",
        "js.zone.group": "Groupe {id}",
        "js.zone.kind": "Type",
        "js.zone.waypoint": "Waypoint",
        "js.zone.garrison": "Garnison",
        "js.zone.buildings": "Bâtiments debout",
        "js.zone.capture": "Capture",
        "js.zone.capture_for": "{side} depuis {time}",
        "js.zone.capture_in_progress": "capture en cours",
        "js.zone.activity": "Activité",
        "js.zone.awake": "active",
        "js.zone.asleep": "en sommeil",
        "js.kind.airfield": "aérodrome",
        "js.kind.outpost": "avant-poste",
        "js.kind.factory": "usine",
        "js.kind.depot": "dépôt",
        "js.ejected.altitude": "Alt : {altitude} m",
        "js.convoy.tooltip": "Convoi d'assaut ({side})",
        "js.convoy.vehicles": "{n} véhicule(s)",
        "js.support.awacs": "AWACS",
        "js.support.tanker_boom": "Ravitailleur (perche)",
        "js.support.tanker_basket": "Ravitailleur (panier)",
        "js.support.tanker_both": "Ravitailleur (perche et panier)",
        "js.support.tanker": "Ravitailleur",
        "js.support.other": "Soutien",
        "js.freshness.offline": "Hors ligne",
        "js.freshness.connection_lost": "Connexion au serveur perdue",
        "js.freshness.fresh": "Données à jour ({age} s) • Actualisation dans {n} s",
        "js.freshness.stale": "Données anciennes ({minutes} min) • Actualisation dans {n} s",
        "js.freshness.refresh_in": "Actualisation dans {n} s",
        "js.ruler.point_a": "Point A",
        "js.ruler.point_b": "Point B",
        "js.ruler.click_to_set": "Cliquer pour placer",
        "js.settings.heading": "Réglages",
        "js.settings.coord_format": "Format des coordonnées",
        "js.settings.cruise_speed": "Vitesse de croisière (règle)",
        "js.settings.save": "Enregistrer",
        "js.pilot.decimal_degrees": "Degrés décimaux",
        "js.pilot.ddm": "Degrés minutes décimales (DDM)",
        "js.pilot.dms": "Degrés minutes secondes (DMS)",
        "js.pilot.other": "Autres infos",
        "js.pilot.altitude": "Altitude",
        "js.pilot.lost_credits": "Crédits perdus",
        "js.markpoint.default": "Markpoint",
        "js.markpoint.add_title": "Ajouter un markpoint",
        "js.markpoint.paste": "Coller des coordonnées",
        "js.markpoint.label_optional": "Libellé (facultatif)",
        "js.markpoint.label_placeholder": "Cible",
        "js.markpoint.add": "Ajouter",
        "js.markpoint.invalid": "Coordonnées invalides",
        "js.markpoint.invalid_alert": "Coordonnées invalides. Saisissez des coordonnées DMS, DDM ou décimales valides.",
        "js.markpoint.delete": "Supprimer",
    },
}

LANGUAGES: tuple[str, ...] = tuple(MESSAGES)

_current_language: ContextVar[str] = ContextVar("current_language", default=DEFAULT_LANGUAGE)


def parse_accept_language(header: str | None) -> list[str]:
    """Return the primary language tags of an Accept-Language header, most preferred first."""
    if not header:
        return []
    weighted: list[tuple[float, int, str]] = []
    for index, part in enumerate(header.split(",")):
        tag, _, params = part.strip().partition(";")
        tag = tag.strip().lower()
        if not tag or tag == "*":
            continue
        quality = 1.0
        params = params.strip()
        if params.startswith("q="):
            try:
                quality = float(params[2:])
            except ValueError:
                continue
        if quality <= 0:
            continue
        weighted.append((-quality, index, tag.split("-")[0]))
    return [tag for _, _, tag in sorted(weighted)]


def negotiate_language(cookie: str | None, accept_language: str | None) -> str:
    """The language of a request: the selector's cookie, else the browser's first supported language."""
    if cookie in LANGUAGES:
        return cookie
    for tag in parse_accept_language(accept_language):
        if tag in LANGUAGES:
            return tag
    return DEFAULT_LANGUAGE


def current_language() -> str:
    return _current_language.get()


def translate(key: str, language: str, **params: object) -> str:
    """The text of a key in a language, falling back to English, then to the key itself."""
    text = MESSAGES.get(language, {}).get(key) or MESSAGES[DEFAULT_LANGUAGE].get(key) or key
    return text.format(**params) if params else text


def t(key: str, **params: object) -> str:
    """The text of a key in the current request's language (the ``t()`` Jinja global)."""
    return translate(key, current_language(), **params)


def js_messages() -> dict[str, str]:
    """The texts the JavaScript needs, in the current language, keyed without their ``js.`` prefix."""
    language = current_language()
    return {
        key[len(JS_PREFIX) :]: translate(key, language)
        for key in MESSAGES[DEFAULT_LANGUAGE]
        if key.startswith(JS_PREFIX)
    }


def language_switch_url(request: Request, language: str) -> str:
    """The URL that sets a language and comes back to the current page."""
    here = request.url.path + (f"?{request.url.query}" if request.url.query else "")
    return f"{request.url_for('set_language', language=language).path}?next={quote(here, safe='')}"


def safe_next_path(next_path: str | None) -> str:
    """Only a local path is a valid redirect target (no open redirect to another site)."""
    if not next_path or not next_path.startswith("/") or next_path.startswith(("//", "/\\")):
        return "/"
    return next_path


class LanguageMiddleware:
    """Picks the language of each HTTP request and makes it the current one while the request runs."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        language = negotiate_language(request.cookies.get(LANGUAGE_COOKIE), request.headers.get("accept-language"))
        token = _current_language.set(language)
        try:
            await self.app(scope, receive, send)
        finally:
            _current_language.reset(token)
