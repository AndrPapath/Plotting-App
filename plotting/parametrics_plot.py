# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""Parametric sweep: every Y trace is one value of a swept parameter.

Column headers such as ``1e-05`` become legend entries like ``$W=10\\ \\mu m$``
using the parameter name, unit and scale from the side panel.
"""

from __future__ import annotations

from matplotlib.axes import Axes
from matplotlib.ticker import EngFormatter

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

DISPLAY_NAME = "Parametric"


GUIDE = Guide(
    summary=(
        "An XY plot for a parameter sweep: each Y column's header is the value "
        "of the swept parameter, and becomes an engineering-formatted legend "
        "entry such as W=1 um instead of the raw 1e-06."
    ),
    data_layout=(
        "First the swept variable (the X column), then one column per "
        "parameter value.",
        "Headers that parse as numbers ('1e-06', '4e-06') are formatted; any "
        "other header (a corner name like 'tt') is shown unchanged.",
    ),
    steps=(
        "Load the file and set the X axis in the Traces window.",
        "Type the parameter symbol into Parameter's Name (for example W) and "
        "its unit into Parameter's Unit (for example m).",
        "Press Replace. The legend now reads W=1 um, W=4 um, ...",
    ),
    tips=(
        "Parameter's Scale multiplies the header value before formatting - "
        "set it to 1e6 if the header is already expressed in microns.",
        "Leave Parameter's Name empty to get just the formatted value.",
        "Cycle Line Styles varies solid/dashed/dash-dot across the family, "
        "which keeps it readable when the figure is printed in black and white.",
        "Renaming a trace in the Traces window overrides the header, so you "
        "can hand-write one awkward legend entry and leave the rest automatic.",
    ),
)

_PARAM_NAME = "Parameter's Name"
_PARAM_UNIT = "Parameter's Unit"
_PARAM_SCALE = "Parameter's Scale"

_LINE_STYLES = ("-", "--", "-.", ":")


def get_option_specs() -> list[OptionSpec]:
    return [
        *common_line_plot_specs(),
        OptionSpec(_PARAM_NAME, "text", "",
                   help="Shown before each value in the legend, e.g. W."),
        OptionSpec(_PARAM_UNIT, "text", "",
                   help="Unit appended to each parameter value, e.g. m or V."),
        OptionSpec(_PARAM_SCALE, "float", 1.0,
                   help="Multiplies the parameter value read from the header."),
        OptionSpec("Cycle Line Styles", "bool", False),
        x_axis_index_spec(),
    ]


_SPECS = get_option_specs()


def format_label(raw_name: str, opts: Options) -> str:
    """Build one legend entry from a column header."""
    name = opts.text(_PARAM_NAME)
    unit = opts.text(_PARAM_UNIT)
    scale = opts.number(_PARAM_SCALE, 1.0)
    try:
        value = float(raw_name) * scale
    except (TypeError, ValueError):
        # Not a swept value (a plain column name); show it unchanged.
        return f"{name}={raw_name}" if name else raw_name
    shown = EngFormatter(unit=unit, sep="\N{THIN SPACE}")(value)
    return f"{name}={shown}" if name else shown


def draw(ax: Axes, traces: list[TraceLike], options) -> None:
    opts = ensure_options(options, _SPECS)
    if not traces:
        raise PlottingError("No data loaded - use Load to open a file first.")

    x_index = resolve_x_index(traces, opts.integer(X_AXIS_INDEX, 0))
    x = values_of(traces[x_index], opts.number("Scale X Axis", 1.0))
    y_scale = opts.number("Scale Y Axis", 1.0)
    width = opts.number("Line Width", 1.0)
    cycle_styles = opts.flag("Cycle Line Styles", False)

    drawn = 0
    for _, trace in visible_traces(traces, skip_index=x_index):
        y = values_of(trace, y_scale)
        if y.shape != x.shape:
            raise PlottingError(
                f"Trace {trace.get_name()!r} has {y.size} points but the X axis "
                f"trace has {x.size}."
            )
        line, = ax.plot(x, y, label=format_label(trace.get_name(), opts),
                        linewidth=width)
        if cycle_styles:
            line.set_linestyle(_LINE_STYLES[drawn % len(_LINE_STYLES)])
        drawn += 1

    if not drawn:
        raise PlottingError(
            "Nothing to plot: every trace is either hidden or used as the X axis."
        )
    refresh(ax, opts)


def refresh(ax: Axes, options) -> None:
    apply_axes_style(ax, ensure_options(options, _SPECS))
