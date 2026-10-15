"""How far the triangles sit from the true surface."""

import numpy as np
import pytest
import trimesh

from enclosure import analytic_volume, export_stl
from tests.conftest import max_distance_to_brep, report

TOLERANCES = [0.1, 0.01]
SAMPLES = 4000


@pytest.mark.parametrize("tolerance", TOLERANCES)
def test_stl_deviation_below_tolerance(tmp_path, default_part, default_params, tolerance):
    """Proves the largest distance from the STL to the B-rep is below the requested tolerance.

    Points are sampled uniformly by area over the triangles, plus every
    triangle centroid, where the chordal error on a cylinder peaks. Each
    point is measured against the exact faces with BRepExtrema.
    """
    path = export_stl(default_part, tmp_path / f"enclosure_{tolerance}.stl", tolerance=tolerance)
    mesh = trimesh.load(path, force="mesh")

    samples, _ = trimesh.sample.sample_surface(mesh, SAMPLES, seed=0)
    points = np.vstack([samples, mesh.triangles_center])
    worst = max_distance_to_brep(points, default_part)

    volume_err = abs(mesh.volume - analytic_volume(default_params)) / analytic_volume(default_params)
    report(
        f"stl_deviation[tol={tolerance}]",
        triangles=len(mesh.faces),
        points=len(points),
        max_deviation_mm=f"{worst:.4f}",
        mesh_volume_rel_err=f"{volume_err:.2e}",
    )
    assert worst < tolerance
