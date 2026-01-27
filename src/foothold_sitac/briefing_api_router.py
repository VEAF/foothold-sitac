"""Briefing API router - REST endpoints for briefing CRUD operations."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from foothold_sitac.briefing import (
    Briefing,
    BriefingCreate,
    BriefingCreateResponse,
    BriefingLinks,
    BriefingListItem,
    BriefingUpdate,
    Flight,
    FlightCreate,
    FlightUpdate,
    Homeplate,
    HomeplateCreate,
    HomeplateUpdate,
    Objective,
    ObjectiveCreate,
    ObjectiveUpdate,
    Package,
    PackageCreate,
    PackageUpdate,
)
from foothold_sitac.briefing_storage import (
    delete_briefing,
    list_briefings,
    load_briefing,
    save_briefing,
)
from foothold_sitac.dependencies import get_sitac_or_none

router = APIRouter()


# === Helper Functions ===


def verify_edit_token(briefing: Briefing, token: UUID) -> None:
    """Verify edit token matches."""
    if briefing.edit_token != token:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid edit token")


def get_briefing_or_404(briefing_id: UUID) -> Briefing:
    """Load briefing or raise 404."""
    briefing = load_briefing(briefing_id)
    if not briefing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Briefing not found")
    return briefing


def make_briefing_response(briefing: Briefing) -> Briefing:
    """Create a copy of briefing with edit_token hidden."""
    return briefing.model_copy(update={"edit_token": UUID(int=0)})


# === Briefing CRUD ===


@router.get("", response_model=list[BriefingListItem])
async def list_all_briefings(server: str | None = None) -> list[BriefingListItem]:
    """List all briefings, optionally filtered by server."""
    briefings = list_briefings(server)
    return [
        BriefingListItem(
            id=b.id,
            title=b.title,
            server_name=b.server_name,
            created_at=b.created_at,
            updated_at=b.updated_at,
            packages_count=len(b.packages),
            objectives_count=len(b.objectives),
        )
        for b in briefings
    ]


@router.post("", response_model=BriefingCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_briefing(data: BriefingCreate) -> BriefingCreateResponse:
    """Create a new briefing."""
    briefing = Briefing(
        server_name=data.server_name,
        title=data.title,
        mission_date=data.mission_date,
        mission_time=data.mission_time,
    )
    save_briefing(briefing)

    return BriefingCreateResponse(
        briefing=briefing,
        links=BriefingLinks(
            view_url=f"/foothold/briefing/{briefing.id}",
            edit_url=f"/foothold/briefing/{briefing.id}/edit?token={briefing.edit_token}",
        ),
    )


@router.get("/{briefing_id}", response_model=Briefing)
async def get_briefing(briefing_id: UUID) -> Briefing:
    """Get a briefing (read-only, edit_token is hidden)."""
    briefing = get_briefing_or_404(briefing_id)
    return make_briefing_response(briefing)


@router.put("/{briefing_id}", response_model=Briefing)
async def update_briefing(
    briefing_id: UUID,
    data: BriefingUpdate,
    token: Annotated[UUID, Query()],
) -> Briefing:
    """Update briefing metadata (requires edit token)."""
    briefing = get_briefing_or_404(briefing_id)
    verify_edit_token(briefing, token)

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(briefing, key, value)
    briefing.updated_at = datetime.now()

    save_briefing(briefing)
    return briefing


@router.delete("/{briefing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_briefing_endpoint(
    briefing_id: UUID,
    token: Annotated[UUID, Query()],
) -> None:
    """Delete a briefing (requires edit token)."""
    briefing = get_briefing_or_404(briefing_id)
    verify_edit_token(briefing, token)
    delete_briefing(briefing_id)


# === Homeplates (airbases) ===


@router.post("/{briefing_id}/homeplates", response_model=Homeplate, status_code=status.HTTP_201_CREATED)
async def add_homeplate(
    briefing_id: UUID,
    data: HomeplateCreate,
    token: Annotated[UUID, Query()],
) -> Homeplate:
    """Add an airbase (homeplate) to the briefing."""
    briefing = get_briefing_or_404(briefing_id)
    verify_edit_token(briefing, token)

    homeplate = Homeplate(**data.model_dump())
    briefing.homeplates.append(homeplate)
    briefing.updated_at = datetime.now()
    save_briefing(briefing)

    return homeplate


@router.put("/{briefing_id}/homeplates/{homeplate_id}", response_model=Homeplate)
async def update_homeplate(
    briefing_id: UUID,
    homeplate_id: UUID,
    data: HomeplateUpdate,
    token: Annotated[UUID, Query()],
) -> Homeplate:
    """Update an airbase (homeplate)."""
    briefing = get_briefing_or_404(briefing_id)
    verify_edit_token(briefing, token)

    homeplate = next((h for h in briefing.homeplates if h.id == homeplate_id), None)
    if not homeplate:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Homeplate not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(homeplate, key, value)
    briefing.updated_at = datetime.now()
    save_briefing(briefing)

    return homeplate


@router.delete("/{briefing_id}/homeplates/{homeplate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_homeplate(
    briefing_id: UUID,
    homeplate_id: UUID,
    token: Annotated[UUID, Query()],
) -> None:
    """Remove an airbase (homeplate) from the briefing."""
    briefing = get_briefing_or_404(briefing_id)
    verify_edit_token(briefing, token)

    briefing.homeplates = [h for h in briefing.homeplates if h.id != homeplate_id]
    briefing.updated_at = datetime.now()
    save_briefing(briefing)


# === Objectives ===


@router.post("/{briefing_id}/objectives", response_model=Objective, status_code=status.HTTP_201_CREATED)
async def add_objective(
    briefing_id: UUID,
    data: ObjectiveCreate,
    token: Annotated[UUID, Query()],
) -> Objective:
    """Add an objective to a briefing."""
    briefing = get_briefing_or_404(briefing_id)
    verify_edit_token(briefing, token)

    objective = Objective(**data.model_dump())
    briefing.objectives.append(objective)
    briefing.updated_at = datetime.now()
    save_briefing(briefing)

    return objective


@router.put("/{briefing_id}/objectives/{objective_id}", response_model=Objective)
async def update_objective(
    briefing_id: UUID,
    objective_id: UUID,
    data: ObjectiveUpdate,
    token: Annotated[UUID, Query()],
) -> Objective:
    """Update an objective."""
    briefing = get_briefing_or_404(briefing_id)
    verify_edit_token(briefing, token)

    objective = next((o for o in briefing.objectives if o.id == objective_id), None)
    if not objective:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Objective not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(objective, key, value)
    briefing.updated_at = datetime.now()
    save_briefing(briefing)

    return objective


@router.delete("/{briefing_id}/objectives/{objective_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_objective(
    briefing_id: UUID,
    objective_id: UUID,
    token: Annotated[UUID, Query()],
) -> None:
    """Remove an objective from a briefing."""
    briefing = get_briefing_or_404(briefing_id)
    verify_edit_token(briefing, token)

    briefing.objectives = [o for o in briefing.objectives if o.id != objective_id]
    briefing.updated_at = datetime.now()
    save_briefing(briefing)


# === Packages ===


@router.post("/{briefing_id}/packages", response_model=Package, status_code=status.HTTP_201_CREATED)
async def add_package(
    briefing_id: UUID,
    data: PackageCreate,
    token: Annotated[UUID, Query()],
) -> Package:
    """Add a package to a briefing."""
    briefing = get_briefing_or_404(briefing_id)
    verify_edit_token(briefing, token)

    package = Package(**data.model_dump())
    briefing.packages.append(package)
    briefing.updated_at = datetime.now()
    save_briefing(briefing)

    return package


@router.put("/{briefing_id}/packages/{package_id}", response_model=Package)
async def update_package(
    briefing_id: UUID,
    package_id: UUID,
    data: PackageUpdate,
    token: Annotated[UUID, Query()],
) -> Package:
    """Update a package."""
    briefing = get_briefing_or_404(briefing_id)
    verify_edit_token(briefing, token)

    package = next((p for p in briefing.packages if p.id == package_id), None)
    if not package:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Package not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(package, key, value)
    briefing.updated_at = datetime.now()
    save_briefing(briefing)

    return package


@router.delete("/{briefing_id}/packages/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_package(
    briefing_id: UUID,
    package_id: UUID,
    token: Annotated[UUID, Query()],
) -> None:
    """Remove a package from a briefing."""
    briefing = get_briefing_or_404(briefing_id)
    verify_edit_token(briefing, token)

    briefing.packages = [p for p in briefing.packages if p.id != package_id]
    briefing.updated_at = datetime.now()
    save_briefing(briefing)


# === Flights ===


@router.post(
    "/{briefing_id}/packages/{package_id}/flights",
    response_model=Flight,
    status_code=status.HTTP_201_CREATED,
)
async def add_flight(
    briefing_id: UUID,
    package_id: UUID,
    data: FlightCreate,
    token: Annotated[UUID, Query()],
) -> Flight:
    """Add a flight to a package."""
    briefing = get_briefing_or_404(briefing_id)
    verify_edit_token(briefing, token)

    package = next((p for p in briefing.packages if p.id == package_id), None)
    if not package:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Package not found")

    flight = Flight(**data.model_dump())
    package.flights.append(flight)
    briefing.updated_at = datetime.now()
    save_briefing(briefing)

    return flight


@router.put("/{briefing_id}/packages/{package_id}/flights/{flight_id}", response_model=Flight)
async def update_flight(
    briefing_id: UUID,
    package_id: UUID,
    flight_id: UUID,
    data: FlightUpdate,
    token: Annotated[UUID, Query()],
) -> Flight:
    """Update a flight."""
    briefing = get_briefing_or_404(briefing_id)
    verify_edit_token(briefing, token)

    package = next((p for p in briefing.packages if p.id == package_id), None)
    if not package:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Package not found")

    flight = next((f for f in package.flights if f.id == flight_id), None)
    if not flight:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Flight not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(flight, key, value)
    briefing.updated_at = datetime.now()
    save_briefing(briefing)

    return flight


@router.delete(
    "/{briefing_id}/packages/{package_id}/flights/{flight_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_flight(
    briefing_id: UUID,
    package_id: UUID,
    flight_id: UUID,
    token: Annotated[UUID, Query()],
) -> None:
    """Remove a flight from a package."""
    briefing = get_briefing_or_404(briefing_id)
    verify_edit_token(briefing, token)

    package = next((p for p in briefing.packages if p.id == package_id), None)
    if not package:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Package not found")

    package.flights = [f for f in package.flights if f.id != flight_id]
    briefing.updated_at = datetime.now()
    save_briefing(briefing)


# === Zone Helper ===


@router.get("/{briefing_id}/zones", response_model=list[str])
async def get_available_zones(briefing_id: UUID) -> list[str]:
    """Get available zones from the linked server for objective selection."""
    briefing = get_briefing_or_404(briefing_id)

    sitac = get_sitac_or_none(briefing.server_name)
    if not sitac:
        return []

    # Return non-hidden zone names
    return sorted([name for name, zone in sitac.zones.items() if not zone.hidden])


# === Export ===


class ExportRequest(BaseModel):
    """Request body for PPTX export."""

    map_image: str | None = None  # Base64-encoded PNG image of the map


@router.post("/{briefing_id}/export/pptx")
async def export_briefing_pptx(
    briefing_id: UUID,
    data: ExportRequest | None = None,
) -> StreamingResponse:
    """Export briefing to PowerPoint format.

    The exported file can be uploaded to Google Drive for editing in Google Slides.
    """
    from foothold_sitac.briefing_export import create_briefing_pptx

    briefing = get_briefing_or_404(briefing_id)

    map_image = data.map_image if data else None
    pptx_buffer = create_briefing_pptx(briefing, map_image)

    # Sanitize filename
    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in briefing.title)
    filename = f"{safe_title}_briefing.pptx"

    return StreamingResponse(
        pptx_buffer,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
