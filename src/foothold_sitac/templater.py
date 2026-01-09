from importlib.resources import files
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from foothold_sitac.config import get_config

templates_path = files("foothold_sitac") / "templates"
static_path = Path(str(files("foothold_sitac") / "static"))


def _base36_encode(num: int) -> str:
    """Encode an integer to base36 string."""
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    if num == 0:
        return "0"
    result = ""
    while num:
        num, rem = divmod(num, 36)
        result = chars[rem] + result
    return result


def static_url(path: str) -> str:
    """Generate static URL with cache-busting version based on file modification time."""
    file_path = static_path / path
    if file_path.exists():
        mtime = int(file_path.stat().st_mtime)
        version = _base36_encode(mtime)
        return f"/static/{path}?v={version}"
    return f"/static/{path}"


env = Environment(loader=FileSystemLoader(str(templates_path)))
env.globals["config"] = get_config()  # add all variables accessibles in templates
env.globals["static_url"] = static_url  # cache-busting for static assets
