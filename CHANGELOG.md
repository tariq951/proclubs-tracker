# Changelog

All notable changes to the **Pro Clubs Malaysia Match Schedule Tracker & Poster Generator** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.3] - 2026-07-30

### 🚀 Features (`feat`)
- **Smart Corner Floodfill Background Removal**: Implemented Pillow's `ImageDraw.floodfill()` starting from 4 corners (`thresh=30`) to remove contiguous outer white boxes while protecting internal white text and crest details.
- **Dynamic Matchweek Calculation**: Implemented automatic matchweek counter (`MATCHWEEK 03`) calculated from the 13/07/2026 season start date.

### 🎨 Visual & Theme Enhancements (`style`)
- **Official Footer Formatting**: Updated bottom poster text to `VIRTUA CF OFFICIAL MATCHDAY SCHEDULE`.

---

## [1.0.2] - 2026-07-30

### 🐛 Bug Fixes & Refinement (`fix`)
- **Logo Bounding Box Cropping**: Added `img.getchannel('A').getbbox()` auto-trimming to strip transparent padding before resizing logos to fixed `52x52px` target boxes maintaining aspect ratio.
- **5:5:5 League Logo Scale Balance**: Applied fine-tuned scaling for VPG, VPL, and LPM footer badges for equal visual volume.

---

## [1.0.1] - 2026-07-29

### 🚀 Features (`feat`)
- **Discord Bot Slash Commands**: Added `/poster` slash command to display ONLY the graphic matchday poster alongside the existing `/schedule` command.

### 🎨 Visual & Theme Enhancements (`style`)
- **Virtua CF Signature Theme**: Transformed matchday poster palette to match official Virtua CF brand identity (`#0b1723` Midnight Navy, `#f4ba1d` Electric Gold, `#132634` Steel Card Navy).
- **Clean Competition Headers**: Removed redundant platform tags e.g. `(LPM MY)` from fixture headers (`LPM JUNIOR A`, `VPL ROOKIE LEAGUE 2`, `VPG MALAYSIA CHAMPIONSHIP`).
- **Centered Top Header Layout**: Positioned `F I X T U R E S` and `MATCHWEEK XX` titles dead-center across the 1080x1080 canvas.

---

## [1.0.0] - 2026-07-28

### 🚀 Features (`feat`)
- **Core Schedule Pipeline**: Built scrapers for Virtua CF across VPL Malaysia, LPM Malaysia, and VPG REST API.
- **Kickly-Style Graphic Poster**: 1080x1080 high-res matchday poster generator with 3-part horizontal fixture bars.
- **Cross-Platform Standalone Build**: Added PyInstaller support for compiling native `.exe` binaries for Windows PCs.
- **GitHub Actions CI/CD**: Added workflow to build `.exe` on cloud runners and attach binaries to GitHub Releases.
