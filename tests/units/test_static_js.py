import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

JS_PATH = Path("src/foothold_sitac/static/js")
MAP_TEMPLATE = Path("src/foothold_sitac/templates/foothold/map.html")

# Data fields that come from persistence files or user input and end up in markup
DATA_FIELD = re.compile(r"\b\w+\.(player_name|name|title|unit_type|label|color|side|flavor_text)\b")
HTML_SINK = re.compile(r"'[^']*<[a-z/]|bindTooltip\(")


def _escaped_spans(line: str) -> list[tuple[int, int]]:
    """Return the (start, end) spans covered by escapeHtml(...) calls on a line."""
    spans = []
    for match in re.finditer(r"escapeHtml\(", line):
        depth, index = 1, match.end()
        while index < len(line) and depth:
            depth += {"(": 1, ")": -1}.get(line[index], 0)
            index += 1
        spans.append((match.start(), index))
    return spans


@pytest.mark.parametrize("script", ["map.js", "modals.js"])
def test_data_fields_are_escaped_in_markup(script: str) -> None:
    unescaped = []
    for number, line in enumerate((JS_PATH / script).read_text(encoding="utf-8").splitlines(), start=1):
        if not HTML_SINK.search(line):
            continue
        spans = _escaped_spans(line)
        for match in DATA_FIELD.finditer(line):
            if not any(start <= match.start() < end for start, end in spans):
                unescaped.append(f"{script}:{number}: {match.group(0)}")
    assert unescaped == []


def test_html_js_is_loaded_before_scripts_using_it() -> None:
    template = MAP_TEMPLATE.read_text(encoding="utf-8")
    html_js = template.index("js/html.js")
    assert html_js < template.index("js/modals.js")
    assert html_js < template.index("js/map.js")


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_escape_html() -> None:
    values = ["<i>Viper</i>", "a & b", "say \"hi\" & 'bye'", "plain", None, 42]
    script = (
        f"const {{ escapeHtml }} = require({json.dumps(str((JS_PATH / 'html.js').resolve()))});"
        f"console.log(JSON.stringify({json.dumps(values)}.map(escapeHtml)));"
    )
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True)

    assert json.loads(result.stdout) == [
        "&lt;i&gt;Viper&lt;/i&gt;",
        "a &amp; b",
        "say &quot;hi&quot; &amp; &#39;bye&#39;",
        "plain",
        "",
        "42",
    ]
