# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""Paired-column plot: the file holds its own X column next to every Y column.

Simulator exports of a swept family look like ``y0, x0, y1, x1, ...`` because
each curve is sampled at its own points. Traces are consumed two at a time.
"""

from __future__ import annotations

from matplotlib.axes import Axes

from .guide import Guide
from .options import OptionSpec, PlottingError, ensure_options
from .styling import apply_axes_style, common_line_plot_specs
from .traces import TraceLike, values_of

DISPLAY_NAME = "Paired Columns"


GUIDE = Guide(
    summary=(
        "For exports where every curve carries its own X column, so the file is "
        "a series of column pairs rather than one shared sweep. Common when the "
        "curves of a family were each sampled at different points."
    ),
    data_layout=(
        "Columns are consumed two at a time: y0, x0, y1, x1, ... Set Column "
        "Order to 'X, Y' if your export puts the X column first.",
        "The two columns of a pair must have the same length; different pairs "
        "may have different lengths.",
        "An odd trailing column is ignored.",
    ),
    steps=(
        "Load the file and open the Traces window to check the pairing: the "
        "column order there is the order they are consumed in.",
        "Set Column Order to match the export.",
        "Hide any pair you do not need - hiding either column of a pair drops "
        "that curve.",
        "Press Replace.",
    ),
    tips=(
        "This mode ignores 'Set as X axis'; the pairing decides which column "
        "is X.",
        "The legend entry comes from the X column's header, which is where "
        "these exports normally put the parameter value.",
        "If every curve comes out wrong-way-round, flip Column Order rather "
        "than editing the file.",
        "Cycle Line Styles is on by default in this mode, because these "
        "families are usually the same signal under different conditions.",
    ),
)

_PAIR_ORDER = "Column Order"
_ORDERS = ("Y, X", "X, Y")
_LINE_STYLES = ("-", "-.", "--", ":")


def get_option_specs() -> list[OptionSpec]:
    return [
        *common_line_plot_specs(),
        OptionSpec(_PAIR_ORDER, "choice", _ORDERS[0], choices=_ORDERS,
                   help="Which column of each pair holds the X values."),
        OptionSpec("Cycle Line Styles", "bool", True),
    ]


_SPECS = get_option_specs()


def draw(ax: Axes, traces: list[TraceLike], options) -> None:
    opts = ensure_options(options, _SPECS)
    if len(traces) < 2:
        raise PlottingError(
            "Paired Columns needs at least two traces (one X and one Y column)."
        )

    y_first = opts.choice(_PAIR_ORDER, _ORDERS[0]) == _ORDERS[0]
    x_scale = opts.number("Scale X Axis", 1.0)
    y_scale = opts.number("Scale Y Axis", 1.0)
    width = opts.number("Line Width", 1.0)
    cycle_styles = opts.flag("Cycle Line Styles", True)

    drawn = 0
    for first, second in zip(traces[::2], traces[1::2]):
        y_trace, x_trace = (first, second) if y_first else (second, first)
        if not (y_trace.is_visible() and x_trace.is_visible()):
            continue
        x = values_of(x_trace, x_scale)
        y = values_of(y_trace, y_scale)
        if x.shape != y.shape:
            raise PlottingError(
                f"Column pair {x_trace.get_name()!r}/{y_trace.get_name()!r} has "
                f"{x.size} and {y.size} points."
            )
        line, = ax.plot(x, y, label=x_trace.get_name() or y_trace.get_name(),
                        linewidth=width)
        if cycle_styles:
            line.set_linestyle(_LINE_STYLES[drawn % len(_LINE_STYLES)])
        drawn += 1

    if not drawn:
        raise PlottingError("Nothing to plot: no visible column pair.")
    refresh(ax, opts)


def refresh(ax: Axes, options) -> None:
    apply_axes_style(ax, ensure_options(options, _SPECS))
