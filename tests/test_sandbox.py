"""Tests for Docker sandbox."""

import pytest


class TestDockerSandbox:
    """Tests for DockerSandbox class."""

    def test_create_sandbox(self, mock_config):
        """Test creating a sandbox."""
        from coding_swarm.sandbox import create_sandbox

        sandbox = create_sandbox(mock_config)
        assert sandbox is not None
        assert sandbox.mock_mode is True

    def test_create_sandbox_default(self):
        """Test creating sandbox with defaults."""
        from coding_swarm.sandbox import create_sandbox

        sandbox = create_sandbox()
        assert sandbox is not None
        assert sandbox.mock_mode is True

    def test_execute_code_mock_mode(self, mock_config):
        """Test executing code in mock mode."""
        from coding_swarm.sandbox import create_sandbox

        sandbox = create_sandbox(mock_config)
        result = sandbox.execute_code("print('hello')")

        assert result.success is True
        assert result.exit_code == 0
        assert "Mock execution" in result.stdout
        assert result.container_id == "mock-container-id"

    def test_execute_code_with_requirements(self, mock_config):
        """Test executing code with requirements."""
        from coding_swarm.sandbox import create_sandbox

        sandbox = create_sandbox(mock_config)
        result = sandbox.execute_code(
            "import requests",
            requirements=["requests"],
        )

        assert result.success is True

    def test_run_tests_mock_mode(self, mock_config):
        """Test running tests in mock mode."""
        from coding_swarm.sandbox import create_sandbox

        sandbox = create_sandbox(mock_config)
        project_files = {
            "main.py": "def add(a, b): return a + b",
            "test_main.py": "def test_add(): assert add(1, 2) == 3",
        }
        result = sandbox.run_tests(project_files)

        assert result.success is True
        assert result.tests_run == 5
        assert result.tests_passed == 5
        assert result.tests_failed == 0

    def test_is_available_mock_mode(self, mock_config):
        """Test checking availability in mock mode."""
        from coding_swarm.sandbox import create_sandbox

        sandbox = create_sandbox(mock_config)
        assert sandbox.is_available() is True

    def test_pull_image_mock_mode(self, mock_config):
        """Test pulling image in mock mode."""
        from coding_swarm.sandbox import create_sandbox

        sandbox = create_sandbox(mock_config)
        assert sandbox.pull_image() is True

    def test_cleanup_mock_mode(self, mock_config):
        """Test cleanup in mock mode."""
        from coding_swarm.sandbox import create_sandbox

        sandbox = create_sandbox(mock_config)
        sandbox.cleanup()
        # Should not raise


class TestSandboxResult:
    """Tests for SandboxResult model."""

    def test_sandbox_result_success(self):
        """Test successful sandbox result."""
        from coding_swarm.models import SandboxResult

        result = SandboxResult(
            success=True,
            exit_code=0,
            stdout="Output",
            stderr="",
            duration_seconds=1.5,
        )
        assert result.success is True
        assert result.exit_code == 0

    def test_sandbox_result_failure(self):
        """Test failed sandbox result."""
        from coding_swarm.models import SandboxResult

        result = SandboxResult(
            success=False,
            exit_code=1,
            stdout="",
            stderr="Error occurred",
            duration_seconds=0.5,
        )
        assert result.success is False
        assert "Error" in result.stderr


class TestTestResult:
    """Tests for TestResult model."""

    def test_test_result_all_passed(self):
        """Test result with all tests passed."""
        from coding_swarm.models import TestResult

        result = TestResult(
            success=True,
            exit_code=0,
            stdout="10 passed",
            tests_run=10,
            tests_passed=10,
            tests_failed=0,
        )
        assert result.success is True
        assert result.tests_run == 10
        assert result.tests_failed == 0

    def test_test_result_some_failed(self):
        """Test result with some tests failed."""
        from coding_swarm.models import TestResult

        result = TestResult(
            success=False,
            exit_code=1,
            stdout="8 passed, 2 failed",
            tests_run=10,
            tests_passed=8,
            tests_failed=2,
        )
        assert result.success is False
        assert result.tests_failed == 2


class TestParsePytestOutput:
    """Tests for pytest output parsing."""

    def test_parse_passed_only(self, mock_config):
        """Test parsing output with only passed tests."""
        from coding_swarm.sandbox import create_sandbox

        sandbox = create_sandbox(mock_config)
        sandbox.mock_mode = False  # Test the actual parsing logic

        output = "===== 5 passed in 0.5s ====="
        total, passed, failed = sandbox._parse_pytest_output(output)

        assert passed == 5
        assert failed == 0
        assert total == 5

    def test_parse_mixed_results(self, mock_config):
        """Test parsing output with mixed results."""
        from coding_swarm.sandbox import create_sandbox

        sandbox = create_sandbox(mock_config)
        sandbox.mock_mode = False

        output = "===== 3 passed, 2 failed in 1.0s ====="
        total, passed, failed = sandbox._parse_pytest_output(output)

        assert passed == 3
        assert failed == 2
        assert total == 5

    def test_parse_with_errors(self, mock_config):
        """Test parsing output with errors."""
        from coding_swarm.sandbox import create_sandbox

        sandbox = create_sandbox(mock_config)
        sandbox.mock_mode = False

        output = "===== 4 passed, 1 failed, 1 error in 1.0s ====="
        total, passed, failed = sandbox._parse_pytest_output(output)

        assert passed == 4
        assert failed == 2  # 1 failed + 1 error

    def test_parse_no_results(self, mock_config):
        """Test parsing output with no test results."""
        from coding_swarm.sandbox import create_sandbox

        sandbox = create_sandbox(mock_config)
        sandbox.mock_mode = False

        output = "No tests found"
        total, passed, failed = sandbox._parse_pytest_output(output)

        assert passed == 0
        assert failed == 0
        assert total == 0
