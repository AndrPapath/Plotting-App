# -*- mode: python ; coding: utf-8 -*-
# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0
"""PyInstaller build: python -m PyInstaller PlottingApp.spec --noconfirm

Prefer `python scripts/build_exe.py`, which runs the tests first and stages the
licence files next to the executable.
"""

import ast
from pathlib import Path

ROOT = Path(SPECPATH)


def app_metadata():
    """Read the constants out of gui/about.py without importing the GUI stack."""
    source = (ROOT / "gui" / "about.py").read_text(encoding="utf-8")
    wanted = {"APP_NAME", "VERSION", "AUTHOR", "COPYRIGHT_YEARS"}
    found = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in wanted:
                found[target.id] = ast.literal_eval(node.value)
    missing = wanted - set(found)
    if missing:
        raise SystemExit(f"gui/about.py is missing: {', '.join(sorted(missing))}")
    found["COPYRIGHT"] = f"Copyright {found['COPYRIGHT_YEARS']} {found['AUTHOR']}"
    return found


META = app_metadata()
NAME = "PlottingApp"


def write_version_resource() -> str:
    """Emit the Windows version resource, so the copyright shows in Properties."""
    parts = [int(piece) for piece in META["VERSION"].split(".")]
    while len(parts) < 4:
        parts.append(0)
    quad = ", ".join(str(piece) for piece in parts[:4])
    text = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({quad}), prodvers=({quad}),
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0,
    date=(0, 0)),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', {META['AUTHOR']!r}),
        StringStruct('FileDescription', {META['APP_NAME']!r}),
        StringStruct('FileVersion', {META['VERSION']!r}),
        StringStruct('InternalName', {NAME!r}),
        StringStruct('LegalCopyright', {META['COPYRIGHT'] + '. Apache-2.0.'!r}),
        StringStruct('OriginalFilename', {NAME + '.exe'!r}),
        StringStruct('ProductName', {META['APP_NAME']!r}),
        StringStruct('ProductVersion', {META['VERSION']!r}),
      ])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    path = ROOT / "build" / "version_info.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(path)


VERSION_FILE = write_version_resource()

a = Analysis(
    ['app.py'],
    pathex=[str(ROOT)],
    binaries=[],
    # Shipped so the About window can display them from the frozen build,
    # and so the binary carries the notices the licences require.
    datas=[('LICENSE', '.'), ('NOTICE', '.')],
    # The plot modules are imported by name through plotting.PLOT_MODES, and
    # matplotlib resolves an output backend by name inside savefig(). Neither
    # is visible to static analysis, so both have to be declared or the frozen
    # build raises ModuleNotFoundError the first time you export.
    hiddenimports=[
        'plotting.csv_plot',
        'plotting.parametrics_plot',
        'plotting.coordinate_plot',
        'plotting.histogram_plot',
        # Save formats: agg backs png/jpg, the rest are one backend each.
        'matplotlib.backends.backend_agg',
        'matplotlib.backends.backend_pdf',
        'matplotlib.backends.backend_svg',
        'matplotlib.backends.backend_ps',
        'matplotlib.backends.backend_pgf',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # The app forces the TkAgg backend; keep the other GUI toolkits, the test
    # tooling and the old scratch scripts out of the bundle.
    excludes=[
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx',
        'IPython', 'jupyter', 'notebook', 'pytest', 'sphinx',
        'scipy', 'tests', 'legacy',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=VERSION_FILE,
)
