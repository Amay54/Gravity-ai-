# Contributing to GravityAI

Thank you for your interest in contributing to the GravityAI Enterprise AI Research Operating System! We welcome bug fixes, enhancement requests, documentation, and pull requests.

## Development Workflow

### 1. Prerequisite Packages
- **Python 3.12+**
- **uv** ( Astral's Python package manager )
- **Docker**

### 2. Sandbox Setup
1. Clone the repository.
2. Initialize environment parameters:
   ```bash
   cp .env.example .env
   ```
3. Sync local virtual environment dependencies:
   ```bash
   uv sync
   ```

### 3. Standards & Guidelines
- **Linting & Formatting**: We use Ruff for code quality check and formatting. Run:
  ```bash
  uv run ruff check .
  uv run ruff format .
  ```
- **Pydantic Validation**: All API schemas and repository records must use strongly-typed Pydantic models.
- **Testing**: Ensure that all changes are verified by unit tests under `tests/`. Run the test suite:
  ```bash
  uv run pytest tests/ -v
  ```
