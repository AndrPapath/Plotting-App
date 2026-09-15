# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""The 'Traces' window: rename, hide, scale, delete and pick the X axis."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from .trace import Trace
from .widgets import ScrollableFrame

__all__ = ["TraceWindow"]


class TraceWindow(tk.Toplevel):
    """Editor for the loaded traces.

    Rows are rebuilt from the trace list on every change, which is what makes
    deletion correct: the old version captured the row index in a lambda, so
    every Delete button removed the *last* row and left the list untouched.
    """

    def __init__(
        self,
        parent: tk.Misc,
        traces: list[Trace],
        x_axis: tk.IntVar,
        on_change: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title("Traces")
        self.traces = traces
        self.x_axis = x_axis
        self.on_change = on_change or (lambda: None)

        self._checkbuttons: dict[int, ttk.Checkbutton] = {}

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self._build_toolbar()
        self.body = ScrollableFrame(self)
        self.body.grid(row=1, column=0, sticky="nsew")

        self._x_axis_trace_id = x_axis.trace_add("write", self._on_x_axis_changed)
        self.bind("<Destroy>", self._on_destroy)
        self.populate()

    # -- construction -----------------------------------------------------
    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self, padding=4)
        bar.grid(row=0, column=0, sticky="ew")
        ttk.Button(bar, text="Show all",
                   command=lambda: self._set_all(True)).grid(row=0, column=0, padx=2)
        ttk.Button(bar, text="Hide all",
                   command=lambda: self._set_all(False)).grid(row=0, column=1, padx=2)
        self.count_label = ttk.Label(bar, text="")
        self.count_label.grid(row=0, column=2, padx=8)

    def populate(self) -> None:
        self.body.clear()
        self._checkbuttons = {}
        container = self.body.interior
        container.columnconfigure(0, weight=1)
        for index, trace in enumerate(self.traces):
            self._build_row(container, index, trace)
        self.count_label.configure(text=f"{len(self.traces)} traces")
        self._sync_x_axis_state()
        self._fit_to_contents()

    def _build_row(self, container: tk.Misc, index: int, trace: Trace) -> None:
        frame = ttk.LabelFrame(container, text=f"Trace {index}: {trace.source_name}")
        frame.grid(row=index, column=0, sticky="ew", pady=4, padx=6)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Name:").grid(row=0, column=0, sticky="w", pady=3, padx=3)
        ttk.Entry(frame, textvariable=trace.name).grid(row=0, column=1, sticky="ew",
                                                       pady=3)
        ttk.Label(frame, text="Visible:").grid(row=0, column=2, sticky="w", padx=(8, 0))
        checkbutton = ttk.Checkbutton(frame, variable=trace.visible)
        checkbutton.grid(row=0, column=3, sticky="w")
        self._checkbuttons[index] = checkbutton

        ttk.Radiobutton(frame, text="Set as X axis", variable=self.x_axis,
                        value=index).grid(row=0, column=4, sticky="w", padx=6)

        ttk.Label(frame, text="Scale:").grid(row=1, column=0, sticky="w", pady=3, padx=3)
        ttk.Entry(frame, textvariable=trace.scale, width=12).grid(row=1, column=1,
                                                                  sticky="w", pady=3)
        ttk.Label(frame, text=f"{trace.data.size} points").grid(row=1, column=2,
                                                                columnspan=2, sticky="w")
        ttk.Button(frame, text="Delete",
                   command=lambda t=trace: self._delete(t)).grid(row=1, column=4,
                                                                 sticky="e", padx=6)

    # -- behaviour --------------------------------------------------------
    def _delete(self, trace: Trace) -> None:
        try:
            position = self.traces.index(trace)
        except ValueError:
            return
        del self.traces[position]
        for new_index, remaining in enumerate(self.traces):
            remaining.index = new_index
        current = self.x_axis.get()
        if current >= len(self.traces):
            self.x_axis.set(max(0, len(self.traces) - 1))
        elif position < current:
            self.x_axis.set(current - 1)
        self.populate()
        self.on_change()

    def _set_all(self, visible: bool) -> None:
        for trace in self.traces:
            trace.set_visible(visible)
        self.on_change()

    def _on_x_axis_changed(self, *_args) -> None:
        self._sync_x_axis_state()
        self.on_change()

    def _sync_x_axis_state(self) -> None:
        """Grey out the Visible box of the trace that supplies the X axis.

        The stored value is deliberately left alone: the plot modules skip the
        X trace anyway, so picking a different X axis brings the previous one
        back as a curve instead of silently leaving it hidden.
        """
        x_index = self.x_axis.get()
        for index in range(len(self.traces)):
            checkbutton = self._checkbuttons.get(index)
            if checkbutton is None or not checkbutton.winfo_exists():
                continue
            checkbutton.state(["disabled"] if index == x_index else ["!disabled"])

    def _fit_to_contents(self) -> None:
        self.update_idletasks()
        width = max(self.winfo_reqwidth() + 40, 460)
        height = min(max(self.winfo_reqheight(), 220), 700)
        self.geometry(f"{width}x{height}")
        self.minsize(width, 220)
        self.resizable(False, True)

    def _on_destroy(self, event: tk.Event) -> None:
        if event.widget is not self:
            return
        try:
            self.x_axis.trace_remove("write", self._x_axis_trace_id)
        except tk.TclError:  # pragma: no cover - interpreter teardown
            pass

