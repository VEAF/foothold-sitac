import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from foothold_sitac.cache import _cache, clear_cache, get_cached_sitac, get_checked_at


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_cache()


@pytest.fixture
def status_file(tmp_path: Path) -> Path:
    """Create a minimal foothold.status file pointing to a Lua fixture."""
    lua_path = Path("tests/fixtures/test_hidden/Missions/Saves/foothold_hidden_test.lua")
    server_dir = tmp_path / "test_server" / "Missions" / "Saves"
    server_dir.mkdir(parents=True)
    status_file = server_dir / "foothold.status"
    status_file.write_text(str(lua_path.absolute()))
    return status_file


def test_cache_miss_calls_load_sitac(tmp_path: Path, status_file: Path) -> None:
    """First call should parse the Lua file."""
    with patch("foothold_sitac.cache.get_foothold_server_status_path", return_value=status_file):
        with patch("foothold_sitac.cache.detect_foothold_mission_path") as mock_detect:
            lua_path = Path("tests/fixtures/test_hidden/Missions/Saves/foothold_hidden_test.lua")
            mock_detect.return_value = lua_path
            with patch("foothold_sitac.cache.load_sitac") as mock_load:
                from foothold_sitac.foothold import load_sitac as real_load

                mock_load.side_effect = real_load
                result = get_cached_sitac("test_server")
                assert result is not None
                mock_load.assert_called_once()


def test_cache_hit_returns_same_object(tmp_path: Path, status_file: Path) -> None:
    """Second call with unchanged mtime should return the cached Sitac (same instance)."""
    with patch("foothold_sitac.cache.get_foothold_server_status_path", return_value=status_file):
        with patch("foothold_sitac.cache.detect_foothold_mission_path") as mock_detect:
            lua_path = Path("tests/fixtures/test_hidden/Missions/Saves/foothold_hidden_test.lua")
            mock_detect.return_value = lua_path
            with patch("foothold_sitac.cache.load_sitac") as mock_load:
                from foothold_sitac.foothold import load_sitac as real_load

                mock_load.side_effect = real_load
                first = get_cached_sitac("test_server")
                second = get_cached_sitac("test_server")
                assert first is second
                mock_load.assert_called_once()


def test_cache_invalidation_on_mtime_change(tmp_path: Path, status_file: Path) -> None:
    """Touching the status file should trigger a reload."""
    with patch("foothold_sitac.cache.get_foothold_server_status_path", return_value=status_file):
        with patch("foothold_sitac.cache.detect_foothold_mission_path") as mock_detect:
            lua_path = Path("tests/fixtures/test_hidden/Missions/Saves/foothold_hidden_test.lua")
            mock_detect.return_value = lua_path
            with patch("foothold_sitac.cache.load_sitac") as mock_load:
                from foothold_sitac.foothold import load_sitac as real_load

                mock_load.side_effect = real_load
                first = get_cached_sitac("test_server")

                # Touch the status file to change mtime
                time.sleep(0.05)
                os.utime(status_file, None)

                second = get_cached_sitac("test_server")
                assert first is not second
                assert mock_load.call_count == 2


def test_returns_none_when_status_file_missing() -> None:
    """Should return None if the status file doesn't exist."""
    missing_path = Path("/nonexistent/foothold.status")
    with patch("foothold_sitac.cache.get_foothold_server_status_path", return_value=missing_path):
        result = get_cached_sitac("no_server")
        assert result is None


def test_clears_stale_cache_when_status_file_disappears(tmp_path: Path, status_file: Path) -> None:
    """Removing the status file should clear the cache entry."""
    with patch("foothold_sitac.cache.get_foothold_server_status_path", return_value=status_file):
        with patch("foothold_sitac.cache.detect_foothold_mission_path") as mock_detect:
            lua_path = Path("tests/fixtures/test_hidden/Missions/Saves/foothold_hidden_test.lua")
            mock_detect.return_value = lua_path
            with patch("foothold_sitac.cache.load_sitac") as mock_load:
                from foothold_sitac.foothold import load_sitac as real_load

                mock_load.side_effect = real_load
                get_cached_sitac("test_server")
                assert "test_server" in _cache

                # Remove status file
                status_file.unlink()
                result = get_cached_sitac("test_server")
                assert result is None
                assert "test_server" not in _cache


def test_clear_cache_empties_all_entries(tmp_path: Path, status_file: Path) -> None:
    """clear_cache() should remove all entries."""
    with patch("foothold_sitac.cache.get_foothold_server_status_path", return_value=status_file):
        with patch("foothold_sitac.cache.detect_foothold_mission_path") as mock_detect:
            lua_path = Path("tests/fixtures/test_hidden/Missions/Saves/foothold_hidden_test.lua")
            mock_detect.return_value = lua_path
            with patch("foothold_sitac.cache.load_sitac") as mock_load:
                from foothold_sitac.foothold import load_sitac as real_load

                mock_load.side_effect = real_load
                get_cached_sitac("test_server")
                assert len(_cache) == 1

                clear_cache()
                assert len(_cache) == 0


def test_checked_at_updated_on_cache_hit(tmp_path: Path, status_file: Path) -> None:
    """checked_at should be updated on cache hit."""
    with patch("foothold_sitac.cache.get_foothold_server_status_path", return_value=status_file):
        with patch("foothold_sitac.cache.detect_foothold_mission_path") as mock_detect:
            lua_path = Path("tests/fixtures/test_hidden/Missions/Saves/foothold_hidden_test.lua")
            mock_detect.return_value = lua_path
            with patch("foothold_sitac.cache.load_sitac") as mock_load:
                from foothold_sitac.foothold import load_sitac as real_load

                mock_load.side_effect = real_load
                get_cached_sitac("test_server")
                first_checked = get_checked_at("test_server")
                assert first_checked is not None

                time.sleep(0.05)
                get_cached_sitac("test_server")
                second_checked = get_checked_at("test_server")
                assert second_checked is not None
                assert second_checked > first_checked


def test_get_checked_at_returns_none_for_unknown_server() -> None:
    """get_checked_at should return None for uncached servers."""
    assert get_checked_at("nonexistent") is None
