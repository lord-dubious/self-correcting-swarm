"""Main swarm orchestrator for self-correcting code generation."""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from coding_swarm.agents import (
    ArchitectAgent,
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
    CodeFile,
    FileOperation,
    ProjectStructure,
    SwarmConfig,
    SwarmSession,
    TestResult,
)
from coding_swarm.refactorer import CodeRefactorer, create_refactorer
from coding_swarm.sandbox import DockerSandbox, create_sandbox


class CodingSwarm:
    """Orchestrates multiple coding agents to generate and refine code."""

    def __init__(self, config: SwarmConfig | None = None) -> None:
        """Initialize the coding swarm.

        Args:
            config: Swarm configuration
        """
        self.config = config or SwarmConfig(enable_mock_mode=True)
        self.mock_mode = self.config.enable_mock_mode

        # Initialize agents
        self.architect: ArchitectAgent = create_architect(self.config)
        self.coder: CoderAgent = create_coder(self.config)
        self.refactorer_agent: RefactorerAgent = create_refactorer_agent(self.config)
        self.reviewer: ReviewerAgent = create_reviewer(self.config)
        self.tester: TesterAgent = create_tester(self.config)

        # Initialize tools
        self.refactorer: CodeRefactorer = create_refactorer(self.config.enable_mock_mode)
        self.sandbox: DockerSandbox = create_sandbox(self.config)

        # Session tracking
        self.current_session: SwarmSession | None = None

    def create_session(self) -> SwarmSession:
        """Create a new coding session.

        Returns:
            New SwarmSession
        """
        session = SwarmSession(id=str(uuid.uuid4()))
        self.current_session = session
        return session

    def generate_project(
        self,
        description: str,
        requirements: list[str] | None = None,
        max_retries: int | None = None,
    ) -> SwarmSession:
        """Generate a complete project from a description.

        Args:
            description: Project description
            requirements: Optional specific requirements
            max_retries: Maximum retry attempts for failed tests

        Returns:
            SwarmSession with generated project
        """
        session = self.create_session()
        max_retries = max_retries or self.config.max_retries

        # Phase 1: Architecture planning
        plan = self.architect.plan_project(description, requirements)

        project = ProjectStructure(
            name=plan.project_name,
            description=plan.description,
            files=[],
            dependencies=plan.dependencies,
        )
        session.project = project

        # Phase 2: Code generation
        generated_files: dict[str, CodeFile] = {}

        for file_path in plan.implementation_order:
            # Get context from already generated files
            context = self._build_context(generated_files)

            # Generate code
            generation = self.coder.generate_code(
                file_path=file_path,
                description=f"Implement {file_path} for {description}",
                context=context,
            )

            # Validate syntax
            is_valid, error = self.refactorer.validate_syntax(generation.code)

            if not is_valid:
                # Try to fix
                fixed = self.coder.fix_code(generation.code, error, file_path)
                generation = fixed

            code_file = CodeFile(
                path=file_path,
                content=generation.code,
                language="python",
                operation=FileOperation.CREATE,
                generation_source=generation.generation_source,
                is_degraded=generation.is_degraded,
                warnings=generation.warnings,
                error=generation.error,
            )
            generated_files[file_path] = code_file
            project.files.append(code_file)

        # Phase 3: Generate tests
        test_files_to_add: dict[str, CodeFile] = {}
        for file_path, code_file in list(generated_files.items()):
            if file_path.startswith("tests/"):
                continue

            test_gen = self.tester.generate_tests(
                code=code_file.content,
                file_path=file_path,
            )

            test_file = CodeFile(
                path=test_gen.file_path,
                content=test_gen.code,
                language="python",
                operation=FileOperation.CREATE,
                generation_source=test_gen.generation_source,
                is_degraded=test_gen.is_degraded,
                warnings=test_gen.warnings,
                error=test_gen.error,
            )
            project.files.append(test_file)
            test_files_to_add[test_gen.file_path] = test_file

        # Add test files after iteration
        generated_files.update(test_files_to_add)

        # Phase 4: Review and refactor
        for file_path, code_file in list(generated_files.items()):
            if file_path.startswith("tests/"):
                continue

            review = self.reviewer.review_code(code_file.content, file_path)

            if not review.approved and review.issues:
                # Get refactoring suggestions
                suggestions = self.refactorer_agent.suggest_refactoring(
                    code_file.content, file_path
                )

                # Apply refactoring
                refactored_code = code_file.content
                for suggestion in suggestions:
                    refactored_code = self._apply_refactoring(refactored_code, suggestion)

                code_file.content = refactored_code

        # Phase 5: Test in sandbox with retry loop
        retry_count = 0
        test_result = self._run_tests(generated_files)

        while not test_result.success and retry_count < max_retries:
            retry_count += 1
            session.total_retries += 1

            # Find failing tests and fix code
            fixed_files = self._fix_failures(generated_files, test_result)
            generated_files.update(fixed_files)

            # Update project files
            for path, code_file in fixed_files.items():
                for pf in project.files:
                    if pf.path == path:
                        pf.content = code_file.content
                        break

            # Rerun tests
            test_result = self._run_tests(generated_files)

        session.test_results.append(test_result)
        session.generated_files = list(generated_files.values())
        session.completed_at = datetime.now()

        return session

    def generate_file(
        self,
        file_path: str,
        description: str,
        context: str | None = None,
    ) -> CodeFile:
        """Generate a single file.

        Args:
            file_path: Target file path
            description: What the code should do
            context: Optional context

        Returns:
            Generated CodeFile
        """
        generation = self.coder.generate_code(
            file_path=file_path,
            description=description,
            context=context,
        )

        # Validate and potentially fix
        is_valid, error = self.refactorer.validate_syntax(generation.code)

        if not is_valid:
            fixed = self.coder.fix_code(generation.code, error, file_path)
            generation = fixed

        return CodeFile(
            path=file_path,
            content=generation.code,
            language="python",
            operation=FileOperation.CREATE,
            generation_source=generation.generation_source,
            is_degraded=generation.is_degraded,
            warnings=generation.warnings,
            error=generation.error,
        )

    def refactor_code(self, code: str, file_path: str = "") -> str:
        """Refactor code using LibCST.

        Args:
            code: Source code
            file_path: Optional file path

        Returns:
            Refactored code
        """
        suggestions = self.refactorer_agent.suggest_refactoring(code, file_path)

        refactored = code
        for suggestion in suggestions:
            refactored = self._apply_refactoring(refactored, suggestion)

        return refactored

    def review_code(self, code: str, file_path: str = "") -> dict[str, Any]:
        """Review code and return findings.

        Args:
            code: Source code
            file_path: Optional file path

        Returns:
            Review results as dict
        """
        review = self.reviewer.review_code(code, file_path)
        return review.model_dump()

    def save_project(self, session: SwarmSession, output_dir: str | None = None) -> Path:
        """Save generated project to disk.

        Args:
            session: Session with generated files
            output_dir: Output directory

        Returns:
            Path to the saved project
        """
        output_dir = output_dir or self.config.output_dir
        project_path = Path(output_dir)

        if session.project:
            project_path = project_path / session.project.name

        project_path.mkdir(parents=True, exist_ok=True)

        for code_file in session.generated_files:
            file_path = project_path / code_file.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(code_file.content)

        # Write requirements.txt if we have dependencies
        if session.project and session.project.dependencies:
            req_path = project_path / "requirements.txt"
            req_path.write_text("\n".join(session.project.dependencies))

        return project_path

    def _build_context(self, files: dict[str, CodeFile]) -> str:
        """Build context string from generated files."""
        if not files:
            return ""

        context_parts = []
        for path, code_file in files.items():
            context_parts.append(f"# {path}\n{code_file.content}")

        return "\n\n".join(context_parts)

    def _apply_refactoring(self, code: str, suggestion: Any) -> str:
        """Apply a refactoring suggestion using LibCST."""
        try:
            if suggestion.operation_type == "add_import":
                return self.refactorer.add_imports(code, [suggestion.new_value])
            if suggestion.operation_type == "rename_function":
                return self.refactorer.rename_function(
                    code, suggestion.target, suggestion.new_value
                )
            if suggestion.operation_type == "rename_class":
                return self.refactorer.rename_class(code, suggestion.target, suggestion.new_value)
            if suggestion.operation_type == "add_docstring":
                return self.refactorer.add_docstring(code, suggestion.target, suggestion.new_value)
        except Exception:
            return code

        return code

    def _run_tests(self, files: dict[str, CodeFile]) -> TestResult:
        """Run tests in sandbox."""
        project_files = {path: cf.content for path, cf in files.items()}
        return self.sandbox.run_tests(project_files)

    def _fix_failures(
        self, files: dict[str, CodeFile], test_result: TestResult
    ) -> dict[str, CodeFile]:
        """Attempt to fix code based on test failures."""
        fixed = {}

        # Parse error from test output
        error = test_result.stderr or test_result.stdout

        # Try to identify which file failed
        for path, code_file in files.items():
            if path.startswith("tests/"):
                continue

            # Ask coder to fix based on error
            fixed_gen = self.coder.fix_code(
                code=code_file.content,
                error=error,
                file_path=path,
            )

            fixed[path] = CodeFile(
                path=path,
                content=fixed_gen.code,
                language="python",
                operation=FileOperation.MODIFY,
                generation_source=fixed_gen.generation_source,
                is_degraded=fixed_gen.is_degraded,
                warnings=fixed_gen.warnings,
                error=fixed_gen.error,
            )

        return fixed

    def cleanup(self) -> None:
        """Clean up resources."""
        self.sandbox.cleanup()


def create_swarm(config: SwarmConfig | None = None) -> CodingSwarm:
    """Create a CodingSwarm instance.

    Args:
        config: Optional swarm configuration

    Returns:
        CodingSwarm instance
    """
    return CodingSwarm(config)
