# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""The copyright shown in the app must match the files that assert it."""

import sys as _sys
from pathlib import Path as _Path

# Runnable straight from the editor: make the project root importable.
_ROOT = str(_Path(__file__).resolve().parents[1])
if _ROOT not in _sys.path:
    _sys.path.insert(0, _ROOT)

import re
import unittest
from pathlib import Path

from gui import about

PROJECT_ROOT = Path(_ROOT)


class MetadataTests(unittest.TestCase):
    def test_copyright_is_assembled_from_its_parts(self):
        self.assertEqual(
            about.COPYRIGHT,
            f"Copyright {about.COPYRIGHT_YEARS} {about.AUTHOR}")
        self.assertIn(about.AUTHOR, about.SHORT_NOTICE)
        self.assertIn(about.COPYRIGHT_YEARS, about.SHORT_NOTICE)

    def test_version_is_a_release_number(self):
        self.assertRegex(about.VERSION, r"^\d+\.\d+\.\d+$")


class ConsistencyTests(unittest.TestCase):
    """The About box, NOTICE and the source headers must agree."""

    def test_about_matches_the_notice_file(self):
        notice = about.notice_text()
        self.assertIsNotNone(notice, "NOTICE is missing from the project root")
        self.assertIn(about.COPYRIGHT, notice)
        self.assertIn(about.APP_NAME, notice)

    def test_about_matches_the_source_headers(self):
        header = f"# {about.COPYRIGHT}"
        checked = 0
        for path in sorted(PROJECT_ROOT.glob("**/*.py")):
            if any(part in (".git", "__pycache__", "legacy") for part in path.parts):
                continue
            text = path.read_text(encoding="utf-8")
            if not text.strip():
                continue
            with self.subTest(file=path.relative_to(PROJECT_ROOT).as_posix()):
                self.assertIn(header, text)
                self.assertIn("SPDX-License-Identifier: Apache-2.0", text)
            checked += 1
        self.assertGreater(checked, 15)

    def test_license_file_is_apache_2_and_unmodified(self):
        text = about.license_text()
        self.assertIsNotNone(text, "LICENSE is missing from the project root")
        self.assertIn("Apache License", text)
        self.assertIn("Version 2.0, January 2004", text)
        # The appendix is a template to copy into sources, not a form to fill
        # in; editing it breaks license detection.
        self.assertIn("Copyright [yyyy] [name of copyright owner]", text)
        self.assertEqual(len(text.splitlines()), 201)

    def test_readme_states_the_same_licence(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(about.AUTHOR, readme)
        self.assertIn(about.COPYRIGHT_YEARS, readme)


class ResourceTests(unittest.TestCase):
    def test_resource_path_resolves_next_to_the_package_from_source(self):
        self.assertEqual(about.resource_path("LICENSE"), PROJECT_ROOT / "LICENSE")

    def test_missing_resource_reads_as_none_rather_than_raising(self):
        self.assertIsNone(about._read("NO-SUCH-FILE"))

    def test_third_party_versions_are_reported(self):
        rows = dict((name, version) for name, version, _ in
                    about.installed_versions())
        self.assertEqual(len(rows), len(about.THIRD_PARTY))
        for name in ("matplotlib", "numpy", "pandas"):
            with self.subTest(package=name):
                self.assertRegex(rows[name], r"^\d+\.")

    def test_spec_bundles_the_licence_files(self):
        """A frozen build must carry what the About window shows."""
        spec = (PROJECT_ROOT / "PlottingApp.spec").read_text(encoding="utf-8")
        datas = re.search(r"datas=\[(.*?)\]", spec, re.S)
        self.assertIsNotNone(datas)
        self.assertIn("'LICENSE'", datas.group(1))
        self.assertIn("'NOTICE'", datas.group(1))

    def test_about_module_stays_free_of_gui_code(self):
        """The window lives in gui.guide_window; this module is just facts.

        Keeping it import-light means the build spec and the tests can read the
        identity without pulling in tkinter.
        """
        source = (PROJECT_ROOT / "gui" / "about.py").read_text(encoding="utf-8")
        self.assertNotIn("tkinter", source)
        self.assertNotIn("Toplevel", source)

    def test_spec_reads_its_metadata_from_about(self):
        """The exe's Windows version resource must not be hand-maintained."""
        spec = (PROJECT_ROOT / "PlottingApp.spec").read_text(encoding="utf-8")
        self.assertIn('"gui" / "about.py"', spec)
        self.assertIn("LegalCopyright", spec)


if __name__ == "__main__":
    unittest.main()
