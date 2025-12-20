# Self-Correcting Coding Swarm

A multi-agent coding system that uses LibCST for safe code refactoring, Docker for sandboxed execution, and Gemini AI for intelligent code generation with automatic self-correction.

## Features

- **Multi-Agent Architecture**: Specialized agents for architecture, coding, refactoring, testing, and review
- **Safe Code Refactoring**: Uses LibCST (Concrete Syntax Tree) for syntax-safe code transformations
- **Docker Sandboxing**: Execute and test generated code in isolated containers
- **Self-Correction Loop**: Automatically fixes code based on test failures
- **Gemini AI Integration**: Leverages Gemini 3.0 for intelligent code generation
- **Type-Safe Models**: Pydantic models for all data structures
- **Rich CLI**: Beautiful command-line interface with progress indicators

## Installation

```bash
# Clone the repository
git clone https://github.com/lord-dubious/self-correcting-swarm.git
cd self-correcting-swarm

# Create virtual environment and install
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Configuration

Create a `.env` file with your settings:

```env
GEMINI_API_KEY=your-api-key-here
DOCKER_IMAGE=python:3.11-slim
DOCKER_TIMEOUT=60
MAX_RETRIES=3
```

## Usage

### Generate a Complete Project

```bash
# Generate a project from a description
swarm generate "A REST API with user authentication and CRUD operations" \
    --output ./my-project \
    --req "Use FastAPI" \
    --req "Include JWT authentication"

# With mock mode for testing
swarm generate "A calculator" --mock
```

### Generate a Single File

```bash
# Generate a specific file
swarm generate-file "src/utils.py" "String manipulation utilities" \
    --output ./utils.py

# Preview without saving
swarm generate-file "src/helpers.py" "Helper functions for data processing"
```

### Refactor Existing Code

```bash
# Refactor a file using LibCST
swarm refactor ./src/main.py --output ./src/main_refactored.py

# Preview refactoring
swarm refactor ./src/main.py
```

### Review Code

```bash
# Get AI code review
swarm review ./src/main.py
```

### Validate Syntax

```bash
# Validate Python syntax using LibCST
swarm validate ./src/main.py
```

### Demo Mode

```bash
# Run a demo in mock mode
swarm demo
```

### System Info

```bash
# Check system status
swarm info
```

## Architecture

### Agents

| Agent | Role | Description |
|-------|------|-------------|
| **Architect** | Planning | Designs project structure and file layout |
| **Coder** | Generation | Generates production-quality Python code |
| **Refactorer** | Improvement | Suggests and applies code refactoring |
| **Tester** | Testing | Generates comprehensive test suites |
| **Reviewer** | Quality | Reviews code for issues and improvements |

### Tools

| Tool | Purpose |
|------|---------|
| **LibCST** | Syntax-safe code transformations |
| **Docker** | Sandboxed code execution |
| **Gemini AI** | Intelligent code generation |

### Self-Correction Flow

```
┌─────────────┐    ┌──────────┐    ┌───────────┐
│  Architect  │───>│  Coder   │───>│ Refactor  │
└─────────────┘    └──────────┘    └───────────┘
                                         │
                   ┌──────────┐    ┌─────▼─────┐
                   │  Review  │<───│   Test    │
                   └──────────┘    └───────────┘
                                         │
                         ┌───────────────┼───────────────┐
                         │               │               │
                         ▼               ▼               ▼
                    [SUCCESS]       [FIX CODE]      [MAX RETRIES]
                                         │
                                         └──> Back to Coder
```

## Python API

```python
from coding_swarm import (
    create_swarm,
    create_config,
    create_refactorer,
)

# Create configuration
config = create_config(
    gemini_api_key="your-key",
    max_retries=3,
    enable_mock_mode=False,
)

# Create swarm
swarm = create_swarm(config)

# Generate a project
session = swarm.generate_project(
    description="A CLI tool for managing tasks",
    requirements=["Use Typer", "Include persistence"],
)

# Save to disk
project_path = swarm.save_project(session, "./output")

# Generate a single file
code_file = swarm.generate_file(
    file_path="src/utils.py",
    description="Utility functions",
)

# Review code
review = swarm.review_code(code_file.content, code_file.path)

# Refactor code using LibCST
refactorer = create_refactorer()
refactored = refactorer.rename_function(code, "old_name", "new_name")

# Clean up
swarm.cleanup()
```

## LibCST Refactoring

The package provides safe code transformations using LibCST:

```python
from coding_swarm import create_refactorer

refactorer = create_refactorer()

# Add imports
code = refactorer.add_imports(code, ["import os", "from typing import List"])

# Rename functions
code = refactorer.rename_function(code, "old_func", "new_func")

# Rename classes
code = refactorer.rename_class(code, "OldClass", "NewClass")

# Add docstrings
code = refactorer.add_docstring(code, "my_function", "This function does X.")

# Extract functions
functions = refactorer.extract_functions(code)

# Extract classes
classes = refactorer.extract_classes(code)

# Validate syntax
is_valid, error = refactorer.validate_syntax(code)
```

## Docker Sandbox

Execute code safely in Docker containers:

```python
from coding_swarm import create_sandbox, create_config

config = create_config()
sandbox = create_sandbox(config)

# Execute code
result = sandbox.execute_code(
    code="print('Hello, World!')",
    filename="main.py",
    requirements=["requests"],
)

# Run tests
test_result = sandbox.run_tests(
    project_files={
        "main.py": "def add(a, b): return a + b",
        "test_main.py": "def test_add(): assert add(1, 2) == 3",
    },
)

print(f"Tests passed: {test_result.tests_passed}")
print(f"Tests failed: {test_result.tests_failed}")
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=coding_swarm

# Run specific test file
pytest tests/test_refactorer.py -v
```

## Docker

```bash
# Build image
docker build -t coding-swarm .

# Run with Docker Compose
docker-compose up
```

## Requirements

- Python 3.10+
- Docker (for sandboxed execution)
- Gemini API key

## License

MIT License - see [LICENSE](LICENSE) for details.
