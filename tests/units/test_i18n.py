# test foothold_sitac/i18n.py

import json
import re
import shutil
import string
import subprocess
from pathlib import Path

import pytest

from foothold_sitac.foothold_router import SUCCESS_CATEGORIES
from foothold_sitac.i18n import (
    DEFAULT_LANGUAGE,
    JS_PREFIX,
    LANGUAGE_NAMES,
    LANGUAGES,
    MESSAGES,
    negotiate_language,
    parse_accept_language,
    safe_next_path,
    translate,
)

TEMPLATES_PATH = Path("src/foothold_sitac/templates")
JS_PATH = Path("src/foothold_sitac/static/js")

# t('key') or t("key") with a literal key; dynamic keys ('award.' ~ key) are checked apart
LITERAL_KEY = re.compile(r"""\bt\(\s*['"]([\w.]+)['"]\s*[,)]""")


def _placeholders(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


@pytest.mark.parametrize("language", [lang for lang in LANGUAGES if lang != DEFAULT_LANGUAGE])
def test_every_language_has_the_same_keys(language: str) -> None:
    reference = set(MESSAGES[DEFAULT_LANGUAGE])
    keys = set(MESSAGES[language])
    assert sorted(reference - keys) == [], f"keys missing in '{language}'"
    assert sorted(keys - reference) == [], f"keys in '{language}' but not in '{DEFAULT_LANGUAGE}'"


@pytest.mark.parametrize("language", LANGUAGES)
def test_translations_keep_the_placeholders(language: str) -> None:
    different = [
        key
        for key, text in MESSAGES[DEFAULT_LANGUAGE].items()
        if key in MESSAGES[language] and _placeholders(MESSAGES[language][key]) != _placeholders(text)
    ]
    assert different == []


def test_every_language_has_a_name() -> None:
    assert set(LANGUAGE_NAMES) == set(LANGUAGES)


def test_template_keys_exist() -> None:
    missing = []
    for template in TEMPLATES_PATH.rglob("*.html"):
        for key in LITERAL_KEY.findall(template.read_text(encoding="utf-8")):
            if key not in MESSAGES[DEFAULT_LANGUAGE]:
                missing.append(f"{template.name}: {key}")
    assert missing == []


def test_success_award_keys_exist() -> None:
    missing = [
        f"award.{category.field}.{part}"
        for category in SUCCESS_CATEGORIES
        for part in ("title", "description")
        if f"award.{category.field}.{part}" not in MESSAGES[DEFAULT_LANGUAGE]
    ]
    assert missing == []


def test_js_keys_exist() -> None:
    missing = []
    for script in JS_PATH.glob("*.js"):
        for key in LITERAL_KEY.findall(script.read_text(encoding="utf-8")):
            if JS_PREFIX + key not in MESSAGES[DEFAULT_LANGUAGE]:
                missing.append(f"{script.name}: {key}")
    assert missing == []


@pytest.mark.parametrize(
    "key",
    [f"side.{side}" for side in ("red", "blue", "neutral", "disabled")]
    + [f"kind.{kind}" for kind in ("airfield", "outpost", "factory", "depot")]
    + [f"support.{kind}" for kind in ("awacs", "tanker_boom", "tanker_basket", "tanker_both", "tanker", "other")],
)
def test_js_dynamic_keys_exist(key: str) -> None:
    assert JS_PREFIX + key in MESSAGES[DEFAULT_LANGUAGE]


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (None, []),
        ("", []),
        ("fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7", ["fr", "fr", "en", "en"]),
        ("en;q=0.5, fr", ["fr", "en"]),
        ("de, *;q=0.1", ["de"]),
        ("fr;q=0, en", ["en"]),
        ("fr;q=abc, en", ["en"]),
    ],
)
def test_parse_accept_language(header: str | None, expected: list[str]) -> None:
    assert parse_accept_language(header) == expected


@pytest.mark.parametrize(
    ("cookie", "accept_language", "expected"),
    [
        (None, None, "en"),
        (None, "fr-FR,fr;q=0.9,en;q=0.8", "fr"),
        (None, "en-US,en;q=0.9,fr;q=0.8", "en"),
        (None, "de-DE,de;q=0.9,fr;q=0.5", "fr"),
        (None, "de-DE", "en"),
        ("en", "fr-FR", "en"),
        ("fr", "en-US", "fr"),
        ("xx", "fr-FR", "fr"),
    ],
)
def test_negotiate_language(cookie: str | None, accept_language: str | None, expected: str) -> None:
    assert negotiate_language(cookie, accept_language) == expected


def test_translate_fills_placeholders_and_falls_back() -> None:
    assert translate("servers.updated_min", "fr", n=3) == "Mis à jour il y a 3 min"
    assert translate("servers.updated_min", "en", n=3) == "Updated 3 min ago"
    assert translate("no.such.key", "fr") == "no.such.key"


@pytest.mark.parametrize(
    ("next_path", "expected"),
    [
        (None, "/"),
        ("", "/"),
        ("/foothold/map/x?a=1", "/foothold/map/x?a=1"),
        ("//evil.example", "/"),
        ("/\\evil.example", "/"),
        ("https://evil.example", "/"),
    ],
)
def test_safe_next_path(next_path: str | None, expected: str) -> None:
    assert safe_next_path(next_path) == expected


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_js_t() -> None:
    script = (
        f"const i18n = require({json.dumps(str((JS_PATH / 'i18n.js').resolve()))});"
        "i18n.setMessages({'a': 'Group {id}', 'side.red': 'rouge'});"
        "console.log(JSON.stringify(["
        "i18n.t('a', {id: 3}), i18n.t('a'), i18n.t('a', {}), i18n.t('missing'),"
        "i18n.tOr('side.red', 'red'), i18n.tOr('side.green', 'green')]));"
    )
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)

    assert json.loads(result.stdout) == ["Group 3", "Group {id}", "Group {id}", "missing", "rouge", "green"]
