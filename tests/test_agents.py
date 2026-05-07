"""Tests for coding agents."""


class TestBaseAgent:
    """Tests for BaseAgent class."""

    def test_base_agent_init(self, mock_config):
        """Test base agent initialization."""
        from coding_swarm.agents import BaseAgent

        agent = BaseAgent(mock_config)
        assert agent.config == mock_config
        assert agent.mock_mode is True

    def test_base_agent_mock_response(self, mock_config):
        """Test mock response generation."""
        from coding_swarm.agents import BaseAgent

        agent = BaseAgent(mock_config)
        response = agent._mock_response("test prompt")
        assert response == "Mock response"


class TestArchitectAgent:
    """Tests for ArchitectAgent class."""

    def test_create_architect(self, mock_config):
        """Test creating an architect agent."""
        from coding_swarm.agents import AgentRole, create_architect

        agent = create_architect(mock_config)
        assert agent is not None
        assert agent.role == AgentRole.ARCHITECT

    def test_plan_project_mock(self, mock_config):
        """Test planning a project in mock mode."""
        from coding_swarm.agents import create_architect

        agent = create_architect(mock_config)
        plan = agent.plan_project("A calculator app")

        assert plan.project_name == "mock_project"
        assert len(plan.file_structure) > 0
        assert len(plan.implementation_order) > 0

    def test_plan_project_with_requirements(self, mock_config):
        """Test planning with requirements."""
        from coding_swarm.agents import create_architect

        agent = create_architect(mock_config)
        plan = agent.plan_project(
            "A web API",
            requirements=["Use FastAPI", "Include authentication"],
        )

        assert plan is not None
        assert plan.project_name is not None


class TestCoderAgent:
    """Tests for CoderAgent class."""

    def test_create_coder(self, mock_config):
        """Test creating a coder agent."""
        from coding_swarm.agents import AgentRole, create_coder

        agent = create_coder(mock_config)
        assert agent is not None
        assert agent.role == AgentRole.CODER

    def test_generate_code_mock(self, mock_config):
        """Test generating code in mock mode."""
        from coding_swarm.agents import create_coder

        agent = create_coder(mock_config)
        result = agent.generate_code(
            file_path="src/main.py",
            description="A hello world program",
        )

        assert result.file_path == "src/main.py"
        assert result.code is not None
        assert len(result.code) > 0
        assert result.generation_source == "mock"
        assert result.is_degraded is True
        assert result.warnings

    def test_generate_code_parse_fallback_has_error_context(self, monkeypatch):
        """Test raw Gemini fallback preserves parsing error context."""
        from coding_swarm.agents import create_coder
        from coding_swarm.models import SwarmConfig

        agent = create_coder(SwarmConfig(enable_mock_mode=False, gemini_api_key="test"))
        monkeypatch.setattr(agent, "_generate", lambda _prompt: "def main():\n    pass\n")

        result = agent.generate_code("src/main.py", "Create a main module")

        assert result.generation_source == "fallback"
        assert result.is_degraded is True
        assert "No valid JSON" in result.error
        assert "Gemini response" in result.warnings[0]

    def test_generate_code_with_context(self, mock_config):
        """Test generating code with context."""
        from coding_swarm.agents import create_coder

        agent = create_coder(mock_config)
        result = agent.generate_code(
            file_path="src/utils.py",
            description="Utility functions",
            context="# main.py\nfrom utils import helper",
        )

        assert result.file_path == "src/utils.py"

    def test_fix_code_mock(self, mock_config):
        """Test fixing code in mock mode."""
        from coding_swarm.agents import create_coder

        agent = create_coder(mock_config)
        broken_code = "def foo(\n  return 1"
        result = agent.fix_code(broken_code, "SyntaxError", "test.py")

        assert result.code == broken_code  # Mock returns same code
        assert result.explanation == "Mock fixed code"
        assert result.generation_source == "mock"


class TestRefactorerAgent:
    """Tests for RefactorerAgent class."""

    def test_create_refactorer_agent(self, mock_config):
        """Test creating a refactorer agent."""
        from coding_swarm.agents import AgentRole, create_refactorer_agent

        agent = create_refactorer_agent(mock_config)
        assert agent is not None
        assert agent.role == AgentRole.REFACTORER

    def test_suggest_refactoring_mock(self, mock_config, sample_code):
        """Test suggesting refactoring in mock mode."""
        from coding_swarm.agents import create_refactorer_agent

        agent = create_refactorer_agent(mock_config)
        suggestions = agent.suggest_refactoring(sample_code, "test.py")

        assert len(suggestions) > 0
        assert suggestions[0].operation_type == "add_import"


class TestReviewerAgent:
    """Tests for ReviewerAgent class."""

    def test_create_reviewer(self, mock_config):
        """Test creating a reviewer agent."""
        from coding_swarm.agents import AgentRole, create_reviewer

        agent = create_reviewer(mock_config)
        assert agent is not None
        assert agent.role == AgentRole.REVIEWER

    def test_review_code_mock(self, mock_config, sample_code):
        """Test reviewing code in mock mode."""
        from coding_swarm.agents import create_reviewer

        agent = create_reviewer(mock_config)
        review = agent.review_code(sample_code, "test.py")

        assert review.file_path == "test.py"
        assert review.approved is True
        assert review.severity == "info"
        assert review.generation_source == "mock"
        assert review.is_degraded is True

    def test_review_code_parse_fallback_is_not_silent_approval(self, monkeypatch, sample_code):
        """Test review parse failures return a conservative degraded review."""
        from coding_swarm.agents import create_reviewer
        from coding_swarm.models import SwarmConfig

        agent = create_reviewer(SwarmConfig(enable_mock_mode=False, gemini_api_key="test"))
        monkeypatch.setattr(agent, "_generate", lambda _prompt: "not json")

        review = agent.review_code(sample_code, "test.py")

        assert review.approved is False
        assert review.generation_source == "fallback"
        assert review.is_degraded is True
        assert review.error


class TestTesterAgent:
    """Tests for TesterAgent class."""

    def test_create_tester(self, mock_config):
        """Test creating a tester agent."""
        from coding_swarm.agents import AgentRole, create_tester

        agent = create_tester(mock_config)
        assert agent is not None
        assert agent.role == AgentRole.TESTER

    def test_generate_tests_mock(self, mock_config, sample_code):
        """Test generating tests in mock mode."""
        from coding_swarm.agents import create_tester

        agent = create_tester(mock_config)
        result = agent.generate_tests(sample_code, "src/main.py")

        assert result.file_path == "tests/test_main.py"
        assert "pytest" in result.imports
        assert "def test_" in result.code
        assert result.generation_source == "mock"
        assert result.is_degraded is True

    def test_generate_tests_custom_path(self, mock_config, sample_code):
        """Test generating tests with custom path."""
        from coding_swarm.agents import create_tester

        agent = create_tester(mock_config)
        result = agent.generate_tests(sample_code, "src/main.py", test_path="custom/tests.py")

        assert result.file_path == "custom/tests.py"


class TestAgentFactories:
    """Tests for agent factory functions."""

    def test_create_architect_default(self):
        """Test create_architect with defaults."""
        from coding_swarm.agents import create_architect

        agent = create_architect()
        assert agent is not None
        assert agent.mock_mode is True

    def test_create_coder_default(self):
        """Test create_coder with defaults."""
        from coding_swarm.agents import create_coder

        agent = create_coder()
        assert agent is not None
        assert agent.mock_mode is True

    def test_create_refactorer_agent_default(self):
        """Test create_refactorer_agent with defaults."""
        from coding_swarm.agents import create_refactorer_agent

        agent = create_refactorer_agent()
        assert agent is not None
        assert agent.mock_mode is True

    def test_create_reviewer_default(self):
        """Test create_reviewer with defaults."""
        from coding_swarm.agents import create_reviewer

        agent = create_reviewer()
        assert agent is not None
        assert agent.mock_mode is True

    def test_create_tester_default(self):
        """Test create_tester with defaults."""
        from coding_swarm.agents import create_tester

        agent = create_tester()
        assert agent is not None
        assert agent.mock_mode is True
