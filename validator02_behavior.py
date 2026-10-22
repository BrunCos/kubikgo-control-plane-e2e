"""Trusted-copy validator 2: independent baseline/task behavioral assertions.

Run only in a separate sandbox: importing candidate Python executes its code.
"""

import importlib.util
import sys
from pathlib import Path


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def rejects_type_error(call):
    try:
        call()
    except TypeError:
        return
    raise SystemExit("invalid input was not rejected with TypeError")


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in {"baseline", "task"}:
        raise SystemExit("usage: validator02_behavior.py WORKSPACE baseline|task")
    path = Path(sys.argv[1]).resolve(strict=True) / "src" / "task_intake.py"
    if path.parent.is_symlink() or path.is_symlink() or not path.is_file():
        raise SystemExit("source must be a regular file")
    spec = importlib.util.spec_from_file_location("synthetic_candidate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for raw, expected in (("", ""), (" \t\n", ""), ("  Alpha\t BETA\n", "Alpha BETA"), ("\u00a0caff\u00e8\u2003delta", "caff\u00e8 delta")):
        require(module.normalize_label(raw) == expected, "baseline normalization mismatch")
        require(module.normalize_label(expected) == expected, "normalization is not idempotent")
    for raw in (None, 1, [], b"alpha"):
        rejects_type_error(lambda raw=raw: module.normalize_label(raw))
    if sys.argv[2] == "task":
        require(callable(getattr(module, "normalize_labels", None)), "task function normalize_labels is missing")
        cases = (
            ([], []),
            ([" ", "\n"], []),
            ([" Alpha ", "alpha", "BETA", " beta ", "Alpha"], ["Alpha", "BETA"]),
            (["x\ty", "x y", "z"], ["x y", "z"]),
            (["Stra\u00dfe", "STRASSE", "Omega"], ["Stra\u00dfe", "Omega"]),
            (["delta", "Alpha", "beta"], ["delta", "Alpha", "beta"]),
        )
        for raw, expected in cases:
            original = list(raw)
            actual = module.normalize_labels(raw)
            require(actual is not raw, "batch normalization must return a new list")
            require(type(actual) is list and actual == expected, "batch normalization mismatch")
            require(raw == original, "input list was mutated")
            require(module.normalize_labels(raw) == expected, "batch normalization is not deterministic")
        for raw in (None, "alpha", ("alpha",), {"alpha"}, ["alpha", 1], [None]):
            original = list(raw) if isinstance(raw, list) else None
            rejects_type_error(lambda raw=raw: module.normalize_labels(raw))
            if isinstance(raw, list):
                require(raw == original, "invalid input list was mutated")
    print("PASS independent behavior " + sys.argv[2])


if __name__ == "__main__":
    main()
