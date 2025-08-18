# DriftTracker - Root Makefile
# SharpByte Software - https://sharpbytesoftware.com/
#
# This Makefile delegates to scripts/Makefile for all operations
# This follows enterprise patterns used by Microsoft, Google, etc.

.PHONY: help install test lint format docker-build docker-run dev clean

# Default target
help:
	@echo "DriftTracker - Ocean Drift Prediction System"
	@echo "============================================="
	@echo ""
	@echo "Available commands:"
	@echo "  make help          Show this help message"
	@echo "  make install       Install dependencies"
	@echo "  make test          Run all tests"
	@echo "  make lint          Run code quality checks"
	@echo "  make format        Format code"
	@echo "  make dev           Start development server"
	@echo "  make docker-build  Build Docker image"
	@echo "  make docker-run    Run Docker container"
	@echo "  make clean         Clean build artifacts"
	@echo ""
	@echo "For detailed commands, see scripts/Makefile"
	@echo "For Docker operations, see docker/README.md"

# Delegate all targets to scripts/Makefile
%:
	@$(MAKE) -f scripts/Makefile $@

# Fallback for common targets
install:
	@$(MAKE) -f scripts/Makefile install

test:
	@$(MAKE) -f scripts/Makefile test

lint:
	@$(MAKE) -f scripts/Makefile lint

format:
	@$(MAKE) -f scripts/Makefile format

dev:
	@$(MAKE) -f scripts/Makefile dev

clean:
	@$(MAKE) -f scripts/Makefile clean

docker-build:
	@$(MAKE) -f scripts/Makefile docker-build

docker-run:
	@$(MAKE) -f scripts/Makefile docker-run 