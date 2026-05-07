"""LibCST-based code refactoring utilities."""

from __future__ import annotations

from typing import cast

import libcst as cst


class ImportAdder(cst.CSTTransformer):
    """Transformer to add imports to a Python module."""

    def __init__(self, imports: list[str]) -> None:
        """Initialize with list of imports to add.

        Args:
            imports: List of import statements (e.g., ["import os", "from typing import List"])
        """
        super().__init__()
        self.imports = imports
        self.existing_imports: set[str] = set()
        self._added = False

    def visit_Import(self, node: cst.Import) -> bool:  # noqa: N802
        """Track existing imports."""
        if isinstance(node.names, cst.ImportStar):
            return True
        for name in node.names:
            if isinstance(name, cst.ImportAlias) and isinstance(name.name, cst.Name):
                self.existing_imports.add(name.name.value)
        return True

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:  # noqa: N802
        """Track existing from imports."""
        if isinstance(node.module, cst.Attribute):
            module_name = _get_dotted_name(node.module)
        elif isinstance(node.module, cst.Name):
            module_name = node.module.value
        else:
            module_name = ""
        self.existing_imports.add(module_name)
        return True

    def leave_Module(  # noqa: N802
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        """Add imports at the top of the module."""
        if self._added:
            return updated_node

        new_imports = []
        for imp in self.imports:
            # Parse the import statement
            try:
                parsed = cst.parse_statement(imp)
                new_imports.append(parsed)
            except Exception:
                continue

        if new_imports:
            # Find the position after existing imports
            insert_pos = 0
            for i, stmt in enumerate(updated_node.body):
                if isinstance(stmt, (cst.SimpleStatementLine,)):
                    if any(isinstance(s, (cst.Import, cst.ImportFrom)) for s in stmt.body):
                        insert_pos = i + 1
                elif isinstance(stmt, cst.EmptyLine):
                    continue
                elif insert_pos > 0:
                    break

            new_body = list(updated_node.body[:insert_pos])
            new_body.extend(new_imports)
            new_body.extend(updated_node.body[insert_pos:])
            self._added = True
            return updated_node.with_changes(body=new_body)

        return updated_node


class FunctionRenamer(cst.CSTTransformer):
    """Transformer to rename functions."""

    def __init__(self, old_name: str, new_name: str) -> None:
        """Initialize with old and new function names."""
        super().__init__()
        self.old_name = old_name
        self.new_name = new_name

    def leave_FunctionDef(  # noqa: N802
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """Rename function definition."""
        if updated_node.name.value == self.old_name:
            return updated_node.with_changes(name=cst.Name(self.new_name))
        return updated_node

    def leave_Call(  # noqa: N802
        self, original_node: cst.Call, updated_node: cst.Call
    ) -> cst.Call:
        """Rename function calls."""
        if isinstance(updated_node.func, cst.Name):
            if updated_node.func.value == self.old_name:
                return updated_node.with_changes(func=cst.Name(self.new_name))
        return updated_node


class ClassRenamer(cst.CSTTransformer):
    """Transformer to rename classes."""

    def __init__(self, old_name: str, new_name: str) -> None:
        """Initialize with old and new class names."""
        super().__init__()
        self.old_name = old_name
        self.new_name = new_name

    def leave_ClassDef(  # noqa: N802
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        """Rename class definition."""
        if updated_node.name.value == self.old_name:
            return updated_node.with_changes(name=cst.Name(self.new_name))
        return updated_node

    def leave_Name(  # noqa: N802
        self, original_node: cst.Name, updated_node: cst.Name
    ) -> cst.Name:
        """Rename class references."""
        if updated_node.value == self.old_name:
            return updated_node.with_changes(value=self.new_name)
        return updated_node


class DocstringAdder(cst.CSTTransformer):
    """Transformer to add docstrings to functions/classes."""

    def __init__(self, target_name: str, docstring: str) -> None:
        """Initialize with target and docstring."""
        super().__init__()
        self.target_name = target_name
        self.docstring = docstring

    def leave_FunctionDef(  # noqa: N802
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """Add docstring to function."""
        if updated_node.name.value != self.target_name:
            return updated_node

        # Check if docstring already exists
        if updated_node.body.body:
            first_stmt = updated_node.body.body[0]
            if isinstance(first_stmt, cst.SimpleStatementLine):
                if first_stmt.body and isinstance(first_stmt.body[0], cst.Expr):
                    if isinstance(first_stmt.body[0].value, cst.SimpleString):
                        return updated_node

        # Create docstring node
        docstring_node = cst.SimpleStatementLine(
            body=[cst.Expr(cst.SimpleString(f'"""{self.docstring}"""'))]
        )

        existing_body = list(cast("tuple[cst.BaseStatement, ...]", updated_node.body.body))
        new_body = cst.IndentedBlock(body=[docstring_node, *existing_body])
        return updated_node.with_changes(body=new_body)


class TypeHintAdder(cst.CSTTransformer):
    """Transformer to add type hints to function parameters."""

    def __init__(self, function_name: str, param_types: dict[str, str]) -> None:
        """Initialize with function name and parameter types."""
        super().__init__()
        self.function_name = function_name
        self.param_types = param_types

    def leave_Param(  # noqa: N802
        self, original_node: cst.Param, updated_node: cst.Param
    ) -> cst.Param:
        """Add type hints to parameters."""
        if updated_node.name.value in self.param_types:
            type_str = self.param_types[updated_node.name.value]
            annotation = cst.Annotation(annotation=cst.Name(type_str))
            return updated_node.with_changes(annotation=annotation)
        return updated_node


def _get_dotted_name(node: cst.BaseExpression) -> str:
    """Get dotted name from an Attribute or Name node."""
    if isinstance(node, cst.Name):
        return node.value
    if isinstance(node, cst.Attribute):
        parent = _get_dotted_name(node.value)
        return f"{parent}.{node.attr.value}"
    return ""


class CodeRefactorer:
    """High-level interface for code refactoring using LibCST."""

    def __init__(self, mock_mode: bool = False) -> None:
        """Initialize the refactorer.

        Args:
            mock_mode: If True, operations return predictable results for testing
        """
        self.mock_mode = mock_mode

    def parse(self, code: str) -> cst.Module:
        """Parse Python code into a CST.

        Args:
            code: Python source code

        Returns:
            Parsed CST module
        """
        return cst.parse_module(code)

    def add_imports(self, code: str, imports: list[str]) -> str:
        """Add imports to Python code.

        Args:
            code: Python source code
            imports: List of import statements

        Returns:
            Modified source code
        """
        if self.mock_mode:
            import_block = "\n".join(imports)
            return f"{import_block}\n\n{code}"

        tree = self.parse(code)
        transformer = ImportAdder(imports)
        modified = tree.visit(transformer)
        return modified.code

    def rename_function(self, code: str, old_name: str, new_name: str) -> str:
        """Rename a function throughout the code.

        Args:
            code: Python source code
            old_name: Current function name
            new_name: New function name

        Returns:
            Modified source code
        """
        if self.mock_mode:
            return code.replace(old_name, new_name)

        tree = self.parse(code)
        transformer = FunctionRenamer(old_name, new_name)
        modified = tree.visit(transformer)
        return modified.code

    def rename_class(self, code: str, old_name: str, new_name: str) -> str:
        """Rename a class throughout the code.

        Args:
            code: Python source code
            old_name: Current class name
            new_name: New class name

        Returns:
            Modified source code
        """
        if self.mock_mode:
            return code.replace(old_name, new_name)

        tree = self.parse(code)
        transformer = ClassRenamer(old_name, new_name)
        modified = tree.visit(transformer)
        return modified.code

    def add_docstring(self, code: str, target_name: str, docstring: str) -> str:
        """Add a docstring to a function or class.

        Args:
            code: Python source code
            target_name: Name of the function or class
            docstring: Docstring content

        Returns:
            Modified source code
        """
        if self.mock_mode:
            return code

        tree = self.parse(code)
        transformer = DocstringAdder(target_name, docstring)
        modified = tree.visit(transformer)
        return modified.code

    def add_type_hints(self, code: str, function_name: str, param_types: dict[str, str]) -> str:
        """Add type hints to function parameters.

        Args:
            code: Python source code
            function_name: Name of the function
            param_types: Mapping of parameter names to type strings

        Returns:
            Modified source code
        """
        if self.mock_mode:
            return code

        tree = self.parse(code)
        transformer = TypeHintAdder(function_name, param_types)
        modified = tree.visit(transformer)
        return modified.code

    def extract_functions(self, code: str) -> list[dict[str, str]]:
        """Extract function definitions from code.

        Args:
            code: Python source code

        Returns:
            List of dicts with function info (name, docstring, params)
        """
        if self.mock_mode:
            return [{"name": "mock_function", "params": "", "docstring": ""}]

        tree = self.parse(code)
        functions = []

        for node in tree.body:
            if isinstance(node, cst.FunctionDef):
                func_info = {
                    "name": node.name.value,
                    "params": "",
                    "docstring": "",
                }
                # Extract parameters
                params = []
                for param in node.params.params:
                    params.append(param.name.value)
                func_info["params"] = ", ".join(params)

                # Extract docstring
                if node.body.body:
                    first_stmt = node.body.body[0]
                    if isinstance(first_stmt, cst.SimpleStatementLine):
                        if first_stmt.body and isinstance(first_stmt.body[0], cst.Expr):
                            if isinstance(first_stmt.body[0].value, cst.SimpleString):
                                func_info["docstring"] = first_stmt.body[0].value.value

                functions.append(func_info)

        return functions

    def extract_classes(self, code: str) -> list[dict[str, str]]:
        """Extract class definitions from code.

        Args:
            code: Python source code

        Returns:
            List of dicts with class info (name, bases, methods)
        """
        if self.mock_mode:
            return [{"name": "MockClass", "bases": "", "methods": ""}]

        tree = self.parse(code)
        classes = []

        for node in tree.body:
            if isinstance(node, cst.ClassDef):
                class_info = {
                    "name": node.name.value,
                    "bases": "",
                    "methods": "",
                }
                # Extract bases
                bases = []
                for base in node.bases:
                    if isinstance(base.value, cst.Name):
                        bases.append(base.value.value)
                class_info["bases"] = ", ".join(bases)

                # Extract methods
                methods = []
                for body_item in node.body.body:
                    if isinstance(body_item, cst.FunctionDef):
                        methods.append(body_item.name.value)
                class_info["methods"] = ", ".join(methods)

                classes.append(class_info)

        return classes

    def validate_syntax(self, code: str) -> tuple[bool, str]:
        """Validate Python syntax.

        Args:
            code: Python source code

        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.mock_mode:
            return True, ""

        try:
            self.parse(code)
            return True, ""
        except cst.ParserSyntaxError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)


def create_refactorer(mock_mode: bool = False) -> CodeRefactorer:
    """Create a CodeRefactorer instance.

    Args:
        mock_mode: If True, operations return predictable results for testing

    Returns:
        CodeRefactorer instance
    """
    return CodeRefactorer(mock_mode=mock_mode)
