# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""Plot modules and the registry the GUI's mode dropdown is built from.

A plot module is any module exposing::

    DISPLAY_NAME: str
    get_option_specs() -> list[OptionSpec]
    draw(ax, traces, options) -> None
    refresh(ax, options) -> None
"""

from __future__ import annotations

import importlib
from types import ModuleType

from .guide import Guide
from .options import (
    LEGEND_LOCATIONS,
    OptionError,
    OptionSpec,
    Options,
    PlottingError,
    ensure_options,
)
from .traces import SimpleTrace, TraceLike

__all__ = [
    "PLOT_MODES",
    "mode_names",
    "load_mode",
    "guide_for",
    "Guide",
    "OptionError",
    "OptionSpec",
    "Options",
    "PlottingError",
    "SimpleTrace",
    "TraceLike",
    "LEGEND_LOCATIONS",
    "ensure_options",
]

#: Display name -> module path. Order sets the order in the mode dropdown.
PLOT_MODES: dict[str, str] = {
    "XY Plot": "plotting.csv_plot",
    "Parametric": "plotting.parametrics_plot",
    "Paired Columns": "plotting.coordinate_plot",
    "Histogram": "plotting.histogram_plot",
}

_REQUIRED = ("get_option_specs", "draw", "refresh")
_loaded: dict[str, ModuleType] = {}


def mode_names() -> list[str]:
    return list(PLOT_MODES)


def guide_for(name: str) -> Guide:
    """The mode's help text, falling back to its module docstring."""
    module = load_mode(name)
    guide = getattr(module, "GUIDE", None)
    if isinstance(guide, Guide):
        return guide
    return Guide(summary=(module.__doc__ or "No guide available.").strip())


def load_mode(name: str) -> ModuleType:
    """Import a plot module by display name, checking it honours the contract."""
    if name not in PLOT_MODES:
        raise PlottingError(
            f"Unknown plot mode {name!r}; expected one of {', '.join(PLOT_MODES)}."
        )
    if name not in _loaded:
        module = importlib.import_module(PLOT_MODES[name])
        missing = [attr for attr in _REQUIRED if not callable(getattr(module, attr, None))]
        if missing:
            raise PlottingError(
                f"Plot module {module.__name__} is missing: {', '.join(missing)}."
            )
        _loaded[name] = module
    return _loaded[name]
