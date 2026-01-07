from importlib.resources import files

from jinja2 import Environment, FileSystemLoader

from foothold_sitac.config import get_config

templates_path = files("foothold_sitac") / "templates"
env = Environment(loader=FileSystemLoader(str(templates_path)))
env.globals["config"] = get_config()  # add all variables accessibles in templates
