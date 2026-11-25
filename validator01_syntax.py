"""Trusted-copy validator 1: compile source and check the bounded module shape."""

import ast
import sys
from pathlib import Path


ALLOWED_NODE_TYPES = (
    ast.Module,
    ast.Expr,
    ast.Constant,
    ast.FunctionDef,
    ast.arguments,
    ast.arg,
    ast.Name,
    ast.Load,
    ast.Store,
    ast.Subscript,
    ast.List,
    ast.If,
    ast.For,
    ast.Assign,
    ast.Raise,
    ast.Return,
    ast.Call,
    ast.Attribute,
    ast.UnaryOp,
    ast.Not,
    ast.BoolOp,
    ast.And,
    ast.Compare,
    ast.IsNot,
    ast.NotIn,
    ast.GeneratorExp,
    ast.comprehension,
)
SAFE_NAMED_CALLS = {
    "TypeError": 1,
    "any": 1,
    "isinstance": 2,
    "normalize_label": 1,
    "set": 0,
}
SAFE_METHOD_CALLS = {
    "add": 1,
    "append": 1,
    "casefold": 0,
    "join": 1,
    "split": 0,
}
SAFE_GLOBAL_NAMES = set(SAFE_NAMED_CALLS) | {"list", "str"}


def bounded_function_names(tree):
    names = set()
    for function in (node for node in tree.body if isinstance(node, ast.FunctionDef)):
        names.update(argument.arg for argument in function.args.args)
        for node in ast.walk(function):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if node.id in SAFE_GLOBAL_NAMES:
                    raise SystemExit("safe callable/type names cannot be rebound")
                names.add(node.id)
    return names


def validate_bounded_tree(tree):
    local_names = bounded_function_names(tree)
    parents = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_NODE_TYPES):
            raise SystemExit(f"unsafe syntax node: {type(node).__name__}")
        if isinstance(node, ast.Name):
            if node.id.startswith("__"):
                raise SystemExit("dunder names are not allowed")
            if isinstance(node.ctx, ast.Load) and node.id not in local_names | SAFE_GLOBAL_NAMES:
                raise SystemExit(f"unsafe global name: {node.id}")
        if isinstance(node, ast.Attribute):
            parent = parents.get(node)
            if not isinstance(parent, ast.Call) or parent.func is not node:
                raise SystemExit("attribute access is allowed only for fixed method calls")
            if node.attr not in SAFE_METHOD_CALLS or node.attr.startswith("__"):
                raise SystemExit(f"unsafe method call: {node.attr}")
            if node.attr == "join":
                if not isinstance(node.value, ast.Constant) or type(node.value.value) is not str:
                    raise SystemExit("join is allowed only on a literal string")
            elif not isinstance(node.value, ast.Name) or node.value.id not in local_names:
                raise SystemExit("methods are allowed only on local values")
        if isinstance(node, ast.Call):
            if node.keywords:
                raise SystemExit("keyword arguments are not allowed")
            if isinstance(node.func, ast.Name):
                expected = SAFE_NAMED_CALLS.get(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                expected = SAFE_METHOD_CALLS.get(node.func.attr)
            else:
                expected = None
            if expected is None or len(node.args) != expected:
                raise SystemExit("call is outside the bounded allowlist")


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
    validate_bounded_tree(tree)
    print("PASS syntax and bounded module shape")


if __name__ == "__main__":
    main()
