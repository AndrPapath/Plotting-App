# legacy/

Standalone scripts from before the app was packaged, kept for reference only.
They are not imported by the application and are not maintained:

* `csv_plotter_*.py`, `histogram*.py` - one-off plotting scripts; their
  behaviour now lives in `plotting/`.
* `gui_object.py`, `gui_object_old_copy.py` - earlier single-file versions of
  the GUI, superseded by the `gui/` package.
* `csv_plot_old_copy.py` - earlier copy of `plotting/csv_plot.py`.
* `GUI_test.py`, `style_test.py`, `dropdown_test.py` - tkinter experiments.

Delete this folder once nothing here is needed; git keeps the history.
