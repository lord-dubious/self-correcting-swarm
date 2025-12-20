"""Gemini-powered code generation agents."""

from __future__ import annotations

import json
from typing import Any

from coding_swarm.models import (
    AgentRole,
    ArchitectPlan,
    CodeGeneration,
    CodeReview,
    ProjectStructure,
    RefactorOperation,
    SwarmConfig,
)


class BaseAgent:
    """Base class for coding agents."""

    role: AgentRole = AgentRole.CODER

    def __init__(self, config: SwarmConfig) -> None:
        """Initialize the agent.

        Args:
            config: Swarm configuration
        """
        self.config = config
        self.mock_mode = config.enable_mock_mode
        self._model = None

    @property
    def model(self):
        """Get or create the Gemini model."""
        if self._model is None and not self.mock_mode:
            import google.generativeai as genai

            genai.configure(api_key=self.config.gemini_api_key)
            self._model = genai.GenerativeModel(self.config.gemini_model)
        return self._model

    def _generate(self, prompt: str) -> str:
        """Generate text using Gemini.

        Args:
            prompt: Input prompt

        Returns:
            Generated text
        """
        if self.mock_mode:
            return self._mock_response(prompt)

        response = self.model.generate_content(prompt)
        return response.text

    def _mock_response(self, prompt: str) -> str:
        """Generate mock response for testing.

        Args:
            prompt: Input prompt

        Returns:
            Mock response
        """
        return "Mock response"


class ArchitectAgent(BaseAgent):
    """Agent responsible for planning project structure."""

    role = AgentRole.ARCHITECT

    def plan_project(
        self, description: str, requirements: list[str] | None = None
    ) -> ArchitectPlan:
        """Plan a project structure.

        Args:
            description: Project description
            requirements: Optional list of requirements

        Returns:
            ArchitectPlan with project structure
        """
        if self.mock_mode:
            return ArchitectPlan(
                project_name="mock_project",
                description=description,
                file_structure=["src/main.py", "src/utils.py", "tests/test_main.py"],
                modules=["Main module", "Utility functions", "Tests"],
                dependencies=["pytest"],
                implementation_order=["utils.py", "main.py", "test_main.py"],
            )

        requirements_text = "\n".join(requirements) if requirements else "No specific requirements"

        prompt = f"""You are a software architect. Plan a Python project structure.

Project Description: {description}

Requirements:
{requirements_text}

Respond with a JSON object containing:
- project_name: A suitable project name (snake_case)
- description: Brief description
- file_structure: List of file paths to create
- modules: Description of each module
- dependencies: List of pip dependencies needed
- implementation_order: Order in which files should be implemented

Return ONLY valid JSON, no markdown."""

        response = self._generate(prompt)

        try:
            # Try to parse JSON from response
            data = self._extract_json(response)
            return ArchitectPlan(**data)
        except Exception:
            # Fallback
            return ArchitectPlan(
                project_name="project",
                description=description,
                file_structure=["src/main.py"],
                modules=["Main module"],
                dependencies=[],
                implementation_order=["main.py"],
            )

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from text response."""
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON block
        import re

        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            return json.loads(json_match.group())

        raise ValueError("No valid JSON found in response")


class CoderAgent(BaseAgent):
    """Agent responsible for generating code."""

    role = AgentRole.CODER

    def generate_code(
        self,
        file_path: str,
        description: str,
        context: str | None = None,
        existing_code: str | None = None,
    ) -> CodeGeneration:
        """Generate code for a file.

        Args:
            file_path: Target file path
            description: What the code should do
            context: Optional context from other files
            existing_code: Optional existing code to modify

        Returns:
            CodeGeneration with the generated code
        """
        if self.mock_mode:
            mock_code = '''"""Mock generated module."""


def main():
    """Main function."""
    print("Hello, World!")


if __name__ == "__main__":
    main()
'''
            return CodeGeneration(
                file_path=file_path,
                code=mock_code,
                explanation="Mock generated code",
                imports=["typing"],
            )

        context_text = f"\nContext from other files:\n{context}" if context else ""
        existing_text = f"\nExisting code to modify:\n{existing_code}" if existing_code else ""

        prompt = f"""You are an expert Python developer. Generate production-quality code.

File: {file_path}
Task: {description}
{context_text}
{existing_text}

Requirements:
1. Use type hints
2. Include docstrings
3. Follow PEP 8
4. Handle errors appropriately
5. Make the code testable

Respond with a JSON object containing:
- code: The complete Python code
- explanation: Brief explanation of the implementation
- imports: List of required imports (just module names)

Return ONLY valid JSON, no markdown code blocks."""

        response = self._generate(prompt)

        try:
            data = self._extract_json(response)
            return CodeGeneration(
                file_path=file_path,
                code=data.get("code", ""),
                explanation=data.get("explanation", ""),
                imports=data.get("imports", []),
            )
        except Exception:
            # Try to extract code directly
            return CodeGeneration(
                file_path=file_path,
                code=response,
                explanation="Generated code",
                imports=[],
            )

    def fix_code(self, code: str, error: str, file_path: str = "") -> CodeGeneration:
        """Fix code based on an error message.

        Args:
            code: Broken code
            error: Error message
            file_path: Optional file path for context

        Returns:
            CodeGeneration with fixed code
        """
        if self.mock_mode:
            return CodeGeneration(
                file_path=file_path,
                code=code,
                explanation="Mock fixed code",
                imports=[],
            )

        prompt = f"""You are an expert Python developer. Fix this broken code.

File: {file_path}

Code:
```python
{code}
```

Error:
{error}

Provide the complete fixed code. Respond with a JSON object containing:
- code: The complete fixed Python code
- explanation: What was wrong and how you fixed it
- imports: List of required imports

Return ONLY valid JSON, no markdown."""

        response = self._generate(prompt)

        try:
            data = self._extract_json(response)
            return CodeGeneration(
                file_path=file_path,
                code=data.get("code", code),
                explanation=data.get("explanation", ""),
                imports=data.get("imports", []),
            )
        except Exception:
            return CodeGeneration(
                file_path=file_path,
                code=response,
                explanation="Attempted fix",
                imports=[],
            )

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from text response."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        import re

        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            return json.loads(json_match.group())

        raise ValueError("No valid JSON found")


class RefactorerAgent(BaseAgent):
    """Agent responsible for refactoring code using LibCST."""

    role = AgentRole.REFACTORER

    def suggest_refactoring(self, code: str, file_path: str = "") -> list[RefactorOperation]:
        """Suggest refactoring operations for code.

        Args:
            code: Source code to analyze
            file_path: Optional file path

        Returns:
            List of suggested refactoring operations
        """
        if self.mock_mode:
            return [
                RefactorOperation(
                    file_path=file_path,
                    operation_type="add_import",
                    target="typing",
                    new_value="from typing import Optional",
                    description="Add typing imports",
                )
            ]

        prompt = f"""You are a code refactoring expert. Analyze this code and suggest improvements.

File: {file_path}

Code:
```python
{code}
```

Suggest refactoring operations. For each, provide:
- operation_type: One of (add_import, rename_function, rename_class, add_docstring, add_type_hints)
- target: The element to modify
- new_value: The new value
- description: Why this improves the code

Respond with a JSON array of operations. Return ONLY valid JSON."""

        response = self._generate(prompt)

        try:
            data = self._extract_json_array(response)
            return [RefactorOperation(file_path=file_path, **op) for op in data]
        except Exception:
            return []

    def _extract_json_array(self, text: str) -> list[dict[str, Any]]:
        """Extract JSON array from text."""
        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result
            return []
        except json.JSONDecodeError:
            pass

        import re

        json_match = re.search(r"\[[\s\S]*\]", text)
        if json_match:
            return json.loads(json_match.group())

        return []


class ReviewerAgent(BaseAgent):
    """Agent responsible for reviewing code."""

    role = AgentRole.REVIEWER

    def review_code(self, code: str, file_path: str = "") -> CodeReview:
        """Review code for issues and improvements.

        Args:
            code: Source code to review
            file_path: Optional file path

        Returns:
            CodeReview with findings
        """
        if self.mock_mode:
            return CodeReview(
                file_path=file_path,
                approved=True,
                issues=[],
                suggestions=["Consider adding more tests"],
                severity="info",
            )

        prompt = f"""You are a senior code reviewer. Review this code thoroughly.

File: {file_path}

Code:
```python
{code}
```

Check for:
1. Bugs and logic errors
2. Security issues
3. Performance problems
4. Code style issues
5. Missing error handling
6. Missing tests

Respond with a JSON object containing:
- approved: boolean, whether the code is acceptable
- issues: List of issues found (strings)
- suggestions: List of improvement suggestions
- severity: "info", "warning", or "error"

Return ONLY valid JSON."""

        response = self._generate(prompt)

        try:
            data = self._extract_json(response)
            return CodeReview(
                file_path=file_path,
                approved=data.get("approved", True),
                issues=data.get("issues", []),
                suggestions=data.get("suggestions", []),
                severity=data.get("severity", "info"),
            )
        except Exception:
            return CodeReview(
                file_path=file_path,
                approved=True,
                issues=[],
                suggestions=[],
                severity="info",
            )

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from text."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        import re

        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            return json.loads(json_match.group())

        raise ValueError("No valid JSON found")


class TesterAgent(BaseAgent):
    """Agent responsible for generating tests."""

    role = AgentRole.TESTER

    def generate_tests(
        self, code: str, file_path: str, test_path: str | None = None
    ) -> CodeGeneration:
        """Generate tests for code.

        Args:
            code: Source code to test
            file_path: Path of the source file
            test_path: Optional custom test file path

        Returns:
            CodeGeneration with test code
        """
        if test_path is None:
            # Convert src/module.py to tests/test_module.py
            import re

            test_path = re.sub(r"^src/", "tests/test_", file_path)
            if not test_path.startswith("tests/test_"):
                test_path = f"tests/test_{file_path}"

        if self.mock_mode:
            mock_tests = '''"""Tests for the module."""

import pytest


def test_placeholder():
    """Placeholder test."""
    assert True


def test_main():
    """Test main function."""
    # TODO: Implement actual test
    pass
'''
            return CodeGeneration(
                file_path=test_path,
                code=mock_tests,
                explanation="Mock generated tests",
                imports=["pytest"],
            )

        prompt = f"""You are a test engineer. Generate comprehensive pytest tests.

Source file: {file_path}

Code to test:
```python
{code}
```

Requirements:
1. Use pytest
2. Test all public functions and classes
3. Include edge cases
4. Use fixtures where appropriate
5. Add docstrings to tests

Respond with a JSON object containing:
- code: Complete test file content
- explanation: Testing strategy explanation
- imports: Required imports

Return ONLY valid JSON."""

        response = self._generate(prompt)

        try:
            data = self._extract_json(response)
            return CodeGeneration(
                file_path=test_path,
                code=data.get("code", ""),
                explanation=data.get("explanation", ""),
                imports=data.get("imports", ["pytest"]),
            )
        except Exception:
            return CodeGeneration(
                file_path=test_path,
                code=response,
                explanation="Generated tests",
                imports=["pytest"],
            )

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from text."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        import re

        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            return json.loads(json_match.group())

        raise ValueError("No valid JSON found")


def create_architect(config: SwarmConfig | None = None) -> ArchitectAgent:
    """Create an ArchitectAgent."""
    if config is None:
        config = SwarmConfig(enable_mock_mode=True)
    return ArchitectAgent(config)


def create_coder(config: SwarmConfig | None = None) -> CoderAgent:
    """Create a CoderAgent."""
    if config is None:
        config = SwarmConfig(enable_mock_mode=True)
    return CoderAgent(config)


def create_refactorer_agent(config: SwarmConfig | None = None) -> RefactorerAgent:
    """Create a RefactorerAgent."""
    if config is None:
        config = SwarmConfig(enable_mock_mode=True)
    return RefactorerAgent(config)


def create_reviewer(config: SwarmConfig | None = None) -> ReviewerAgent:
    """Create a ReviewerAgent."""
    if config is None:
        config = SwarmConfig(enable_mock_mode=True)
    return ReviewerAgent(config)


def create_tester(config: SwarmConfig | None = None) -> TesterAgent:
    """Create a TesterAgent."""
    if config is None:
        config = SwarmConfig(enable_mock_mode=True)
    return TesterAgent(config)
