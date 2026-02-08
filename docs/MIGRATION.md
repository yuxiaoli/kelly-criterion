# Migration from Poetry to UV

This project has been migrated from Poetry to [uv](https://github.com/astral-sh/uv) for dependency management and packaging.

## Key Changes

### 1. Configuration File
- **Old**: `pyproject.toml` with `[tool.poetry]` sections.
- **New**: `pyproject.toml` using standard PEP 621 `[project]` table and `[tool.uv]`.

### 2. Lock File
- **Old**: `poetry.lock`
- **New**: `uv.lock` (cross-platform, universal lock file).

### 3. Build System
- **Old**: `poetry-core`
- **New**: `hatchling` (standard PEP 517 build backend).

### 4. Command Mapping

| Action | Poetry Command | UV Command |
|--------|---------------|------------|
| Install dependencies | `poetry install` | `uv sync` |
| Add dependency | `poetry add <pkg>` | `uv add <pkg>` |
| Run command | `poetry run <cmd>` | `uv run <cmd>` |
| Update lock file | `poetry lock` | `uv lock` |
| Run tests | `poetry run pytest` | `uv run pytest` |

## Docker
The `Dockerfile` has been updated to use `uv` for faster builds. It uses `uv sync --frozen --no-dev` to install production dependencies.

## CI/CD
Any CI/CD pipelines should be updated to install `uv` (e.g., via `pip install uv` or the official action) and use the commands listed above.

## Development
- `uv` automatically creates and manages a virtual environment in `.venv`.
- `uv` is significantly faster than Poetry for resolution and installation.
