# Changelog

All notable changes to the **Pro Clubs Malaysia Match Schedule Tracker & Poster Generator** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-30

### 🚀 Features (`feat`)
- **Discord Bot Slash Commands**: Added dedicated `/poster` slash command to display ONLY the graphic matchday poster alongside the existing `/schedule` command.
- **Smart Corner Floodfill Background Removal**: Implemented Pillow's `ImageDraw.floodfill()` starting from 4 corners (with `thresh=30` artifact tolerance) to remove contiguous outer white boxes while protecting internal white text and crest details.
- **Dynamic Matchweek Calculation**: Implemented automatic matchweek counter (e.g. `MATCHWEEK 03`) calculated from the 13/07/2026 Season start date.
- **Cross-Platform Standalone Build**: Added PyInstaller support for compiling native `.exe` binaries for Windows PCs.

### 🎨 Visual & Theme Enhancements (`style`)
- **Virtua CF Signature Theme**: Transformed matchday poster palette to match official Virtua CF brand identity (`#0b1723` Midnight Navy, `#f4ba1d` Electric Gold, `#132634` Steel Card Navy).
- **Clean Competition Headers**: Removed redundant platform tags e.g. `(LPM MY)` from fixture headers (`LPM JUNIOR A`, `VPL ROOKIE LEAGUE 2`, `VPG MALAYSIA CHAMPIONSHIP`).
- **Centered Top Header Layout**: Positioned `F I X T U R E S` and `MATCHWEEK XX` titles dead-center across the 1080x1080 canvas.
- **Official Footer Formatting**: Updated bottom text to `VIRTUA CF OFFICIAL MATCHDAY SCHEDULE`.

### 🐛 Bug Fixes & Refinement (`fix`)
- **Logo Bounding Box Cropping**: Added `img.getchannel('A').getbbox()` auto-trimming to strip transparent padding before resizing logos to fixed `52x52px` target boxes maintaining aspect ratio.
- **Discord Interaction Deferral**: Wrapped `interaction.response.defer()` in try/except blocks to prevent `404 Unknown Interaction` errors during gateway reconnects.
- **5:5:5 League Logo Scale Balance**: Applied fine-tuned scaling for VPG, VPL, and LPM footer badges for equal visual volume.

### ⚙️ CI/CD & Automation (`ci`)
- **GitHub Actions Windows `.exe` Builder**: Created `.github/workflows/build_windows.yml` to automatically compile `pro_clubs_tracker.exe` on Windows cloud runners upon release publication or manual dispatch.
- **Release Asset Upload**: Integrated `softprops/action-gh-release@v2` to attach compiled `.exe` files directly to published GitHub Releases.
- **Dependency Caching & Retention**: Enabled `cache: 'pip'` and set `retention-days: 7` to optimize workflow build times and storage.

### 📚 Documentation (`docs`)
- **README Guide**: Updated project documentation with `/schedule` and `/poster` usage, local setup, `.env` token configuration, and `.exe` compilation steps.
