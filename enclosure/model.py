"""Geometry of the enclosure and the hand-derived volume it must match.

Coordinates follow the April 2026 script: the outer box is centred on the
origin, so the floor's underside is at z = -H/2 and the open rim is at
z = +H/2.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path

from build123d import (
    Axis,
    Box,
    BuildPart,
    Cylinder,
    GridLocations,
    Locations,
    Mode,
    Part,
    fillet,
    offset,
)


@dataclass(frozen=True)
class Params:
    """All dimensions in millimetres. The defaults reproduce my_enclosure_v1.step."""

    L: float = 100.0
    W: float = 60.0
    H: float = 30.0
    thickness: float = 2.0
    fillet_radius: float = 5.0
    post_radius: float = 4.0
    hole_radius: float = 1.5
    # Option 1: through-holes (April behaviour) or blind holes that stop at
    # the top of the floor.
    hole_blind: bool = False
    # Option 2: how far the post is sunk into the floor. The April script
    # sank it 1.0 mm without saying so.
    post_seat_depth: float = 1.0
    # Distance from the open rim down to the top of each post.
    post_top_recess: float = 1.0
    # Distance from the outer wall to the post centre.
    post_inset: float = 7.5
    posts_x: int = 2
    posts_y: int = 2

    # ---- derived levels -------------------------------------------------
    @property
    def floor_top(self) -> float:
        return -self.H / 2 + self.thickness

    @property
    def post_top(self) -> float:
        return self.H / 2 - self.post_top_recess

    @property
    def post_bottom(self) -> float:
        return self.floor_top - self.post_seat_depth

    @property
    def hole_bottom(self) -> float:
        return self.floor_top if self.hole_blind else -self.H / 2

    @property
    def n_posts(self) -> int:
        return self.posts_x * self.posts_y

    @property
    def inner_fillet_radius(self) -> float:
        return max(self.fillet_radius - self.thickness, 0.0)

    def post_pitch(self, span: float, count: int) -> float:
        """Centre-to-centre distance for `count` posts across an outer span."""
        return (span - 2 * self.post_inset) / (count - 1) if count > 1 else 1.0

    # ---- checks -----------------------------------------------------------
    def validate(self) -> None:
        if min(self.L, self.W, self.H) <= 0 or self.thickness <= 0:
            raise ValueError("L, W, H and thickness must be positive")
        if 2 * self.thickness >= min(self.L, self.W):
            raise ValueError("walls meet in the middle: 2 * thickness >= min(L, W)")
        if self.fillet_radius <= 0 or 2 * self.fillet_radius > min(self.L, self.W):
            raise ValueError("fillet_radius must fit inside the footprint")
        if not 0.0 <= self.post_seat_depth <= self.thickness:
            raise ValueError("post_seat_depth must be between 0 and thickness")
        if self.post_top <= self.floor_top:
            raise ValueError("posts have no height above the floor")
        if self.hole_radius >= self.post_radius:
            raise ValueError("hole_radius must be smaller than post_radius")
        if self.posts_x < 1 or self.posts_y < 1:
            raise ValueError("need at least one post in each direction")
        for x, y in self.post_centres():
            if abs(x) + self.post_radius >= self.L / 2 - self.thickness:
                raise ValueError("a post touches the long wall")
            if abs(y) + self.post_radius >= self.W / 2 - self.thickness:
                raise ValueError("a post touches the short wall")

    def post_centres(self) -> list[tuple[float, float]]:
        px = self.post_pitch(self.L, self.posts_x)
        py = self.post_pitch(self.W, self.posts_y)
        xs = [(i - (self.posts_x - 1) / 2) * px for i in range(self.posts_x)]
        ys = [(j - (self.posts_y - 1) / 2) * py for j in range(self.posts_y)]
        return [(x, y) for x in xs for y in ys]

    # ---- serialisation ------------------------------------------------------
    def with_changes(self, **changes) -> "Params":
        return replace(self, **changes)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Params":
        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"unknown parameter(s): {sorted(unknown)}")
        return cls(**data)

    @classmethod
    def from_json(cls, path: str | Path) -> "Params":
        with open(path, encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))

    def to_json(self, path: str | Path) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
            fh.write("\n")


def build_enclosure(params: Params | None = None) -> Part:
    """Build the solid. Same operation order as the April script."""
    p = params or Params()
    p.validate()

    post_height = p.post_top - p.post_bottom
    hole_height = p.post_top - p.hole_bottom
    pitch_x = p.post_pitch(p.L, p.posts_x)
    pitch_y = p.post_pitch(p.W, p.posts_y)

    with BuildPart() as enclosure:
        Box(p.L, p.W, p.H)
        fillet(enclosure.edges().filter_by(Axis.Z), radius=p.fillet_radius)

        top_face = enclosure.faces().sort_by(Axis.Z)[-1]
        offset(amount=-p.thickness, openings=[top_face])

        with Locations((0, 0, (p.post_top + p.post_bottom) / 2)):
            with GridLocations(pitch_x, pitch_y, p.posts_x, p.posts_y):
                Cylinder(radius=p.post_radius, height=post_height, mode=Mode.ADD)

        with Locations((0, 0, (p.post_top + p.hole_bottom) / 2)):
            with GridLocations(pitch_x, pitch_y, p.posts_x, p.posts_y):
                Cylinder(radius=p.hole_radius, height=hole_height, mode=Mode.SUBTRACT)

    return enclosure.part


def rounded_rect_area(length: float, width: float, radius: float) -> float:
    """Area of a rectangle whose four corners are rounded with `radius`.

    Each corner loses a square of side r and gains back a quarter disc, so the
    exact correction is (4 - pi) * r^2 for the four corners together.
    """
    return length * width - (4.0 - math.pi) * radius * radius


def analytic_volume(params: Params | None = None) -> float:
    """Closed-form volume of the part, derived by hand from the parameters.

    V = outer block - cavity + posts above the floor - holes

    outer block : rounded-rect area (L, W, r) times H
    cavity      : rounded-rect area (L - 2t, W - 2t, r - t) times (H - t),
                  because shelling a filleted box with an open top gives an
                  inner fillet of r - t and a floor of thickness t
    posts       : n * pi * R^2 * (post_top - floor_top); the seat below the
                  floor top is already solid and adds nothing
    holes       : n * pi * rh^2 * (post_top - hole_bottom); through-holes
                  run to the underside, blind holes stop at the floor top
    """
    p = params or Params()
    outer = rounded_rect_area(p.L, p.W, p.fillet_radius) * p.H
    cavity = rounded_rect_area(
        p.L - 2 * p.thickness, p.W - 2 * p.thickness, p.inner_fillet_radius
    ) * (p.H - p.thickness)
    posts = p.n_posts * math.pi * p.post_radius**2 * (p.post_top - p.floor_top)
    holes = p.n_posts * math.pi * p.hole_radius**2 * (p.post_top - p.hole_bottom)
    return outer - cavity + posts - holes


def expected_topology(params: Params | None = None) -> tuple[int, int, int]:
    """Face, edge and vertex counts predicted from the construction.

    Shelled filleted box: 10 outer faces + 9 inner faces = 19, 48 edges,
    32 vertices. Each post adds its cylinder wall and top annulus plus the
    hole wall (3 faces, 6 edges, 4 vertices from the two seams). A blind hole
    adds a bottom disc per post, which reuses the existing hole circle, so
    only the face count changes.
    """
    p = params or Params()
    n = p.n_posts
    faces = 19 + 3 * n + (n if p.hole_blind else 0)
    edges = 48 + 6 * n
    vertices = 32 + 4 * n
    return faces, edges, vertices
