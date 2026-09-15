# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

# plotting/csv_plot.py
import numpy as np
from .utils import read_csv_file

def get_side_panel_items():
    return {
        "Plot Title": {"type": "entry", "default": ""},
        "X Axis Label": {"type": "entry", "default": ""},
        "Y Axis Label": {"type": "entry", "default": ""},
        "Z Axis Label": {"type": "entry", "default": ""},
        "Font Size": {"type": "int_entry", "default": 14},
        "Legend Font Size": {"type": "int_entry", "default": 10},
        "Grid": {"type": "bool", "default": True},
        "Legend": {"type": "bool", "default": True},
        "Legend Location": {"type": "dropdown", "default": "best", "options": [
            'best', 'upper left', 'upper center', 'upper right', 'lower left', 'lower center', 'lower right',
            'outside upper left', 'outside upper center', 'outside upper right', 'outside lower left',
            'outside lower center', 'outside lower right', 'outside left upper', 'outside left center',
            'outside left lower', 'outside right upper', 'outside right center', 'outside right lower',
        ]},
        #"Horizontal": {"type": "radio", "default": "Orientation", "options": 1},
        #"Vertical": {"type": "radio", "default": "Orientation", "options": 0},
        "Legend Columns": {"type": "int_entry", "default": 1},
        "Axes have Trace Color": {"type": "bool", "default": False},
        "Default Trace Colors": {"type": "bool", "default": True},
        "Scale X Axis": {"type": "float_entry", "default": 1.0},
        "Scale Y Axis": {"type": "float_entry", "default": 1.0},
        "Log Y Axis": {"type": "bool", "default": False},
        "Log X Axis": {"type": "bool", "default": False},
        "Manual limits (X)": {"type": "bool", "default": False},
        "X tick interval": {"type": "float_entry", "default": 1},
        "Offset X": {"type": "float_entry", "default": 0.0},
        "Min X": {"type": "float_entry", "default": 0.0},
        "Max X": {"type": "float_entry", "default": 0.0},
        "Manual limits (Y)": {"type": "bool", "default": False},
        "Y tick interval": {"type": "float_entry", "default": 1},
        "Offset Y": {"type": "float_entry", "default": 0.0},
        "Min Y": {"type": "float_entry", "default": 0.0},
        "Max Y": {"type": "float_entry", "default": 0.0},
        "Line Width": {"type": "int_entry", "default": 1},
    }

def process_data(file_path, options):
    data = read_csv_file(file_path)
    return data

def draw(ax, traces, options):
    # Use the trace marked as X axis (from parent.x_axis.get())
    x_axis_index = 0
    if hasattr(traces[0], 'parent') and hasattr(traces[0].parent, 'x_axis'):
        x_axis_index = traces[0].parent.x_axis.get()
    if x_axis_index < 0 or x_axis_index >= len(traces):
        x_axis_index = 0
    x_trace = traces[x_axis_index]
    x = x_trace.data * float(options.get("Scale X Axis", 1.0))
    for i, trace in enumerate(traces):
        if i == x_axis_index:
            continue
        #if hasattr(trace, 'is_visible') and not trace.is_visible():
        if trace.index==x_axis_index or not trace.is_visible():
            continue
        y = trace.data * trace.get_scale() * float(options.get("Scale Y Axis", 1.0))
        #y = trace.data
        if options.get("Log Y Axis"):
            ax.semilogy(x, y, label=trace.get_name(), linewidth=float(options.get("Line Width", 1)))
        else:
            #ax.plot(x, y, label=trace.get_name())
            ax.plot(x, y, label=trace.get_name(), linewidth=float(options.get("Line Width", 1)))
        # if options.get("Log X Axis"):
        #     ax.set_xscale('log')
        # if options.get("Log Y Axis"):
        #     ax.set_yscale('log')
        # if not options.get("Log X Axis"):
        #     ax.plot(x, y, label=trace.get_name(), linewidth=float(options.get("Line Width", 1)))
        # else:
        #     ax.semilogx(x, y, label=trace.get_name(), linewidth=float(options.get("Line Width", 1)))
        refresh(ax, options)

def refresh(ax, options):
    ax.set_title(options.get("Plot Title", ""), fontsize=int(options.get("Font Size", 14)))
    for line in ax.lines:
        line.set_linewidth(float(options.get("Line Width", 1)))
    if options.get("Manual limits (X)"):
        if options.get("Log X Axis"):
            ax.set_xticks(np.logspace(1,7,10,endpoint=False))
        else:
            ax.set_xticks(np.arange(options.get("Min X")+float(options.get("Offset X")), options.get("Max X"), options.get("X tick interval")))
        ax.set_xlim(left=options.get("Min X"), right=options.get("Max X"))
    if options.get("Manual limits (Y)"):
        ax.set_yticks(np.arange((float(options.get("Offset Y"))+options.get("Min Y")), options.get("Max Y"), options.get("Y tick interval")))
        ax.set_ylim(bottom=options.get("Min Y"), top=options.get("Max Y"))
    ax.grid(options.get("Grid", True))
    if options.get("Legend"):
        ax.legend(loc=options.get("Legend Location", "best"), fontsize=int(options.get("Legend Font Size", 10)), ncol = options.get("Legend Columns"))
    ax.set_xlabel(options.get("X Axis Label", ""), fontsize=int(options.get("Font Size", 14)))
    ax.set_ylabel(options.get("Y Axis Label", ""), fontsize=int(options.get("Font Size", 14)))
    ax.tick_params(axis='both', labelsize=int(options.get("Font Size", 14)))


