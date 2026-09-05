from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from foothold_sitac.cache import clear_cache
from foothold_sitac.config import AppConfig
from foothold_sitac.foothold import load_sitac
from foothold_sitac.main import app


OLD_SAVE = Path("tests/fixtures/test_player_stats/Missions/Saves/foothold_player_stats.lua")
VIPER_ID = "00000000000000000000000000000001"
EAGLE_ID = "00000000000000000000000000000002"


@pytest.fixture
def identity_save(tmp_path: Path) -> Path:
    save = tmp_path / "identity" / "Missions" / "Saves" / "mission.lua"
    save.parent.mkdir(parents=True)
    save.write_text(
        OLD_SAVE.read_text(encoding="utf-8")
        + f"""
local old = zonePersistance.playerStats
zonePersistance.playerStatsIdentityVersion = 1
zonePersistance.playerStats = {{
    ["{VIPER_ID}"] = {{name = "Viper", stats = old.Viper}},
    ["{EAGLE_ID}"] = {{name = "Eagle", stats = old.Eagle}},
}}
zonePersistance.legacyPlayerStats = {{Falcon = old.Falcon}}
zonePersistance.players = {{
    {{playerName = "Viper", coalition = "blue", unitType = "F-16C_50", latitude = 50, longitude = 8}}
}}
""",
        encoding="utf-8",
    )
    (save.parent / "foothold.status").write_text(save.as_posix(), encoding="utf-8")
    return save


@pytest.fixture
def identity_client(identity_save: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    config = AppConfig.model_validate({"dcs": {"saved_games": str(identity_save.parents[3])}})
    monkeypatch.setattr("foothold_sitac.foothold.get_config", lambda: config)
    clear_cache()
    with TestClient(app) as client:
        yield client
    clear_cache()


def test_unversioned_stats_keep_names_and_counters() -> None:
    sitac = load_sitac(OLD_SAVE)
    assert set(sitac.player_stats) == {"Viper", "Eagle", "Falcon"}
    assert sitac.player_stats["Viper"].points == 1500
    assert sitac.player_stats["Viper"].air == 12
    assert sitac.player_stats["Viper"].flight_time == 320.5


def test_versioned_stats_preserve_all_counters_and_legacy_players(identity_save: Path) -> None:
    sitac = load_sitac(identity_save)
    assert set(sitac.player_stats) == {"Viper", "Eagle", "Falcon"}
    assert sitac.player_stats["Viper"].points == 1500
    assert sitac.player_stats["Eagle"].points == 2000
    assert sitac.player_stats["Falcon"].points == 800
    assert sitac.player_stats == load_sitac(OLD_SAVE).player_stats


def test_duplicate_names_never_overwrite_histories(identity_save: Path) -> None:
    with identity_save.open("a", encoding="utf-8") as save:
        save.write(f'\nzonePersistance.playerStats["{EAGLE_ID}"].name = "Viper"\n')
        save.write('zonePersistance.legacyPlayerStats["Viper"] = {Points = 25}\n')
        save.write('zonePersistance.legacyPlayerStats["Viper (2)"] = {Points = 77}\n')
    expected = {"Viper": 1500, "Viper (3)": 2000, "Falcon": 800, "Viper (4)": 25, "Viper (2)": 77}
    for _ in range(3):
        sitac = load_sitac(identity_save)
        assert {name: stats.points for name, stats in sitac.player_stats.items()} == expected


@pytest.mark.parametrize("version", ["2", "0", "true", "false", '"1"'])
def test_unsupported_identity_version_is_not_silently_misread(identity_save: Path, version: str) -> None:
    with identity_save.open("a", encoding="utf-8") as save:
        save.write(f"\nzonePersistance.playerStatsIdentityVersion = {version}\n")
    with pytest.raises(ValueError, match="Unsupported playerStatsIdentityVersion"):
        load_sitac(identity_save)


@pytest.mark.parametrize("statistics", ["nil", "false", "0", '"invalid"'])
def test_missing_or_invalid_statistics_table_is_rejected(identity_save: Path, statistics: str) -> None:
    with identity_save.open("a", encoding="utf-8") as save:
        save.write(f"\nzonePersistance.playerStats = {statistics}\n")
    with pytest.raises(ValueError, match="Invalid playerStats"):
        load_sitac(identity_save)


@pytest.mark.parametrize("record", ["{stats = {Points = 10}}", '{name = "Viper"}', '{name = "", stats = {}}'])
def test_malformed_identity_record_does_not_become_zero_stats(identity_save: Path, record: str) -> None:
    with identity_save.open("a", encoding="utf-8") as save:
        save.write(f'\nzonePersistance.playerStats["{VIPER_ID}"] = {record}\n')
    with pytest.raises(ValueError, match="Invalid UCID playerStats record"):
        load_sitac(identity_save)


def test_empty_new_statistics_and_absent_legacy_section(identity_save: Path) -> None:
    with identity_save.open("a", encoding="utf-8") as save:
        save.write("\nzonePersistance.playerStats = {}\nzonePersistance.legacyPlayerStats = nil\n")
    assert load_sitac(identity_save).player_stats == {}


def test_empty_counters_for_a_named_player_are_valid(identity_save: Path) -> None:
    with identity_save.open("a", encoding="utf-8") as save:
        save.write(f'\nzonePersistance.playerStats["{VIPER_ID}"].stats = {{}}\n')
    assert load_sitac(identity_save).player_stats["Viper"].points == 0


def test_versioned_stats_api_preserves_values_without_exposing_ucids(identity_client: TestClient) -> None:
    response = identity_client.get("/api/foothold/identity/sitac")
    assert response.status_code == 200
    stats = response.json()["playerStats"]
    assert set(stats) == {"Viper", "Eagle", "Falcon"}
    assert stats["Viper"]["Points"] == 1500
    assert stats["Viper"]["Air"] == 12
    assert stats["Falcon"]["Points"] == 800
    assert VIPER_ID not in response.text
    assert EAGLE_ID not in response.text


@pytest.mark.parametrize(
    ("page", "score"),
    [
        ("/sitac/identity", "1500"),
        ("/map/identity/players", "1500"),
        ("/player/identity/Viper", "1500"),
        ("/success/identity", "2000"),
    ],
)
def test_versioned_player_pages_render_names_and_scores(identity_client: TestClient, page: str, score: str) -> None:
    response = identity_client.get("/foothold" + page)
    assert response.status_code == 200
    assert "Viper" in response.text
    assert score in response.text
    assert VIPER_ID not in response.text
    assert EAGLE_ID not in response.text


def test_versioned_stats_do_not_change_map_players_or_zones(identity_client: TestClient) -> None:
    response = identity_client.get("/api/foothold/identity/map.json")
    assert response.status_code == 200
    data = response.json()
    assert [zone["name"] for zone in data["zones"]] == ["TestZone"]
    assert data["players"][0]["player_name"] == "Viper"
