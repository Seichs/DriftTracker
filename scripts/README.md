# DriftTracker Build Scripts

This directory contains build scripts and automation tools for the DriftTracker project.

## Overview

The build system follows enterprise patterns used by Microsoft, Google, and other large software companies:

- **Root Makefile**: Simple delegation to scripts
- **Scripts Directory**: All build logic and automation
- **Docker Directory**: Containerization and deployment
- **Modular Structure**: Clear separation of concerns

## Files

### Build Tools

- `Makefile` - Main build automation with all development commands
- `test_core_functionality.py` - Comprehensive functionality test script

## Usage

### From Root Directory

```bash
# All commands work from the project root
make help          # Show available commands
make install       # Install dependencies
make test          # Run all tests
make dev           # Start development server
make docker-build  # Build Docker image
```

### From Scripts Directory

```bash
# Direct access to build tools
cd scripts
make help          # Show detailed help
make test-unit     # Run unit tests only
make test-coverage # Run tests with coverage
make lint          # Run code quality checks
```

## Build System Architecture

```
DriftTracker/
├── Makefile              # Root delegation (simple)
├── scripts/
│   ├── Makefile         # Main build logic
│   ├── test_core_functionality.py
│   └── README.md        # This file
├── docker/
│   ├── Dockerfile       # Production container
│   ├── Dockerfile.dev   # Development container
│   ├── docker-compose.yml
│   └── README.md        # Docker documentation
├── backend/             # Application code
├── frontend/            # Frontend assets
└── tests/               # Test suite
```

## Why This Structure?

### Enterprise Benefits

1. **Separation of Concerns**: Build tools separate from application code
2. **Scalability**: Easy to add new build tools and scripts
3. **Maintainability**: Clear organization and documentation
4. **Team Collaboration**: Standardized build processes
5. **CI/CD Integration**: Easy integration with automated pipelines

### Microsoft/Google Patterns

This structure follows patterns used by:
- **Microsoft VS Code**: Scripts in dedicated directories
- **Google Cloud**: Build tools in separate modules
- **Kubernetes**: Scripts organized by function
- **Docker**: Build context separated from application

## Adding New Scripts

When adding new build tools:

1. **Place in scripts/**: All build automation goes here
2. **Update Makefile**: Add new targets to scripts/Makefile
3. **Document**: Update this README with new functionality
4. **Test**: Ensure scripts work from both root and scripts directories

## Best Practices

- **Keep root Makefile simple**: Only delegation, no complex logic
- **Document everything**: Each script should have clear documentation
- **Follow conventions**: Use consistent naming and structure
- **Test thoroughly**: All scripts should be tested and reliable
- **Version control**: All scripts should be tracked in git

---

**SharpByte Software** - Innovatieve Softwareproducten met Impact

*Delft, Nederland | [sharpbytesoftware.com](https://sharpbytesoftware.com/)* 