# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""Builds the side panel from a plot module's option specs."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Sequence

from plotting.options import OptionSpec, Options, specs_by_label

from .widgets import Tooltip

__all__ = ["OptionPanel"]

_ENTRY_WIDTH = 14


class OptionPanel:
    """Widgets for one plot module, and the typed values they hold.

    Every field is backed by a :class:`tkinter.StringVar` (or ``BooleanVar``)
    rather than ``IntVar``/``DoubleVar``: those raise ``TclError`` deep inside
    Tk as soon as a user types something unparseable. Conversion happens once,
    in :meth:`options`, where a bad value becomes a readable message.
    """

    def __init__(self, parent: tk.Misc) -> None:
        self.parent = parent
        self.specs: dict[str, OptionSpec] = {}
        self.variables: dict[str, tk.Variable] = {}

    def build(self, specs: Sequence[OptionSpec]) -> None:
        """Replace the current widgets with fields for ``specs``."""
        for child in self.parent.winfo_children():
            child.destroy()
        self.specs = specs_by_label(specs)
        self.variables = {}
        self.parent.columnconfigure(1, weight=1)

        row = 0
        for spec in specs:
            if spec.hidden:
                self.variables[spec.label] = tk.StringVar(value=str(spec.default))
                continue
            label = ttk.Label(self.parent, text=spec.label)
            label.grid(row=row, column=0, sticky="w", padx=(6, 4), pady=3)
            widget, variable = self._make_widget(spec)
            widget.grid(row=row, column=1, sticky="ew", padx=(0, 6), pady=3)
            self.variables[spec.label] = variable
            if spec.help:
                Tooltip(label, spec.help)
                Tooltip(widget, spec.help)
            row += 1

    def _make_widget(self, spec: OptionSpec) -> tuple[tk.Widget, tk.Variable]:
        if spec.kind == "bool":
            variable: tk.Variable = tk.BooleanVar(value=bool(spec.default))
            return ttk.Checkbutton(self.parent, variable=variable), variable

        variable = tk.StringVar(value=str(spec.default))
        if spec.kind == "choice":
            # ttk.OptionMenu takes the default as its third argument; passing
            # only *choices silently swallowed the first entry of the list.
            return (
                ttk.OptionMenu(self.parent, variable, str(spec.default), *spec.choices),
                variable,
            )
        if spec.kind == "int":
            return (
                ttk.Spinbox(
                    self.parent,
                    textvariable=variable,
                    from_=spec.minimum if spec.minimum is not None else 0,
                    to=spec.maximum if spec.maximum is not None else 10_000,
                    width=_ENTRY_WIDTH,
                ),
                variable,
            )
        return ttk.Entry(self.parent, textvariable=variable, width=_ENTRY_WIDTH), variable

    # -- values -----------------------------------------------------------
    def raw_values(self) -> dict[str, Any]:
        return {label: var.get() for label, var in self.variables.items()}

    def set_value(self, label: str, value: Any) -> None:
        """Update one field (used for state owned elsewhere, e.g. the X axis)."""
        variable = self.variables.get(label)
        if variable is None:
            return
        variable.set(value if isinstance(variable, tk.BooleanVar) else str(value))

    def options(self, **overrides: Any) -> Options:
        """Return the panel as typed options, raising ``OptionError`` on bad input."""
        values = self.raw_values()
        values.update(overrides)
        return Options.from_specs(list(self.specs.values()), values)
