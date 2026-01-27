"""Briefing and ATO data models."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MissionType(str, Enum):
    """Fixed list of mission types."""

    CAP = "CAP"  # Combat Air Patrol
    SEAD = "SEAD"  # Suppression of Enemy Air Defenses
    DEAD = "DEAD"  # Destruction of Enemy Air Defenses
    CAS = "CAS"  # Close Air Support
    STRIKE = "Strike"  # Precision Strike
    SWEEP = "Sweep"  # Fighter Sweep
    ESCORT = "Escort"  # Escort mission
    RECCE = "Recce"  # Reconnaissance


class Homeplate(BaseModel):
    """Home base for the mission."""

    name: str  # Ex: "Incirlik", "Batumi"
    latitude: float
    longitude: float
    runway_heading: int | None = None  # Runway heading in degrees
    tacan: str | None = None  # Ex: "21X ICK"
    frequencies: list[str] = Field(default_factory=list)  # Ex: ["251.0 Tower"]


class Waypoint(BaseModel):
    """A waypoint in a flight plan."""

    name: str
    latitude: float
    longitude: float
    altitude_ft: int | None = None
    notes: str | None = None


class Flight(BaseModel):
    """A flight within a package."""

    id: UUID = Field(default_factory=uuid4)
    callsign: str  # Ex: "Viper 1-1"
    aircraft_type: str  # Ex: "F-16C"
    num_aircraft: int = 1
    mission_type: MissionType
    push_time: str | None = None  # Ex: "0900L" or "ASAP"
    tot: str | None = None  # Time on Target
    waypoints: list[Waypoint] = Field(default_factory=list)
    notes: str | None = None


class Package(BaseModel):
    """A package containing multiple flights."""

    id: UUID = Field(default_factory=uuid4)
    name: str  # Ex: "Package Alpha"
    target_zone: str | None = None  # Reference to zone name
    mission_type: MissionType | None = None  # Primary mission type
    flights: list[Flight] = Field(default_factory=list)
    notes: str | None = None


class Objective(BaseModel):
    """An objective linked to an existing zone."""

    id: UUID = Field(default_factory=uuid4)
    zone_name: str  # Must match a zone in the sitac
    mission_requirements: list[MissionType] = Field(default_factory=list)
    priority: int = 1  # 1 = highest priority
    notes: str | None = None


class Briefing(BaseModel):
    """Root briefing/ATO document."""

    id: UUID = Field(default_factory=uuid4)
    edit_token: UUID = Field(default_factory=uuid4)  # Secret token for edit access
    server_name: str  # Linked DCS server
    title: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Homeplate
    homeplate: Homeplate | None = None

    # Mission timing
    mission_date: str | None = None  # Ex: "2024-01-15"
    mission_time: str | None = None  # Ex: "0800L"

    # Content
    situation: str | None = None  # Intel/situation description
    objectives: list[Objective] = Field(default_factory=list)
    packages: list[Package] = Field(default_factory=list)

    # Additional info
    weather: str | None = None
    comms_plan: str | None = None
    notes: str | None = None


# API Request schemas


class BriefingCreate(BaseModel):
    """Request body for creating a briefing."""

    server_name: str
    title: str
    mission_date: str | None = None
    mission_time: str | None = None


class BriefingUpdate(BaseModel):
    """Request body for updating briefing metadata."""

    title: str | None = None
    mission_date: str | None = None
    mission_time: str | None = None
    situation: str | None = None
    weather: str | None = None
    comms_plan: str | None = None
    notes: str | None = None


class HomeplateUpdate(BaseModel):
    """Request body for updating homeplate."""

    name: str
    latitude: float
    longitude: float
    runway_heading: int | None = None
    tacan: str | None = None
    frequencies: list[str] = Field(default_factory=list)


class ObjectiveCreate(BaseModel):
    """Request body for creating an objective."""

    zone_name: str
    mission_requirements: list[MissionType] = Field(default_factory=list)
    priority: int = 1
    notes: str | None = None


class ObjectiveUpdate(BaseModel):
    """Request body for updating an objective."""

    mission_requirements: list[MissionType] | None = None
    priority: int | None = None
    notes: str | None = None


class PackageCreate(BaseModel):
    """Request body for creating a package."""

    name: str
    target_zone: str | None = None
    mission_type: MissionType | None = None
    notes: str | None = None


class PackageUpdate(BaseModel):
    """Request body for updating a package."""

    name: str | None = None
    target_zone: str | None = None
    mission_type: MissionType | None = None
    notes: str | None = None


class FlightCreate(BaseModel):
    """Request body for creating a flight."""

    callsign: str
    aircraft_type: str
    num_aircraft: int = 1
    mission_type: MissionType
    push_time: str | None = None
    tot: str | None = None
    notes: str | None = None


class FlightUpdate(BaseModel):
    """Request body for updating a flight."""

    callsign: str | None = None
    aircraft_type: str | None = None
    num_aircraft: int | None = None
    mission_type: MissionType | None = None
    push_time: str | None = None
    tot: str | None = None
    notes: str | None = None


# API Response schemas


class BriefingLinks(BaseModel):
    """URLs for accessing the briefing."""

    view_url: str
    edit_url: str


class BriefingCreateResponse(BaseModel):
    """Response after creating a briefing."""

    briefing: Briefing
    links: BriefingLinks


class BriefingListItem(BaseModel):
    """Summary for listing briefings."""

    id: UUID
    title: str
    server_name: str
    created_at: datetime
    updated_at: datetime
    packages_count: int
    objectives_count: int
