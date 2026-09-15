# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""Small reusable tkinter widgets."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

__all__ = ["ScrollableFrame", "Tooltip"]


class ScrollableFrame(ttk.Frame):
    """A vertically scrollable container.

    Put children into :attr:`interior`. The mouse wheel is captured only while
    the pointer is over this widget, so several scrollable frames can coexist -
    the previous ``bind_all`` version let whichever frame was created last
    steal every wheel event in the application.
    """

    def __init__(self, container: tk.Misc, **kwargs) -> None:
        super().__init__(container, **kwargs)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical",
                                       command=self.canvas.yview)
        self.interior = ttk.Frame(self.canvas)
        self._window = self.canvas.create_window((0, 0), window=self.interior,
                                                 anchor="nw")

        self.interior.bind("<Configure>", self._on_interior_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.bind("<Enter>", self._grab_wheel)
        self.bind("<Leave>", self._release_wheel)
        self.bind("<Destroy>", lambda _event: self._release_wheel())

    # -- geometry ---------------------------------------------------------
    def _on_interior_configure(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        # Let the contents use the full width instead of their requested width.
        self.canvas.itemconfigure(self._window, width=event.width)

    # -- mouse wheel ------------------------------------------------------
    def _grab_wheel(self, _event: tk.Event | None = None) -> None:
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _release_wheel(self, _event: tk.Event | None = None) -> None:
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            try:
                self.canvas.unbind_all(sequence)
            except tk.TclError:  # during interpreter teardown
                pass

    def _on_mousewheel(self, event: tk.Event) -> str | None:
        if not self._can_scroll():
            return None
        if getattr(event, "num", None) in (4, 5):  # X11
            step = -1 if event.num == 4 else 1
        else:  # Windows / macOS
            step = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(step, "units")
        return "break"

    def _can_scroll(self) -> bool:
        box = self.canvas.bbox("all")
        return bool(box) and box[3] > self.canvas.winfo_height()

    def clear(self) -> None:
        """Destroy every child of :attr:`interior`."""
        for child in self.interior.winfo_children():
            child.destroy()
        self.canvas.yview_moveto(0.0)


class Tooltip:
    """Minimal hover tooltip; used to surface each option's help text."""

    DELAY_MS = 500

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self._after_id: str | None = None
        self._window: tk.Toplevel | None = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event: tk.Event) -> None:
        self._cancel()
        self._after_id = self.widget.after(self.DELAY_MS, self._show)

    def _cancel(self) -> None:
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None

    def _show(self) -> None:
        if self._window is not None or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self._window = tk.Toplevel(self.widget)
        self._window.wm_overrideredirect(True)
        self._window.wm_geometry(f"+{x}+{y}")
        tk.Label(self._window, text=self.text, justify="left", relief="solid",
                 borderwidth=1, background="#ffffe0", padx=6, pady=3).pack()

    def _hide(self, _event: tk.Event | None = None) -> None:
        self._cancel()
        if self._window is not None:
            self._window.destroy()
            self._window = None
