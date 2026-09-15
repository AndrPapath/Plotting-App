# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""The info window: how each plot mode works, and what this program is.

One window behind the (i) button holds both - the mode guides and the about /
licence page - so there is a single place to look for "what is this".
"""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

import plotting

from . import about

__all__ = ["GuideWindow", "INFO_GLYPH"]

#: Label for the little buttons that open this window.
INFO_GLYPH = "\N{CIRCLED LATIN SMALL LETTER I}"

_BULLET = "\N{BULLET}  "
_ABOUT = "about"


class GuideWindow(tk.Toplevel):
    """Read-only help: one plot mode at a time, or the about page.

    Mode text is built from each module's ``GUIDE`` plus the ``help`` string of
    its option specs, so a mode that gains an option documents itself. The
    about page reads :mod:`gui.about`, which is also what stamps the copyright
    into the executable.
    """

    def __init__(self, parent: tk.Misc, mode: str | None = None) -> None:
        super().__init__(parent)
        self.title(f"{about.APP_NAME} - information")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_text()
        self._build_buttons()

        self.bind("<Escape>", lambda _event: self.destroy())
        self.geometry("780x580")
        self.minsize(580, 400)
        self.show(mode or plotting.mode_names()[0])

    # -- construction -----------------------------------------------------
    def _build_sidebar(self) -> None:
        frame = ttk.Frame(self, padding=(8, 8, 4, 8))
        frame.grid(row=0, column=0, sticky="ns")
        frame.rowconfigure(1, weight=1)

        ttk.Label(frame, text="Plot modes").grid(row=0, column=0, sticky="w",
                                                 pady=(0, 4))
        self.mode_list = tk.Listbox(frame, exportselection=False, width=20,
                                    activestyle="none", highlightthickness=0)
        for name in plotting.mode_names():
            self.mode_list.insert("end", name)
        self.mode_list.grid(row=1, column=0, sticky="ns")
        self.mode_list.bind("<<ListboxSelect>>", self._on_select)

        ttk.Separator(frame, orient="horizontal").grid(row=2, column=0,
                                                       sticky="ew", pady=8)
        self.about_button = ttk.Button(frame, text=f"{INFO_GLYPH}  About & licence",
                                       command=self.show_about)
        self.about_button.grid(row=3, column=0, sticky="ew")

    def _build_text(self) -> None:
        frame = ttk.Frame(self, padding=(4, 8, 8, 8))
        frame.grid(row=0, column=1, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.text = tk.Text(frame, wrap="word", padx=12, pady=10, relief="sunken",
                            borderwidth=1, highlightthickness=0, cursor="arrow")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._configure_tags()

    def _configure_tags(self) -> None:
        base = tkfont.nametofont("TkTextFont")
        size = abs(base.cget("size") or 10)
        family = base.cget("family")
        self.text.tag_configure("title", font=(family, size + 4, "bold"), spacing3=8)
        self.text.tag_configure("summary", font=(family, size), spacing1=2,
                                spacing3=10, lmargin1=2, lmargin2=2)
        self.text.tag_configure("heading", font=(family, size + 1, "bold"),
                                spacing1=12, spacing3=6)
        # Hanging indent so wrapped bullet text lines up under the first word.
        self.text.tag_configure("bullet", lmargin1=14, lmargin2=32, spacing3=6)
        self.text.tag_configure("option", font=(family, size, "bold"))
        self.text.tag_configure("copyright", font=(family, size, "bold"),
                                spacing1=4, spacing3=4)
        self.text.tag_configure("mono", font=tkfont.nametofont("TkFixedFont"))

    def _build_buttons(self) -> None:
        bar = ttk.Frame(self, padding=(8, 0, 8, 8))
        bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        ttk.Button(bar, text="Close", command=self.destroy).pack(side="right")
        ttk.Button(
            bar, text="Full licence",
            command=lambda: self._show_text(about.LICENSE_NAME,
                                            about.license_text()),
        ).pack(side="left")
        ttk.Button(
            bar, text="NOTICE",
            command=lambda: self._show_text("NOTICE", about.notice_text()),
        ).pack(side="left", padx=(6, 0))

    # -- navigation -------------------------------------------------------
    def show(self, mode: str) -> None:
        """Select ``mode`` in the list and render its guide."""
        names = plotting.mode_names()
        if mode not in names:
            mode = names[0]
        self.mode_list.selection_clear(0, "end")
        self.mode_list.selection_set(names.index(mode))
        self.mode_list.see(names.index(mode))
        self._render_mode(mode)
        self._raise()

    def show_about(self) -> None:
        """Render the about / licence page."""
        self.mode_list.selection_clear(0, "end")
        self._render_about()
        self._raise()

    def _raise(self) -> None:
        self.lift()
        self.focus_set()

    def _on_select(self, _event: tk.Event) -> None:
        selection = self.mode_list.curselection()
        if selection:
            self._render_mode(self.mode_list.get(selection[0]))

    # -- rendering --------------------------------------------------------
    def _begin(self) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")

    def _end(self) -> None:
        self.text.configure(state="disabled")
        self.text.yview_moveto(0.0)

    def _bullet(self, item: str) -> None:
        self.text.insert("end", f"{_BULLET}{item}\n", "bullet")

    def _render_mode(self, mode: str) -> None:
        guide = plotting.guide_for(mode)
        self._begin()
        self.text.insert("end", f"{mode}\n", "title")
        self.text.insert("end", f"{guide.summary}\n", "summary")
        for heading, items in guide.sections():
            self.text.insert("end", f"{heading}\n", "heading")
            for item in items:
                self._bullet(item)
        self._render_options(mode)
        self._end()

    def _render_options(self, mode: str) -> None:
        """List the panel fields that carry a help string."""
        documented = [
            spec for spec in plotting.load_mode(mode).get_option_specs()
            if spec.help and not spec.hidden
        ]
        if not documented:
            return
        self.text.insert("end", "Options in the side panel\n", "heading")
        for spec in documented:
            self.text.insert("end", _BULLET, "bullet")
            self.text.insert("end", spec.label, ("bullet", "option"))
            self.text.insert("end", f" - {spec.help}\n", "bullet")

    def _render_about(self) -> None:
        self._begin()
        self.text.insert("end", f"{about.APP_NAME}\n", "title")
        self.text.insert("end", f"Version {about.VERSION}\n", "summary")
        self.text.insert("end", f"{about.COPYRIGHT}\n", "copyright")
        self.text.insert(
            "end",
            f"Licensed under the {about.LICENSE_NAME} ({about.LICENSE_SPDX}).\n"
            "You may not use this software except in compliance with the "
            "License. Unless required by applicable law or agreed to in "
            'writing, it is distributed on an "AS IS" BASIS, WITHOUT '
            "WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n"
            f"{about.LICENSE_URL}\n",
            "summary",
        )

        self.text.insert("end", "Built with\n", "heading")
        python_version = ".".join(str(number) for number in sys.version_info[:3])
        self._bullet(f"Python {python_version} - PSF licence")
        for name, version, licence in about.installed_versions():
            self._bullet(f"{name} {version} - {licence}")

        self.text.insert("end", "Licence files\n", "heading")
        self._bullet("Full licence and NOTICE open with the buttons below; both "
                     "are bundled inside the application.")
        self._bullet("A packaged build also ships THIRD-PARTY-LICENSES.txt "
                     "next to the executable, covering every bundled library.")
        self._end()

    # -- licence viewers --------------------------------------------------
    def _show_text(self, title: str, body: str | None) -> None:
        """Open a read-only viewer; explains itself if the file was not shipped."""
        if body is None:
            body = (
                f"{title} was not found next to the application.\n\n"
                f"The full licence text is available at {about.LICENSE_URL}"
            )
        window = tk.Toplevel(self)
        window.title(title)
        window.geometry("720x560")
        window.rowconfigure(0, weight=1)
        window.columnconfigure(0, weight=1)

        text = tk.Text(window, wrap="word", padx=12, pady=10,
                       font=tkfont.nametofont("TkFixedFont"))
        scrollbar = ttk.Scrollbar(window, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        text.insert("1.0", body)
        text.configure(state="disabled")
        window.bind("<Escape>", lambda _event: window.destroy())
        window.transient(self)
        window.lift()
