"""CLI entry point for Foothold Sitac.

Usage::

    foothold-sitac serve
    foothold-sitac extract-unit-names --dcs-path "C:\\..."
"""

from pathlib import Path
from typing import Annotated, Optional

import typer
import uvicorn

from foothold_sitac.config import get_config

app = typer.Typer(name="foothold-sitac", help="Foothold Sitac — tactical map server for DCS World")


@app.command()
def serve() -> None:
    """Start the Foothold Sitac web server."""
    config = get_config()
    uvicorn.run(
        "foothold_sitac.main:app",
        host=config.web.host,
        port=config.web.port,
        reload=config.web.reload,
    )


@app.command()
def extract_unit_names(
    dcs_path: Annotated[
        Optional[str],
        typer.Option(help="Path to DCS World installation (reads dcs.install_path from config if not set)"),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option(help="Output JSON file path"),
    ] = None,
) -> None:
    """Extract unit type DisplayNames from a DCS World installation."""
    from foothold_sitac.unit_names import UNIT_NAMES_PATH, extract_all, save_unit_display_names

    resolved_path = dcs_path or get_config().dcs.install_path
    if not resolved_path:
        typer.echo("Error: No DCS path provided. Use --dcs-path or set dcs.install_path in config.yml", err=True)
        raise typer.Exit(code=1)

    dcs = Path(resolved_path)
    if not dcs.exists():
        typer.echo(f"Error: DCS path does not exist: {dcs}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Extracting unit names from: {dcs}")
    mappings = extract_all(dcs)

    if not mappings:
        typer.echo("Warning: No unit mappings found. Check the DCS path.", err=True)
        raise typer.Exit(code=1)

    out = output or UNIT_NAMES_PATH
    save_unit_display_names(mappings, out)
    typer.echo(f"Written {len(mappings)} unit display names to {out}")
