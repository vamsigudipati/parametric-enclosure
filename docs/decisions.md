# Decisions

Why the options and defaults are what they are.

## Defaults reproduce the April file

Every default in `Params` is the value the April 2026 script used, including
the two it never named. The test `test_default_reproduces_the_april_step`
rebuilds the part and takes the symmetric difference against
`original/my_enclosure_v1.step`. It is zero. That is the anchor for everything
else: if I change a default, that test tells me the reference file no longer
matches.

## `hole_blind` (default `False`)

The April script subtracted a cylinder of height H centred on the origin. The
box is also centred on the origin, so the hole ran from the top of the post
straight out of the underside of the floor. Nothing in the code said so.

`hole_blind=False` keeps that behaviour because it is what the shipped STEP
contains. `hole_blind=True` stops the hole at the top of the floor, so the
floor keeps its full thickness under the screw. I did not pick a depth into
the floor because that would be a third hidden number; the floor top is a
level that already exists in the model.

Two tests make the difference visible. The underside of the floor must have a
single wire and no closed circular edges when `hole_blind` is on, and the STL
Euler characteristic must be 2 for blind holes and 2 minus twice the hole
count for through-holes.

## `post_seat_depth` (default 1.0 mm)

The April post was a cylinder of height H minus thickness, centred on the
origin. With H = 30 and thickness = 2 that runs from z = -14 to z = +14. The
floor top is at z = -13, so the post sank 1 mm into the floor. The rim is at
z = +15, so the post top sat 1 mm below the rim. Both came out of one
expression and neither was a stated design intent.

The seat is now an explicit parameter. A seat of zero works (the tests build
it and the volume still matches), but a seat makes the fuse robust against
coplanar faces when parameters change, and it gives a fillet or chamfer
something to land on later. Valid range is 0 to the floor thickness; the
validator rejects a seat that would poke through.

The 1 mm below the rim became `post_top_recess` for the same reason. Posts
flush with the rim would clash with a lid that sits inside the wall.

## Post positions

The April grid used a pitch of L minus 15 for two posts, which puts the post
centres 7.5 mm from the outer wall. `post_inset` keeps that number and
`posts_x` / `posts_y` generalise it. The pitch is derived so that the outer
posts stay at the same inset regardless of count. The validator refuses a
layout where a post touches a wall, because the face count prediction and the
analytic volume both assume free-standing posts.

## STL export goes to Open CASCADE directly

build123d's `export_stl` calls the mesher with `isRelative=True`, so the
"tolerance" is scaled by each edge's size. It also does not clear an existing
triangulation, so the second export at a finer tolerance reuses the first
mesh. During the first run both exports came back with the same 5100
triangles. `enclosure/export.py` clears the triangulation and passes an
absolute deflection, which is the only way the deviation test means what it
says.

## Angular tolerance 0.5 rad

With the Open CASCADE default of 0.1 rad the angular limit decides the
cylinder facets and the linear tolerance never gets a vote: 0.1 mm and
0.01 mm produce the same mesh. At 0.5 rad the linear tolerance is the binding
constraint for both settings in the test, which is what a "linear tolerance
argument" should mean. The argument is exposed if you want the finer default
back.

## Deviation is measured mesh to B-rep, not B-rep to mesh

The question I want answered is "does any triangle lie off the true surface
by more than the tolerance", so points are sampled on the triangles and
measured against the exact faces with `BRepExtrema_DistShapeShape`. Sampling
the other way round would also need to catch missing geometry, which the
watertight and Euler checks already cover.

## Volume tolerance 0.1 percent

The brief. The kernel actually agrees with the closed form to about 1e-15
relative, because every face is planar or cylindrical and the fillet
correction is exact. The loose threshold is there so the test survives a
kernel upgrade that changes rounding, not because the geometry needs it.
