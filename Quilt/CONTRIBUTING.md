# Contributing to Quilt

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. **Fork and clone the repository**:
   ```bash
   git clone <your-fork-url>
   cd Quilt
   ```

2. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Set up the development environment**:
   ```bash
   uv sync --dev
   ```

4. **Activate the environment**:
   ```bash
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```

## Code Style

We use:
- **Black** for code formatting (line length: 100)
- **Ruff** for linting
- **Python 3.12+** syntax

### Formatting

```bash
# Format all code
uv run black macro_gate_detector/ tests/ examples/

# Check formatting
uv run black --check macro_gate_detector/ tests/ examples/
```

### Linting

```bash
# Run linter
uv run ruff check macro_gate_detector/ tests/ examples/

# Auto-fix issues
uv run ruff check --fix macro_gate_detector/ tests/ examples/
```

## Testing

1. **Run all tests**:
   ```bash
   uv run pytest macro_gate_detector/tests/
   ```

2. **Run with coverage**:
   ```bash
   uv run pytest macro_gate_detector/tests/ --cov=macro_gate_detector --cov-report=html
   ```

3. **Run specific test**:
   ```bash
   uv run pytest macro_gate_detector/tests/test_3_qasm.py -v
   ```

## Project Structure

- `macro_gate_detector/` - Main package code
- `macro_gate_detector/tests/` - Test suite
- `examples/` - Example scripts demonstrating usage
- `output/` - Generated files (images, JSON) - not committed to git

## Adding New Features

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the code style guidelines

3. Add tests for new functionality

4. Update documentation if needed

5. Run tests and ensure they pass:
   ```bash
   uv run pytest macro_gate_detector/tests/
   ```

6. Format and lint your code:
   ```bash
   uv run black macro_gate_detector/
   uv run ruff check macro_gate_detector/
   ```

7. Commit your changes:
   ```bash
   git add .
   git commit -m "Add: description of your feature"
   ```

## Adding Dependencies

If you need to add a new dependency:

```bash
# Runtime dependency
uv add package-name

# Dev dependency
uv add --dev package-name
```

This automatically updates `pyproject.toml` and `uv.lock`.

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Follow the commit message format: `Type: Description`
   - Types: `Add`, `Fix`, `Update`, `Remove`, `Refactor`, `Docs`
4. Create a pull request with a clear description

## Questions?

Feel free to open an issue for questions or discussions!

