from jinja2 import Environment, FileSystemLoader
from app.config import get_config

env = Environment(loader=FileSystemLoader("templates"))
env.globals["config"] = get_config()  # add all variables accessibles in templates
