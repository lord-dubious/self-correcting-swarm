"""Tests for LibCST refactoring utilities."""

import pytest


class TestCodeRefactorer:
    """Tests for CodeRefactorer class."""

    def test_create_refactorer(self):
        """Test creating a refactorer."""
        from coding_swarm.refactorer import create_refactorer

        refactorer = create_refactorer()
        assert refactorer is not None
        assert refactorer.mock_mode is False

    def test_create_refactorer_mock_mode(self):
        """Test creating a refactorer in mock mode."""
        from coding_swarm.refactorer import create_refactorer

        refactorer = create_refactorer(mock_mode=True)
        assert refactorer.mock_mode is True

    def test_parse_valid_code(self, sample_code):
        """Test parsing valid Python code."""
        from coding_swarm.refactorer import create_refactorer

        refactorer = create_refactorer()
        tree = refactorer.parse(sample_code)
        assert tree is not None

    def test_validate_syntax_valid(self, sample_code):
        """Test validating valid syntax."""
        from coding_swarm.refactorer import create_refactorer

        refactorer = create_refactorer()
        is_valid, error = refactorer.validate_syntax(sample_code)
        assert is_valid is True
        assert error == ""

    def test_validate_syntax_invalid(self, sample_code_with_syntax_error):
        """Test validating invalid syntax."""
        from coding_swarm.refactorer import create_refactorer

        refactorer = create_refactorer()
        is_valid, error = refactorer.validate_syntax(sample_code_with_syntax_error)
        assert is_valid is False
        assert error != ""

    def test_add_imports(self, sample_code):
        """Test adding imports to code."""
        from coding_swarm.refactorer import create_refactorer

        refactorer = create_refactorer()
        imports = ["import os", "from typing import List"]
        result = refactorer.add_imports(sample_code, imports)

        assert "import os" in result
        assert "from typing import List" in result

    def test_add_imports_mock_mode(self, sample_code):
        """Test adding imports in mock mode."""
        from coding_swarm.refactorer import create_refactorer

        refactorer = create_refactorer(mock_mode=True)
        imports = ["import os"]
        result = refactorer.add_imports(sample_code, imports)

        assert "import os" in result

    def test_rename_function(self, sample_code):
        """Test renaming a function."""
        from coding_swarm.refactorer import create_refactorer

        refactorer = create_refactorer()
        result = refactorer.rename_function(sample_code, "greet", "say_hello")

        assert "def say_hello" in result
        assert "def greet" not in result

    def test_rename_function_mock_mode(self, sample_code):
        """Test renaming a function in mock mode."""
        from coding_swarm.refactorer import create_refactorer

        refactorer = create_refactorer(mock_mode=True)
        result = refactorer.rename_function(sample_code, "greet", "say_hello")

        assert "say_hello" in result

    def test_rename_class(self, sample_code):
        """Test renaming a class."""
        from coding_swarm.refactorer import create_refactorer

        refactorer = create_refactorer()
        result = refactorer.rename_class(sample_code, "Calculator", "MathHelper")

        assert "class MathHelper" in result
        assert "class Calculator" not in result

    def test_add_docstring(self, sample_code_without_docstrings):
        """Test adding a docstring to a function."""
        from coding_swarm.refactorer import create_refactorer

        refactorer = create_refactorer()
        result = refactorer.add_docstring(
            sample_code_without_docstrings, "greet", "Greet a person by name."
        )

        assert "Greet a person by name." in result

    def test_extract_functions(self, sample_code):
        """Test extracting functions from code."""
        from coding_swarm.refactorer import create_refactorer

        refactorer = create_refactorer()
        functions = refactorer.extract_functions(sample_code)

        assert len(functions) >= 2
        names = [f["name"] for f in functions]
        assert "greet" in names
        assert "add" in names

    def test_extract_functions_mock_mode(self, sample_code):
        """Test extracting functions in mock mode."""
        from coding_swarm.refactorer import create_refactorer

        refactorer = create_refactorer(mock_mode=True)
        functions = refactorer.extract_functions(sample_code)

        assert len(functions) == 1
        assert functions[0]["name"] == "mock_function"

    def test_extract_classes(self, sample_code):
        """Test extracting classes from code."""
        from coding_swarm.refactorer import create_refactorer

        refactorer = create_refactorer()
        classes = refactorer.extract_classes(sample_code)

        assert len(classes) >= 1
        names = [c["name"] for c in classes]
        assert "Calculator" in names

    def test_extract_classes_mock_mode(self, sample_code):
        """Test extracting classes in mock mode."""
        from coding_swarm.refactorer import create_refactorer

        refactorer = create_refactorer(mock_mode=True)
        classes = refactorer.extract_classes(sample_code)

        assert len(classes) == 1
        assert classes[0]["name"] == "MockClass"


class TestImportAdder:
    """Tests for ImportAdder transformer."""

    def test_import_adder_single(self):
        """Test adding a single import."""
        from coding_swarm.refactorer import ImportAdder
        import libcst as cst

        code = "x = 1"
        tree = cst.parse_module(code)
        transformer = ImportAdder(["import os"])
        modified = tree.visit(transformer)

        assert "import os" in modified.code

    def test_import_adder_multiple(self):
        """Test adding multiple imports."""
        from coding_swarm.refactorer import ImportAdder
        import libcst as cst

        code = "x = 1"
        tree = cst.parse_module(code)
        transformer = ImportAdder(["import os", "import sys"])
        modified = tree.visit(transformer)

        assert "import os" in modified.code
        assert "import sys" in modified.code


class TestFunctionRenamer:
    """Tests for FunctionRenamer transformer."""

    def test_function_renamer_definition(self):
        """Test renaming function definition."""
        from coding_swarm.refactorer import FunctionRenamer
        import libcst as cst

        code = "def foo(): pass"
        tree = cst.parse_module(code)
        transformer = FunctionRenamer("foo", "bar")
        modified = tree.visit(transformer)

        assert "def bar" in modified.code
        assert "def foo" not in modified.code

    def test_function_renamer_call(self):
        """Test renaming function calls."""
        from coding_swarm.refactorer import FunctionRenamer
        import libcst as cst

        code = "def foo(): pass\nfoo()"
        tree = cst.parse_module(code)
        transformer = FunctionRenamer("foo", "bar")
        modified = tree.visit(transformer)

        assert "bar()" in modified.code


class TestClassRenamer:
    """Tests for ClassRenamer transformer."""

    def test_class_renamer_definition(self):
        """Test renaming class definition."""
        from coding_swarm.refactorer import ClassRenamer
        import libcst as cst

        code = "class Foo: pass"
        tree = cst.parse_module(code)
        transformer = ClassRenamer("Foo", "Bar")
        modified = tree.visit(transformer)

        assert "class Bar" in modified.code
        assert "class Foo" not in modified.code


class TestDocstringAdder:
    """Tests for DocstringAdder transformer."""

    def test_docstring_adder(self):
        """Test adding docstring to function."""
        from coding_swarm.refactorer import DocstringAdder
        import libcst as cst

        code = "def foo(): pass"
        tree = cst.parse_module(code)
        transformer = DocstringAdder("foo", "This is a docstring.")
        modified = tree.visit(transformer)

        assert "This is a docstring." in modified.code

    def test_docstring_adder_skip_existing(self):
        """Test that existing docstrings are not replaced."""
        from coding_swarm.refactorer import DocstringAdder
        import libcst as cst

        code = '''def foo():
    """Existing docstring."""
    pass'''
        tree = cst.parse_module(code)
        transformer = DocstringAdder("foo", "New docstring.")
        modified = tree.visit(transformer)

        # Should keep existing docstring
        assert "Existing docstring." in modified.code


class TestTypeHintAdder:
    """Tests for TypeHintAdder transformer."""

    def test_type_hint_adder(self):
        """Test adding type hints to parameters."""
        from coding_swarm.refactorer import TypeHintAdder
        import libcst as cst

        code = "def greet(name): return name"
        tree = cst.parse_module(code)
        transformer = TypeHintAdder("greet", {"name": "str"})
        modified = tree.visit(transformer)

        assert "name: str" in modified.code
