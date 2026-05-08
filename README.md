# Self-Correcting Coding Swarm

Experimental Python helpers for combining Gemini text generation, LibCST refactoring utilities, and Docker-based execution checks. The project is useful for local demos and tests, but generated output should be reviewed before use.

## Portfolio Review

- [Architecture](docs/ARCHITECTURE.md) - component boundaries, data flow, external dependencies, and degraded-mode behavior.
- [Demo Guide](docs/DEMO.md) - safe local walkthrough commands and recruiter-facing talking points.

## What Works Today

- Pydantic models describe tasks, generated files, reviews, test results, and sandbox results.
- Mock mode returns deterministic code, reviews, tests, and sandbox results for tests and demos.
- Gemini-backed agents can request project plans, code, tests, fixes, and reviews when configured with an API key.
- LibCST helpers support focused transformations such as adding imports, renaming functions/classes, adding docstrings, and validating Python syntax.
- Docker sandbox methods can execute code or run pytest when Docker is available locally.

## Current Limits

- Generated code and tests are drafts. They may be incomplete, unsafe, or syntactically invalid.
- The retry loop is simple and may apply broad fixes to multiple files.
- Review results are model-generated and are not a substitute for human review or CI.
- Refactoring support is intentionally narrow and does not cover large architectural changes.
- Docker execution depends on the local daemon, image availability, and environment permissions.

## Dependency Behavior

- Gemini calls require `GEMINI_API_KEY` and the `google-generativeai` package.
- Docker sandboxing requires the Docker Python SDK and a reachable Docker daemon.
- Sandbox commands install requested requirements inside the container command; failures are returned in result metadata and stderr.
- In mock mode, Gemini and Docker are skipped and results include provenance metadata such as `generation_source="mock"`, `execution_source="mock"`, and `is_degraded=True`.

## Mock/Sandbox Boundaries

- Mock generated code, tests, and reviews are placeholders for tests and demos only.
- Gemini JSON parsing failures fall back to raw model text where possible and include `warnings` plus `error` context.
- Docker failures return `execution_source="fallback"`, `is_degraded=True`, and formatted error details instead of silently looking successful.
- Sandbox execution is not a security guarantee; keep inputs and mounted paths limited.

## Installation

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Configuration

Create a `.env` file or export environment variables as needed:

```env
GEMINI_API_KEY=your-api-key-here
DOCKER_IMAGE=python:3.11-slim
DOCKER_TIMEOUT=60
MAX_RETRIES=3
```

## Usage

Generate a project draft:

```bash
swarm generate "A REST API with user authentication" --output ./my-project --req "Use FastAPI"
```

Run deterministic mock mode:

```bash
swarm generate "A calculator" --mock
swarm demo
```

Generate one file:

```bash
swarm generate-file "src/utils.py" "String manipulation utilities" --output ./utils.py
```

Use LibCST helpers:

```bash
swarm validate ./src/main.py
swarm refactor ./src/main.py --output ./src/main_refactored.py
```

Review a file with the configured agent path:

```bash
swarm review ./src/main.py
```

## Python API

```python
import logging

from coding_swarm import create_config, create_swarm

logger = logging.getLogger(__name__)
config = create_config(gemini_api_key="your-key", enable_mock_mode=False)
swarm = create_swarm(config)

code_file = swarm.generate_file(
    file_path="src/utils.py",
    description="Utility functions",
)
logger.info(
    "generated file provenance",
    extra={
        "source": code_file.generation_source,
        "degraded": code_file.is_degraded,
        "warnings": code_file.warnings,
    },
)

swarm.cleanup()
```

## Testing

```bash
/home/violet/.local/bin/ruff check src/ tests/
/home/violet/.local/bin/ruff format --check src/ tests/
python -m compileall -q src tests
uv run pytest tests/ -v --cov=coding_swarm --cov-report=xml
uv run mypy src/ --ignore-missing-imports
```

## Requirements

- Python 3.10+
- Docker for real sandbox execution
- Gemini API key for non-mock generation

## License

MIT License - see [LICENSE](LICENSE) for details.
