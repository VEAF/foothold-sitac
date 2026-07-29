"""DCS unit type to display name translation.

Loads a static JSON mapping of DCS internal unit type codes to
human-readable display names from var/unit_display_names.json.
The file is generated via the CLI: ``foothold-sitac extract-unit-names``.

Keys are stored in **lowercase** to avoid case-mismatch issues at lookup time.
"""

import json
import logging
import re
from functools import cache
from pathlib import Path

logger = logging.getLogger(__name__)

UNIT_NAMES_PATH = Path("var/unit_display_names.json")

# ---------------------------------------------------------------------------
# Extraction helpers (used by the CLI command and startup auto-refresh)
# ---------------------------------------------------------------------------

# Regex patterns for DCS Lua unit definitions
_TYPE_PATTERN = re.compile(r'(?:type|Name)\s*=\s*"([^"]+)"')
_DISPLAY_NAME_PATTERN = re.compile(r'DisplayName\s*=\s*_\(\s*"([^"]+)"\s*\)')

# Glob patterns that match Lua files likely to contain unit definitions.
# This avoids scanning thousands of irrelevant Lua files (cockpit, UI, …).
_UNIT_FILE_GLOBS = [
    "Scripts/Database/**/*.lua",
    "CoreMods/**/Database/**/*.lua",
    "CoreMods/**/Entry/**/*.lua",
    "CoreMods/**/Entries/**/*.lua",
    "CoreMods/aircraft/*/*.lua",
    "CoreMods/WWII Units/*/*.lua",
    "Mods/tech/**/Database/**/*.lua",
    "Mods/tech/**/Entries/**/*.lua",
]


def extract_from_file(filepath: Path) -> dict[str, str]:
    """Extract type -> DisplayName pairs from a single Lua file.

    Uses a proximity-based approach: for each DisplayName found,
    looks backward for the nearest type/Name declaration within
    a reasonable range (same logical block).
    Keys are lowercased.
    """
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}

    mappings: dict[str, str] = {}

    for dn_match in _DISPLAY_NAME_PATTERN.finditer(content):
        display_name = dn_match.group(1)
        dn_pos = dn_match.start()

        search_start = max(0, dn_pos - 2000)
        search_region = content[search_start:dn_pos]

        type_matches = list(_TYPE_PATTERN.finditer(search_region))
        if type_matches:
            type_name = type_matches[-1].group(1)
            if len(type_name) < 100 and "/" not in type_name and "\\" not in type_name:
                mappings[type_name.lower()] = display_name

    return mappings


def extract_all(dcs_path: Path) -> dict[str, str]:
    """Scan a DCS installation directory and extract all unit type mappings.

    Returns a sorted dict ``{type_name_lower: display_name, ...}``.
    """
    all_mappings: dict[str, str] = {}
    seen_files: set[Path] = set()

    for pattern in _UNIT_FILE_GLOBS:
        for lua_file in dcs_path.glob(pattern):
            if lua_file in seen_files:
                continue
            seen_files.add(lua_file)
            all_mappings.update(extract_from_file(lua_file))

    logger.info("Scanned %d files, found %d unit type mappings", len(seen_files), len(all_mappings))
    return dict(sorted(all_mappings.items()))


def save_unit_display_names(mappings: dict[str, str], output: Path = UNIT_NAMES_PATH) -> None:
    """Write the mapping dict as sorted JSON."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(mappings, f, indent=2, ensure_ascii=False)
    logger.info("Written %d unit display names to %s", len(mappings), output)


def refresh_unit_display_names(dcs_path: Path) -> int:
    """Extract unit names from *dcs_path* and save to the default JSON file.

    Returns the number of mappings written.
    """
    mappings = extract_all(dcs_path)
    if mappings:
        save_unit_display_names(mappings)
    return len(mappings)


# ---------------------------------------------------------------------------
# Runtime lookup (used by the API router)
# ---------------------------------------------------------------------------


@cache
def get_unit_display_names() -> dict[str, str]:
    """Load unit type -> display name mapping from JSON file.

    Keys are lowercase. Returns an empty dict with a warning if the file
    does not exist.
    """
    if not UNIT_NAMES_PATH.exists():
        logger.warning(
            "Unit display names file not found at %s. Run 'foothold-sitac extract-unit-names' to generate it.",
            UNIT_NAMES_PATH,
        )
        return {}
    with open(UNIT_NAMES_PATH, encoding="utf-8") as f:
        mapping: dict[str, str] = json.load(f)
    logger.info("Loaded %d unit display names from %s", len(mapping), UNIT_NAMES_PATH)
    return mapping
