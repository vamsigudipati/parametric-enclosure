"""Mesh integrity of the exported STL, checked with trimesh."""

import pytest
import trimesh

from enclosure import Params, build_enclosure, export_stl
from tests.conftest import report

TOLERANCES = [0.1, 0.01]


@pytest.mark.parametrize("tolerance", TOLERANCES)
@pytest.mark.parametrize("hole_blind", [False, True], ids=["through", "blind"])
def test_stl_is_a_clean_closed_mesh(tmp_path, tolerance, hole_blind):
    """Proves the STL is watertight, one body, consistently wound, with the right Euler characteristic.

    A closed surface of genus g has V - E + F = 2 - 2g. Blind holes give a
    genus 0 solid and chi = 2. Every through-hole is a tunnel from the cavity
    to the underside, so the April default is genus 4 and chi = -6. The
    Euler number alone tells you the floor is perforated.
    """
    params = Params(hole_blind=hole_blind)
    part = build_enclosure(params)
    path = export_stl(part, tmp_path / f"enclosure_{tolerance}.stl", tolerance=tolerance)
    mesh = trimesh.load(path, force="mesh")

    expected_euler = 2 - 2 * (0 if hole_blind else params.n_posts)
    report(
        f"stl_integrity[{'blind' if hole_blind else 'through'}, tol={tolerance}]",
        triangles=len(mesh.faces),
        watertight=mesh.is_watertight,
        bodies=mesh.body_count,
        winding_consistent=mesh.is_winding_consistent,
        euler=mesh.euler_number,
    )
    assert mesh.is_watertight
    assert mesh.body_count == 1
    assert mesh.is_winding_consistent
    assert mesh.is_volume
    assert mesh.euler_number == expected_euler
