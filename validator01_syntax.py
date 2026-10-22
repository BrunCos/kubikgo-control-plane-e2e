"""Trusted-copy validator 1: compile source and check the bounded module shape."""

import ast
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: validator01_syntax.py WORKSPACE")
    path = Path(sys.argv[1]).resolve(strict=True) / "src" / "task_intake.py"
    if path.parent.is_symlink() or path.is_symlink() or not path.is_file():
        raise SystemExit("source must be a regular file")
    source = path.read_bytes()
    if len(source) > 65536:
        raise SystemExit("source exceeds the exercise size limit")
    tree = ast.parse(source, filename="task_intake.py")
    compile(tree, "task_intake.py", "exec", dont_inherit=True)
    if any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(tree)):
        raise SystemExit("imports are not allowed anywhere in the exercise")
    signatures = {
        "normalize_label": ast.parse("def normalize_label(value: str) -> str: pass").body[0],
        "normalize_labels": ast.parse("def normalize_labels(values: list[str]) -> list[str]: pass").body[0],
    }
    names = []
    for index, node in enumerate(tree.body):
        if index == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if not isinstance(node, ast.FunctionDef) or node.decorator_list:
            raise SystemExit("only undecorated function definitions are allowed")
        expected = signatures.get(node.name)
        if expected is None:
            raise SystemExit("unexpected module interface")
        if (
            ast.dump(node.args) != ast.dump(expected.args)
            or node.returns is None
            or ast.dump(node.returns) != ast.dump(expected.returns)
            or getattr(node, "type_params", ())
        ):
            raise SystemExit("fixed typed signatures without defaults are required")
        names.append(node.name)
    if names not in (["normalize_label"], ["normalize_label", "normalize_labels"]):
        raise SystemExit("unexpected module interface")
    print("PASS syntax and bounded module shape")


if __name__ == "__main__":
    main()
