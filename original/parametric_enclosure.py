from build123d import *
from ocp_vscode import show

# 1. PARAMETERS (Define these so the AI can see your logic)
L, W, H = 100.0, 60.0, 30.0  # External dimensions
THICKNESS = 2.0               # Wall thickness
FILLET_RADIUS = 5.0           # External corner rounding
POST_RADIUS = 4.0             # Corner screw post size

# 2. THE MODELING WORKFLOW
with BuildPart() as enclosure:
    # Create the main block
    Box(L, W, H)
    
    # Fillet all vertical edges (Logic-based selection)
    vertical_edges = enclosure.edges().filter_by(Axis.Z)
    fillet(vertical_edges, radius=FILLET_RADIUS)
    
    # Hollow out the top (Shelling operation)
    # We select the top face by sorting along the Z axis
    top_face = enclosure.faces().sort_by(Axis.Z)[-1]
    offset(amount=-THICKNESS, openings=[top_face])
    
    # Add mounting posts in the corners
    # GridLocations automatically calculates the spacing
    with GridLocations(L - 15, W - 15, 2, 2):
        Cylinder(radius=POST_RADIUS, height=H - THICKNESS, mode=Mode.ADD)

    # Subtract screw holes from those posts
    with GridLocations(L - 15, W - 15, 2, 2):
        # M3 screw hole
        Cylinder(radius=1.5, height=H, mode=Mode.SUBTRACT)

# 3. EXPORT FOR VALIDATION
# This generates the 'B' model for your symmetric difference test
export_step(enclosure.part, "my_enclosure_v1.step")

print(f"Enclosure volume: {enclosure.part.volume} mm^3")
show(enclosure.part)