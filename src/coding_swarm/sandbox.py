"""Docker sandbox for safe code execution."""

from __future__ import annotations

import tempfile
import time
from importlib import import_module
from pathlib import Path
from typing import Any

from coding_swarm.models import SandboxResult, SwarmConfig, TestResult


class DockerSandbox:
    """Docker-based sandbox for executing code safely."""

    def __init__(self, config: SwarmConfig) -> None:
        """Initialize the sandbox.

        Args:
            config: Swarm configuration
        """
        self.config = config
        self.mock_mode = config.enable_mock_mode
        self._client: Any | None = None

    @property
    def client(self) -> Any:
        """Get or create Docker client."""
        if self._client is None:
            if self.mock_mode:
                raise RuntimeError("Docker client is unavailable while mock mode is enabled")
            docker = import_module("docker")
            self._client = docker.from_env()
        return self._client

    def _format_error(self, error: Exception) -> str:
        """Return concise exception context for sandbox metadata."""
        return f"{error.__class__.__name__}: {error}"

    def execute_code(
        self,
        code: str,
        filename: str = "main.py",
        requirements: list[str] | None = None,
        timeout: int | None = None,
    ) -> SandboxResult:
        """Execute Python code in a Docker container.

        Args:
            code: Python code to execute
            filename: Filename for the code
            requirements: List of pip requirements
            timeout: Execution timeout (uses config default if None)

        Returns:
            SandboxResult with execution details
        """
        if self.mock_mode:
            return SandboxResult(
                success=True,
                exit_code=0,
                stdout="Mock execution successful",
                stderr="",
                duration_seconds=0.1,
                container_id="mock-container-id",
                execution_source="mock",
                is_degraded=True,
                warnings=["Mock mode skipped Docker execution and returned a canned result."],
            )

        timeout = timeout or self.config.docker_timeout
        requirements = requirements or []

        start_time = time.time()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write code to temp file
            code_path = Path(tmpdir) / filename
            code_path.write_text(code)

            # Write requirements if any
            if requirements:
                req_path = Path(tmpdir) / "requirements.txt"
                req_path.write_text("\n".join(requirements))

            # Build command
            if requirements:
                cmd = f"pip install -q -r /code/requirements.txt && python /code/{filename}"
            else:
                cmd = f"python /code/{filename}"

            try:
                container = self.client.containers.run(
                    image=self.config.docker_image,
                    command=["sh", "-c", cmd],
                    volumes={tmpdir: {"bind": "/code", "mode": "ro"}},
                    mem_limit=self.config.docker_memory_limit,
                    cpu_period=100000,
                    cpu_quota=int(self.config.docker_cpu_limit * 100000),
                    network_disabled=True,
                    remove=False,
                    detach=True,
                )

                # Wait for completion
                result = container.wait(timeout=timeout)
                exit_code = result.get("StatusCode", 1)

                # Get logs
                stdout = container.logs(stdout=True, stderr=False).decode("utf-8")
                stderr = container.logs(stdout=False, stderr=True).decode("utf-8")

                container_id = container.id or ""
                container.remove()

                duration = time.time() - start_time

                return SandboxResult(
                    success=exit_code == 0,
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                    duration_seconds=duration,
                    container_id=container_id,
                    execution_source="docker",
                )

            except Exception as e:
                duration = time.time() - start_time
                error = self._format_error(e)
                return SandboxResult(
                    success=False,
                    exit_code=1,
                    stdout="",
                    stderr=error,
                    duration_seconds=duration,
                    container_id="",
                    execution_source="fallback",
                    is_degraded=True,
                    warnings=[
                        "Docker execution failed before a successful sandbox result was available."
                    ],
                    error=error,
                )

    def run_tests(
        self,
        project_files: dict[str, str],
        test_command: str = "python -m pytest -v",
        requirements: list[str] | None = None,
        timeout: int | None = None,
    ) -> TestResult:
        """Run tests in a Docker container.

        Args:
            project_files: Dict mapping file paths to contents
            test_command: Command to run tests
            requirements: List of pip requirements
            timeout: Execution timeout

        Returns:
            TestResult with test execution details
        """
        if self.mock_mode:
            return TestResult(
                success=True,
                exit_code=0,
                stdout="===== 5 passed in 0.1s =====",
                stderr="",
                duration_seconds=0.1,
                tests_run=5,
                tests_passed=5,
                tests_failed=0,
                execution_source="mock",
                is_degraded=True,
                warnings=[
                    "Mock mode skipped Docker test execution and returned canned pytest counts."
                ],
            )

        timeout = timeout or self.config.docker_timeout
        requirements = requirements or []

        start_time = time.time()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write all project files
            for file_path, content in project_files.items():
                full_path = Path(tmpdir) / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)

            # Write requirements
            all_requirements = requirements + ["pytest"]
            req_path = Path(tmpdir) / "requirements.txt"
            req_path.write_text("\n".join(all_requirements))

            # Build command
            cmd = f"pip install -q -r /code/requirements.txt && cd /code && {test_command}"

            try:
                container = self.client.containers.run(
                    image=self.config.docker_image,
                    command=["sh", "-c", cmd],
                    volumes={tmpdir: {"bind": "/code", "mode": "ro"}},
                    mem_limit=self.config.docker_memory_limit,
                    cpu_period=100000,
                    cpu_quota=int(self.config.docker_cpu_limit * 100000),
                    network_disabled=True,
                    remove=False,
                    detach=True,
                )

                # Wait for completion
                result = container.wait(timeout=timeout)
                exit_code = result.get("StatusCode", 1)

                # Get logs
                stdout = container.logs(stdout=True, stderr=False).decode("utf-8")
                stderr = container.logs(stdout=False, stderr=True).decode("utf-8")

                container.remove()

                duration = time.time() - start_time

                # Parse test results
                tests_run, tests_passed, tests_failed = self._parse_pytest_output(stdout)

                return TestResult(
                    success=exit_code == 0,
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                    duration_seconds=duration,
                    tests_run=tests_run,
                    tests_passed=tests_passed,
                    tests_failed=tests_failed,
                    execution_source="docker",
                )

            except Exception as e:
                duration = time.time() - start_time
                error = self._format_error(e)
                return TestResult(
                    success=False,
                    exit_code=1,
                    stdout="",
                    stderr=error,
                    duration_seconds=duration,
                    tests_run=0,
                    tests_passed=0,
                    tests_failed=0,
                    execution_source="fallback",
                    is_degraded=True,
                    warnings=["Docker test execution failed before pytest results were available."],
                    error=error,
                )

    def _parse_pytest_output(self, output: str) -> tuple[int, int, int]:
        """Parse pytest output to extract test counts.

        Args:
            output: Pytest stdout

        Returns:
            Tuple of (tests_run, tests_passed, tests_failed)
        """
        import re

        # Try to find the summary line like "5 passed, 2 failed"
        passed_match = re.search(r"(\d+) passed", output)
        failed_match = re.search(r"(\d+) failed", output)
        error_match = re.search(r"(\d+) error", output)

        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        errors = int(error_match.group(1)) if error_match else 0

        total = passed + failed + errors
        return total, passed, failed + errors

    def cleanup(self) -> None:
        """Clean up Docker resources."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def pull_image(self) -> bool:
        """Pull the Docker image if not present.

        Returns:
            True if image is available
        """
        if self.mock_mode:
            return True

        try:
            self.client.images.get(self.config.docker_image)
            return True
        except Exception:
            try:
                self.client.images.pull(self.config.docker_image)
                return True
            except Exception:
                return False

    def is_available(self) -> bool:
        """Check if Docker is available.

        Returns:
            True if Docker is running and accessible
        """
        if self.mock_mode:
            return True

        try:
            self.client.ping()
            return True
        except Exception:
            return False


def create_sandbox(config: SwarmConfig | None = None) -> DockerSandbox:
    """Create a DockerSandbox instance.

    Args:
        config: Optional swarm configuration

    Returns:
        DockerSandbox instance
    """
    if config is None:
        config = SwarmConfig(enable_mock_mode=True)
    return DockerSandbox(config)
