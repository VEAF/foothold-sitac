from pathlib import Path

import pytest

from foothold_sitac.veaf_campaign import (
    campaign_key,
    has_sitac_block,
    load_campaign_sitac,
    split_campaign_key,
)

FIXTURE = Path("tests/fixtures/test_veaf_campaign/Missions/Saves/Bouclier de l_Oronte/persistent.state")
OLD_STATE = Path("tests/fixtures/test_veaf_campaign/Missions/Saves/Old Campaign/persistent.state")


def test_campaign_key_round_trip() -> None:
    key = campaign_key("foothold2", "Bouclier de l_Oronte")
    assert key == "foothold2@Bouclier de l_Oronte"
    assert split_campaign_key(key) == ("foothold2", "Bouclier de l_Oronte")


@pytest.mark.parametrize("key", ["foothold2", "@campaign", "server@", "a@b@c", "server@..", "server@a/b", "..@x"])
def test_split_campaign_key_rejects_anything_else(key: str) -> None:
    assert split_campaign_key(key) is None


def test_has_sitac_block() -> None:
    assert has_sitac_block(FIXTURE)
    assert not has_sitac_block(OLD_STATE)
    assert not has_sitac_block(Path("tests/fixtures/does-not-exist.state"))


def test_load_campaign_sitac_reads_the_campaign() -> None:
    sitac = load_campaign_sitac(FIXTURE)
    assert sitac.source == "veaf"
    assert sitac.campaign_name == "Bouclier de l'Oronte"
    assert sitac.theatre == "Syria"
    assert list(sitac.zones) == ["Minakh", "Tal Rifaat", "Kafr Naya", "Anadan", "Aleppo"]


def test_zones_take_their_side_position_and_kind() -> None:
    zones = load_campaign_sitac(FIXTURE).zones
    assert zones["Minakh"].side == 2
    assert zones["Aleppo"].side == 1
    assert zones["Tal Rifaat"].side == 0
    assert zones["Minakh"].position.latitude == pytest.approx(36.5225, abs=1e-3)
    assert zones["Minakh"].position.longitude == pytest.approx(36.8778, abs=1e-3)
    assert zones["Minakh"].veaf is not None
    assert [zone.veaf.kind for zone in zones.values() if zone.veaf] == [
        "airfield",
        "outpost",
        "factory",
        "depot",
        "airfield",
    ]


def test_zone_details_are_counts_only() -> None:
    zones = load_campaign_sitac(FIXTURE).zones
    factory = zones["Kafr Naya"].veaf
    assert factory is not None
    assert factory.waypoint == 4
    assert (factory.garrison_alive, factory.garrison_total) == (5, 6)
    assert (factory.structures_standing, factory.structures_total) == (2, 3)
    assert factory.awake is False
    assert zones["Kafr Naya"].total_units == 5
    assert zones["Kafr Naya"].unit_groups == []
    neutral = zones["Tal Rifaat"].veaf
    assert neutral is not None
    assert (neutral.capture_side, neutral.capture_seconds) == ("blue", 42.5)
    assert neutral.garrison_total is None
    assert zones["Tal Rifaat"].total_units == 0


def test_connections_convoys_credits_and_resources() -> None:
    sitac = load_campaign_sitac(FIXTURE)
    assert [(c.from_zone, c.to_zone) for c in sitac.connections][0] == ("Minakh", "Tal Rifaat")
    assert len(sitac.connections) == 4
    assert len(sitac.convoys) == 1
    convoy = sitac.convoys[0]
    assert (convoy.side, convoy.from_zone, convoy.to_zone, convoy.units) == ("blue", "Minakh", "Tal Rifaat", 3)
    assert (sitac.accounts.blue, sitac.accounts.red) == (1915, 0)
    assert sitac.resources is not None
    assert (sitac.resources.blue, sitac.resources.red) == (600, 250)


def test_progress_counts_owned_zones() -> None:
    # 1 blue, 3 red, the neutral ignored
    assert load_campaign_sitac(FIXTURE).campaign_progress == pytest.approx(25.0)


def test_a_state_file_cannot_run_code(tmp_path: Path) -> None:
    state = tmp_path / "persistent.state"
    state.write_text('return { sitac = { campaign = os.getenv("PATH") } }', encoding="utf-8")
    with pytest.raises(ValueError):
        load_campaign_sitac(state)


def test_a_state_file_without_sitac_is_refused() -> None:
    with pytest.raises(ValueError):
        load_campaign_sitac(OLD_STATE)


def test_a_campaign_is_listed_while_only_its_temporary_holds_the_block(tmp_path: Path) -> None:
    from unittest.mock import patch

    from foothold_sitac.veaf_campaign import list_campaigns

    folder = tmp_path / "Oronte"
    folder.mkdir()
    (folder / "persistent.state.tmp").write_bytes(FIXTURE.read_bytes())
    (folder / "persistent.state").write_text("return {", encoding="utf-8")
    with patch("foothold_sitac.veaf_campaign.get_foothold_server_saves_path", return_value=tmp_path):
        assert list_campaigns("server") == ["server@Oronte"]
