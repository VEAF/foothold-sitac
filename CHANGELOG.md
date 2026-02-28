# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- Display remaining units on objectives ([#103](https://github.com/VEAF/foothold-sitac/issues/103))
- Display coalition credits ([#102](https://github.com/VEAF/foothold-sitac/pull/102))

### Fixed

- Avoid publish with wrong tag format ([#96](https://github.com/VEAF/foothold-sitac/pull/96))

## [0.2.0] - 2026-02-28

### Added

- Markpoints from coordinates, saved in local storage ([#95](https://github.com/VEAF/foothold-sitac/pull/95))
- Build project as a distributable package ([#88](https://github.com/VEAF/foothold-sitac/pull/88))

### Fixed

- Fix campaign progress calculation bug ([#90](https://github.com/VEAF/foothold-sitac/pull/90))
- Force refresh of static JS and CSS assets to avoid browser cache issues ([#94](https://github.com/VEAF/foothold-sitac/pull/94))
- Fix negative timestamp handling ([#94](https://github.com/VEAF/foothold-sitac/pull/94))

## [0.1.0] - 2026-01-07

### Added

- Alternative map tile layers with layer switcher control ([#34](https://github.com/VEAF/foothold-sitac/pull/34))
- Data freshness widget showing last update timestamp ([#33](https://github.com/VEAF/foothold-sitac/pull/33))
- Hidden zones and objectives are filtered from the map ([#32](https://github.com/VEAF/foothold-sitac/pull/32))
- Dark mode UI with icons and modals ([#36](https://github.com/VEAF/foothold-sitac/pull/36))
- Player rank position in ranking view ([#40](https://github.com/VEAF/foothold-sitac/pull/40))
- Campaign progress information ([#41](https://github.com/VEAF/foothold-sitac/pull/41))
- Reworked map markers with zone labels depending on zoom level and info modals ([#42](https://github.com/VEAF/foothold-sitac/pull/42))
- Display active missions from status file ([#45](https://github.com/VEAF/foothold-sitac/pull/45))
- Waypoints names and connections on the map ([#46](https://github.com/VEAF/foothold-sitac/pull/46))
- Players positions on the map ([#50](https://github.com/VEAF/foothold-sitac/pull/50))
- Auto-refresh of navbar information ([#55](https://github.com/VEAF/foothold-sitac/pull/55))
- Ejected pilots information ([#57](https://github.com/VEAF/foothold-sitac/pull/57))
- Mouse cursor lat/long position display ([#65](https://github.com/VEAF/foothold-sitac/pull/65))
- Zone hover tooltip ([#68](https://github.com/VEAF/foothold-sitac/pull/68))
- Ruler tool to measure distances ([#72](https://github.com/VEAF/foothold-sitac/pull/72))
- Update script (`update.cmd`) for self-updating ([#69](https://github.com/VEAF/foothold-sitac/pull/69))
- Documentation ([#74](https://github.com/VEAF/foothold-sitac/pull/74))
- VEAF favicon ([#74](https://github.com/VEAF/foothold-sitac/pull/74))
- Configurable refresh interval with progress indicator ([#81](https://github.com/VEAF/foothold-sitac/pull/81))
- GitHub repository link in the UI ([#82](https://github.com/VEAF/foothold-sitac/pull/82))
- Disabled (inactive) zones displayed in dark gray ([#84](https://github.com/VEAF/foothold-sitac/pull/84))
- Linter setup with ruff and mypy ([#35](https://github.com/VEAF/foothold-sitac/pull/35))

### Changed

- Updated hidden flag location for waypoints ([#52](https://github.com/VEAF/foothold-sitac/pull/52))
- Updated format for waypoints names ([#49](https://github.com/VEAF/foothold-sitac/pull/49))
- Refactored CSS, JS and HTML into separate files ([#67](https://github.com/VEAF/foothold-sitac/pull/67))

### Fixed

- Ejected pilots with decimal `lost_credits`, display Unknown pilots ([#62](https://github.com/VEAF/foothold-sitac/pull/62))
- Navbar responsive layout and tooltips ([#58](https://github.com/VEAF/foothold-sitac/pull/58))
- Zone click not working on disabled zones ([#71](https://github.com/VEAF/foothold-sitac/pull/71))
- Hidden objectives excluded from campaign progress calculation ([#80](https://github.com/VEAF/foothold-sitac/pull/80))
- CSS browser compatibility fix ([#81](https://github.com/VEAF/foothold-sitac/pull/81))
- Truncated flavor names on multilines ([#87](https://github.com/VEAF/foothold-sitac/pull/87))

## [0.0.1] - 2025-11-12

### Added

- Initial proof of concept: Lua persistence file parsing ([#2](https://github.com/VEAF/foothold-sitac/pull/2))
- Auto-detection and listing of Foothold servers ([#5](https://github.com/VEAF/foothold-sitac/pull/5))
- Interactive Leaflet map display with zone circles ([#6](https://github.com/VEAF/foothold-sitac/pull/6))
- YAML configuration file support ([#12](https://github.com/VEAF/foothold-sitac/pull/12))
- Improved Foothold server detection logic ([#13](https://github.com/VEAF/foothold-sitac/pull/13))
- Customizable web server host, port and title ([#16](https://github.com/VEAF/foothold-sitac/pull/16))
- Install and run CMD shortcuts ([#17](https://github.com/VEAF/foothold-sitac/pull/17))
- Sitac JSON export API ([#21](https://github.com/VEAF/foothold-sitac/pull/21))
- Remaining units count on zones, circle size based on zone level ([#23](https://github.com/VEAF/foothold-sitac/pull/23))
- Custom map tile URL configuration ([#24](https://github.com/VEAF/foothold-sitac/pull/24))
- Configurable min/max zoom levels ([#27](https://github.com/VEAF/foothold-sitac/pull/27))
- Mobile-friendly font sizes ([#28](https://github.com/VEAF/foothold-sitac/pull/28))
