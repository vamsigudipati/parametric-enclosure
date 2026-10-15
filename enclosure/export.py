"""STEP and STL export.

The STL path talks to Open CASCADE directly for two reasons that the tests
depend on:

1. The deflection is absolute. build123d's export_stl passes isRelative=True,
   which scales the tolerance by the size of each edge, so "0.1 mm" does not
   mean 0.1 mm on a 100 mm edge.
2. Any triangulation already cached on the shape is cleared first. Otherwise
   a second export at a different tolerance silently reuses the first mesh.
"""

from __future__ import annotations

from pathlib import Path

from build123d import Shape
from build123d import export_step as _export_step
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepTools import BRepTools
from OCP.StlAPI import StlAPI_Writer

DEFAULT_STL_TOLERANCE = 0.1
# Loose enough that the linear tolerance, not the angle, decides the mesh.
DEFAULT_ANGULAR_TOLERANCE = 0.5


def export_step(shape: Shape, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not _export_step(shape, str(path)):
        raise RuntimeError(f"STEP export failed: {path}")
    return path


def export_stl(
    shape: Shape,
    path: str | Path,
    tolerance: float = DEFAULT_STL_TOLERANCE,
    angular_tolerance: float = DEFAULT_ANGULAR_TOLERANCE,
    ascii_format: bool = False,
) -> Path:
    """Write a binary STL whose chordal deviation is at most `tolerance` mm."""
    if tolerance <= 0:
        raise ValueError("tolerance must be positive")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    BRepTools.Clean_s(shape.wrapped)
    mesher = BRepMesh_IncrementalMesh(
        shape.wrapped, tolerance, False, angular_tolerance, True
    )
    mesher.Perform()
    if not mesher.IsDone():
        raise RuntimeError("meshing failed")

    writer = StlAPI_Writer()
    writer.ASCIIMode = ascii_format
    if not writer.Write(shape.wrapped, str(path)):
        raise RuntimeError(f"STL export failed: {path}")
    return path
