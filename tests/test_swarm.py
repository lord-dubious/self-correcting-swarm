"""Tests for the CodingSwarm orchestrator."""

import pytest
from pathlib import Path
import tempfile


class TestCodingSwarm:
    """Tests for CodingSwarm class."""

    def test_create_swarm(self, mock_config):
        """Test creating a swarm."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        assert swarm is not None
        assert swarm.mock_mode is True

    def test_create_swarm_default(self):
        """Test creating swarm with defaults."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm()
        assert swarm is not None
        assert swarm.mock_mode is True

    def test_create_session(self, mock_config):
        """Test creating a session."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        session = swarm.create_session()

        assert session is not None
        assert session.id is not None
        assert swarm.current_session == session

    def test_generate_project_mock(self, mock_config):
        """Test generating a project in mock mode."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        session = swarm.generate_project(
            description="A simple calculator",
            requirements=["Support basic operations"],
        )

        assert session is not None
        assert session.project is not None
        assert len(session.generated_files) > 0
        assert session.completed_at is not None

    def test_generate_project_with_retries(self, mock_config):
        """Test project generation with retry limit."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        session = swarm.generate_project(
            description="A web scraper",
            max_retries=5,
        )

        assert session is not None
        assert session.total_retries == 0  # Mock mode succeeds first try

    def test_generate_file(self, mock_config):
        """Test generating a single file."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        code_file = swarm.generate_file(
            file_path="src/utils.py",
            description="Utility functions for string manipulation",
        )

        assert code_file is not None
        assert code_file.path == "src/utils.py"
        assert len(code_file.content) > 0

    def test_generate_file_with_context(self, mock_config):
        """Test generating file with context."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        context = "# main.py\nfrom utils import helper"
        code_file = swarm.generate_file(
            file_path="src/utils.py",
            description="Helper functions",
            context=context,
        )

        assert code_file is not None

    def test_refactor_code(self, mock_config, sample_code):
        """Test refactoring code."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        refactored = swarm.refactor_code(sample_code, "test.py")

        assert refactored is not None
        assert len(refactored) > 0

    def test_review_code(self, mock_config, sample_code):
        """Test reviewing code."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        review = swarm.review_code(sample_code, "test.py")

        assert review is not None
        assert "approved" in review
        assert "issues" in review
        assert "suggestions" in review

    def test_save_project(self, mock_config):
        """Test saving project to disk."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        session = swarm.generate_project("A calculator")

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = swarm.save_project(session, tmpdir)

            assert project_path.exists()
            # Check that at least one file was created
            assert list(project_path.rglob("*.py"))

    def test_cleanup(self, mock_config):
        """Test cleanup."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        swarm.cleanup()
        # Should not raise


class TestSwarmAgents:
    """Tests for swarm's internal agents."""

    def test_swarm_has_architect(self, mock_config):
        """Test swarm has architect agent."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        assert swarm.architect is not None

    def test_swarm_has_coder(self, mock_config):
        """Test swarm has coder agent."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        assert swarm.coder is not None

    def test_swarm_has_refactorer_agent(self, mock_config):
        """Test swarm has refactorer agent."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        assert swarm.refactorer_agent is not None

    def test_swarm_has_reviewer(self, mock_config):
        """Test swarm has reviewer agent."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        assert swarm.reviewer is not None

    def test_swarm_has_tester(self, mock_config):
        """Test swarm has tester agent."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        assert swarm.tester is not None


class TestSwarmTools:
    """Tests for swarm's internal tools."""

    def test_swarm_has_refactorer(self, mock_config):
        """Test swarm has LibCST refactorer."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        assert swarm.refactorer is not None

    def test_swarm_has_sandbox(self, mock_config):
        """Test swarm has Docker sandbox."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        assert swarm.sandbox is not None


class TestSwarmSession:
    """Tests for SwarmSession operations."""

    def test_session_tracks_files(self, mock_config):
        """Test that session tracks generated files."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        session = swarm.generate_project("A calculator")

        assert len(session.generated_files) > 0

    def test_session_tracks_test_results(self, mock_config):
        """Test that session tracks test results."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        session = swarm.generate_project("A calculator")

        assert len(session.test_results) > 0

    def test_session_has_project_structure(self, mock_config):
        """Test that session has project structure."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        session = swarm.generate_project("A calculator")

        assert session.project is not None
        assert session.project.name is not None


class TestBuildContext:
    """Tests for context building."""

    def test_build_context_empty(self, mock_config):
        """Test building context from empty files."""
        from coding_swarm.swarm import create_swarm

        swarm = create_swarm(mock_config)
        context = swarm._build_context({})

        assert context == ""

    def test_build_context_with_files(self, mock_config):
        """Test building context from files."""
        from coding_swarm.swarm import create_swarm
        from coding_swarm.models import CodeFile

        swarm = create_swarm(mock_config)
        files = {
            "main.py": CodeFile(path="main.py", content="# Main module"),
            "utils.py": CodeFile(path="utils.py", content="# Utils"),
        }
        context = swarm._build_context(files)

        assert "main.py" in context
        assert "utils.py" in context
        assert "# Main module" in context
