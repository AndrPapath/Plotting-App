# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""The GUI's trace model: one data column plus the widgets' state."""

from __future__ import annotations

import tkinter as tk

import numpy as np

from plotting.options import OptionError, OptionSpec

__all__ = ["Trace", "traces_from_series"]

_SCALE_SPEC = OptionSpec("Scale", "float", 1.0)


class Trace:
    """A named column of numbers with its per-trace display settings.

    Implements ``plotting.traces.TraceLike`` so the plot modules never see a
    tkinter object.
    """

    def __init__(self, name: str, data: np.ndarray, index: int = 0) -> None:
        self.data = np.asarray(data, dtype=float)
        self.index = index
        self.source_name = str(name)
        self.name = tk.StringVar(value=str(name))
        self.visible = tk.BooleanVar(value=True)
        self.scale = tk.StringVar(value="1")
        self.twinx = tk.BooleanVar(value=False)

    # -- TraceLike --------------------------------------------------------
    def get_name(self) -> str:
        return self.name.get()

    def get_data(self) -> np.ndarray:
        return self.data

    def get_scale(self) -> float:
        raw = self.scale.get()
        try:
            return float(_SCALE_SPEC.coerce(raw))
        except OptionError:
            raise OptionError(
                f"Trace {self.get_name()!r}: scale {raw!r} is not a number."
            ) from None

    def is_visible(self) -> bool:
        return bool(self.visible.get())

    # -- convenience ------------------------------------------------------
    def set_visible(self, value: bool) -> None:
        self.visible.set(bool(value))

    def on_twin_x(self) -> bool:
        return bool(self.twinx.get())

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Trace {self.get_name()!r} n={self.data.size}>"


def traces_from_series(series: list[tuple[str, np.ndarray]]) -> list[Trace]:
    """Build traces from :func:`gui.dataio.load_series` output."""
    return [Trace(name, values, index) for index, (name, values) in enumerate(series)]
