# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""Histograms of one or more traces.

Two layouts share the panel:

* **Grouped** - every visible trace is binned over one common set of bins and
  drawn as a group of bars per bin, for comparing runs side by side.
* **Monte Carlo** - the classic filled-plus-outlined histogram of a single
  sweep, with a percentage formatted X axis.
"""

from __future__ import annotations

import matplotlib as mpl
import numpy as np
from matplotlib.axes import Axes
from matplotlib.ticker import AutoMinorLocator, PercentFormatter

from .guide import Guide
from .options import OptionSpec, Options, PlottingError, ensure_options
from .styling import apply_axes_style, font_specs, grid_spec, legend_specs, log_specs, title_specs
from .traces import TraceLike, values_of, visible_traces

DISPLAY_NAME = "Histogram"


GUIDE = Guide(
    summary=(
        "Bins the visible traces. Grouped mode compares several runs over one "
        "shared set of bins; Monte Carlo mode draws the single filled-and-"
        "outlined distribution used for yield and accuracy plots."
    ),
    data_layout=(
        "One column per run; each row is one iteration or sample.",
        "Columns may be of different lengths - blank cells and non-finite "
        "values are ignored rather than binned.",
        "Every value is multiplied by Value Scale (default 100) before "
        "binning, so an accuracy of 0.91 is plotted as 91.",
    ),
    steps=(
        "Load the file and hide the runs you are not comparing.",
        "Leave Monte Carlo Mode off to compare runs as grouped bars; tick it "
        "for a single distribution with a percentage X axis.",
        "Set Number of Bins, then Decimals - Decimals controls how the bin "
        "range labels under each group are rounded.",
        "Press Replace.",
    ),
    tips=(
        "All visible traces share one set of bins computed from the pooled "
        "data, so the groups really are comparable; bar width adapts to the "
        "number of runs so they never overlap.",
        "Set Value Scale to 1 when the data is already in the units you want "
        "on the axis.",
        "Grid Axis defaults to y: horizontal lines only, the usual convention "
        "for bar charts.",
        "Percent X Axis adds the % suffix in Monte Carlo mode; turn it off for "
        "quantities that are not percentages.",
        "Bar Color accepts any matplotlib colour name ('xkcd:orangered', "
        "'firebrick', '#1f77b4') and applies to the first Monte Carlo trace.",
    ),
)

_MC_MODE = "Monte Carlo Mode"
_VALUE_SCALE = "Value Scale"
_BINS = "Number of Bins"
_DECIMALS = "Decimals"
_GRID_AXIS = "Grid Axis"
_PERCENT_AXIS = "Percent X Axis"
_BAR_COLOR = "Bar Color"

_GRID_AXES = ("y", "x", "both")

#: Distinct, print-friendly defaults; extra traces fall back to the rc cycle.
_PALETTE = ("indianred", "sandybrown", "mediumaquamarine", "orchid",
            "cornflowerblue", "khaki", "lightslategray", "palevioletred")

_DEFAULT_X_LABEL = "Classification Accuracy (%)"
_DEFAULT_Y_LABEL = "Number of iterations"


def get_option_specs() -> list[OptionSpec]:
    return [
        OptionSpec(_MC_MODE, "bool", False,
                   help="Single filled histogram instead of grouped bars."),
        *title_specs(x_label=_DEFAULT_X_LABEL, y_label=_DEFAULT_Y_LABEL),
        OptionSpec(_BINS, "int", 5, minimum=1, maximum=500),
        OptionSpec(_VALUE_SCALE, "float", 100.0,
                   help="Multiplies every sample (100 turns a ratio into %)."),
        OptionSpec(_DECIMALS, "int", 2, minimum=0, maximum=10),
        *font_specs(),
        *grid_spec(),
        OptionSpec(_GRID_AXIS, "choice", _GRID_AXES[0], choices=_GRID_AXES),
        *legend_specs(),
        *log_specs(),
        OptionSpec(_PERCENT_AXIS, "bool", True,
                   help="Monte Carlo mode: format the X axis as percentages."),
        OptionSpec(_BAR_COLOR, "text", "xkcd:orangered",
                   help="Monte Carlo mode bar colour."),
    ]


_SPECS = get_option_specs()


def _samples(trace: TraceLike, scale: float) -> np.ndarray:
    """Finite samples of one trace, scaled for display."""
    values = values_of(trace, scale)
    return values[np.isfinite(values)]


def _collect(traces: list[TraceLike], scale: float) -> list[tuple[str, np.ndarray]]:
    collected = [
        (trace.get_name() or f"Trace {index}", _samples(trace, scale))
        for index, trace in visible_traces(traces)
    ]
    collected = [(name, values) for name, values in collected if values.size]
    if not collected:
        raise PlottingError("No visible trace holds any finite value to bin.")
    return collected


def _bar_color(position: int) -> str:
    """Distinct colours first, then the active style's cycle, never random."""
    if position < len(_PALETTE):
        return _PALETTE[position]
    cycle = list(mpl.rcParams["axes.prop_cycle"].by_key().get("color", []))
    return cycle[(position - len(_PALETTE)) % len(cycle)] if cycle else "gray"


def draw(ax: Axes, traces: list[TraceLike], options) -> None:
    opts = ensure_options(options, _SPECS)
    if not traces:
        raise PlottingError("No data loaded - use Load to open a file first.")
    if opts.flag(_MC_MODE, False):
        _draw_monte_carlo(ax, traces, opts)
    else:
        _draw_grouped(ax, traces, opts)
    refresh(ax, opts)


def _draw_grouped(ax: Axes, traces: list[TraceLike], opts: Options) -> None:
    scale = opts.number(_VALUE_SCALE, 100.0)
    n_bins = opts.integer(_BINS, 5)
    decimals = opts.integer(_DECIMALS, 2)
    series = _collect(traces, scale)

    pooled = np.concatenate([values for _, values in series])
    edges = np.histogram_bin_edges(pooled, bins=n_bins)
    centers = np.arange(len(edges) - 1)

    # Leave a 20% gap between groups whatever the number of traces.
    width = 0.8 / len(series)
    for position, (name, values) in enumerate(series):
        counts, _ = np.histogram(values, bins=edges)
        offset = (position - (len(series) - 1) / 2) * width
        ax.bar(centers + offset, counts, width, label=name,
               color=_bar_color(position),
               edgecolor="black" if position >= len(_PALETTE) else None)

    labels = [
        f"{edges[i]:.{decimals}f}-\n{edges[i + 1]:.{decimals}f}"
        for i in range(len(edges) - 1)
    ]
    ax.set_xticks(centers, labels, rotation=45)


def _draw_monte_carlo(ax: Axes, traces: list[TraceLike], opts: Options) -> None:
    scale = opts.number(_VALUE_SCALE, 100.0)
    n_bins = opts.integer(_BINS, 5)
    color = opts.text(_BAR_COLOR) or "xkcd:orangered"
    series = _collect(traces, scale)

    for position, (name, values) in enumerate(series):
        face = color if position == 0 else _bar_color(position)
        ax.hist(values, bins=n_bins, label=name, facecolor=face, alpha=0.6)
        # Redraw the same bins as a crisp outline; reads much better in print.
        ax.hist(values, bins=n_bins, facecolor="none", edgecolor=face, linewidth=2)

    if opts.flag(_PERCENT_AXIS, True):
        ax.xaxis.set_major_formatter(
            PercentFormatter(decimals=opts.integer(_DECIMALS, 2))
        )
    ax.xaxis.set_minor_locator(AutoMinorLocator())


def refresh(ax: Axes, options) -> None:
    opts = ensure_options(options, _SPECS)
    apply_axes_style(ax, opts)
    # apply_axes_style grids both axes; histograms usually want horizontals only.
    ax.grid(False)
    ax.grid(opts.flag("Grid", True), axis=opts.choice(_GRID_AXIS, "y"))
