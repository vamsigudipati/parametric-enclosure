"""Kernel volume against the closed-form volume derived from the parameters."""

import pytest

from enclosure import Params, analytic_volume, build_enclosure
from tests.conftest import report

CASES = {
    "default": Params(),
    "blind_holes": Params(hole_blind=True),
    "thick_wall": Params(thickness=3.0),
    "six_posts": Params(posts_x=3, posts_y=2),
    "no_seat": Params(post_seat_depth=0.0),
}


@pytest.mark.parametrize("name", CASES)
def test_volume_matches_analytic(name):
    """Proves the kernel volume equals the hand-derived volume within 0.1 percent.

    The expected value is box minus shelled cavity minus holes plus posts, with
    the corner fillets accounted for exactly through the (4 - pi) r^2 term.
    """
    params = CASES[name]
    kernel = build_enclosure(params).volume
    expected = analytic_volume(params)
    rel = abs(kernel - expected) / expected
    report(f"volume[{name}]", kernel=f"{kernel:.3f}", analytic=f"{expected:.3f}", rel_err=f"{rel:.1e}")
    assert rel < 1e-3
