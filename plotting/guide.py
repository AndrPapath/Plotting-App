# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""Structured help text a plot module can offer about itself.

Each module exposes a module-level ``GUIDE``; the GUI renders it in the info
window. Keeping it structured (rather than one blob of text) means every mode
is documented in the same shape, and the renderer stays simple.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["Guide"]


@dataclass(frozen=True)
class Guide:
    """What a mode draws, what it expects from the file, and how to drive it."""

    #: One or two sentences: what this mode is for.
    summary: str
    #: How the columns of the file need to be arranged.
    data_layout: tuple[str, ...] = field(default_factory=tuple)
    #: The click-by-click path from a loaded file to a finished plot.
    steps: tuple[str, ...] = field(default_factory=tuple)
    #: Non-obvious options and the mistakes they prevent.
    tips: tuple[str, ...] = field(default_factory=tuple)

    def sections(self) -> list[tuple[str, tuple[str, ...]]]:
        """Return ``(heading, items)`` pairs, skipping the empty ones."""
        candidates = (
            ("Expected data layout", self.data_layout),
            ("Step by step", self.steps),
            ("Tips", self.tips),
        )
        return [(heading, items) for heading, items in candidates if items]
