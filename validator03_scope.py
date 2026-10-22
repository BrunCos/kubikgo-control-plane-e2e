"""Trusted-copy validator 3: exact immutable-file and one-file change policy.

Both this script and MANIFEST must be provisioned outside the candidate workspace.
This validator does not execute candidate source or use candidate test results.
"""

import hashlib
import os
import re
import sys
from pathlib import Path, PurePosixPath


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: validator03_scope.py WORKSPACE TRUSTED_MANIFEST")
    workspace = Path(sys.argv[1]).resolve(strict=True)
    manifest_path = Path(sys.argv[2]).resolve(strict=True)
    if manifest_path.is_relative_to(workspace):
        raise SystemExit("manifest must be trusted and outside the workspace")
    manifest_bytes = manifest_path.read_bytes()
    expected = {}
    for line in manifest_bytes.decode("ascii").splitlines():
        if not re.fullmatch(r"[a-f0-9]{64}  [A-Za-z0-9_./-]+", line):
            raise SystemExit("invalid trusted manifest")
        digest, relative = line.split("  ", 1)
        parsed = PurePosixPath(relative)
        if parsed.is_absolute() or ".." in parsed.parts or relative in expected:
            raise SystemExit("unsafe or duplicate manifest path")
        expected[relative] = digest
    mutable = "src/task_intake.py"
    manifest_name = "immutable-files.sha256"
    allowed = set(expected) | {mutable, manifest_name}
    observed = set()
    for directory, dirs, files in os.walk(workspace, followlinks=False):
        for name in list(dirs):
            path = Path(directory) / name
            if path.is_symlink():
                raise SystemExit("symlinked directories are not allowed")
            if path == workspace / ".git":
                dirs.remove(name)
        for name in files:
            path = Path(directory) / name
            relative = path.relative_to(workspace).as_posix()
            if path.is_symlink() or not path.is_file() or relative not in allowed:
                raise SystemExit("unexpected or non-regular repository file")
            observed.add(relative)
            content = path.read_bytes()
            if relative == manifest_name:
                if content != manifest_bytes:
                    raise SystemExit("repository manifest changed")
            elif relative in expected and hashlib.sha256(content).hexdigest() != expected[relative]:
                raise SystemExit("an immutable file changed")
    if observed != allowed:
        raise SystemExit("required files are missing")
    print("PASS exact one-file change scope")


if __name__ == "__main__":
    main()
