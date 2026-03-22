"""DCS World coordinate conversion using Transverse Mercator projection.

Converts DCS internal coordinates (x=north, z=east in meters) to lat/lon.
Each DCS theater uses a Transverse Mercator projection with specific parameters
(central meridian, false northing, scale factor=1.0).

Parameters were reverse-engineered from DCS grid data (github.com/Kilcekru/dcs-coordinates).
Accuracy: ~300m, sufficient for tactical map display.

Theater auto-detection is a hack: we check if the center of zone coordinates
falls within a theater's known lat/lon bounding box.
"""

import math
from dataclasses import dataclass

# WGS84 ellipsoid constants
_A = 6378137.0
_F = 1.0 / 298.257223563
_E2 = 2 * _F - _F * _F
_E_PRIME2 = _E2 / (1 - _E2)


@dataclass(frozen=True)
class TheaterParams:
    central_meridian: float
    false_northing: float
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float


# Parameters extracted from DCS grid data origin points (DCS 0,0 -> lat/lon).
# false_northing = meridional arc to the origin latitude.
# false_easting = 0 for all theaters (z=0 maps to the central meridian).
# scale_factor = 1.0 (DCS does not use UTM's 0.9996 scale factor).
THEATERS: dict[str, TheaterParams] = {
    "persianGulf": TheaterParams(
        central_meridian=56.241935354469,
        false_northing=2895870.30,
        lat_min=22.7,
        lat_max=31.1,
        lon_min=51.5,
        lon_max=58.8,
    ),
    "normandy": TheaterParams(
        central_meridian=-0.30034887075907,
        false_northing=5483503.30,
        lat_min=48.2,
        lat_max=51.8,
        lon_min=-3.1,
        lon_max=3.4,
    ),
    "syria": TheaterParams(
        central_meridian=35.900560445898,
        false_northing=3877024.53,
        lat_min=31.8,
        lat_max=37.9,
        lon_min=31.2,
        lon_max=40.9,
    ),
    "sinai": TheaterParams(
        central_meridian=31.244759702481,
        false_northing=3325345.02,
        lat_min=27.8,
        lat_max=33.0,
        lon_min=29.6,
        lon_max=36.2,
    ),
    "southAtlantic": TheaterParams(
        central_meridian=-59.173518498838,
        false_northing=-5815521.99,
        lat_min=-57.0,
        lat_max=-48.1,
        lon_min=-76.8,
        lon_max=-56.1,
    ),
    # Caucasus: DCS origin (0,0) is outside the mapped area, parameters are estimated.
    # Accuracy may be lower than other theaters.
    "caucasus": TheaterParams(
        central_meridian=33.0,
        false_northing=4998115.0,
        lat_min=40.4,
        lat_max=46.0,
        lon_min=36.0,
        lon_max=47.0,
    ),
}


def dcs_to_latlon(x: float, z: float, theater: str) -> tuple[float, float]:
    """Convert DCS coordinates (x=north, z=east) to (latitude, longitude).

    Uses inverse Transverse Mercator projection with WGS84 ellipsoid.
    Raises ValueError if the theater is not supported.
    """
    params = THEATERS.get(theater)
    if not params:
        available = ", ".join(sorted(THEATERS.keys()))
        raise ValueError(f"Unsupported DCS theater '{theater}'. Available: {available}")

    northing = x + params.false_northing
    easting = z  # false_easting = 0

    # Footpoint latitude from meridional arc
    mu = northing / (_A * (1 - _E2 / 4 - 3 * _E2**2 / 64 - 5 * _E2**3 / 256))
    e1 = (1 - math.sqrt(1 - _E2)) / (1 + math.sqrt(1 - _E2))
    phi1 = (
        mu
        + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
        + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
        + (151 * e1**3 / 96) * math.sin(6 * mu)
        + (1097 * e1**4 / 512) * math.sin(8 * mu)
    )

    sin_phi1 = math.sin(phi1)
    cos_phi1 = math.cos(phi1)
    tan_phi1 = math.tan(phi1)
    n1 = _A / math.sqrt(1 - _E2 * sin_phi1**2)
    t1 = tan_phi1**2
    c1 = _E_PRIME2 * cos_phi1**2
    r1 = _A * (1 - _E2) / (1 - _E2 * sin_phi1**2) ** 1.5
    d = easting / n1

    lat = phi1 - (n1 * tan_phi1 / r1) * (
        d**2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * _E_PRIME2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * _E_PRIME2 - 3 * c1**2) * d**6 / 720
    )

    lon = (
        d - (1 + 2 * t1 + c1) * d**3 / 6 + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * _E_PRIME2 + 24 * t1**2) * d**5 / 120
    ) / cos_phi1

    return (math.degrees(lat), params.central_meridian + math.degrees(lon))


def detect_theater(center_lat: float, center_lon: float) -> str | None:
    """Detect DCS theater from a geographic center point.

    Checks if the point falls within a theater's known bounding box.
    Returns the theater name or None if no match.
    """
    for name, params in THEATERS.items():
        if params.lat_min <= center_lat <= params.lat_max and params.lon_min <= center_lon <= params.lon_max:
            return name
    return None
