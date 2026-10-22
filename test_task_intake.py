"""Baseline tests use only invented example strings and Python's standard library."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from task_intake import normalize_label


class NormalizeLabelTests(unittest.TestCase):
    def test_plain_text(self):
        self.assertEqual(normalize_label("alpha beta"), "alpha beta")

    def test_trim(self):
        self.assertEqual(normalize_label("  alpha  "), "alpha")

    def test_collapse_spaces(self):
        self.assertEqual(normalize_label("alpha   beta"), "alpha beta")

    def test_tabs_and_newlines(self):
        self.assertEqual(normalize_label("\talpha\n beta\r\n"), "alpha beta")

    def test_unicode_whitespace(self):
        self.assertEqual(normalize_label("\u00a0alpha\u2003beta\u00a0"), "alpha beta")

    def test_case_is_preserved(self):
        self.assertEqual(normalize_label(" Alpha BETA "), "Alpha BETA")

    def test_empty_text(self):
        self.assertEqual(normalize_label(""), "")

    def test_whitespace_only(self):
        self.assertEqual(normalize_label(" \n\t "), "")

    def test_unicode_letters_are_preserved(self):
        self.assertEqual(normalize_label("  caff\u00e8  "), "caff\u00e8")

    def test_idempotence(self):
        result = normalize_label("  alpha \t beta  ")
        self.assertEqual(normalize_label(result), result)

    def test_non_string_rejected(self):
        for value in (None, 7, True, [], {}, b"alpha"):
            with self.subTest(type=type(value).__name__):
                with self.assertRaises(TypeError):
                    normalize_label(value)


if __name__ == "__main__":
    unittest.main()
