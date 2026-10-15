"""The hole_blind option must keep the floor closed."""

from build123d import Axis, GeomType

from enclosure import Params
from tests.conftest import report


def closed_circles(face):
    return [e for e in face.edges() if e.geom_type == GeomType.CIRCLE and e.is_closed]


def test_blind_floor_has_no_hole_edges(blind_part):
    """Proves that with hole_blind the underside of the floor has no circular hole edges.

    The four fillet arcs on the outline are circular too, but they are open
    arcs. A hole shows up as a closed circle and as an inner wire.
    """
    bottom = blind_part.faces().sort_by(Axis.Z)[0]
    circles = closed_circles(bottom)
    report("blind_holes[blind]", bottom_face_wires=len(bottom.wires()), closed_circles=len(circles))
    assert len(bottom.wires()) == 1
    assert circles == []


def test_through_floor_shows_the_holes(default_part, default_params):
    """Proves the detector is real: the April default has one circle per post on the underside."""
    bottom = default_part.faces().sort_by(Axis.Z)[0]
    circles = closed_circles(bottom)
    report("blind_holes[through]", bottom_face_wires=len(bottom.wires()), closed_circles=len(circles))
    assert len(circles) == default_params.n_posts
    assert all(abs(c.radius - default_params.hole_radius) < 1e-9 for c in circles)


def test_blind_adds_one_bottom_face_per_hole(default_part, blind_part):
    """Proves blind holes add exactly one planar face per post and nothing else."""
    assert len(blind_part.faces()) - len(default_part.faces()) == Params().n_posts
    assert len(blind_part.edges()) == len(default_part.edges())
    assert len(blind_part.vertices()) == len(default_part.vertices())
