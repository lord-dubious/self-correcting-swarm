"""Experimental coding-swarm helpers with explicit mock and sandbox boundaries."""

from coding_swarm.agents import (
    ArchitectAgent,
    BaseAgent,
    CoderAgent,
    RefactorerAgent,
    ReviewerAgent,
    TesterAgent,
    create_architect,
    create_coder,
    create_refactorer_agent,
    create_reviewer,
    create_tester,
)
from coding_swarm.models import (
    AgentRole,
    ArchitectPlan,
    CodeFile,
    CodeGeneration,
    CodeReview,
    CodingTask,
    FileOperation,
    ProjectStructure,
    RefactorOperation,
    SandboxResult,
    SwarmConfig,
    SwarmSession,
    TaskStatus,
    TestResult,
    create_config,
    create_session,
    create_task,
)
from coding_swarm.refactorer import (
    ClassRenamer,
    CodeRefactorer,
    DocstringAdder,
    FunctionRenamer,
    ImportAdder,
    TypeHintAdder,
    create_refactorer,
)
from coding_swarm.sandbox import (
    DockerSandbox,
    create_sandbox,
)
from coding_swarm.swarm import (
    CodingSwarm,
    create_swarm,
)

__version__ = "0.1.0"

__all__ = [
    # Models
    "AgentRole",
    "ArchitectPlan",
    "CodeFile",
    "CodeGeneration",
    "CodeReview",
    "CodingTask",
    "FileOperation",
    "ProjectStructure",
    "RefactorOperation",
    "SandboxResult",
    "SwarmConfig",
    "SwarmSession",
    "TaskStatus",
    "TestResult",
    "create_config",
    "create_session",
    "create_task",
    # Agents
    "ArchitectAgent",
    "BaseAgent",
    "CoderAgent",
    "RefactorerAgent",
    "ReviewerAgent",
    "TesterAgent",
    "create_architect",
    "create_coder",
    "create_refactorer_agent",
    "create_reviewer",
    "create_tester",
    # Refactorer
    "CodeRefactorer",
    "ClassRenamer",
    "DocstringAdder",
    "FunctionRenamer",
    "ImportAdder",
    "TypeHintAdder",
    "create_refactorer",
    # Sandbox
    "DockerSandbox",
    "create_sandbox",
    # Swarm
    "CodingSwarm",
    "create_swarm",
]
