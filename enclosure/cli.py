"""python -m enclosure build --params params/default.json --out out/"""

from __future__ import annotations

import argparse
from pathlib import Path

from .compare import load_step, symmetric_difference
from .export import DEFAULT_STL_TOLERANCE, export_step, export_stl
from .model import Params, analytic_volume, build_enclosure, expected_topology


def _build(args: argparse.Namespace) -> int:
    params = Params.from_json(args.params) if args.params else Params()
    part = build_enclosure(params)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    step = export_step(part, out / f"{args.name}.step")
    stl = export_stl(part, out / f"{args.name}.stl", tolerance=args.stl_tolerance)
    params.to_json(out / f"{args.name}.params.json")

    kernel = part.volume
    analytic = analytic_volume(params)
    faces, edges, vertices = len(part.faces()), len(part.edges()), len(part.vertices())
    print(f"wrote {step}")
    print(f"wrote {stl} (tolerance {args.stl_tolerance} mm)")
    print(f"volume kernel   {kernel:.3f} mm^3")
    print(f"volume analytic {analytic:.3f} mm^3  (rel. error {abs(kernel - analytic) / analytic:.2e})")
    print(f"topology F/E/V  {faces}/{edges}/{vertices}  expected {expected_topology(params)}")
    return 0


def _diff(args: argparse.Namespace) -> int:
    a = load_step(args.a)
    b = load_step(args.b)
    d = symmetric_difference(a, b)
    print(f"volume A          {a.volume:.3f} mm^3")
    print(f"volume B          {b.volume:.3f} mm^3")
    print(f"A minus B         {d.a_minus_b:.3f} mm^3")
    print(f"B minus A         {d.b_minus_a:.3f} mm^3")
    print(f"symmetric diff    {d.total:.3f} mm^3")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m enclosure")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="build the part and export STEP and STL")
    build.add_argument("--params", help="JSON file with Params fields (default: built-in defaults)")
    build.add_argument("--out", default="out", help="output directory (default: out/)")
    build.add_argument("--name", default="enclosure", help="base file name (default: enclosure)")
    build.add_argument("--stl-tolerance", type=float, default=DEFAULT_STL_TOLERANCE,
                       help=f"STL linear tolerance in mm (default: {DEFAULT_STL_TOLERANCE})")
    build.set_defaults(func=_build)

    diff = sub.add_parser("diff", help="symmetric difference between two STEP files")
    diff.add_argument("a")
    diff.add_argument("b")
    diff.set_defaults(func=_diff)

    args = parser.parse_args(argv)
    return args.func(args)
