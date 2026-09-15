# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""The trace interface the plotting modules work against.

The GUI's ``Trace`` is backed by Tk variables; this module defines the small
protocol the plotting code actually needs, plus a plain implementation used by
tests and scripts. Nothing in ``plotting`` imports tkinter as a result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence, runtime_checkable

import numpy as np

__all__ = ["TraceLike", "SimpleTrace", "visible_traces", "values_of", "resolve_x_index"]


@runtime_checkable
class TraceLike(Protocol):
    """One named column of data with the display state the user controls."""

    def get_name(self) -> str: ...

    def get_data(self) -> np.ndarray: ...

    def get_scale(self) -> float: ...

    def is_visible(self) -> bool: ...


@dataclass
class SimpleTrace:
    """A :class:`TraceLike` with no GUI attached."""

    name: str
    data: np.ndarray
    scale: float = 1.0
    visible: bool = True
    index: int = 0

    def __post_init__(self) -> None:
        self.data = np.asarray(self.data, dtype=float)

    def get_name(self) -> str:
        return self.name

    def get_data(self) -> np.ndarray:
        return self.data

    def get_scale(self) -> float:
        return float(self.scale)

    def is_visible(self) -> bool:
        return bool(self.visible)


def values_of(trace: TraceLike, extra_scale: float = 1.0) -> np.ndarray:
    """Return a trace's samples as floats, with its own scale applied."""
    data = np.asarray(trace.get_data(), dtype=float)
    factor = float(trace.get_scale()) * float(extra_scale)
    return data if factor == 1.0 else data * factor


def visible_traces(
    traces: Sequence[TraceLike], skip_index: int | None = None
) -> list[tuple[int, TraceLike]]:
    """Return ``(index, trace)`` pairs the user asked to see."""
    return [
        (i, trace)
        for i, trace in enumerate(traces)
        if i != skip_index and trace.is_visible()
    ]


def resolve_x_index(traces: Sequence[TraceLike], requested: int) -> int:
    """Clamp a requested X-axis index onto the traces we actually have."""
    if not traces:
        raise IndexError("no traces loaded")
    if 0 <= requested < len(traces):
        return requested
    return 0
