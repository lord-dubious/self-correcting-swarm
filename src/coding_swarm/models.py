"""Pydantic models for the self-correcting coding swarm."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentRole(str, Enum):
    """Roles for agents in the coding swarm."""

    ARCHITECT = "architect"
    CODER = "coder"
    REFACTORER = "refactorer"
    TESTER = "tester"
    REVIEWER = "reviewer"


class TaskStatus(str, Enum):
    """Status of a coding task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class FileOperation(str, Enum):
    """Types of file operations."""

    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"


class SwarmConfig(BaseSettings):
    """Configuration for the coding swarm."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    gemini_api_key: str = Field(default="", description="Gemini API key")
    gemini_model: str = Field(default="gemini-2.0-flash", description="Gemini model to use")
    docker_image: str = Field(default="python:3.11-slim", description="Docker image for sandbox")
    docker_timeout: int = Field(default=60, description="Docker execution timeout in seconds")
    docker_memory_limit: str = Field(default="512m", description="Docker memory limit")
    docker_cpu_limit: float = Field(default=1.0, description="Docker CPU limit")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    enable_mock_mode: bool = Field(default=False, description="Enable mock mode for testing")
    output_dir: str = Field(default="./output", description="Output directory for generated code")


class CodeFile(BaseModel):
    """Represents a code file."""

    path: str = Field(..., description="File path relative to project root")
    content: str = Field(default="", description="File content")
    language: str = Field(default="python", description="Programming language")
    operation: FileOperation = Field(default=FileOperation.CREATE, description="File operation")
    generation_source: str = Field(default="unknown", description="Source of generated content")
    is_degraded: bool = Field(
        default=False, description="Whether content came from a degraded path"
    )
    warnings: list[str] = Field(default_factory=list, description="Non-fatal generation warnings")
    error: str = Field(default="", description="Generation error context, if any")

    @property
    def filename(self) -> str:
        """Get the filename from path."""
        return Path(self.path).name

    @property
    def extension(self) -> str:
        """Get file extension."""
        return Path(self.path).suffix


class ProjectStructure(BaseModel):
    """Represents a project file structure."""

    name: str = Field(..., description="Project name")
    description: str = Field(default="", description="Project description")
    files: list[CodeFile] = Field(default_factory=list, description="Project files")
    dependencies: list[str] = Field(default_factory=list, description="Project dependencies")
    python_version: str = Field(default="3.11", description="Python version")


class CodeGeneration(BaseModel):
    """Represents generated code from the coder agent."""

    file_path: str = Field(..., description="Target file path")
    code: str = Field(..., description="Generated code")
    explanation: str = Field(default="", description="Explanation of the code")
    imports: list[str] = Field(default_factory=list, description="Required imports")
    generation_source: str = Field(default="unknown", description="mock, gemini, or fallback")
    is_degraded: bool = Field(default=False, description="Whether generation used a degraded path")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal generation warnings")
    error: str = Field(default="", description="Generation or parsing error context")


class RefactorOperation(BaseModel):
    """Represents a refactoring operation."""

    file_path: str = Field(..., description="File to refactor")
    operation_type: str = Field(..., description="Type of refactoring (add_import, rename, etc.)")
    target: str = Field(default="", description="Target element (function, class, etc.)")
    new_value: str = Field(default="", description="New value after refactoring")
    description: str = Field(default="", description="Description of the refactoring")


class TestResult(BaseModel):
    """Result of running tests in the sandbox."""

    success: bool = Field(..., description="Whether tests passed")
    exit_code: int = Field(default=0, description="Process exit code")
    stdout: str = Field(default="", description="Standard output")
    stderr: str = Field(default="", description="Standard error")
    duration_seconds: float = Field(default=0.0, description="Execution duration")
    tests_run: int = Field(default=0, description="Number of tests run")
    tests_passed: int = Field(default=0, description="Number of tests passed")
    tests_failed: int = Field(default=0, description="Number of tests failed")
    execution_source: str = Field(default="unknown", description="mock, docker, or fallback")
    is_degraded: bool = Field(default=False, description="Whether execution used a degraded path")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal execution warnings")
    error: str = Field(default="", description="Execution error context")


class SandboxResult(BaseModel):
    """Result of sandbox code execution."""

    success: bool = Field(..., description="Whether execution succeeded")
    exit_code: int = Field(default=0, description="Process exit code")
    stdout: str = Field(default="", description="Standard output")
    stderr: str = Field(default="", description="Standard error")
    duration_seconds: float = Field(default=0.0, description="Execution duration")
    container_id: str = Field(default="", description="Docker container ID")
    execution_source: str = Field(default="unknown", description="mock, docker, or fallback")
    is_degraded: bool = Field(default=False, description="Whether execution used a degraded path")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal execution warnings")
    error: str = Field(default="", description="Execution error context")


class CodingTask(BaseModel):
    """Represents a coding task for the swarm."""

    id: str = Field(..., description="Unique task ID")
    description: str = Field(..., description="Task description")
    requirements: list[str] = Field(default_factory=list, description="Task requirements")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    assigned_agent: AgentRole | None = Field(default=None, description="Assigned agent")
    retry_count: int = Field(default=0, description="Number of retries")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")
    error_message: str = Field(default="", description="Error message if failed")
    result: dict[str, Any] = Field(default_factory=dict, description="Task result")


class SwarmSession(BaseModel):
    """Represents a swarm coding session."""

    id: str = Field(..., description="Session ID")
    project: ProjectStructure | None = Field(default=None, description="Project being worked on")
    tasks: list[CodingTask] = Field(default_factory=list, description="Tasks in the session")
    generated_files: list[CodeFile] = Field(default_factory=list, description="Generated files")
    test_results: list[TestResult] = Field(default_factory=list, description="Test results")
    started_at: datetime = Field(default_factory=datetime.now, description="Session start time")
    completed_at: datetime | None = Field(default=None, description="Session completion time")
    total_retries: int = Field(default=0, description="Total retry count")


class AgentMessage(BaseModel):
    """Message passed between agents."""

    from_agent: AgentRole = Field(..., description="Sending agent")
    to_agent: AgentRole = Field(..., description="Receiving agent")
    message_type: str = Field(..., description="Message type")
    content: dict[str, Any] = Field(default_factory=dict, description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")


class ArchitectPlan(BaseModel):
    """Plan generated by the architect agent."""

    project_name: str = Field(..., description="Project name")
    description: str = Field(..., description="Project description")
    file_structure: list[str] = Field(default_factory=list, description="Planned file structure")
    modules: list[str] = Field(default_factory=list, description="Module descriptions")
    dependencies: list[str] = Field(default_factory=list, description="Required dependencies")
    implementation_order: list[str] = Field(
        default_factory=list, description="Order of implementation"
    )


class CodeReview(BaseModel):
    """Code review from the reviewer agent."""

    file_path: str = Field(..., description="Reviewed file path")
    approved: bool = Field(default=False, description="Whether code is approved")
    issues: list[str] = Field(default_factory=list, description="Issues found")
    suggestions: list[str] = Field(default_factory=list, description="Improvement suggestions")
    severity: str = Field(default="info", description="Review severity (info, warning, error)")
    generation_source: str = Field(default="unknown", description="mock, gemini, or fallback")
    is_degraded: bool = Field(default=False, description="Whether review used a degraded path")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal review warnings")
    error: str = Field(default="", description="Review generation or parsing error context")


def create_config(**kwargs) -> SwarmConfig:
    """Create a SwarmConfig with optional overrides."""
    return SwarmConfig(**kwargs)


def create_task(task_id: str, description: str, **kwargs) -> CodingTask:
    """Create a new coding task."""
    return CodingTask(id=task_id, description=description, **kwargs)


def create_session(session_id: str, **kwargs) -> SwarmSession:
    """Create a new swarm session."""
    return SwarmSession(id=session_id, **kwargs)
