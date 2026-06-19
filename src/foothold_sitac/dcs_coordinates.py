"""DCS World coordinate conversion using Transverse Mercator projection.

Converts DCS internal coordinates (x=north, z=east in meters) to lat/lon.
Each DCS theater uses a standard Transverse Mercator projection:

    +proj=tmerc +lat_0=0 +k_0=0.9996 +lon_0=<central meridian>
    +x_0=<false easting> +y_0=<false northing> +ellps=WGS84

Only three constants change per map (``lon_0``, ``x_0``, ``y_0``). They are
vendored verbatim from the authoritative VEAF/dcs-maps dataset:
https://github.com/VEAF/dcs-maps/blob/main/exports/maps.yaml
(cross-checked there against github.com/JonathanTurnock/dcs-projections).

This conversion is the *fallback* path used only for legacy CTLD FARP CSVs that
lack latitude/longitude columns; current CSVs carry lat/lon directly.

Theater auto-detection is a hack: we check if the center of zone coordinates
falls within a theater's known lat/lon bounding box. Some maps overlap
geographically (e.g. Sinai/Syria, Iraq/Syria, Iraq/PersianGulf, Normandy/TheChannel,
Marianas/MarianasWWII); those resolve by dict order, which is acceptable for a
tactical-display fallback.
"""

import math
from dataclasses import dataclass

# WGS84 ellipsoid constants
_A = 6378137.0
_F = 1.0 / 298.257223563
_E2 = 2 * _F - _F * _F
_E_PRIME2 = _E2 / (1 - _E2)

# All DCS theaters share the same scale factor (UTM) and lat_0=0 (so M0=0).
_K0 = 0.9996


@dataclass(frozen=True)
class TheaterParams:
    lon_0: float  # central meridian (degrees)
    x_0: float  # false easting (meters)
    y_0: float  # false northing (meters)
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    k_0: float = _K0


# Projection params vendored from VEAF/dcs-maps exports/maps.yaml.
# Bounding boxes are best-effort geographic extents for theater auto-detection.
THEATERS: dict[str, TheaterParams] = {
    "persianGulf": TheaterParams(
        lon_0=57.0,
        x_0=75755.99999870236,
        y_0=-2894933.000000028,
        lat_min=22.5,
        lat_max=31.5,
        lon_min=47.0,
        lon_max=60.0,
    ),
    "caucasus": TheaterParams(
        lon_0=33.0,
        x_0=-99516.99999766012,
        y_0=-4998115.000001914,
        lat_min=38.5,
        lat_max=48.0,
        lon_min=33.0,
        lon_max=48.0,
    ),
    "syria": TheaterParams(
        lon_0=39.0,
        x_0=282801.00000019063,
        y_0=-3879866.000000911,
        lat_min=32.0,
        lat_max=38.0,
        lon_min=32.0,
        lon_max=43.0,
    ),
    "sinai": TheaterParams(
        lon_0=33.0,
        x_0=169221.99999983577,
        y_0=-3325312.9999987846,
        lat_min=27.0,
        lat_max=32.0,
        lon_min=30.0,
        lon_max=36.5,
    ),
    "southAtlantic": TheaterParams(
        lon_0=-57.0,
        x_0=147639.99999997593,
        y_0=5815417.000000032,
        lat_min=-57.0,
        lat_max=-49.0,
        lon_min=-77.0,
        lon_max=-52.0,
    ),
    "normandy": TheaterParams(
        lon_0=-3.0,
        x_0=-195525.99999845505,
        y_0=-5484812.999999176,
        lat_min=48.0,
        lat_max=50.5,
        lon_min=-4.0,
        lon_max=1.5,
    ),
    "afghanistan": TheaterParams(
        lon_0=63.0,
        x_0=-300150.00000261003,
        y_0=-3759657.000001035,
        lat_min=29.0,
        lat_max=39.0,
        lon_min=60.0,
        lon_max=75.0,
    ),
    "germanyCW": TheaterParams(
        lon_0=21.0,
        x_0=35427.62000060154,
        y_0=-6061633.12800163,
        lat_min=47.0,
        lat_max=55.0,
        lon_min=5.0,
        lon_max=16.0,
    ),
    "nevada": TheaterParams(
        lon_0=-117.0,
        x_0=-193996.80999964548,
        y_0=-4410028.063999966,
        lat_min=34.5,
        lat_max=39.5,
        lon_min=-119.0,
        lon_max=-112.0,
    ),
    "theChannel": TheaterParams(
        lon_0=3.0,
        x_0=99376.00000000288,
        y_0=-5636889.00000001,
        lat_min=50.0,
        lat_max=52.0,
        lon_min=0.0,
        lon_max=4.0,
    ),
    "marianaIslands": TheaterParams(
        lon_0=147.0,
        x_0=238418.00000022806,
        y_0=-1491839.9999989243,
        lat_min=12.0,
        lat_max=22.0,
        lon_min=143.0,
        lon_max=149.0,
    ),
    "marianaIslandsWWII": TheaterParams(
        lon_0=147.0,
        x_0=238418.00000022806,
        y_0=-1491839.9999989243,
        lat_min=12.0,
        lat_max=22.0,
        lon_min=143.0,
        lon_max=149.0,
    ),
    "iraq": TheaterParams(
        lon_0=45.0,
        x_0=72290.0000013377,
        y_0=-3680056.999997638,
        lat_min=29.0,
        lat_max=38.0,
        lon_min=38.0,
        lon_max=50.0,
    ),
    "kola": TheaterParams(
        lon_0=21.0,
        x_0=-62701.99999924752,
        y_0=-7543625.000001493,
        lat_min=63.0,
        lat_max=71.5,
        lon_min=10.0,
        lon_max=42.0,
    ),
}


def _meridional_arc(lat_rad: float) -> float:
    """WGS84 meridional arc length (meters) from the equator to ``lat_rad``."""
    return _A * (
        (1 - _E2 / 4 - 3 * _E2**2 / 64 - 5 * _E2**3 / 256) * lat_rad
        - (3 * _E2 / 8 + 3 * _E2**2 / 32 + 45 * _E2**3 / 1024) * math.sin(2 * lat_rad)
        + (15 * _E2**2 / 256 + 45 * _E2**3 / 1024) * math.sin(4 * lat_rad)
        - (35 * _E2**3 / 3072) * math.sin(6 * lat_rad)
    )


def dcs_to_latlon(x: float, z: float, theater: str) -> tuple[float, float]:
    """Convert DCS coordinates (x=north, z=east) to (latitude, longitude).

    Uses the inverse Transverse Mercator projection (WGS84, lat_0=0) with the
    theater's vendored parameters. Raises ValueError if the theater is unknown.
    """
    params = THEATERS.get(theater)
    if not params:
        available = ", ".join(sorted(THEATERS.keys()))
        raise ValueError(f"Unsupported DCS theater '{theater}'. Available: {available}")

    # Meridional arc (lat_0=0 -> M0=0), then footpoint latitude.
    m = (x - params.y_0) / params.k_0
    mu = m / (_A * (1 - _E2 / 4 - 3 * _E2**2 / 64 - 5 * _E2**3 / 256))
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
    d = (z - params.x_0) / (n1 * params.k_0)

    lat = phi1 - (n1 * tan_phi1 / r1) * (
        d**2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * _E_PRIME2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * _E_PRIME2 - 3 * c1**2) * d**6 / 720
    )

    lon = (
        d - (1 + 2 * t1 + c1) * d**3 / 6 + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * _E_PRIME2 + 24 * t1**2) * d**5 / 120
    ) / cos_phi1

    return (math.degrees(lat), params.lon_0 + math.degrees(lon))


def latlon_to_dcs(lat: float, lon: float, theater: str) -> tuple[float, float]:
    """Convert (latitude, longitude) to DCS coordinates (x=north, z=east).

    Forward Transverse Mercator (WGS84, lat_0=0). Inverse of :func:`dcs_to_latlon`;
    used to validate the projection. Raises ValueError if the theater is unknown.
    """
    params = THEATERS.get(theater)
    if not params:
        available = ", ".join(sorted(THEATERS.keys()))
        raise ValueError(f"Unsupported DCS theater '{theater}'. Available: {available}")

    phi = math.radians(lat)
    sin_phi = math.sin(phi)
    cos_phi = math.cos(phi)
    tan_phi = math.tan(phi)
    n = _A / math.sqrt(1 - _E2 * sin_phi**2)
    t = tan_phi**2
    c = _E_PRIME2 * cos_phi**2
    a = cos_phi * math.radians(lon - params.lon_0)
    m = _meridional_arc(phi)

    easting = params.x_0 + params.k_0 * n * (
        a + (1 - t + c) * a**3 / 6 + (5 - 18 * t + t**2 + 72 * c - 58 * _E_PRIME2) * a**5 / 120
    )
    northing = params.y_0 + params.k_0 * (
        m
        + n
        * tan_phi
        * (
            a**2 / 2
            + (5 - t + 9 * c + 4 * c**2) * a**4 / 24
            + (61 - 58 * t + t**2 + 600 * c - 330 * _E_PRIME2) * a**6 / 720
        )
    )

    return (northing, easting)  # DCS x = north, z = east


def detect_theater(center_lat: float, center_lon: float) -> str | None:
    """Detect DCS theater from a geographic center point.

    Checks if the point falls within a theater's known bounding box.
    Returns the theater name or None if no match.
    """
    for name, params in THEATERS.items():
        if params.lat_min <= center_lat <= params.lat_max and params.lon_min <= center_lon <= params.lon_max:
            return name
    return None
