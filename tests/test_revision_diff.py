"""Symmetric difference between two STEP files as a revision check."""

from enclosure import Params, analytic_volume, build_enclosure, export_step, load_step, symmetric_difference
from tests.conftest import APRIL_STEP, report


def test_thicker_wall_differs_by_the_expected_volume(tmp_path):
    """Proves the symmetric difference between the default and a 1 mm thicker wall equals the analytic value.

    The thicker wall contains the thinner one, so A minus B must be empty and
    B minus A must equal the difference of the two closed-form volumes.
    Both parts go through STEP on disk, so the check covers the exporter too.
    """
    pa, pb = Params(), Params(thickness=3.0)
    a_path = export_step(build_enclosure(pa), tmp_path / "default.step")
    b_path = export_step(build_enclosure(pb), tmp_path / "thick_wall.step")

    d = symmetric_difference(load_step(a_path), load_step(b_path))
    expected = analytic_volume(pb) - analytic_volume(pa)
    report(
        "revision_diff[t=2 vs t=3]",
        a_minus_b=f"{d.a_minus_b:.3f}",
        b_minus_a=f"{d.b_minus_a:.3f}",
        symmetric_difference=f"{d.total:.3f}",
        analytic=f"{expected:.3f}",
    )
    assert d.a_minus_b < 1e-6
    assert abs(d.total - expected) / expected < 1e-6


def test_default_reproduces_the_april_step(tmp_path, default_part):
    """Proves the default parameters rebuild the April file: zero symmetric difference."""
    april = load_step(APRIL_STEP)
    d = symmetric_difference(default_part, april)
    report("revision_diff[default vs April]", symmetric_difference=f"{d.total:.6f}")
    assert d.total < 1e-6
