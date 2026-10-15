"""Revision diff: compare two STEP files by symmetric difference of volume."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from build123d import Shape, ShapeList, import_step


@dataclass(frozen=True)
class SymmetricDifference:
    a_minus_b: float
    b_minus_a: float

    @property
    def total(self) -> float:
        return self.a_minus_b + self.b_minus_a


def load_step(path: str | Path) -> Shape:
    shape = import_step(str(path))
    solids = shape.solids()
    if len(solids) != 1:
        raise ValueError(f"{path}: expected one solid, found {len(solids)}")
    return solids[0]


def _volume(result) -> float:
    # A boolean that removes everything comes back as an empty ShapeList.
    if isinstance(result, ShapeList):
        return sum(s.volume for s in result)
    return result.volume


def symmetric_difference(a: Shape, b: Shape) -> SymmetricDifference:
    return SymmetricDifference(a_minus_b=_volume(a - b), b_minus_a=_volume(b - a))
