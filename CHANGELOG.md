# Changelog

All notable changes to Deep Lynctus will be documented in this file.

## [Unreleased]

### Code Quality and Documentation Improvements
- Enhanced type hints across multiple service modules for better code clarity
- Improved docstring documentation with comprehensive parameter descriptions
- Refactored magic numbers to named constants for better maintainability
- Organized import statements according to PEP 8 conventions
- Added structured logging and error handling improvements
- Enhanced package.json metadata for better project discoverability
- Updated README files with table of contents and better organization
- Improved requirements.txt formatting and documentation structure

### Documentation
- Minor README wording updates
- Deployment guide clarifications
- Enhanced browser extension documentation with detailed features
- Comprehensive examples documentation structure

## [2.0.0] - 2026-01-09

### Added - Major Features

#### Project Comparison Feature
- **Backend Service** (`backend/services/project_comparison_service.py`)
  - Comprehensive project comparison logic
  - Winner determination algorithm with weighted scoring
  - Calculate quality score, complexity, and issue differences
  - Detailed breakdowns for complexity, security, quality, maintainability
  
- **Backend Controller** (`backend/controllers/project_comparison_controller.py`)
  - `GET /projects/compare/{project_a_id}/vs/{project_b_id}` - Compare two projects
  - `GET /projects/compare/list` - List all available projects
  
- **Frontend Page** (`frontend/src/pages/ProjectComparison.jsx`)
  - Dual project selector dropdowns
  - Side-by-side metric comparison cards
  - Winner banner with scoring
  - Differences table with percentage changes
  - Color-coded indicators (cyan for Project A, purple for Project B)
  - Detailed breakdowns for all metrics
  
- **Navigation Integration**
  - Added "Compare" button (🆚) to main navigation
  - Routing integration in `frontend/src/main.jsx`

#### Browser Extension
- **Chrome Extension** (`browser-extension/`)
  - Manifest V3 configuration
  - Popup interface with analysis controls
  - Content script injection on GitHub repository pages
  - Background service worker for API communication
  - Glassmorphic UI design matching main application
  
- **Extension Features**
  - Auto-detect GitHub repositories
  - One-click analysis from GitHub pages
  - Real-time progress updates
  - Quality metrics display in popup
  - Auto-open dashboard when analysis completes
  - Configurable backend URL
  
- **Extension Files**
  - `manifest.json` - Extension configuration
  - `popup.html` / `popup.js` - Popup interface
  - `content.js` - GitHub page injection
  - `content.css` - Styling for injected elements
  - `background.js` - Service worker
  - `icons/` - Extension icons (SVG + PNG)
  - `README.md` - Installation and usage guide

### Fixed - Bug Fixes

#### AI Chat Service
- Fixed import error in `backend/services/chatbot_service.py`
- Changed from `from services.db import db` to `from services.db import get_database`
- Resolved 500 Internal Server Error on chat endpoint

#### Comparison Timeline
- Fixed datetime parsing error in `backend/services/comparison_service.py`
- Added support for ISO timestamps with 'Z' suffix
- Implemented try-except wrapper for robust date handling
- Resolved 500 Internal Server Error on timeline endpoint

#### Security Detection False Positives
- Significantly reduced false positive detections in `backend/services/repo_analyzer.py`
- Increased password detection threshold from 8 to 12 characters
- Increased API key detection threshold from 20 to 32 characters
- Added exclusions for placeholders (test, demo, example, xxx, $, {, <)
- Database credentials now require complete connection strings with domains
- Command injection only flagged when user input is involved
- Result: More accurate security scanning with fewer false alarms

#### Deployment
- Added `email-validator==2.1.0` to `requirements.txt`
- Added `pydantic[email]==2.9.0` for EmailStr validation support
- Fixed Render deployment ImportError

### Improved - Enhancements

#### MongoDB Atlas Integration
- Successfully connected to MongoDB Atlas cloud database
- Connection string configured with SSL/TLS support
- All collections operational (projects, file_metrics, risks, smells, scan_history)
- Persistent data storage enabled

#### Code Quality
- Compiled regex patterns for 3-5x performance improvement
- Stricter security detection patterns reduce noise
- Better error handling across services

### Documentation

- Updated main README.md with new features
- Added Browser Extension README with installation guide
- Added API endpoint documentation for comparison feature
- Added usage instructions for both new features
- Created comprehensive extension development guide

## [1.0.0] - 2025-12-XX

### Initial Release
- GitHub repository analysis
- Python code parsing and metrics extraction
- ML-based bug risk prediction
- NLP-based code smell detection
- AI refactoring suggestions
- Interactive dashboards (heatmap, trends, overview)
- PDF report generation
- Chatbot interface
- Dependency graph visualization
- File detail analysis

---

## Version History Summary

- **v2.0.0** (2026-01-09): Project Comparison + Browser Extension + Bug Fixes
- **v1.0.0** (2025-12-XX): Initial Release

## Upcoming Features

- [ ] Firefox browser extension support (Manifest V2)
- [ ] Private repository analysis (OAuth integration)
- [ ] Batch analysis for multiple projects
- [ ] Export comparison reports
- [ ] Browser extension keyboard shortcuts
- [ ] Analysis history in extension popup
- [ ] Multi-language support (JavaScript, Java, C++)
- [ ] CI/CD integration plugins
