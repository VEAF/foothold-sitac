import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from foothold_sitac.unit_names import get_unit_display_names


def test_get_unit_display_names_missing_file() -> None:
    """Returns empty dict and logs warning when file does not exist."""
    get_unit_display_names.cache_clear()
    with patch("foothold_sitac.unit_names.UNIT_NAMES_PATH", Path("/nonexistent/path.json")):
        result = get_unit_display_names()
    assert result == {}
    get_unit_display_names.cache_clear()


def test_get_unit_display_names_loads_file() -> None:
    """Returns mapping from JSON file when it exists."""
    get_unit_display_names.cache_clear()
    mapping = {"T-72B3": "T-72B3", "M1A2C_SEP_V3": "M1A2 SEP V3 Abrams"}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(mapping, f)
        tmp_path = Path(f.name)

    try:
        with patch("foothold_sitac.unit_names.UNIT_NAMES_PATH", tmp_path):
            result = get_unit_display_names()
        assert result == mapping
    finally:
        tmp_path.unlink(missing_ok=True)
        get_unit_display_names.cache_clear()
