"""Shared fixtures and the one helper that talks to the kernel for distances."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.gp import gp_Pnt

from enclosure import Params, build_enclosure

REPO = Path(__file__).resolve().parent.parent
APRIL_STEP = REPO / "original" / "my_enclosure_v1.step"


@pytest.fixture(scope="session")
def default_params() -> Params:
    return Params()


@pytest.fixture(scope="session")
def default_part(default_params):
    return build_enclosure(default_params)


@pytest.fixture(scope="session")
def blind_part():
    return build_enclosure(Params(hole_blind=True))


def max_distance_to_brep(points: np.ndarray, shape) -> float:
    """Largest exact distance from any of `points` to the B-rep surface."""
    worst = 0.0
    for x, y, z in points:
        vertex = BRepBuilderAPI_MakeVertex(gp_Pnt(float(x), float(y), float(z))).Vertex()
        dist = BRepExtrema_DistShapeShape(vertex, shape.wrapped)
        assert dist.IsDone()
        worst = max(worst, dist.Value())
    return worst


def report(label: str, **values) -> None:
    """One line per measurement so `pytest -rA` shows the numbers in the README."""
    body = "  ".join(f"{k}={v}" for k, v in values.items())
    print(f"REPORT {label}: {body}")
