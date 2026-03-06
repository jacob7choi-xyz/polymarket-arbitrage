# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Restructured to standard src layout (`src/polymarket_arbitrage/`)
- Migrated from Poetry to uv for package management and builds
- Replaced black with ruff for formatting (ruff handles both linting and formatting)
- Updated Dockerfile to use uv with multi-stage build
- Updated pre-commit config to use ruff format instead of black
- All imports now use `polymarket_arbitrage` package name instead of `src`

### Fixed
- All mypy strict-mode errors resolved (26 errors across 9 files)
- All ruff lint errors resolved
- Test fixtures updated to use relative dates (no more hardcoded 2025 dates)
- Pydantic v2 compatibility: replaced `**dict` unpacking with `model_validate`

### Removed
- `demo.py` (referenced attributes that no longer exist)
- Poetry lock file and Poetry-based workflow

## [0.1.0] - 2025-01-15

### Added
- Core arbitrage detection engine (YES + NO < threshold)
- Async API client with HTTP/2 support (httpx)
- Circuit breaker pattern for API resilience
- Exponential backoff with jitter for retries
- Token bucket rate limiter
- Multi-endpoint fallback for API calls
- Flexible response parser (camelCase/snake_case, wrapped/unwrapped)
- Paper trading executor with capital management
- Position tracker with P&L calculations
- Pydantic v2 domain models (frozen, validated)
- Custom exception hierarchy
- Protocol-based interfaces (PEP 544)
- Structured logging with structlog (JSON + console modes)
- Prometheus metrics (golden signals + business metrics)
- Pydantic BaseSettings for typed configuration
- Environment variable support with `.env` files
- Docker multi-stage build
- docker-compose stack (app + Prometheus + Grafana)
- Unit test suite (54 tests)
- Pre-commit hooks (ruff, mypy)
- MIT license
