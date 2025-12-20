"""Tests for Pydantic models."""

import pytest
from datetime import datetime


class TestSwarmConfig:
    """Tests for SwarmConfig model."""

    def test_default_config(self, monkeypatch):
        """Test default configuration values."""
        # Clear the env var set by conftest to test true defaults
        monkeypatch.delenv("ENABLE_MOCK_MODE", raising=False)
        from coding_swarm.models import SwarmConfig

        config = SwarmConfig()
        assert config.gemini_model == "gemini-2.0-flash"
        assert config.docker_image == "python:3.11-slim"
        assert config.docker_timeout == 60
        assert config.max_retries == 3
        # Note: enable_mock_mode may be True due to env var in conftest

    def test_config_with_overrides(self):
        """Test configuration with custom values."""
        from coding_swarm.models import SwarmConfig

        config = SwarmConfig(
            gemini_api_key="test-key",
            docker_timeout=120,
            max_retries=5,
            enable_mock_mode=True,
        )
        assert config.gemini_api_key == "test-key"
        assert config.docker_timeout == 120
        assert config.max_retries == 5
        assert config.enable_mock_mode is True

    def test_create_config_factory(self):
        """Test create_config factory function."""
        from coding_swarm.models import create_config

        config = create_config(enable_mock_mode=True)
        assert config.enable_mock_mode is True


class TestCodeFile:
    """Tests for CodeFile model."""

    def test_code_file_creation(self):
        """Test creating a CodeFile."""
        from coding_swarm.models import CodeFile, FileOperation

        code_file = CodeFile(
            path="src/main.py",
            content="print('hello')",
            language="python",
        )
        assert code_file.path == "src/main.py"
        assert code_file.content == "print('hello')"
        assert code_file.operation == FileOperation.CREATE

    def test_code_file_filename(self):
        """Test filename property."""
        from coding_swarm.models import CodeFile

        code_file = CodeFile(path="src/utils/helpers.py")
        assert code_file.filename == "helpers.py"

    def test_code_file_extension(self):
        """Test extension property."""
        from coding_swarm.models import CodeFile

        code_file = CodeFile(path="src/main.py")
        assert code_file.extension == ".py"


class TestProjectStructure:
    """Tests for ProjectStructure model."""

    def test_project_structure_creation(self):
        """Test creating a ProjectStructure."""
        from coding_swarm.models import ProjectStructure

        project = ProjectStructure(
            name="test_project",
            description="A test project",
            dependencies=["pytest", "requests"],
        )
        assert project.name == "test_project"
        assert project.description == "A test project"
        assert "pytest" in project.dependencies

    def test_project_structure_defaults(self):
        """Test default values."""
        from coding_swarm.models import ProjectStructure

        project = ProjectStructure(name="test")
        assert project.files == []
        assert project.dependencies == []
        assert project.python_version == "3.11"


class TestCodingTask:
    """Tests for CodingTask model."""

    def test_task_creation(self):
        """Test creating a task."""
        from coding_swarm.models import CodingTask, TaskStatus

        task = CodingTask(
            id="task-1",
            description="Implement feature X",
        )
        assert task.id == "task-1"
        assert task.status == TaskStatus.PENDING
        assert task.retry_count == 0

    def test_create_task_factory(self):
        """Test create_task factory function."""
        from coding_swarm.models import create_task, TaskStatus

        task = create_task("task-2", "Build API", status=TaskStatus.IN_PROGRESS)
        assert task.id == "task-2"
        assert task.description == "Build API"
        assert task.status == TaskStatus.IN_PROGRESS


class TestSwarmSession:
    """Tests for SwarmSession model."""

    def test_session_creation(self):
        """Test creating a session."""
        from coding_swarm.models import SwarmSession

        session = SwarmSession(id="session-1")
        assert session.id == "session-1"
        assert session.tasks == []
        assert session.generated_files == []
        assert session.total_retries == 0

    def test_create_session_factory(self):
        """Test create_session factory function."""
        from coding_swarm.models import create_session

        session = create_session("session-2")
        assert session.id == "session-2"


class TestAgentModels:
    """Tests for agent-related models."""

    def test_architect_plan(self):
        """Test ArchitectPlan model."""
        from coding_swarm.models import ArchitectPlan

        plan = ArchitectPlan(
            project_name="my_project",
            description="A sample project",
            file_structure=["src/main.py", "tests/test_main.py"],
            modules=["Main module", "Tests"],
        )
        assert plan.project_name == "my_project"
        assert len(plan.file_structure) == 2

    def test_code_generation(self):
        """Test CodeGeneration model."""
        from coding_swarm.models import CodeGeneration

        gen = CodeGeneration(
            file_path="src/main.py",
            code="def main(): pass",
            explanation="Simple main function",
            imports=["typing"],
        )
        assert gen.file_path == "src/main.py"
        assert "def main" in gen.code

    def test_refactor_operation(self):
        """Test RefactorOperation model."""
        from coding_swarm.models import RefactorOperation

        op = RefactorOperation(
            file_path="src/main.py",
            operation_type="rename_function",
            target="old_name",
            new_value="new_name",
        )
        assert op.operation_type == "rename_function"

    def test_code_review(self):
        """Test CodeReview model."""
        from coding_swarm.models import CodeReview

        review = CodeReview(
            file_path="src/main.py",
            approved=True,
            issues=[],
            suggestions=["Add more tests"],
        )
        assert review.approved is True
        assert len(review.suggestions) == 1


class TestResultModels:
    """Tests for result models."""

    def test_test_result(self):
        """Test TestResult model."""
        from coding_swarm.models import TestResult

        result = TestResult(
            success=True,
            exit_code=0,
            stdout="5 passed",
            tests_run=5,
            tests_passed=5,
            tests_failed=0,
        )
        assert result.success is True
        assert result.tests_passed == 5

    def test_sandbox_result(self):
        """Test SandboxResult model."""
        from coding_swarm.models import SandboxResult

        result = SandboxResult(
            success=True,
            exit_code=0,
            stdout="Output",
            duration_seconds=1.5,
        )
        assert result.success is True
        assert result.duration_seconds == 1.5


class TestEnums:
    """Tests for enum types."""

    def test_agent_role_values(self):
        """Test AgentRole enum values."""
        from coding_swarm.models import AgentRole

        assert AgentRole.ARCHITECT.value == "architect"
        assert AgentRole.CODER.value == "coder"
        assert AgentRole.REFACTORER.value == "refactorer"

    def test_task_status_values(self):
        """Test TaskStatus enum values."""
        from coding_swarm.models import TaskStatus

        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"

    def test_file_operation_values(self):
        """Test FileOperation enum values."""
        from coding_swarm.models import FileOperation

        assert FileOperation.CREATE.value == "create"
        assert FileOperation.MODIFY.value == "modify"
        assert FileOperation.DELETE.value == "delete"
