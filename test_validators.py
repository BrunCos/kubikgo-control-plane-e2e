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

    def test_task_gate_requires_the_new_function(self):
        source = self.workspace / "src" / "task_intake.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        tree.body = [node for node in tree.body if not isinstance(node, ast.FunctionDef) or node.name != "normalize_labels"]
        source.write_text(ast.unparse(tree) + "\n", encoding="utf-8")
        result = self.invoke("validator02_behavior.py", "task")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("normalize_labels is missing", result.stderr)


if __name__ == "__main__":
    unittest.main()
