# DriftTracker - AI-Powered Ocean Drift Prediction for Search & Rescue

[![Tests](https://github.com/Seichs/DriftTracker/workflows/Tests/badge.svg)](https://github.com/Seichs/DriftTracker/actions)
[![Tests](https://github.com/Seichs/DriftTracker/workflows/Tests/badge.svg)](https://github.com/Seichs/DriftTracker/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

> **DriftTracker** is an AI-enhanced web application that predicts drift patterns in the ocean for search and rescue (SAR) missions. It estimates the position of a person or vessel based on the incident time, location, and ocean current data, helping rescue teams optimize their search strategies.

## 🌊 What is DriftTracker?

DriftTracker combines advanced ocean current modeling with machine learning to provide accurate drift predictions for search and rescue operations. When someone goes missing at sea, every minute counts. Our system helps rescue teams:

- **Predict drift trajectories** using real-time ocean current data
- **Recommend optimal search patterns** based on drift characteristics
- **Visualize search areas** with interactive maps and current overlays
- **Integrate multiple data sources** including Copernicus Marine and Open-Meteo APIs

## 🚀 Features

### Core Functionality
- **Real-time Drift Prediction**: Calculate where a person or vessel will drift based on ocean currents
- **Search Pattern Recommendations**: AI-powered suggestions for Sector Search, Expanding Square, and Parallel Sweep patterns
- **Interactive Visualization**: Dynamic maps with current vectors and drift trajectories
- **Multi-object Support**: Different drift models for people, boats, and various vessel types

### Technical Capabilities
- **High-accuracy Ocean Data**: Integration with Copernicus Marine hourly NetCDF files
- **Machine Learning Models**: Trained on simulated drifts around Dutch coastal waters
- **FastAPI Backend**: Lightweight, high-performance REST API
- **Real-time Processing**: Sub-second response times for drift calculations
- **Scalable Architecture**: Designed for enterprise deployment

### Supported Object Types
- **People**: Adults, children, with/without life jackets
- **Vessels**: Catamarans, fishing trawlers, RHIBs, kayaks, SUP boards
- **Custom Objects**: Configurable drag factors for any floating object

## 📊 Demo

![DriftTracker Demo](https://i.imgur.com/4SoiPkz.png)

*Interactive drift prediction with real-time ocean current visualization*

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **xarray** - Advanced N-dimensional array operations for ocean data
- **scikit-learn** - Machine learning for drift pattern classification
- **Copernicus Marine API** - High-resolution ocean current data
- **Open-Meteo API** - Real-time marine weather data

### Frontend
- **Leaflet.js** - Interactive maps with current vector overlays
- **leaflet-velocity** - Ocean current visualization
- **Modern CSS/HTML** - Responsive, accessible interface

### Infrastructure
- **Docker** - Containerized deployment
- **GitHub Actions** - Automated testing and CI/CD
- **pytest** - Comprehensive test suite with 80%+ coverage

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Copernicus Marine account (free registration)
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Seichs/DriftTracker.git
   cd DriftTracker
   ```

2. **Install dependencies**
   ```bash
   # Install production dependencies
   pip install -r requirements.txt
   
   # Install development dependencies
   pip install -r requirements-test.txt
   ```

3. **Set up environment variables**
   ```bash
   export COPERNICUS_USERNAME="your-email@example.com"
   export COPERNICUS_PASSWORD="your-password"
   ```

4. **Run the application**
   ```bash
   # Development server
   make dev
   
   # Or directly
   cd backend && python -m cli
   ```

5. **Access the application**
   - Open http://localhost:8001 in your browser
   - Login with your Copernicus Marine credentials
   - Start predicting drift patterns!

### Docker Deployment

#### Production
```bash
# Build and run production container
docker-compose -f docker/docker-compose.yml up drifttracker

# Or build manually
docker build -f docker/Dockerfile -t drifttracker .
docker run -p 8000:8000 drifttracker
```

#### Development
```bash
# Build and run development container with hot-reload
docker-compose -f docker/docker-compose.yml --profile dev up drifttracker-dev

# Or build manually
docker build -f docker/Dockerfile.dev -t drifttracker-dev .
docker run -p 8001:8000 -v $(pwd)/backend:/app/backend drifttracker-dev
```

#### Testing
```bash
# Run tests in container
docker-compose -f docker/docker-compose.yml --profile test up drifttracker-test
```

## 🧪 Testing

DriftTracker includes a comprehensive test suite following enterprise standards:

```bash
# Run all tests
make test

# Run specific test types
make test-unit          # Unit tests
make test-integration   # Integration tests
make test-e2e          # End-to-end tests
make test-performance  # Performance benchmarks

# Code quality checks
make lint              # Linting and style checks
make type-check        # Type checking
make security-check    # Security vulnerability scanning

# Coverage report
make test-coverage     # Generate coverage report
```

### Test Coverage
- **Unit Tests**: Core drift calculation and utility functions
- **Integration Tests**: API workflow and data processing
- **Performance Tests**: Benchmarking and memory usage
- **End-to-End Tests**: Complete user workflows
- **Security Tests**: Vulnerability scanning with Bandit

## 📚 API Documentation

### Core Endpoints

#### POST `/predict`
Calculate drift prediction for a given scenario.

**Request Body:**
```json
{
  "lat": 52.5,
  "lon": 4.2,
  "hours": 6,
  "object_type": "Person_Adult_LifeJacket",
  "date": "2023-01-01",
  "time": "12:00",
  "username": "your-copernicus-username",
  "password": "your-copernicus-password"
}
```

**Response:**
```json
{
  "status": "success",
  "final_position": {
    "lat": 52.51,
    "lon": 4.21
  },
  "drift_distance_km": 1.2,
  "search_pattern": "Expanding Square",
  "trajectory": [...]
}
```

#### GET `/debug-data/{lat}/{lon}`
Test ocean data download and processing for debugging.

### Object Types

| Object Type | Drag Factor | Wind Factor | Use Case |
|-------------|-------------|-------------|----------|
| Person_Adult_LifeJacket | 0.8 | 0.01 | Adult with life jacket |
| Person_Adult_NoLifeJacket | 1.1 | 0.005 | Adult without life jacket |
| Catamaran | 0.4 | 0.05 | Sailing catamaran |
| Fishing_Trawler | 0.2 | 0.03 | Commercial fishing vessel |
| RHIB | 0.6 | 0.02 | Rigid hull inflatable boat |

## 🔧 Development

### Project Structure
```
DriftTracker/
├── backend/                 # FastAPI backend application
│   ├── cli/                # Main application entry point
│   ├── drifttracker/       # Core drift calculation engine
│   │   ├── drift_calculator.py
│   │   ├── data_service.py
│   │   └── utils.py
│   └── ml/                 # Machine learning models
├── frontend/               # Web interface
│   ├── html/              # HTML templates
│   └── src/               # JavaScript and CSS
├── tests/                 # Comprehensive test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   ├── e2e/             # End-to-end tests
│   └── performance/     # Performance benchmarks
└── docs/                 # Documentation
```

### Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** and add tests
4. **Run the test suite** (`make test`)
5. **Commit your changes** (`git commit -m 'Add amazing feature'`)
6. **Push to the branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

### Development Workflow

```bash
# Set up development environment
make setup-dev

# Run tests before committing
make test

# Format code
make format

# Check code quality
make lint
make type-check

# Performance testing
make benchmark
```

## 🌍 Use Cases

### Search and Rescue Operations
- **Coast Guard**: Optimize search patterns for missing vessels
- **Marine Police**: Track drift of evidence or debris
- **Emergency Services**: Locate missing persons in water

### Marine Research
- **Oceanographers**: Study drift patterns and current effects
- **Environmental Scientists**: Track marine debris and pollution
- **Fisheries**: Monitor fishing gear and equipment drift

### Recreational Safety
- **Sailing Clubs**: Safety planning for regattas
- **Diving Operations**: Emergency response planning
- **Water Sports**: Safety protocols for events

## 📈 Performance

### Benchmarks
- **Drift Calculation**: Optimized for real-time predictions
- **API Response**: FastAPI-based high-performance endpoints
- **Scalable Architecture**: Designed for enterprise deployment
- **Data Processing**: Efficient ocean current data handling

### Scalability
- **Horizontal Scaling**: Stateless API design
- **Caching**: Intelligent data caching for repeated requests
- **Load Balancing**: Ready for production deployment
- **Monitoring**: Built-in performance metrics
- **Enterprise Ready**: Professional architecture for large-scale deployment

## 🔒 Security

- **API Authentication**: Copernicus Marine credential validation
- **Input Validation**: Comprehensive parameter sanitization
- **Error Handling**: Secure error messages without data leakage
- **Dependency Scanning**: Automated security vulnerability detection

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏢 About SharpByte Software

**DriftTracker** is developed by [SharpByte Software](https://sharpbytesoftware.com/), a Dutch software company specializing in innovative software products with impact.

### Our Mission
We develop smart solutions that solve real problems, focusing on:
- **Eigen Producten**: We develop our own apps and websites that we scale and sell
- **Innovatieve Start-ups**: Creating fresh, innovative startups that solve real problems
- **Zelfstandige Groei**: Building small, smart software solutions that grow into successful products

### Location
- **Delft, Nederland** 🇳🇱
- **Website**: [sharpbytesoftware.com](https://sharpbytesoftware.com/)
- **Email**: info@sharpbytesoftware.com

## 🤝 Support

### Getting Help
- **Documentation**: [API Reference](docs/api_reference.md)
- **Issues**: [GitHub Issues](https://github.com/Seichs/DriftTracker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Seichs/DriftTracker/discussions)
- **Email**: info@sharpbytesoftware.com

### Community
- **Contributors**: [View Contributors](https://github.com/Seichs/DriftTracker/graphs/contributors)
- **Code of Conduct**: [Contributor Covenant](CODE_OF_CONDUCT.md)
- **Changelog**: [Release Notes](CHANGELOG.md)

## 🙏 Acknowledgments

- **Copernicus Marine Service** for ocean current data
- **Open-Meteo** for marine weather data
- **FastAPI** team for the excellent web framework
- **Leaflet.js** community for mapping capabilities
- **All contributors** who help make DriftTracker better
- **SharpByte Software** team for development and innovation

## 📊 Statistics

![GitHub stars](https://img.shields.io/github/stars/Seichs/DriftTracker)
![GitHub forks](https://img.shields.io/github/forks/Seichs/DriftTracker)
![GitHub issues](https://img.shields.io/github/issues/Seichs/DriftTracker)
![GitHub pull requests](https://img.shields.io/github/issues-pr/Seichs/DriftTracker)

---

**DriftTracker** - Saving lives through intelligent drift prediction 🌊

*Built with ❤️ by [SharpByte Software](https://sharpbytesoftware.com/) for the search and rescue community*


