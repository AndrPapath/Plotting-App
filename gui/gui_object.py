# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""Backwards-compatible entry point.

The single-file ``gui_object`` module was split into :mod:`gui.app`,
:mod:`gui.trace`, :mod:`gui.trace_window` and :mod:`gui.widgets`. This shim
keeps older imports - and the habit of running this file directly - working.
"""

if __name__ == "__main__" and __package__ in (None, ""):
    # Running this file as a script puts gui/ on sys.path instead of the
    # project root, which breaks both `import plotting` and the relative
    # imports below. Fix the path, then run the real module.
    import os as _os
    import sys as _sys

    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    from gui.app import main as _main

    _main()
    _sys.exit(0)

from .app import PlottingApp, main
from .trace import Trace
from .trace_window import TraceWindow
from .widgets import ScrollableFrame

#: Old name of the trace editor window.
Window = TraceWindow

__all__ = ["PlottingApp", "Trace", "TraceWindow", "Window", "ScrollableFrame", "main"]

if __name__ == "__main__":
    main()
