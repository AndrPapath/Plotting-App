# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""The build script's licence bookkeeping, checked without running a build."""

import sys as _sys
from pathlib import Path as _Path

# Runnable straight from the editor: make the project root importable.
_ROOT = str(_Path(__file__).resolve().parents[1])
if _ROOT not in _sys.path:
    _sys.path.insert(0, _ROOT)
_sys.path.insert(0, str(_Path(_ROOT) / "scripts"))

import tempfile
import unittest
from pathlib import Path

import build_exe
from gui.about import THIRD_PARTY

ROOTS = [package for _, package, _ in THIRD_PARTY]


class DependencyClosureTests(unittest.TestCase):
    def test_closure_contains_the_declared_roots(self):
        closure = build_exe.dependency_closure(ROOTS)
        for package in ROOTS:
            with self.subTest(package=package):
                self.assertIn(package, closure)

    def test_closure_reaches_transitive_dependencies(self):
        """matplotlib pulls in packages that also end up inside the exe."""
        closure = build_exe.dependency_closure(ROOTS)
        for package in ("pillow", "fonttools", "cycler", "python-dateutil"):
            with self.subTest(package=package):
                self.assertIn(package, closure)

    def test_unknown_package_is_ignored_not_fatal(self):
        self.assertEqual(build_exe.dependency_closure(["no-such-package-xyz"]), [])


class HiddenImportTests(unittest.TestCase):
    """Anything imported by name at runtime must be declared in the spec.

    Static analysis cannot see these, so the frozen build fails at the moment
    the user clicks the button - which is how PDF export shipped broken.
    """

    SPEC = (Path(_ROOT) / "PlottingApp.spec").read_text(encoding="utf-8")

    def test_every_save_format_has_its_backend_declared(self):
        from gui.app import SAVE_FORMATS

        for extension, backend in SAVE_FORMATS.items():
            with self.subTest(format=extension):
                self.assertIn(backend, self.SPEC)

    def test_every_registered_plot_mode_is_declared(self):
        import plotting

        for mode, module_path in plotting.PLOT_MODES.items():
            with self.subTest(mode=mode):
                self.assertIn(module_path, self.SPEC)


class LicenceFileTests(unittest.TestCase):
    def test_collected_file_carries_real_licence_text(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "THIRD-PARTY-LICENSES.txt"
            build_exe.collect_third_party_licences(target)
            text = target.read_text(encoding="utf-8")

        # Not just a list of names: the actual notices have to be in there.
        self.assertGreater(len(text), 50_000)
        self.assertGreater(text.upper().count("COPYRIGHT"), 50)
        for package in ROOTS:
            with self.subTest(package=package):
                self.assertIn(package, text.lower())


if __name__ == "__main__":
    unittest.main()
