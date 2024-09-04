"""NOT DONE, NEEDS UNIT TESTING AND MORE!!! """
import ast
from collections import defaultdict
from pathlib import Path


class ImportVisitor(ast.NodeVisitor):
    def __init__(self, base_path=""):
        self.imports = defaultdict(list)
        self.base_path = Path(".")

    def visit_Import(self, node):
        for alias in node.names:
            module_name = alias.name.split(".")[0]
            module_path = (
                self.base_path / module_name
            )  # Use / operator for joining paths
            if module_path.is_dir() and (module_path / "__init__.py").exists():
                self.imports["imports"].append((module_name, str(module_path)))
            elif (self.base_path / f"{module_path}.py").is_file():
                self.imports["imports"].append(
                    (module_name, str(self.base_path / f"{module_path}.py"))
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module
        if module:
            # Resolve relative imports
            resolved_module = self.base_path.joinpath(*module.split("."))
            if resolved_module.is_dir() and (resolved_module / "__init__.py").exists():
                self.imports["imports_from"].append((module, str(resolved_module)))
            elif resolved_module.with_suffix(".py").is_file():
                self.imports["imports_from"].append(
                    (module, str(resolved_module.with_suffix(".py")))
                )
        self.generic_visit(node)


# Adjusted function to find local imports recursively
def find_local_imports_recursively(start_file, base_path=""):
    visited_files = set()
    local_deps = [(start_file, start_file)]

    def visit_file(file_path):
        file_path = Path(file_path)  # Convert string to Path object
        if not file_path.is_file():
            raise Exception(f"Path {file_path} does not exist")
        if file_path in visited_files:
            return
        visited_files.add(file_path)

        with open(file_path, "r") as file:
            tree = ast.parse(file.read(), filename=str(file_path))
        visitor = ImportVisitor(base_path=str(file_path.parent))
        visitor.visit(tree)

        for imp, path in visitor.imports["imports"]:
            local_deps.append((imp, path))
            visit_file(Path(path))  # Ensure path is a Path object
        for imp_from, path in visitor.imports["imports_from"]:
            path = Path(path)
            if ".py" != path.suffix:
                # init file
                for s_path in path.glob("*.py"):
                    local_deps.append((imp_from, str(s_path)))
                    visit_file(s_path)
            else:
                local_deps.append((imp_from, str(path)))
                visit_file(Path(path))  # Ensure path is a Path object
        for wildcard, path in visitor.imports["wildcards"]:
            local_deps.append((wildcard, path))

    start_file = Path(start_file)  # Convert string to Path object
    visit_file(start_file)
    return local_deps

