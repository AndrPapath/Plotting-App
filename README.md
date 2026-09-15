# Plotting App

A small tkinter + matplotlib tool for turning simulation and measurement
exports (CSV / Excel / whitespace-separated text) into publication figures.

## Running

```bash
pip install -r requirements.txt
python app.py
```

Shortcuts: `Ctrl+O` load, `Ctrl+R` replace, `F5` refresh, `Ctrl+S` save.

## Workflow

1. **Load** a file. Every numeric column becomes a *trace*; text columns are
   skipped and named in the status bar.
2. The **Traces** window is where you rename traces, hide them, scale them
   individually, delete them, and pick which one supplies the X axis.
3. Pick a **Mode** (top right) - it decides what is drawn and which options the
   side panel offers.
4. **Plot** draws on top of the current figure, **Replace** clears first
   (the usual button), **Refresh** re-applies the cosmetic options without
   touching the data, **Save** writes a PDF/PNG/SVG.

The **ⓘ** button beside the Mode dropdown (or `F1`) opens the information
window. Its sidebar lists every plot mode - what each expects from the file,
the click-by-click path to a finished plot, the non-obvious options, and every
documented side-panel field - so you can read one guide while another mode is
active, and it follows the dropdown while it stays open. Below the modes,
**About & licence** (or `Shift+F1`) shows the version, copyright, licence
summary and the bundled library versions, with buttons that open the full
licence and NOTICE text. Individual panel fields also show their help on
hover.

Anything the tool cannot do - an unparseable entry box, a file with no numbers,
a tick interval that would need a million ticks - is reported in a dialog and
in the status bar. It never leaves the window in a broken state.

## Layout

```
app.py              entry point
gui/
  app.py            main window: buttons, canvas, error handling
  panel.py          builds the side panel from a mode's option specs
  trace.py          Trace: one column plus its Tk-backed display state
  trace_window.py   the Traces editor
  guide_window.py   the info window behind the (i) button: mode guides + about
  widgets.py        ScrollableFrame, Tooltip
  dataio.py         file -> numeric columns (no tkinter, no matplotlib)
  about.py          app identity, copyright, licence facts (no GUI)
  gui_object.py     backwards-compatible shim for the old single-file module
plotting/
  __init__.py       PLOT_MODES registry + load_mode() / guide_for()
  guide.py          Guide: the structured help each mode publishes
  options.py        OptionSpec / Options: typed, validated panel values
  styling.py        shared option groups + apply_axes_style()
  traces.py         the TraceLike protocol and SimpleTrace (no tkinter)
  csv_plot.py       XY Plot
  parametrics_plot.py  Parametric (legend from swept parameter values)
  coordinate_plot.py   Paired Columns (own X column per curve)
  histogram_plot.py    Histogram (grouped + Monte Carlo)
tests/              unittest suite, runs headless
legacy/             pre-refactor scripts, kept for reference only
```

## License

Copyright 2024-2026 Andreas Papathanasiou, licensed under the
[Apache License 2.0](LICENSE). Every source file carries an SPDX header; see
[NOTICE](NOTICE) for the notice that redistributors must pass on.

The app states this itself, on the **About & licence** page of the ⓘ window:
version, copyright, licence summary, the versions and licences of the bundled
libraries, and buttons that display the full `LICENSE` and `NOTICE` text. All
of it comes from `gui/about.py` - which holds no GUI code, so the build spec
reads the same constants when stamping the executable. `tests/test_about.py`
checks those strings against `NOTICE`, the source headers and this README, so
they cannot drift apart.

A bundled build also ships matplotlib, numpy, pandas, openpyxl and their
dependencies. Those are BSD/MIT-style licensed - permissive and compatible with
Apache-2.0 - but their notices have to travel with the binary, which is what
`THIRD-PARTY-LICENSES.txt` is for. The build script writes it; see below.

## Building the executable

```bash
pip install -r requirements-dev.txt
python scripts/build_exe.py
```

The script runs the test suite, builds with PyInstaller from `PlottingApp.spec`,
and fills `dist/` with everything a recipient needs:

| file | what it is |
| --- | --- |
| `PlottingApp.exe` | one-file build, ~52 MB, no Python needed on the target machine |
| `LICENSE.txt` | this project's Apache-2.0 licence |
| `NOTICE.txt` | the notice redistributors must pass on |
| `THIRD-PARTY-LICENSES.txt` | licences of all 15 bundled dependencies, generated from the installed wheels |

`--skip-tests` builds without testing first; `--clean` discards `build/` and
`dist/` beforehand.

Then check the build itself:

```bash
dist\PlottingApp.exe --selftest
```

It draws every mode, exports a PDF, a PNG and an SVG, confirms the bundled
licence files are readable, prints a report and exits non-zero on failure.
This is worth running after any change to the spec, because a frozen build
fails in ways the source never does: anything imported *by name* at runtime is
invisible to PyInstaller's static analysis. That is how PDF export shipped
broken - `savefig()` resolves `matplotlib.backends.backend_pdf` by name, so it
was never bundled. `tests/test_build.py` now checks the spec declares a backend
for every entry in `gui.app.SAVE_FORMATS` and a hidden import for every mode in
`PLOT_MODES`.

The spec reads the name, version and copyright straight out of `gui/about.py`
and writes them into the exe's Windows version resource, so right-clicking the
file shows *Copyright 2024-2026 Andreas Papathanasiou. Apache-2.0.* under
Details. `LICENSE` and `NOTICE` are bundled inside the exe as well, which is
what the About window reads at runtime. Bump `VERSION` in `gui/about.py` and
everything follows.

## Distributing

The exe is self-contained, so the source can stay private - Apache-2.0 is
permissive, not copyleft, and PyInstaller's bootloader carries an explicit
exception for shipping frozen applications closed-source.

One thing GitHub does not allow: **release assets inherit repository
visibility**. A private repo cannot serve public downloads; anonymous visitors
get a 404. The options are to keep the repo private and either add the
recipients as collaborators, publish the exe through a second, public repo, or
hand out `dist/` directly.

Whichever route, ship the three `.txt` files alongside the exe (or the whole
`dist/` folder). Recipients on Windows will see a SmartScreen warning on first
run because the binary is unsigned - worth telling them in advance so it does
not read as a malware alert.

## Tests

```bash
python -m unittest discover -s tests -t .
```

They run on the `Agg` backend, so no window opens and they work over SSH/CI.

## Adding a plot mode

Create `plotting/my_plot.py` exposing:

```python
DISPLAY_NAME = "My Plot"
GUIDE = Guide(summary=..., data_layout=(...), steps=(...), tips=(...))

def get_option_specs() -> list[OptionSpec]: ...
def draw(ax, traces, options) -> None: ...     # options is an Options mapping
def refresh(ax, options) -> None: ...          # cosmetics only, idempotent
```

`GUIDE` is what the info window shows; it appends the `help` text of your
option specs automatically, so document options there rather than repeating
them in the guide.

Compose the option list from `plotting.styling` (`common_line_plot_specs()`,
`title_specs()`, `legend_specs()`, ...) so the panel stays consistent, read
values with `options.text/integer/number/flag/choice`, raise `PlottingError`
for anything the user should fix, then register the module in `PLOT_MODES`.
The registry checks the contract at load time, and
`tests/test_plotting.py::ModeContractTests` exercises every registered mode.
