#!/usr/bin/env python3
"""A10 detector for Python: find scripts whose imports no longer resolve.

    python scripts/dead-import-scan.py mypkg scripts/*.py

Argument 1 is your own package name; the rest are files to check. Exit code 1 if
anything is dead, so it drops straight into CI.

Two passes, and **both are needed**:

  1. top-level  — `import foo` / `from foo import x` where foo is third-party or stdlib.
  2. dotted     — `from mypkg.sub.mod import x`. Without this pass a script referencing
                  `mypkg.deleted.thing` looks healthy, because `mypkg` itself still
                  imports fine. That is exactly how a dead script survives for weeks
                  while the test suite stays green: nothing imports it, so nothing fails.

`importlib.util.find_spec` **raises** ModuleNotFoundError when an intermediate package
is missing rather than returning None — that exception is the positive result, not an
error in this script, so it is caught.

Static only: nothing is imported, no side effects, safe on untrusted files.
"""
from __future__ import annotations

import ast
import importlib.util
import sys


def _resolves(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except (ModuleNotFoundError, ImportError, ValueError):
        return False        # intermediate package gone → the thing we are looking for


def scan(path: str, own_pkg: str) -> list[str]:
    """Return the dotted names in `path` that no longer resolve."""
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except SyntaxError as exc:
        return [f"<syntax error: {exc}>"]

    top: set[str] = set()
    dotted: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                (dotted if a.name.startswith(own_pkg + ".") else top).add(a.name)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            (dotted if node.module.startswith(own_pkg) else top).add(node.module)

    dead = [m for m in top
            if m.split(".")[0] not in sys.stdlib_module_names and not _resolves(m)]
    dead += [m for m in dotted if not _resolves(m)]
    return sorted(set(dead))


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    own_pkg, files = argv[1], argv[2:]
    bad = 0
    for f in files:
        dead = scan(f, own_pkg)
        print(f"{f:<48} {'DEAD: ' + ', '.join(dead) if dead else 'ok'}")
        bad += bool(dead)
    if bad:
        print(f"\n{bad} file(s) reference modules that no longer exist. "
              f"Repair, or park them somewhere labelled as parked — and fix the "
              f"documents that still point at them.", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
