"""Briefing storage module - JSON file persistence."""

import json
from pathlib import Path
from uuid import UUID

from foothold_sitac.briefing import Briefing
from foothold_sitac.config import get_config


def get_briefings_path() -> Path:
    """Get path to briefings storage directory."""
    base_path = Path(get_config().dcs.saved_games)
    briefings_path = base_path / "_briefings"
    briefings_path.mkdir(exist_ok=True)
    return briefings_path


def get_briefing_file(briefing_id: UUID) -> Path:
    """Get path to a specific briefing file."""
    return get_briefings_path() / f"{briefing_id}.json"


def save_briefing(briefing: Briefing) -> None:
    """Save a briefing to disk."""
    file_path = get_briefing_file(briefing.id)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(briefing.model_dump(mode="json"), f, indent=2, default=str)


def load_briefing(briefing_id: UUID) -> Briefing | None:
    """Load a briefing from disk."""
    file_path = get_briefing_file(briefing_id)
    if not file_path.exists():
        return None
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    return Briefing.model_validate(data)


def delete_briefing(briefing_id: UUID) -> bool:
    """Delete a briefing file. Returns True if deleted, False if not found."""
    file_path = get_briefing_file(briefing_id)
    if file_path.exists():
        file_path.unlink()
        return True
    return False


def list_briefings(server_name: str | None = None) -> list[Briefing]:
    """List all briefings, optionally filtered by server."""
    briefings: list[Briefing] = []
    briefings_path = get_briefings_path()

    for file_path in briefings_path.glob("*.json"):
        try:
            briefing = load_briefing(UUID(file_path.stem))
            if briefing and (server_name is None or briefing.server_name == server_name):
                briefings.append(briefing)
        except (ValueError, json.JSONDecodeError):
            continue  # Skip invalid files

    return sorted(briefings, key=lambda b: b.updated_at, reverse=True)
