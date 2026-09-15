# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""Post-build check: `PlottingApp.exe --selftest`.

A frozen build can fail in ways the source never does, because PyInstaller has
to be told about anything imported by name at runtime. This exercises exactly
those paths - every plot mode, every save format, the bundled licence files -
and reports through the exit code, so a windowed build with no console can
still be verified.
"""

from __future__ import annotations

import tempfile
import traceback
from pathlib import Path

__all__ = ["run_selftest"]


def _check_licences(report: list[str]) -> bool:
    from . import about

    ok = True
    for name, reader in (("LICENSE", about.license_text),
                         ("NOTICE", about.notice_text)):
        text = reader()
        if text and len(text) > 100:
            report.append(f"  ok    {name} bundled ({len(text)} chars)")
        else:
            report.append(f"  FAIL  {name} missing from the bundle")
            ok = False
    return ok


def _check_modes(report: list[str], directory: Path) -> bool:
    import numpy as np
    from matplotlib.figure import Figure

    import plotting
    from plotting import SimpleTrace

    x = np.linspace(0.5, 10.0, 40)
    traces = [
        SimpleTrace("x", x),
        SimpleTrace("1e-06", np.sin(x) + 2.0),
        SimpleTrace("2e-06", np.cos(x) + 2.0),
    ]
    ok = True
    for name in plotting.mode_names():
        try:
            module = plotting.load_mode(name)
            figure = Figure(layout="constrained")
            axes = figure.add_subplot()
            options = plotting.Options.from_specs(module.get_option_specs(), {})
            module.draw(axes, traces, options)
            module.refresh(axes, options)
            figure.savefig(directory / f"mode-{name.replace(' ', '-')}.png")
            report.append(f"  ok    mode {name}")
        except Exception as error:
            report.append(f"  FAIL  mode {name}: {type(error).__name__}: {error}")
            ok = False
    return ok


def _check_save_formats(report: list[str], directory: Path) -> bool:
    """The failure this was written for: savefig imports its backend by name."""
    import numpy as np
    from matplotlib.figure import Figure

    from .app import SAVE_FORMATS

    figure = Figure(layout="constrained")
    axes = figure.add_subplot()
    axes.plot(np.linspace(0, 1, 10), np.linspace(0, 1, 10), label="line")
    axes.legend()

    ok = True
    for extension in SAVE_FORMATS:
        target = directory / f"export.{extension}"
        try:
            figure.savefig(target)
            size = target.stat().st_size
            if size <= 0:
                raise OSError("wrote an empty file")
            report.append(f"  ok    save .{extension} ({size} bytes)")
        except Exception as error:
            report.append(
                f"  FAIL  save .{extension}: {type(error).__name__}: {error}")
            ok = False
    return ok


def run_selftest(output_dir: str | None = None) -> int:
    """Run every check. Returns 0 when they all pass, 1 otherwise."""
    from . import about

    report = [f"{about.APP_NAME} {about.VERSION} self-test", ""]
    directory = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(
        prefix="plottingapp-selftest-"))
    directory.mkdir(parents=True, exist_ok=True)

    try:
        passed = all([
            _check_licences(report),
            _check_modes(report, directory),
            _check_save_formats(report, directory),
        ])
    except Exception:  # pragma: no cover - a broken bundle, not a failed check
        report.append("  FAIL  the self-test itself crashed:")
        report.append(traceback.format_exc())
        passed = False

    report.append("")
    report.append("PASS" if passed else "FAIL")
    text = "\n".join(report)

    # A windowed build has no console, so the report goes to a file too.
    log = directory / "selftest.log"
    try:
        log.write_text(text, encoding="utf-8")
    except OSError:  # pragma: no cover
        pass
    print(text)
    print(f"\nreport: {log}")
    return 0 if passed else 1
