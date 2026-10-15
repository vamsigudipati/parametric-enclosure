"""Render docs/enclosure.png from the default part.

Needs matplotlib, which is not in requirements.txt because the tests do not
use it:  python scripts/render_png.py [--params params/default.json]
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import trimesh  # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402

from enclosure import Params, build_enclosure, export_stl  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--params")
    ap.add_argument("--out", default=REPO / "docs" / "enclosure.png")
    args = ap.parse_args()

    params = Params.from_json(args.params) if args.params else Params()
    part = build_enclosure(params)
    with tempfile.TemporaryDirectory() as tmp:
        mesh = trimesh.load(export_stl(part, Path(tmp) / "r.stl", tolerance=0.02), force="mesh")
    # Small triangles keep matplotlib's painter's algorithm honest on the big flat faces.
    mesh = mesh.subdivide_to_size(max_edge=3.0)

    tris = mesh.triangles
    normals = mesh.face_normals
    light = np.array([-0.4, -0.6, 1.0])
    light /= np.linalg.norm(light)
    shade = 0.35 + 0.65 * np.clip(normals @ light, 0, 1)
    base = np.array([0.33, 0.52, 0.78])
    colors = np.clip(shade[:, None] * base, 0, 1)

    fig = plt.figure(figsize=(9, 6), dpi=160)
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection(tris, facecolors=colors, edgecolors=colors, linewidths=0.15))
    pad = 1.04
    ax.set_xlim(-pad * params.L / 2, pad * params.L / 2)
    ax.set_ylim(-pad * params.W / 2, pad * params.W / 2)
    ax.set_zlim(-pad * params.H / 2, pad * params.H / 2)
    ax.set_box_aspect((params.L, params.W, params.H), zoom=0.95)
    ax.view_init(elev=38, azim=-55)
    ax.set_axis_off()
    fig.subplots_adjust(0, 0, 1, 1)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, facecolor="white")
    print(f"wrote {out}  ({len(tris)} triangles)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
