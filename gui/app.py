# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""The main window of the CSV plotting tool."""

from __future__ import annotations

if __name__ == "__main__" and __package__ in (None, ""):
    # Launched as a loose script (VS Code's Run button, `python gui/app.py`).
    # Python puts *this* folder on sys.path, not the project root, so neither
    # `plotting` nor the `gui` package itself can be imported. Put the root on
    # the path and hand over to the properly imported module.
    import os as _os
    import sys as _sys

    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from gui.app import main as _main

    _main()
    _sys.exit(0)

import os
import sys
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from types import ModuleType

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("TkAgg")

from matplotlib.backends.backend_tkagg import (  # noqa: E402  (after use())
    FigureCanvasTkAgg,
    NavigationToolbar2Tk,
)
from matplotlib.figure import Figure  # noqa: E402

import plotting  # noqa: E402
from plotting.options import X_AXIS_INDEX, PlottingError  # noqa: E402
from plotting.styling import clear_legends  # noqa: E402

from .about import APP_NAME  # noqa: E402
from .dataio import FILE_TYPES, DataLoadError, load_series  # noqa: E402
from .guide_window import INFO_GLYPH, GuideWindow  # noqa: E402
from .panel import OptionPanel  # noqa: E402
from .trace import Trace, traces_from_series  # noqa: E402
from .trace_window import TraceWindow  # noqa: E402
from .widgets import ScrollableFrame, Tooltip  # noqa: E402

__all__ = ["PlottingApp", "main"]

_MIN_CANVAS = (420, 320)
_MIN_PANEL = 240
_STYLES = ("default", "fivethirtyeight", "ggplot", "bmh", "seaborn-v0_8-talk")
#: Save formats, and the matplotlib backend each one needs. savefig() imports
#: that backend by name, so a frozen build must declare them as hidden imports
#: - tests/test_about.py checks the spec against this mapping.
SAVE_FORMATS = {
    "pdf": "matplotlib.backends.backend_pdf",
    "png": "matplotlib.backends.backend_agg",
    "svg": "matplotlib.backends.backend_svg",
}
_SAVE_TYPES = [
    ("PDF", "*.pdf"),
    ("PNG", "*.png"),
    ("SVG", "*.svg"),
    ("All files", "*.*"),
]


class PlottingApp(tk.Tk):
    """Loads a data file, then draws it with the selected plot module.

    Every user action goes through :meth:`_guard`, so a bad entry box or an
    unreadable file produces a message instead of a traceback on a console the
    user never sees.
    """

    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)

        self.traces: list[Trace] = []
        self.source_path: str = ""
        self.trace_window: TraceWindow | None = None
        self.guide_window: GuideWindow | None = None
        self.plot_module: ModuleType | None = None

        self.x_axis = tk.IntVar(value=0)
        self.mode = tk.StringVar(value=plotting.mode_names()[0])
        self.style = tk.StringVar(value=_STYLES[1])
        self.status = tk.StringVar(value="Load a file to begin.")

        self._build_layout()
        self._build_top_bar()
        self._build_side_panel()
        self._build_status_bar()
        self._create_canvas()
        self._bind_shortcuts()
        self.switch_mode(self.mode.get())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # -- construction -----------------------------------------------------
    def _build_layout(self) -> None:
        self.rowconfigure(1, weight=1, minsize=_MIN_CANVAS[1])
        self.columnconfigure(0, weight=1, minsize=_MIN_CANVAS[0])
        self.columnconfigure(1, minsize=_MIN_PANEL)
        self.minsize(_MIN_CANVAS[0] + _MIN_PANEL + 20, _MIN_CANVAS[1] + 120)

    def _build_top_bar(self) -> None:
        bar = ttk.Frame(self, padding=4)
        bar.grid(row=0, column=0, sticky="nsew")
        buttons = (
            ("Load", self.load_file),
            ("Traces", self.show_trace_window),
            ("Plot", self.plot_draw),
            ("Replace", self.plot_replace),
            ("Clear", self.plot_clear),
            ("Refresh", self.plot_refresh),
            ("Save", self.plot_save),
        )
        for column, (text, command) in enumerate(buttons):
            ttk.Button(bar, text=text, width=9,
                       command=self._guarded(text, command)).grid(row=0, column=column,
                                                                  padx=2)

        selector = ttk.Frame(self, padding=4)
        selector.grid(row=0, column=1, sticky="nsew")
        selector.columnconfigure(1, weight=1)
        ttk.Label(selector, text="Mode").grid(row=0, column=0, sticky="w")
        ttk.OptionMenu(selector, self.mode, self.mode.get(), *plotting.mode_names(),
                       command=self._guarded("Mode", self.switch_mode)).grid(
            row=0, column=1, sticky="ew")
        info = ttk.Button(selector, text=INFO_GLYPH, width=3,
                          command=self._guarded("Guide", self.show_guide))
        info.grid(row=0, column=2, sticky="w", padx=(4, 0))
        Tooltip(info, "Guides for each plot mode, plus about and licence "
                     "(F1)")

        ttk.Label(selector, text="Style").grid(row=1, column=0, sticky="w")
        ttk.OptionMenu(selector, self.style, self.style.get(), *_STYLES,
                       command=self._guarded("Style", self.switch_style)).grid(
            row=1, column=1, sticky="ew")

    def _build_side_panel(self) -> None:
        self.side_panel = ScrollableFrame(self, relief="sunken", borderwidth=2)
        self.side_panel.grid(row=1, column=1, sticky="nsew")
        self.panel = OptionPanel(self.side_panel.interior)

    def _build_status_bar(self) -> None:
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w",
                  padding=(6, 2)).grid(row=3, column=0, columnspan=2, sticky="ew")

    def _create_canvas(self) -> None:
        with plt.style.context(self.style.get()):
            self.figure = Figure(figsize=(6, 4.5), dpi=100, layout="constrained")
            self.axes = self.figure.add_subplot()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")
        self.toolbar = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.grid(row=2, column=0, sticky="ew")
        self.canvas.draw_idle()

    def _bind_shortcuts(self) -> None:
        for sequence, name, command in (
            ("<Control-o>", "Load", self.load_file),
            ("<Control-s>", "Save", self.plot_save),
            ("<Control-r>", "Replace", self.plot_replace),
            ("<F5>", "Refresh", self.plot_refresh),
            ("<F1>", "Guide", self.show_guide),
            ("<Shift-F1>", "About", self.show_about),
        ):
            handler = self._guarded(name, command)
            self.bind(sequence, lambda _event, run=handler: run())

    # -- error handling ---------------------------------------------------
    def _guarded(self, name: str, command):
        """Wrap a callback so failures become messages, not tracebacks."""

        def run(*args):
            try:
                return self._invoke(command, args)
            except (PlottingError, DataLoadError) as error:
                self.set_status(str(error))
                messagebox.showwarning(name, str(error), parent=self)
            except Exception as error:  # unexpected: show and log the details
                traceback.print_exc()
                self.set_status(f"{name} failed: {error}")
                messagebox.showerror(
                    name,
                    f"{type(error).__name__}: {error}\n\n"
                    "The full traceback was written to the console.",
                    parent=self,
                )
            return None

        return run

    @staticmethod
    def _invoke(command, args):
        # ttk.OptionMenu passes the chosen value; buttons pass nothing.
        return command(*args) if args else command()

    def set_status(self, message: str) -> None:
        self.status.set(message)

    # -- modes and options ------------------------------------------------
    def switch_mode(self, mode: str | None = None) -> None:
        """Load the selected plot module and rebuild the side panel."""
        name = mode or self.mode.get()
        self.plot_module = plotting.load_mode(name)
        self.panel.build(self.plot_module.get_option_specs())
        if self.guide_window is not None and self.guide_window.winfo_exists():
            self.guide_window.show(name)
        self.set_status(f"Mode: {name}")

    def show_about(self) -> None:
        """Open the info window on its About & licence page."""
        self._open_guide_window().show_about()

    def show_guide(self) -> None:
        """Open the info window on the current mode's guide."""
        self._open_guide_window().show(self.mode.get())

    def _open_guide_window(self) -> GuideWindow:
        if self.guide_window is None or not self.guide_window.winfo_exists():
            self.guide_window = GuideWindow(self, self.mode.get())
        return self.guide_window

    def switch_style(self, style: str | None = None) -> None:
        """Rebuild the figure under a new matplotlib style, keeping the data."""
        if style:
            self.style.set(style)
        had_content = bool(self.axes.lines or self.axes.patches)
        self.canvas.get_tk_widget().destroy()
        self.toolbar.destroy()
        plt.close(self.figure)
        self._create_canvas()
        if had_content and self.traces:
            self.plot_replace()

    def current_options(self):
        return self.panel.options(**{X_AXIS_INDEX: self.x_axis.get()})

    def _require_module(self) -> ModuleType:
        if self.plot_module is None:
            raise PlottingError("No plot mode selected.")
        return self.plot_module

    # -- data -------------------------------------------------------------
    def load_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Open a data file",
            filetypes=FILE_TYPES,
            initialdir=os.path.dirname(self.source_path) or os.getcwd(),
            parent=self,
        )
        if not path:  # the user cancelled - leave the current data alone
            return
        loaded = load_series(path)
        self.source_path = loaded.path
        self.traces = traces_from_series(loaded.series)
        self.x_axis.set(0)
        message = f"Loaded {len(self.traces)} traces from {os.path.basename(path)}"
        if loaded.skipped:
            message += f" (skipped non-numeric: {', '.join(loaded.skipped)})"
        self.set_status(message)
        self.show_trace_window()

    def show_trace_window(self) -> None:
        if not self.traces:
            raise PlottingError("No data loaded - use Load to open a file first.")
        if self.trace_window is not None and self.trace_window.winfo_exists():
            self.trace_window.destroy()
        self.trace_window = TraceWindow(self, self.traces, self.x_axis,
                                        on_change=self._on_traces_changed)

    def _on_traces_changed(self) -> None:
        if not self.traces:
            self.set_status("All traces deleted.")

    # -- plotting ---------------------------------------------------------
    def plot_draw(self) -> None:
        """Draw on top of whatever is already on the axes."""
        module = self._require_module()
        options = self.current_options()
        with plt.style.context(self.style.get()):
            module.draw(self.axes, self.traces, options)
        self.canvas.draw_idle()
        self.set_status(f"{self.mode.get()}: {self._artist_summary()}")

    def _artist_summary(self) -> str:
        for count, noun in ((len(self.axes.lines), "curve"), (len(self.axes.patches), "bar")):
            if count:
                return f"{count} {noun}{'s' if count != 1 else ''}"
        return "nothing drawn"

    def plot_replace(self) -> None:
        """Clear first, then draw - the usual 'update the plot' action."""
        self._clear_axes()
        self.plot_draw()

    def plot_clear(self) -> None:
        self._clear_axes()
        self.canvas.draw_idle()
        self.set_status("Cleared.")

    def _clear_axes(self) -> None:
        clear_legends(self.axes)
        self.axes.clear()

    def plot_refresh(self) -> None:
        """Re-apply the cosmetic options without redrawing the data."""
        module = self._require_module()
        module.refresh(self.axes, self.current_options())
        self.canvas.draw_idle()
        self.set_status("Refreshed.")

    def plot_save(self) -> None:
        default_name = "plot.pdf"
        if self.source_path:
            default_name = os.path.splitext(os.path.basename(self.source_path))[0] + ".pdf"
        path = filedialog.asksaveasfilename(
            title="Save figure",
            defaultextension=".pdf",
            initialfile=default_name,
            initialdir=os.path.dirname(self.source_path) or os.getcwd(),
            filetypes=_SAVE_TYPES,
            parent=self,
        )
        if not path:
            return
        try:
            self.figure.savefig(path)
        except OSError as error:
            raise PlottingError(f"Could not save to {path}: {error}") from error
        self.set_status(f"Saved {os.path.basename(path)}")

    # -- teardown ---------------------------------------------------------
    def _on_close(self) -> None:
        plt.close(self.figure)
        self.destroy()


def main(argv: list[str] | None = None) -> None:
    """Start the GUI, or run the post-build check with ``--selftest``."""
    arguments = sys.argv[1:] if argv is None else argv
    if "--selftest" in arguments:
        from .selftest import run_selftest

        rest = [item for item in arguments if item != "--selftest"]
        raise SystemExit(run_selftest(rest[0] if rest else None))
    PlottingApp().mainloop()


if __name__ == "__main__":
    main()
