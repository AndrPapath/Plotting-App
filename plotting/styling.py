# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""Reusable option groups and the axis styling every plot module shares.

Before this module each plot module repeated the same thirty lines of panel
definitions and the same title/grid/legend/limits code, and drifted apart in
the details. Modules now compose the groups below and call
:func:`apply_axes_style`.
"""

from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes

from .options import LEGEND_LOCATIONS, OptionError, OptionSpec, Options

__all__ = [
    "MAX_TICKS",
    "title_specs",
    "font_specs",
    "grid_spec",
    "legend_specs",
    "axis_scale_specs",
    "log_specs",
    "limit_specs",
    "line_specs",
    "common_line_plot_specs",
    "clear_legends",
    "apply_legend",
    "apply_axes_style",
]

#: Guard against an interval of 1e-9 over a range of 1e9 locking up the GUI.
MAX_TICKS = 1000


def title_specs(x_label: str = "", y_label: str = "") -> list[OptionSpec]:
    return [
        OptionSpec("Plot Title", "text", ""),
        OptionSpec("X Axis Label", "text", x_label),
        OptionSpec("Y Axis Label", "text", y_label),
    ]


def font_specs() -> list[OptionSpec]:
    return [
        OptionSpec("Font Size", "int", 14, minimum=1, maximum=72),
        OptionSpec("Legend Font Size", "int", 10, minimum=1, maximum=72),
    ]


def grid_spec(default: bool = True) -> list[OptionSpec]:
    return [OptionSpec("Grid", "bool", default)]


def legend_specs(default: bool = True) -> list[OptionSpec]:
    return [
        OptionSpec("Legend", "bool", default),
        OptionSpec(
            "Legend Location", "choice", LEGEND_LOCATIONS[0], choices=LEGEND_LOCATIONS
        ),
        OptionSpec("Legend Columns", "int", 1, minimum=1, maximum=20),
    ]


def axis_scale_specs() -> list[OptionSpec]:
    return [
        OptionSpec("Scale X Axis", "float", 1.0, help="Multiplies every X value."),
        OptionSpec("Scale Y Axis", "float", 1.0, help="Multiplies every Y value."),
    ]


def log_specs() -> list[OptionSpec]:
    return [
        OptionSpec("Log X Axis", "bool", False),
        OptionSpec("Log Y Axis", "bool", False),
    ]


def limit_specs(axis: str) -> list[OptionSpec]:
    """Manual limit / tick controls for ``"X"`` or ``"Y"``."""
    axis = axis.upper()
    return [
        OptionSpec(f"Manual limits ({axis})", "bool", False),
        OptionSpec(f"Min {axis}", "float", 0.0),
        OptionSpec(f"Max {axis}", "float", 0.0),
        OptionSpec(f"{axis} tick interval", "float", 0.0, minimum=0.0,
                   help="0 keeps the automatic ticks."),
        OptionSpec(f"Offset {axis}", "float", 0.0, help="Shifts the tick positions."),
    ]


def line_specs() -> list[OptionSpec]:
    return [OptionSpec("Line Width", "float", 1.0, minimum=0.1, maximum=20.0)]


def common_line_plot_specs() -> list[OptionSpec]:
    """The full set shared by every XY-style plot module."""
    return [
        *title_specs(),
        *font_specs(),
        *grid_spec(),
        *legend_specs(),
        *axis_scale_specs(),
        *log_specs(),
        *limit_specs("X"),
        *limit_specs("Y"),
        *line_specs(),
    ]


def clear_legends(ax: Axes) -> None:
    """Drop both the axes legend and any figure level legend."""
    figure = ax.get_figure()
    if figure is not None:
        for legend in list(figure.legends):
            legend.remove()
    legend = ax.get_legend()
    if legend is not None:
        legend.remove()


def apply_legend(ax: Axes, options: Options) -> None:
    """(Re)build the legend, honouring the ``outside *`` placements.

    ``Axes.legend`` rejects the ``outside`` locations, so those have to go on
    the figure instead - previously picking one raised a ValueError.
    """
    clear_legends(ax)
    if not options.flag("Legend", True):
        return
    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        return
    location = options.choice("Legend Location", "best")
    kwargs = {
        "ncols": max(1, options.integer("Legend Columns", 1)),
        "fontsize": options.integer("Legend Font Size", 10),
    }
    if location.startswith("outside"):
        figure = ax.get_figure()
        figure.legend(handles, labels, loc=location, **kwargs)
    else:
        ax.legend(handles, labels, loc=location, **kwargs)


def _tick_positions(low: float, high: float, step: float, offset: float,
                    label: str) -> np.ndarray:
    count = (high - low) / step
    if count > MAX_TICKS:
        raise OptionError(
            f"{label}: an interval of {step:g} over {low:g}..{high:g} would need "
            f"{count:.0f} ticks (limit {MAX_TICKS})"
        )
    # Nudge the stop value so a limit that lands exactly on a tick is kept.
    return np.arange(low + offset, high + step / 2.0, step)


def _set_scale(ax: Axes, axis: str, logarithmic: bool) -> None:
    """Switch an axis to log/linear only when it is not already there.

    ``set_xscale`` resets that axis' locator and formatter, so calling it
    unconditionally on every Refresh threw away the histogram's bin labels and
    its percentage formatter.
    """
    target = "log" if logarithmic else "linear"
    getter, setter = (ax.get_xscale, ax.set_xscale) if axis == "x" else (
        ax.get_yscale, ax.set_yscale)
    if getter() != target:
        setter(target)


def _apply_axis_limits(ax: Axes, options: Options, axis: str) -> None:
    if not options.flag(f"Manual limits ({axis})", False):
        return
    low = options.number(f"Min {axis}")
    high = options.number(f"Max {axis}")
    if high <= low:
        raise OptionError(f"Max {axis} ({high:g}) must be greater than Min {axis} ({low:g})")
    is_log = options.flag(f"Log {axis} Axis", False)
    if is_log and low <= 0:
        raise OptionError(f"Min {axis} must be positive on a logarithmic axis")

    step = options.number(f"{axis} tick interval")
    if step > 0 and not is_log:
        ticks = _tick_positions(low, high, step, options.number(f"Offset {axis}"),
                                f"{axis} tick interval")
        (ax.set_xticks if axis == "X" else ax.set_yticks)(ticks)
    if axis == "X":
        ax.set_xlim(left=low, right=high)
    else:
        ax.set_ylim(bottom=low, top=high)


def apply_axes_style(ax: Axes, options: Options, *, legend: bool = True) -> None:
    """Apply every purely cosmetic option to ``ax``.

    Safe to call repeatedly - that is what the Refresh button does.
    """
    font_size = options.integer("Font Size", 14)

    ax.set_title(options.text("Plot Title"), fontsize=font_size)
    ax.set_xlabel(options.text("X Axis Label"), fontsize=font_size)
    ax.set_ylabel(options.text("Y Axis Label"), fontsize=font_size)
    ax.tick_params(axis="both", labelsize=font_size)

    line_width = options.number("Line Width", 1.0)
    if line_width > 0:
        for line in ax.lines:
            line.set_linewidth(line_width)

    _set_scale(ax, "x", options.flag("Log X Axis", False))
    _set_scale(ax, "y", options.flag("Log Y Axis", False))

    _apply_axis_limits(ax, options, "X")
    _apply_axis_limits(ax, options, "Y")

    ax.grid(options.flag("Grid", True))

    if legend:
        apply_legend(ax, options)
