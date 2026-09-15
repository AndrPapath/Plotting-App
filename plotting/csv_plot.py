# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""XY line plot: one trace supplies X, every other visible trace a Y curve."""

from __future__ import annotations

from matplotlib.axes import Axes

from .guide import Guide
from .options import (
    X_AXIS_INDEX,
    OptionSpec,
    Options,
    PlottingError,
    ensure_options,
    x_axis_index_spec,
)
from .styling import apply_axes_style, common_line_plot_specs
from .traces import TraceLike, resolve_x_index, values_of, visible_traces

DISPLAY_NAME = "XY Plot"


GUIDE = Guide(
    summary=(
        "The default mode. Plots every visible trace as a curve against the one "
        "trace you nominate as the X axis - the usual shape of a simulator or "
        "instrument export where the first column is the swept variable."
    ),
    data_layout=(
        "One column per signal, all with the same number of rows.",
        "One of the columns holds the X values (usually the first).",
        "Text columns are dropped when the file is loaded and named in the "
        "status bar; columns that are only partly numeric keep gaps.",
    ),
    steps=(
        "Load the file - every numeric column becomes a trace.",
        "In the Traces window, select 'Set as X axis' on the swept column. "
        "Its Visible box greys out, because it is the axis rather than a curve.",
        "Hide the traces you do not want, and rename the ones you do: the "
        "trace name is what the legend shows.",
        "Press Replace to draw, then Refresh after changing any cosmetic "
        "option - Refresh restyles what is already drawn without re-reading "
        "the data.",
    ),
    tips=(
        "Scale Y Axis multiplies every curve at once; the per-trace Scale in "
        "the Traces window multiplies a single one - that is how you get a mA "
        "and a uA signal onto the same plot.",
        "Manual limits (X) / (Y) is what enables Min, Max and the tick "
        "interval. A tick interval of 0 keeps matplotlib's automatic ticks; "
        "Offset shifts where the ticks start without moving the limits.",
        "The 'outside ...' legend locations put the legend beside the axes "
        "instead of on top of the data.",
        "Axes have Trace Color tints the Y axis label and ticks with the "
        "first curve's colour - useful for single-signal figures.",
    ),
)

_AXIS_COLOR = "Axes have Trace Color"


def get_option_specs() -> list[OptionSpec]:
    return [
        *common_line_plot_specs(),
        OptionSpec(_AXIS_COLOR, "bool", False,
                   help="Tint the Y axis with the first curve's colour."),
        x_axis_index_spec(),
    ]


_SPECS = get_option_specs()


def draw(ax: Axes, traces: list[TraceLike], options) -> None:
    """Plot every visible trace against the trace chosen as the X axis."""
    opts = ensure_options(options, _SPECS)
    if not traces:
        raise PlottingError("No data loaded - use Load to open a file first.")

    x_index = resolve_x_index(traces, opts.integer(X_AXIS_INDEX, 0))
    x = values_of(traces[x_index], opts.number("Scale X Axis", 1.0))
    y_scale = opts.number("Scale Y Axis", 1.0)
    width = opts.number("Line Width", 1.0)

    drawn = 0
    for index, trace in visible_traces(traces, skip_index=x_index):
        y = values_of(trace, y_scale)
        if y.shape != x.shape:
            raise PlottingError(
                f"Trace {trace.get_name()!r} has {y.size} points but the X axis "
                f"trace {traces[x_index].get_name()!r} has {x.size}."
            )
        label = trace.get_name() or f"Trace {index}"
        ax.plot(x, y, label=label, linewidth=width)
        drawn += 1

    if not drawn:
        raise PlottingError(
            "Nothing to plot: every trace is either hidden or used as the X axis."
        )
    refresh(ax, opts)


def refresh(ax: Axes, options) -> None:
    """Re-apply the cosmetic options to an already drawn axes."""
    opts = ensure_options(options, _SPECS)
    apply_axes_style(ax, opts)
    _color_y_axis(ax, opts)


def _color_y_axis(ax: Axes, opts: Options) -> None:
    if not opts.flag(_AXIS_COLOR, False) or not ax.lines:
        return
    color = ax.lines[0].get_color()
    ax.yaxis.label.set_color(color)
    ax.tick_params(axis="y", color=color, labelcolor=color)

