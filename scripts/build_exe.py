# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""Build the distributable Windows executable.

    python scripts/build_exe.py            # test, build, stage licences
    python scripts/build_exe.py --skip-tests
    python scripts/build_exe.py --clean    # discard build/ and dist/ first

Everything a recipient needs ends up in ``dist/``: the executable, the licence
of this project, its NOTICE, and the licences of the bundled libraries.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# This project lives under a path with Greek characters; the default Windows
# console codepage cannot encode it, and printing one would abort the build.
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


def show(path: Path) -> str:
    """Path relative to the project root, for readable log lines."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)

SPEC = ROOT / "PlottingApp.spec"
DIST = ROOT / "dist"
BUILD = ROOT / "build"
THIRD_PARTY_FILE = "THIRD-PARTY-LICENSES.txt"


def remove_tree(directory: Path) -> None:
    """Delete a build directory, coping with read-only files and OneDrive locks.

    A stale artifact is not worth aborting the build over, so a directory that
    refuses to go away is reported and left alone - PyInstaller overwrites it.
    """
    if not directory.exists():
        return
    print(f"removing {show(directory)}")

    def force(func, path, _exception):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    try:
        shutil.rmtree(directory, onexc=force)
    except OSError as error:
        print(f"  warning: could not fully remove {show(directory)}: {error}")
        print("  (a synced folder or an open file may be holding it)")


def run(command: list[str], what: str) -> None:
    print(f"\n=== {what} ===\n$ {' '.join(command)}", flush=True)
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"{what} failed (exit {result.returncode})")


def run_tests() -> None:
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
        "Tests")


def _requirement_names(distribution) -> list[str]:
    """Runtime dependency names of a distribution, ignoring extras."""
    names = []
    for requirement in distribution.requires or []:
        # "numpy>=1.23", "pillow>=8; extra == 'dev'", 'foo; python_version<"3.9"'
        head, _, marker = requirement.partition(";")
        if "extra ==" in marker:
            continue
        name = re.split(r"[<>=!~\[\s(]", head.strip(), maxsplit=1)[0]
        if name:
            names.append(name)
    return names


def dependency_closure(roots: list[str]) -> list[str]:
    """Every distribution that ends up inside the bundle, roots included."""
    import importlib.metadata as metadata

    seen: set[str] = set()
    queue = list(roots)
    while queue:
        name = queue.pop()
        key = name.lower().replace("_", "-")
        if key in seen:
            continue
        try:
            distribution = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            continue
        seen.add(key)
        queue.extend(_requirement_names(distribution))
    return sorted(seen)


def _declared_licence(distribution) -> str:
    metadata_ = distribution.metadata
    expression = metadata_.get("License-Expression")
    if expression:
        return expression
    classifiers = [value for key, value in metadata_.items()
                   if key == "Classifier" and value.startswith("License ::")]
    if classifiers:
        return " / ".join(c.split(" :: ")[-1] for c in classifiers)
    declared = (metadata_.get("License") or "").strip()
    return declared.splitlines()[0][:60] if declared else "see text below"


def collect_third_party_licences(target: Path | None = None) -> Path:
    """Gather the licence text of every bundled dependency into one file.

    BSD- and MIT-licensed dependencies require their notices to travel with a
    binary distribution, so this is not optional politeness. The whole runtime
    dependency closure is walked, not just the four headline packages - the
    bundle contains the transitive dependencies too.
    """
    import importlib.metadata as metadata

    from gui.about import THIRD_PARTY

    roots = [package for _, package, _ in THIRD_PARTY]
    chunks = [
        "Third-party components bundled in this application.",
        "Each is distributed under its own licence, reproduced below.",
        "",
    ]
    for name in dependency_closure(roots):
        try:
            distribution = metadata.distribution(name)
        except metadata.PackageNotFoundError:  # pragma: no cover
            continue
        chunks.append("=" * 78)
        chunks.append(f"{distribution.metadata.get('Name', name)} "
                      f"{distribution.version} - {_declared_licence(distribution)}\n")

        texts = [
            file for file in (distribution.files or [])
            if ".dist-info" in str(file).replace("\\", "/")
            and file.name.upper().startswith(("LICENSE", "LICENCE", "COPYING",
                                              "NOTICE", "AUTHORS"))
        ]
        if not texts:
            chunks.append(f"(no licence file shipped in the wheel; see the "
                          f"{name} project for the full text)\n")
        for file in texts:
            # read_text() resolves relative to the dist-info directory, so a
            # full path silently yields nothing - locate() gives the real one.
            try:
                located = file.locate()
                chunks.append(f"--- {file.name} ---")
                chunks.append(Path(located).read_text(encoding="utf-8",
                                                      errors="replace"))
            except (OSError, UnicodeDecodeError) as error:  # pragma: no cover
                chunks.append(f"(could not read {file}: {error})\n")

    target = target or (DIST / THIRD_PARTY_FILE)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(chunks), encoding="utf-8")
    return target


def stage_licences() -> list[Path]:
    """Copy the notices next to the executable, alongside the embedded copies."""
    staged = []
    for name in ("LICENSE", "NOTICE"):
        source = ROOT / name
        if not source.exists():
            print(f"  warning: {name} is missing from the project root")
            continue
        target = DIST / f"{name}.txt"
        shutil.copyfile(source, target)
        staged.append(target)
    staged.append(collect_third_party_licences())
    return staged


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-tests", action="store_true",
                        help="build without running the test suite first")
    parser.add_argument("--clean", action="store_true",
                        help="remove build/ and dist/ before building")
    arguments = parser.parse_args()

    if not SPEC.exists():
        raise SystemExit(f"missing spec file: {show(SPEC)}")

    if arguments.clean:
        for directory in (BUILD, DIST):
            remove_tree(directory)

    if arguments.skip_tests:
        print("skipping tests (--skip-tests)")
    else:
        run_tests()

    run([sys.executable, "-m", "PyInstaller", str(SPEC), "--noconfirm",
         "--distpath", str(DIST), "--workpath", str(BUILD)], "PyInstaller")

    executable = DIST / "PlottingApp.exe"
    if not executable.exists():  # pragma: no cover - build failure
        raise SystemExit(f"expected {show(executable)}, but it was not produced")

    staged = stage_licences()
    size_mb = executable.stat().st_size / (1024 * 1024)
    print(f"\n=== Done ===\n{show(executable)}  ({size_mb:.1f} MB)")
    for path in staged:
        print(show(path))
    print("\nShip the whole dist/ folder, or the .exe together with those "
          "text files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
