# Changelog

All notable changes to DriftTracker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of DriftTracker
- Core drift calculation engine with DriftCalculator class
- Integration with Copernicus Marine API for ocean current data
- FastAPI backend with RESTful API endpoints
- Interactive web interface with Leaflet.js maps
- Machine learning models for drift pattern classification
- Support for multiple object types (people, vessels, equipment)
- Real-time ocean current visualization
- Search pattern recommendations (Sector Search, Expanding Square, Parallel Sweep)
- Comprehensive utility functions for coordinate calculations
- Docker containerization support
- Basic authentication with Copernicus Marine credentials
- Dutch North Sea geographic focus (52.5°N, 4.2°E)
- Comprehensive test suite with unit, integration, and performance tests
- GitHub Actions CI/CD pipeline with automated testing
- Professional documentation and contributing guidelines
- Code quality tools (Black, flake8, mypy, pylint)
- Security scanning with Bandit
- Performance benchmarking framework
- Enterprise-grade project structure
- SharpByte Software branding and contact information

### Features
- **Drift Prediction**: Calculate drift trajectories for any floating object
- **Ocean Data Integration**: Real-time and historical ocean current data
- **Interactive Maps**: Visualize drift paths with current overlays
- **Search Optimization**: AI-powered search pattern recommendations
- **Multi-object Support**: Different drift models for various object types
- **High Performance**: Optimized for real-time drift calculations
- **Scalable Architecture**: Designed for enterprise deployment

### Technical Stack
- **Backend**: FastAPI, Python 3.9+, xarray, scikit-learn
- **Frontend**: HTML5, CSS3, JavaScript, Leaflet.js
- **Data Sources**: Copernicus Marine API, Open-Meteo API
- **Deployment**: Docker, uvicorn
- **Development**: pytest, Black, flake8, mypy
- **Company**: SharpByte Software (Delft, Netherlands)

### Supported Object Types
- **People**: Adults, children, with/without life jackets
- **Vessels**: Catamarans, fishing trawlers, RHIBs, kayaks, SUP boards
- **Equipment**: Custom objects with configurable drag factors

### API Endpoints
- `POST /predict` - Calculate drift prediction
- `GET /debug-data/{lat}/{lon}` - Test ocean data download
- `GET /` - Login page
- `GET /app` - Main application interface

### Geographic Focus
- **Primary Area**: Dutch North Sea waters
- **Default Coordinates**: 52.5°N, 4.2°E (North Sea off Dutch coast)
- **Training Data**: Dutch coastal waters simulation

### Performance
- **Drift Calculation**: Optimized for real-time predictions
- **API Response**: FastAPI-based high-performance endpoints
- **Scalable Architecture**: Designed for enterprise deployment
- **Data Processing**: Efficient ocean current data handling

---

## Version History

### Version Numbering
We follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH**
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality in a backward-compatible manner
- **PATCH**: Backward-compatible bug fixes

### Release Schedule
- **Major Releases**: Quarterly (every 3 months)
- **Minor Releases**: Monthly (first week of each month)
- **Patch Releases**: As needed for critical fixes
- **Pre-releases**: Alpha and beta versions for testing

### Support Policy
- **Current Version**: Full support
- **Previous Major Version**: Security updates only
- **Older Versions**: No support

## Contributing to the Changelog

When contributing to DriftTracker, please update this changelog:

1. **Add entries** under the appropriate version section
2. **Use the correct categories**: Added, Changed, Deprecated, Removed, Fixed, Security
3. **Write clear, concise descriptions**
4. **Include issue numbers** when applicable
5. **Follow the existing format**

### Categories
- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security vulnerability fixes

---

*This changelog follows the format established by the [VS Code project](https://github.com/microsoft/vscode) and adapted for DriftTracker's specific needs.*

---

**SharpByte Software** - Innovatieve Softwareproducten met Impact

*Delft, Nederland | [sharpbytesoftware.com](https://sharpbytesoftware.com/)* 