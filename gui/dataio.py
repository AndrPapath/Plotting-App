# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""Loading measurement files into plain numeric series.

Kept free of tkinter and matplotlib so the file handling can be tested on its
own - it is where most of the "it crashed on my file" reports come from.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
import pandas as pd

__all__ = [
    "DataLoadError",
    "LoadedData",
    "SUPPORTED_EXTENSIONS",
    "FILE_TYPES",
    "load_table",
    "load_series",
]


class DataLoadError(Exception):
    """A file could not be turned into numeric columns."""


#: Extensions we know how to read, grouped by the reader they need.
_DELIMITED = (".csv", ".tsv")
_WHITESPACE = (".txt", ".dat", ".out")
_EXCEL = (".xlsx", ".xls", ".xlsm")
SUPPORTED_EXTENSIONS = _DELIMITED + _WHITESPACE + _EXCEL

FILE_TYPES = [
    ("All supported", " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)),
    ("Comma-separated values", "*.csv *.tsv"),
    ("Text / data", "*.txt *.dat *.out"),
    ("Excel files", "*.xlsx *.xls *.xlsm"),
    ("All files", "*.*"),
]


@dataclass
class LoadedData:
    """Numeric columns of a file, plus what had to be left out."""

    path: str
    series: list[tuple[str, np.ndarray]]
    skipped: list[str]

    @property
    def is_empty(self) -> bool:
        return not self.series


def _looks_numeric(token: str) -> bool:
    try:
        float(token)
    except ValueError:
        return False
    return True


def _has_header(path: str, separator: str | None) -> bool:
    """True when the first non-blank line is not all numbers."""
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            tokens = line.split(separator) if separator else line.split()
            tokens = [token.strip() for token in tokens if token.strip()]
            return bool(tokens) and not all(_looks_numeric(t) for t in tokens)
    return False


def _generic_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame.columns = [f"Column{i + 1}" for i in range(frame.shape[1])]
    return frame


def load_table(path: str) -> pd.DataFrame:
    """Read a measurement file into a DataFrame, guessing layout as needed."""
    if not path:
        raise DataLoadError("No file selected.")
    if not os.path.isfile(path):
        raise DataLoadError(f"File not found: {path}")
    if os.path.getsize(path) == 0:
        raise DataLoadError(f"File is empty: {os.path.basename(path)}")

    extension = os.path.splitext(path)[1].lower()
    try:
        if extension in _EXCEL:
            frame = pd.read_excel(path)
        elif extension in _WHITESPACE:
            header = 0 if _has_header(path, None) else None
            frame = pd.read_csv(path, sep=r"\s+", engine="python", header=header)
            if header is None:
                frame = _generic_columns(frame)
        else:
            header = 0 if _has_header(path, ",") else None
            frame = pd.read_csv(path, header=header)
            if frame.shape[1] == 1:
                # A single column usually means the separator was not a comma.
                sniffed = pd.read_csv(path, sep=None, engine="python", header=header)
                if sniffed.shape[1] > 1:
                    frame = sniffed
            if header is None:
                frame = _generic_columns(frame)
    except DataLoadError:
        raise
    except (OSError, ValueError, pd.errors.ParserError, ImportError) as error:
        raise DataLoadError(
            f"Could not read {os.path.basename(path)}: {error}"
        ) from error

    if frame.empty or frame.shape[1] == 0:
        raise DataLoadError(f"No data rows found in {os.path.basename(path)}.")
    return frame


def load_series(path: str) -> LoadedData:
    """Load a file and return its numeric columns as ``(name, values)`` pairs.

    Columns that hold no numbers at all (comments, text annotations) are
    reported in ``skipped`` instead of blowing up later inside matplotlib.
    """
    frame = load_table(path)
    series: list[tuple[str, np.ndarray]] = []
    skipped: list[str] = []
    for name in frame.columns:
        values = pd.to_numeric(frame[name], errors="coerce").to_numpy(dtype=float)
        if np.isnan(values).all():
            skipped.append(str(name))
            continue
        series.append((str(name), values))
    if not series:
        raise DataLoadError(
            f"{os.path.basename(path)} has no numeric columns "
            f"(found: {', '.join(skipped) or 'nothing'})."
        )
    return LoadedData(path=path, series=series, skipped=skipped)
