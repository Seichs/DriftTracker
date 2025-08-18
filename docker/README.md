# DriftTracker Docker Configuration

This directory contains Docker configuration files for the DriftTracker ocean drift prediction system.

## Overview

DriftTracker is containerized using Docker for consistent deployment across different environments. The Docker setup includes:

- **Production-ready containers** with security best practices
- **Development environment** with hot-reload capabilities
- **Testing environment** for automated testing
- **Multi-stage builds** for optimized image sizes

## Files

### Dockerfiles

- `Dockerfile` - Production Dockerfile with security hardening
- `Dockerfile.dev` - Development Dockerfile with additional tools

### Configuration

- `docker-compose.yml` - Multi-service orchestration
- `.dockerignore` - Optimized build context

## Quick Start

### Production

```bash
# Build and run production container
docker-compose up drifttracker

# Or build manually
docker build -f docker/Dockerfile -t drifttracker .
docker run -p 8000:8000 drifttracker
```

### Development

```bash
# Build and run development container with hot-reload
docker-compose --profile dev up drifttracker-dev

# Or build manually
docker build -f docker/Dockerfile.dev -t drifttracker-dev .
docker run -p 8001:8000 -v $(pwd)/backend:/app/backend drifttracker-dev
```

### Testing

```bash
# Run tests in container
docker-compose --profile test up drifttracker-test

# Or run manually
docker build -f docker/Dockerfile.dev -t drifttracker-test .
docker run drifttracker-test python -m pytest tests/ -v
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PYTHONPATH` | Python module path | `/app/backend` |
| `PYTHONUNBUFFERED` | Disable Python output buffering | `1` |
| `ENVIRONMENT` | Application environment | `production` |

## Volumes

The following directories are mounted as volumes:

- `../data` → `/app/data` - Ocean data storage
- `../logs` → `/app/logs` - Application logs
- `../backend` → `/app/backend` - Backend code (dev only)
- `../frontend` → `/app/frontend` - Frontend code (dev only)
- `../tests` → `/app/tests` - Test files (dev only)

## Security Features

- **Non-root user**: Application runs as `drifttracker` user
- **Minimal base image**: Uses Python slim image
- **No unnecessary packages**: Only required dependencies installed
- **Health checks**: Built-in health monitoring
- **Resource limits**: Configurable via docker-compose

## Performance Optimizations

- **Multi-stage builds**: Separate build and runtime stages
- **Layer caching**: Optimized Docker layer ordering
- **Build context**: Excludes unnecessary files via `.dockerignore`
- **Dependency caching**: Requirements installed before code copy

## Troubleshooting

### Common Issues

1. **Permission errors**: Ensure data/logs directories exist and are writable
2. **Port conflicts**: Change ports in docker-compose.yml if 8000/8001 are in use
3. **Build failures**: Check that all required files are present in the build context

### Debug Commands

```bash
# Check container logs
docker-compose logs drifttracker

# Access container shell
docker-compose exec drifttracker bash

# Check container health
docker-compose ps
```

## Contributing

When modifying Docker configurations:

1. Test both production and development builds
2. Update this README if adding new features
3. Ensure security best practices are maintained
4. Test with different Python versions if needed

---

**SharpByte Software** - Innovatieve Softwareproducten met Impact

*Delft, Nederland | [sharpbytesoftware.com](https://sharpbytesoftware.com/)* 