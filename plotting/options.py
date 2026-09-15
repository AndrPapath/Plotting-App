# Copyright 2024-2026 Andreas Papathanasiou
# SPDX-License-Identifier: Apache-2.0

"""Typed option specifications shared by the plotting modules.

Every plot module describes its side panel as a list of :class:`OptionSpec`.
The GUI builds widgets from those specs and converts the widget values back
into a typed :class:`Options` mapping, so a plot module never has to guess
whether ``options["Font Size"]`` is an ``int``, a ``str`` or something else.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

__all__ = [
    "PlottingError",
    "OptionError",
    "OptionSpec",
    "Options",
    "ensure_options",
    "specs_by_label",
    "LEGEND_LOCATIONS",
    "X_AXIS_INDEX",
    "x_axis_index_spec",
]

#: Reserved label. Modules that declare it get the trace index the user picked
#: as the X axis in the trace window; the GUI injects the value on every draw.
X_AXIS_INDEX = "X axis Index"

LEGEND_LOCATIONS: tuple[str, ...] = (
    "best",
    "upper left",
    "upper center",
    "upper right",
    "lower left",
    "lower center",
    "lower right",
    "center left",
    "center right",
    "center",
    "outside upper left",
    "outside upper center",
    "outside upper right",
    "outside lower left",
    "outside lower center",
    "outside lower right",
    "outside left upper",
    "outside left center",
    "outside left lower",
    "outside right upper",
    "outside right center",
    "outside right lower",
)


class PlottingError(Exception):
    """A problem the user can fix, reported verbatim in the GUI.

    Anything else escaping a plot module is a bug and is reported with its
    traceback instead.
    """


class OptionError(PlottingError, ValueError):
    """Raised when a user supplied value cannot be used.

    The message is meant to be shown to the user as-is, so it always names the
    offending field.
    """


@dataclass(frozen=True)
class OptionSpec:
    """Declarative description of a single side panel field."""

    label: str
    kind: str  # "text" | "int" | "float" | "bool" | "choice"
    default: Any
    choices: tuple[str, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    hidden: bool = False
    help: str = ""

    KINDS = ("text", "int", "float", "bool", "choice")

    def __post_init__(self) -> None:
        if self.kind not in self.KINDS:
            raise ValueError(f"{self.label!r}: unknown option kind {self.kind!r}")
        if self.kind == "choice" and not self.choices:
            raise ValueError(f"{self.label!r}: a choice option needs choices")
        # Fail loudly at import time rather than at the first click.
        self.coerce(self.default)

    def coerce(self, raw: Any) -> Any:
        """Convert a raw widget value to this spec's type.

        Raises :class:`OptionError` with a user readable message on bad input.
        """
        if self.kind == "text":
            return "" if raw is None else str(raw)
        if self.kind == "bool":
            return self._coerce_bool(raw)
        if self.kind == "choice":
            value = str(raw)
            if value not in self.choices:
                raise OptionError(
                    f"{self.label}: {value!r} is not one of {', '.join(self.choices)}"
                )
            return value
        return self._coerce_number(raw)

    def _coerce_bool(self, raw: Any) -> bool:
        if isinstance(raw, str):
            text = raw.strip().lower()
            if text in ("1", "true", "yes", "on"):
                return True
            if text in ("0", "false", "no", "off", ""):
                return False
            raise OptionError(f"{self.label}: {raw!r} is not a yes/no value")
        return bool(raw)

    def _coerce_number(self, raw: Any) -> int | float:
        text = str(raw).strip()
        if text == "":
            # An emptied entry box means "use the default", not "crash".
            return self.default
        try:
            value: int | float = float(text)
        except (TypeError, ValueError):
            raise OptionError(f"{self.label}: {raw!r} is not a number") from None
        if not math.isfinite(value):
            raise OptionError(f"{self.label}: {raw!r} is not a finite number")
        if self.kind == "int":
            if not float(value).is_integer():
                raise OptionError(f"{self.label}: {raw!r} is not a whole number")
            value = int(value)
        if self.minimum is not None and value < self.minimum:
            raise OptionError(f"{self.label}: must be at least {self.minimum}")
        if self.maximum is not None and value > self.maximum:
            raise OptionError(f"{self.label}: must be at most {self.maximum}")
        return value


def specs_by_label(specs: Iterable[OptionSpec]) -> dict[str, OptionSpec]:
    """Index a spec sequence by label, rejecting duplicates."""
    indexed: dict[str, OptionSpec] = {}
    for spec in specs:
        if spec.label in indexed:
            raise ValueError(f"duplicate option label {spec.label!r}")
        indexed[spec.label] = spec
    return indexed


@dataclass(frozen=True)
class Options(Mapping):
    """Read-only, spec-backed view over the values collected from the panel.

    Missing keys fall back to the spec default, so a plot module keeps working
    if the panel is rebuilt or an older configuration is replayed.
    """

    values: Mapping[str, Any] = field(default_factory=dict)
    specs: Mapping[str, OptionSpec] = field(default_factory=dict)

    @classmethod
    def from_specs(
        cls, specs: Sequence[OptionSpec], values: Mapping[str, Any] | None = None
    ) -> "Options":
        indexed = specs_by_label(specs)
        raw = dict(values or {})
        coerced = {
            label: indexed[label].coerce(value)
            for label, value in raw.items()
            if label in indexed
        }
        return cls(values=coerced, specs=indexed)

    def with_values(self, **extra: Any) -> "Options":
        """Return a copy with ``extra`` merged in (used to inject GUI state)."""
        merged = dict(self.values)
        for label, value in extra.items():
            spec = self.specs.get(label)
            merged[label] = spec.coerce(value) if spec else value
        return Options(values=merged, specs=self.specs)

    # -- Mapping protocol -------------------------------------------------
    def __getitem__(self, label: str) -> Any:
        if label in self.values:
            return self.values[label]
        spec = self.specs.get(label)
        if spec is None:
            raise KeyError(label)
        return spec.default

    def __iter__(self):
        seen = list(self.specs)
        seen += [label for label in self.values if label not in self.specs]
        return iter(seen)

    def __len__(self) -> int:
        return len(set(self.specs) | set(self.values))

    # -- Typed accessors --------------------------------------------------
    def _typed(self, label: str, kind: str, fallback: Any) -> Any:
        try:
            raw = self[label]
        except KeyError:
            return fallback
        spec = self.specs.get(label)
        if spec is None:
            spec = OptionSpec(label, kind, fallback)
        return spec.coerce(raw)

    def text(self, label: str, fallback: str = "") -> str:
        return str(self._typed(label, "text", fallback))

    def flag(self, label: str, fallback: bool = False) -> bool:
        return bool(self._typed(label, "bool", fallback))

    def integer(self, label: str, fallback: int = 0) -> int:
        return int(self._typed(label, "int", fallback))

    def number(self, label: str, fallback: float = 0.0) -> float:
        return float(self._typed(label, "float", fallback))

    def choice(self, label: str, fallback: str = "") -> str:
        try:
            return str(self[label])
        except KeyError:
            return fallback


def ensure_options(options: Any, specs: Sequence[OptionSpec]) -> Options:
    """Accept either an :class:`Options` or a plain mapping from a script/test."""
    if isinstance(options, Options):
        return options
    return Options.from_specs(specs, options or {})


def x_axis_index_spec() -> OptionSpec:
    """Spec for the hidden X-axis selection injected by the trace window."""
    return OptionSpec(
        X_AXIS_INDEX,
        "int",
        0,
        minimum=0,
        hidden=True,
        help="Index of the trace used as the X axis.",
    )
