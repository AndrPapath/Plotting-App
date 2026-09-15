# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""Option coercion: the layer that used to let bad input reach matplotlib."""

import sys as _sys
from pathlib import Path as _Path

# Runnable straight from the editor: make the project root importable.
_ROOT = str(_Path(__file__).resolve().parents[1])
if _ROOT not in _sys.path:
    _sys.path.insert(0, _ROOT)

import unittest

from plotting.options import OptionError, OptionSpec, Options, ensure_options


class OptionSpecTests(unittest.TestCase):
    def test_int_accepts_numeric_strings(self):
        spec = OptionSpec("Font Size", "int", 14, minimum=1, maximum=72)
        self.assertEqual(spec.coerce("18"), 18)
        self.assertEqual(spec.coerce(18.0), 18)

    def test_empty_entry_falls_back_to_default(self):
        spec = OptionSpec("Min X", "float", 0.5)
        self.assertEqual(spec.coerce(""), 0.5)
        self.assertEqual(spec.coerce("   "), 0.5)

    def test_rejects_garbage_with_a_readable_message(self):
        spec = OptionSpec("Line Width", "float", 1.0)
        with self.assertRaises(OptionError) as caught:
            spec.coerce("two")
        self.assertIn("Line Width", str(caught.exception))

    def test_rejects_out_of_range_and_non_finite(self):
        spec = OptionSpec("Font Size", "int", 14, minimum=1, maximum=72)
        with self.assertRaises(OptionError):
            spec.coerce(0)
        with self.assertRaises(OptionError):
            spec.coerce(100)
        with self.assertRaises(OptionError):
            OptionSpec("Scale", "float", 1.0).coerce("nan")

    def test_int_rejects_fractions(self):
        with self.assertRaises(OptionError):
            OptionSpec("Number of Bins", "int", 5).coerce("2.5")

    def test_bool_reads_widget_strings(self):
        spec = OptionSpec("Grid", "bool", True)
        self.assertTrue(spec.coerce("1"))
        self.assertFalse(spec.coerce("0"))
        self.assertFalse(spec.coerce(""))
        with self.assertRaises(OptionError):
            spec.coerce("maybe")

    def test_choice_must_be_known(self):
        spec = OptionSpec("Legend Location", "choice", "best", choices=("best", "upper left"))
        self.assertEqual(spec.coerce("upper left"), "upper left")
        with self.assertRaises(OptionError):
            spec.coerce("nowhere")

    def test_invalid_default_fails_at_definition_time(self):
        with self.assertRaises(OptionError):
            OptionSpec("Font Size", "int", 0, minimum=1)


class OptionsTests(unittest.TestCase):
    SPECS = [
        OptionSpec("Plot Title", "text", ""),
        OptionSpec("Font Size", "int", 14, minimum=1),
        OptionSpec("Scale X Axis", "float", 1.0),
        OptionSpec("Grid", "bool", True),
    ]

    def test_missing_keys_use_spec_defaults(self):
        options = Options.from_specs(self.SPECS, {"Plot Title": "Vout"})
        self.assertEqual(options.text("Plot Title"), "Vout")
        self.assertEqual(options.integer("Font Size"), 14)
        self.assertTrue(options.flag("Grid"))

    def test_unknown_labels_fall_back_to_the_caller_default(self):
        options = Options.from_specs(self.SPECS, {})
        self.assertEqual(options.number("Not A Field", 3.5), 3.5)

    def test_with_values_coerces_injected_state(self):
        options = Options.from_specs(self.SPECS, {}).with_values(**{"Font Size": "20"})
        self.assertEqual(options.integer("Font Size"), 20)

    def test_ensure_options_wraps_plain_dicts(self):
        options = ensure_options({"Font Size": "9"}, self.SPECS)
        self.assertEqual(options.integer("Font Size"), 9)
        self.assertIs(ensure_options(options, self.SPECS), options)


if __name__ == "__main__":
    unittest.main()
