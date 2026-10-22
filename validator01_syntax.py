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
    names = []
    for index, node in enumerate(tree.body):
        if index == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if not isinstance(node, ast.FunctionDef) or node.decorator_list:
            raise SystemExit("only undecorated function definitions are allowed")
        names.append(node.name)
    if names not in (["normalize_label"], ["normalize_label", "normalize_labels"]):
        raise SystemExit("unexpected module interface")
    print("PASS syntax and bounded module shape")


if __name__ == "__main__":
    main()
