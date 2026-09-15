# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""Every mode documents itself, and the docs stay in step with the options."""

import sys as _sys
from pathlib import Path as _Path

# Runnable straight from the editor: make the project root importable.
_ROOT = str(_Path(__file__).resolve().parents[1])
if _ROOT not in _sys.path:
    _sys.path.insert(0, _ROOT)

import unittest

import plotting
from plotting.guide import Guide


class GuideTests(unittest.TestCase):
    def test_every_mode_has_a_usable_guide(self):
        for name in plotting.mode_names():
            with self.subTest(mode=name):
                guide = plotting.guide_for(name)
                self.assertIsInstance(guide, Guide)
                self.assertGreater(len(guide.summary), 40)
                headings = [heading for heading, _ in guide.sections()]
                self.assertEqual(
                    headings, ["Expected data layout", "Step by step", "Tips"])

    def test_guides_reference_real_option_labels(self):
        """A tip naming an option must name one the panel actually has."""
        # Options unique to one mode; a typo in a guide is caught here.
        watched = {
            "XY Plot": ["Scale Y Axis", "Axes have Trace Color", "Manual limits (X)"],
            "Parametric": ["Parameter's Name", "Parameter's Unit",
                           "Parameter's Scale", "Cycle Line Styles"],
            "Paired Columns": ["Column Order", "Cycle Line Styles"],
            "Histogram": ["Value Scale", "Number of Bins", "Decimals", "Grid Axis",
                          "Percent X Axis", "Bar Color", "Monte Carlo Mode"],
        }
        for mode, labels in watched.items():
            module = plotting.load_mode(mode)
            available = {spec.label for spec in module.get_option_specs()}
            text = " ".join(
                [plotting.guide_for(mode).summary]
                + [item for _, items in plotting.guide_for(mode).sections()
                   for item in items]
            )
            for label in labels:
                with self.subTest(mode=mode, option=label):
                    self.assertIn(label, available)  # the option exists
                    self.assertIn(label, text)       # and the guide mentions it

    def test_fallback_guide_for_a_module_without_one(self):
        class Bare:
            __doc__ = "A module with no GUIDE."

        original = plotting._loaded.get("XY Plot")
        plotting._loaded["XY Plot"] = Bare()
        try:
            self.assertEqual(plotting.guide_for("XY Plot").summary,
                             "A module with no GUIDE.")
        finally:
            if original is not None:
                plotting._loaded["XY Plot"] = original
            else:  # pragma: no cover - only if the mode was never loaded
                del plotting._loaded["XY Plot"]

    def test_unknown_mode_has_no_guide(self):
        with self.assertRaises(plotting.PlottingError):
            plotting.guide_for("Sankey")


if __name__ == "__main__":
    unittest.main()
