# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""File loading: headers, separators, junk columns and unreadable files."""

import sys as _sys
from pathlib import Path as _Path

# Runnable straight from the editor: make the project root importable.
_ROOT = str(_Path(__file__).resolve().parents[1])
if _ROOT not in _sys.path:
    _sys.path.insert(0, _ROOT)

import os
import tempfile
import unittest

import numpy as np

from gui.dataio import DataLoadError, load_series, load_table


class TempFileMixin:
    def write(self, name, content):
        path = os.path.join(self.directory.name, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return path

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)


class LoadTableTests(TempFileMixin, unittest.TestCase):
    def test_csv_with_header(self):
        path = self.write("a.csv", "time,vout\n0,1\n1,2\n")
        frame = load_table(path)
        self.assertEqual(list(frame.columns), ["time", "vout"])
        self.assertEqual(frame.shape, (2, 2))

    def test_csv_without_header_gets_generic_names(self):
        path = self.write("b.csv", "0,1\n1,2\n2,3\n")
        frame = load_table(path)
        self.assertEqual(list(frame.columns), ["Column1", "Column2"])
        self.assertEqual(frame.shape, (3, 2))

    def test_whitespace_separated_text(self):
        path = self.write("c.txt", "time   vout\n0   1.5\n1   2.5\n")
        frame = load_table(path)
        self.assertEqual(list(frame.columns), ["time", "vout"])

    def test_semicolon_csv_is_sniffed(self):
        path = self.write("d.csv", "time;vout\n0;1\n1;2\n")
        frame = load_table(path)
        self.assertEqual(frame.shape[1], 2)

    def test_missing_and_empty_files_are_reported(self):
        with self.assertRaises(DataLoadError):
            load_table(os.path.join(self.directory.name, "nope.csv"))
        with self.assertRaises(DataLoadError):
            load_table(self.write("empty.csv", ""))
        with self.assertRaises(DataLoadError):
            load_table("")


class LoadSeriesTests(TempFileMixin, unittest.TestCase):
    def test_numeric_columns_become_float_arrays(self):
        path = self.write("a.csv", "time,vout\n0,1\n1,2\n")
        loaded = load_series(path)
        names = [name for name, _ in loaded.series]
        self.assertEqual(names, ["time", "vout"])
        self.assertEqual(loaded.series[1][1].dtype, np.dtype(float))
        self.assertEqual(loaded.skipped, [])

    def test_text_columns_are_skipped_not_fatal(self):
        path = self.write("a.csv", "time,note,vout\n0,start,1\n1,end,2\n")
        loaded = load_series(path)
        self.assertEqual(loaded.skipped, ["note"])
        self.assertEqual([name for name, _ in loaded.series], ["time", "vout"])

    def test_partially_numeric_column_keeps_nans(self):
        path = self.write("a.csv", "time,vout\n0,1\n1,oops\n")
        loaded = load_series(path)
        values = dict(loaded.series)["vout"]
        self.assertTrue(np.isnan(values[1]))

    def test_file_without_any_numbers_is_rejected(self):
        path = self.write("a.csv", "note,label\nfoo,bar\nbaz,qux\n")
        with self.assertRaises(DataLoadError):
            load_series(path)


if __name__ == "__main__":
    unittest.main()
