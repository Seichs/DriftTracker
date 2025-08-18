# Contributing to DriftTracker

Thank you for your interest in contributing to DriftTracker! This document provides guidelines and information for contributors.

## 🌊 What is DriftTracker?

DriftTracker is an AI-powered ocean drift prediction system designed for search and rescue operations. Our mission is to help save lives by providing accurate drift predictions that enable rescue teams to optimize their search strategies.

## 🤝 How to Contribute

There are many ways to contribute to DriftTracker:

- **Report bugs** and help us verify fixes
- **Suggest new features** and improvements
- **Review source code changes**
- **Improve documentation** (fix typos, add examples, clarify concepts)
- **Contribute code** (fix bugs, implement features, improve performance)
- **Help with testing** and quality assurance
- **Share your expertise** in oceanography, search & rescue, or software development

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- A GitHub account
- Basic knowledge of Python, FastAPI, and oceanography (helpful but not required)
- Copernicus Marine account for ocean data access

### Development Setup

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/Seichs/DriftTracker.git
   cd DriftTracker
   ```

2. **Set up the development environment**
   ```bash
   # Install dependencies
   make install-dev
   
   # Set up pre-commit hooks
   make pre-commit-install
   ```

3. **Create a development branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make your changes and test them**
   ```bash
   # Run tests
   make test
   
   # Check code quality
   make lint
   make type-check
   ```

5. **Commit and push your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**

## 📋 Development Guidelines

### Code Style

We follow Python best practices and use automated tools to maintain code quality:

- **Black** for code formatting (line length: 127 characters)
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking
- **pylint** for additional code analysis

Run these tools before submitting:
```bash
make format    # Format code with Black and isort
make lint      # Run linting checks
make type-check # Run type checking
```

### Testing

All code changes must include appropriate tests:

- **Unit tests** for individual functions and classes
- **Integration tests** for API endpoints and workflows
- **Performance tests** for critical functions
- **End-to-end tests** for complete user workflows

Run tests with:
```bash
make test              # Run all tests
make test-unit         # Run unit tests only
make test-coverage     # Run tests with coverage report
```

**Coverage Requirements:**
- Minimum 80% code coverage
- 100% coverage for critical functions
- All new features must have tests

### Documentation

- **Docstrings** for all public functions and classes
- **Type hints** for all function parameters and return values
- **README updates** for new features
- **API documentation** for new endpoints

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat: add wind influence to drift calculations
fix: resolve coordinate validation edge case
docs: update API documentation for new endpoints
test: add performance benchmarks for drift calculator
```

## 🐛 Reporting Bugs

Before reporting a bug, please:

1. **Search existing issues** to see if it's already reported
2. **Check the documentation** to ensure it's not a configuration issue
3. **Try to reproduce** the issue with the latest version

When reporting a bug, include:

- **Clear description** of the problem
- **Steps to reproduce** the issue
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, dependencies)
- **Error messages** and stack traces
- **Screenshots** if applicable

## 💡 Suggesting Features

We welcome feature suggestions! When proposing a feature:

1. **Describe the problem** you're trying to solve
2. **Explain your proposed solution**
3. **Consider the impact** on existing functionality
4. **Think about implementation** complexity
5. **Consider use cases** beyond your specific need

## 🔧 Development Workflow

### Before Starting Work

1. **Check the roadmap** and current issues
2. **Discuss your approach** in an issue or discussion
3. **Ensure your idea aligns** with project goals
4. **Consider the impact** on performance and maintainability

### During Development

1. **Write tests first** (TDD approach)
2. **Keep commits small** and focused
3. **Update documentation** as you go
4. **Test thoroughly** with different scenarios
5. **Consider edge cases** and error conditions

### Before Submitting

1. **Run the full test suite**
2. **Check code quality** with all tools
3. **Update documentation** if needed
4. **Test with real data** if applicable
5. **Review your changes** for clarity and completeness

## 📚 Project Structure

```
DriftTracker/
├── backend/                 # FastAPI backend
│   ├── cli/                # Application entry point
│   ├── drifttracker/       # Core engine
│   └── ml/                 # Machine learning models
├── frontend/               # Web interface
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── e2e/              # End-to-end tests
│   └── performance/      # Performance tests
└── docs/                  # Documentation
```

## 🧪 Testing Guidelines

### Unit Tests
- Test individual functions and methods
- Use mocking for external dependencies
- Cover edge cases and error conditions
- Aim for fast execution (< 1 second per test)

### Integration Tests
- Test component interactions
- Use real data when possible
- Test API endpoints end-to-end
- Verify data flow between components

### Performance Tests
- Benchmark critical functions
- Test with large datasets
- Monitor memory usage
- Ensure scalability

### Test Data
- Use realistic North Sea ocean current data
- Include Dutch coastal coordinate ranges (52.0-53.0°N, 3.5-4.8°E)
- Test different object types (people, vessels, equipment)
- Cover multiple time periods and seasonal variations

## 🔒 Security Considerations

- **Never commit credentials** or sensitive data
- **Validate all inputs** thoroughly
- **Handle errors securely** (no information leakage)
- **Follow security best practices** for web applications
- **Report security issues** privately to maintainers

## 🌍 Domain Knowledge

DriftTracker involves oceanography and search & rescue concepts. If you're new to these domains:

### Oceanography Basics
- **North Sea currents**: Surface and subsurface water movement in Dutch waters
- **Wind effects**: How wind influences surface drift in the North Sea
- **Tidal effects**: Impact of tides on drift patterns in coastal areas
- **Geographic considerations**: How latitude affects calculations in the North Sea region

### Search & Rescue
- **Search patterns**: Sector Search, Expanding Square, Parallel Sweep, Parallel Track
- **Time criticality**: Why accurate predictions matter in North Sea conditions
- **Resource optimization**: How to maximize search effectiveness in Dutch waters
- **Safety considerations**: Protecting rescue personnel in challenging North Sea conditions

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check the docs folder and README
- **Code Examples**: Look at existing tests and examples

## 🏆 Recognition

Contributors are recognized in several ways:

- **Contributors list** on GitHub
- **Release notes** for significant contributions
- **Documentation credits** for major features
- **Community appreciation** for all contributions

## 📄 License

By contributing to DriftTracker, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You

Thank you for contributing to DriftTracker! Every contribution, no matter how small, helps us improve our ability to save lives through better drift prediction.

---

*This contributing guide is inspired by the excellent documentation from the [VS Code project](https://github.com/microsoft/vscode) and adapted for DriftTracker's specific needs.*

---

**SharpByte Software** - Innovatieve Softwareproducten met Impact

*Delft, Nederland | [sharpbytesoftware.com](https://sharpbytesoftware.com/)* 