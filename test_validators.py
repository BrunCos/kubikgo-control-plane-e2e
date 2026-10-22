"""Validator regression tests create only disposable, synthetic file copies."""

import ast
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "workspace"
        shutil.copytree(ROOT, self.workspace, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        self.trusted = self.root / "trusted"
        self.trusted.mkdir()
        for name in ("validator01_syntax.py", "validator02_behavior.py", "validator03_scope.py", "immutable-files.sha256"):
            shutil.copyfile(ROOT / name, self.trusted / name)

    def invoke(self, name, *arguments):
        return subprocess.run(
            [sys.executable, "-I", "-B", str(self.trusted / name), str(self.workspace), *arguments],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

    def scope(self):
        return self.invoke("validator03_scope.py", str(self.trusted / "immutable-files.sha256"))

    def write_synthetic_batch_candidate(self, *, return_identity=False, mutate_invalid=False):
        """Create a disposable reference or deliberately faulty candidate."""
        source = self.workspace / "src" / "task_intake.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        tree.body = [node for node in tree.body if not isinstance(node, ast.FunctionDef) or node.name != "normalize_labels"]
        invalid_statement = "values.clear(); raise TypeError('invalid item')" if mutate_invalid else "raise TypeError('invalid item')"
        return_statement = "return values if result == values else result" if return_identity else "return result"
        implementation = f'''
def normalize_labels(values: list[str]) -> list[str]:
    if not isinstance(values, list):
        raise TypeError('values must be a list')
    if any(not isinstance(value, str) for value in values):
        {invalid_statement}
    result = []
    seen = set()
    for value in values:
        normalized = normalize_label(value)
        key = normalized.casefold()
        if normalized and key not in seen:
            result.append(normalized)
            seen.add(key)
    {return_statement}
'''
        source.write_text(ast.unparse(tree) + "\n" + implementation, encoding="utf-8")

    def test_baseline_scope_is_valid(self):
        result = self.scope()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_source_is_the_only_mutable_file(self):
        with (self.workspace / "src" / "task_intake.py").open("a", encoding="utf-8") as handle:
            handle.write("\n# Synthetic test-only comment.\n")
        result = self.scope()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_changed_test_is_rejected(self):
        (self.workspace / "test_task_intake.py").write_text("", encoding="utf-8")
        self.assertNotEqual(self.scope().returncode, 0)

    def test_unexpected_file_is_rejected(self):
        (self.workspace / "unexpected.txt").write_text("synthetic", encoding="ascii")
        self.assertNotEqual(self.scope().returncode, 0)

    def test_workspace_manifest_is_not_trusted(self):
        result = self.invoke("validator03_scope.py", str(self.workspace / "immutable-files.sha256"))
        self.assertNotEqual(result.returncode, 0)

    def test_module_level_side_effect_is_rejected(self):
        with (self.workspace / "src" / "task_intake.py").open("a", encoding="utf-8") as handle:
            handle.write("\nprint('synthetic')\n")
        result = self.invoke("validator01_syntax.py")
        self.assertNotEqual(result.returncode, 0)

    def test_nested_imports_are_rejected_without_execution(self):
        source = self.workspace / "src" / "task_intake.py"
        original = source.read_text(encoding="utf-8")
        for statement in ("import os", "from pathlib import Path"):
            with self.subTest(statement=statement):
                source.write_text(original + "\ndef normalize_labels(values: list[str]) -> list[str]:\n    " + statement + "\n    return []\n", encoding="utf-8")
                result = self.invoke("validator01_syntax.py")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("imports are not allowed", result.stderr)

    def test_function_defaults_are_rejected_without_execution(self):
        source = self.workspace / "src" / "task_intake.py"
        original = source.read_text(encoding="utf-8")
        for default in ("[]", "print('synthetic-default-side-effect')"):
            with self.subTest(default=default):
                source.write_text(original + "\ndef normalize_labels(values: list[str] = " + default + ") -> list[str]:\n    return []\n", encoding="utf-8")
                result = self.invoke("validator01_syntax.py")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("fixed typed signatures", result.stderr)
                self.assertNotIn("synthetic-default-side-effect", result.stdout)

    def test_argument_annotation_call_is_rejected_without_execution(self):
        source = self.workspace / "src" / "task_intake.py"
        with source.open("a", encoding="utf-8") as handle:
            handle.write("\ndef normalize_labels(values: print('synthetic-argument-side-effect')) -> list[str]:\n    return []\n")
        result = self.invoke("validator01_syntax.py")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixed typed signatures", result.stderr)
        self.assertNotIn("synthetic-argument-side-effect", result.stdout)

    def test_return_annotation_call_is_rejected_without_execution(self):
        source = self.workspace / "src" / "task_intake.py"
        with source.open("a", encoding="utf-8") as handle:
            handle.write("\ndef normalize_labels(values: list[str]) -> print('synthetic-return-side-effect'):\n    return []\n")
        result = self.invoke("validator01_syntax.py")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixed typed signatures", result.stderr)
        self.assertNotIn("synthetic-return-side-effect", result.stdout)

    def test_task_gate_requires_the_new_function(self):
        source = self.workspace / "src" / "task_intake.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        tree.body = [node for node in tree.body if not isinstance(node, ast.FunctionDef) or node.name != "normalize_labels"]
        source.write_text(ast.unparse(tree) + "\n", encoding="utf-8")
        result = self.invoke("validator02_behavior.py", "task")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("normalize_labels is missing", result.stderr)

    def test_task_gate_rejects_identity_return(self):
        self.write_synthetic_batch_candidate(return_identity=True)
        result = self.invoke("validator02_behavior.py", "task")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must return a new list", result.stderr)

    def test_task_gate_rejects_invalid_input_mutation(self):
        self.write_synthetic_batch_candidate(mutate_invalid=True)
        result = self.invoke("validator02_behavior.py", "task")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid input list was mutated", result.stderr)

    def test_valid_synthetic_task_candidate_passes_all_gates(self):
        self.write_synthetic_batch_candidate()
        for name, arguments in (
            ("validator03_scope.py", (str(self.trusted / "immutable-files.sha256"),)),
            ("validator01_syntax.py", ()),
            ("validator02_behavior.py", ("task",)),
        ):
            with self.subTest(validator=name):
                result = self.invoke(name, *arguments)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
