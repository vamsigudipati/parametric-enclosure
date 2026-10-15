"""Face, edge and vertex counts of the B-rep."""

import pytest

from enclosure import Params, build_enclosure
from enclosure.model import expected_topology
from tests.conftest import report


def counts(part):
    return len(part.faces()), len(part.edges()), len(part.vertices())


def test_default_topology(default_part):
    """Proves the default part has exactly 31 faces, 72 edges and 48 vertices."""
    got = counts(default_part)
    report("topology[default]", faces=got[0], edges=got[1], vertices=got[2])
    assert got == (31, 72, 48)


@pytest.mark.parametrize("grid", [(1, 1), (1, 2), (3, 2)])
def test_topology_scales_with_post_count(grid):
    """Proves each post adds exactly 3 faces, 6 edges and 4 vertices.

    One post is one cylinder wall, one top annulus and one hole wall. Each of
    the two cylinders carries a seam edge with two vertices plus two circles.
    """
    nx, ny = grid
    params = Params(posts_x=nx, posts_y=ny)
    got = counts(build_enclosure(params))
    n = nx * ny
    report(f"topology[{n} posts]", faces=got[0], edges=got[1], vertices=got[2])
    assert got == expected_topology(params)
    assert got == (31 + 3 * (n - 4), 72 + 6 * (n - 4), 48 + 4 * (n - 4))
