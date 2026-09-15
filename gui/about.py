# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""Application identity, and the About window that shows it.

Single source of truth for the name, version, copyright and licence. The
strings here are checked against ``NOTICE`` by ``tests/test_about.py``, so the
box in the app cannot quietly drift away from the file the licence requires
redistributors to pass on.
"""

from __future__ import annotations

import sys
from pathlib import Path

__all__ = [
    "APP_NAME",
    "VERSION",
    "AUTHOR",
    "COPYRIGHT_YEARS",
    "COPYRIGHT",
    "LICENSE_NAME",
    "LICENSE_URL",
    "SHORT_NOTICE",
    "THIRD_PARTY",
    "license_text",
    "notice_text",
    "resource_path",
    "installed_versions",
]

APP_NAME = "Plotting App"
VERSION = "1.0.0"
AUTHOR = "Andreas Papathanasiou"
COPYRIGHT_YEARS = "2024-2026"
COPYRIGHT = f"Copyright {COPYRIGHT_YEARS} {AUTHOR}"
LICENSE_NAME = "Apache License 2.0"
LICENSE_SPDX = "Apache-2.0"
LICENSE_URL = "http://www.apache.org/licenses/LICENSE-2.0"

#: Compact form for the status bar.
SHORT_NOTICE = f"\N{COPYRIGHT SIGN} {COPYRIGHT_YEARS} {AUTHOR} · {LICENSE_SPDX}"

#: Bundled dependencies whose own licences must travel with a binary build.
THIRD_PARTY: tuple[tuple[str, str, str], ...] = (
    ("matplotlib", "matplotlib", "matplotlib licence (BSD-style)"),
    ("numpy", "numpy", "BSD 3-Clause"),
    ("pandas", "pandas", "BSD 3-Clause"),
    ("openpyxl", "openpyxl", "MIT"),
)


def resource_path(name: str) -> Path:
    """Locate a data file both from a source checkout and a frozen build.

    PyInstaller unpacks bundled data into ``sys._MEIPASS``; from source the
    files sit next to the package directory.
    """
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).resolve().parents[1]
    return base / name


def _read(name: str) -> str | None:
    path = resource_path(name)
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def license_text() -> str | None:
    """The full Apache-2.0 text, or ``None`` if it was not shipped."""
    return _read("LICENSE")


def notice_text() -> str | None:
    return _read("NOTICE")


def installed_versions() -> list[tuple[str, str, str]]:
    """``(display name, version, licence)`` for the bundled dependencies."""
    import importlib
    import importlib.metadata as metadata

    rows = []
    for display, module_name, licence in THIRD_PARTY:
        version = "not installed"
        try:
            version = metadata.version(module_name)
        except metadata.PackageNotFoundError:
            try:  # a frozen build has the module but no distribution metadata
                version = getattr(importlib.import_module(module_name),
                                  "__version__", "bundled")
            except ImportError:
                pass
        rows.append((display, version, licence))
    return rows

