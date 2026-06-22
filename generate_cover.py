"""
Kiro MagLev - Rear Cover with Engraved Text
=============================================
Cover that plugs into the rear magnetic box cavity.
Outside face has "Design by AWS Kiro" engraved.
"""

import numpy as np
import trimesh
import math


def create_rounded_box(width, height, depth, corner_radius=1.5, segments=8):
    """Create a box with rounded edges (XZ face, extruded along Y)."""
    # Create 2D rounded rectangle profile in XZ
    hw, hh = width / 2, height / 2
    cr = min(corner_radius, hw, hh)
    
    profile = []
    # Four corners with arcs
    corners = [
        (hw - cr, hh - cr, 0, math.pi/2),
        (-hw + cr, hh - cr, math.pi/2, math.pi),
        (-hw + cr, -hh + cr, math.pi, 1.5*math.pi),
        (hw - cr, -hh + cr, 1.5*math.pi, 2*math.pi),
    ]
    for cx, cz, start_a, end_a in corners:
        for i in range(segments + 1):
            a = start_a + (end_a - start_a) * i / segments
            profile.append([cx + cr * math.cos(a), cz + cr * math.sin(a)])
    
    # Extrude along Y
    n = len(profile)
    verts = []
    faces = []
    
    # Front face (Y=0)
    for x, z in profile:
        verts.append([x, 0, z])
    # Back face (Y=depth)
    for x, z in profile:
        verts.append([x, depth, z])
    
    # Front center
    fc = len(verts)
    verts.append([0, 0, 0])
    # Back center
    bc = len(verts)
    verts.append([0, depth, 0])
    
    # Side faces
    for i in range(n):
        ni = (i + 1) % n
        faces.append([i, ni, n + ni])
        faces.append([i, n + ni, n + i])
    
    # Front cap
    for i in range(n):
        ni = (i + 1) % n
        faces.append([fc, i, ni])
    
    # Back cap
    for i in range(n):
        ni = (i + 1) % n
        faces.append([bc, n + ni, n + i])
    
    mesh = trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces))
    mesh.fix_normals()
    return mesh


def create_text_mesh(text, font_size=5.0, depth=0.5):
    """Create 3D text mesh for engraving using trimesh's text generation."""
    try:
        # Try to create text path and extrude
        from trimesh.path import Path2D
        from trimesh.creation import extrude_polygon
        from shapely.geometry import MultiPolygon
        import shapely
        
        # Create 2D text
        text_path = trimesh.path.entities.Text(text)
        # This may not work on all systems, fallback below
        raise ImportError("Use fallback")
    except (ImportError, Exception):
        # Fallback: create simple block letters
        return create_block_text(text, font_size, depth)


def create_block_text(text, char_height=5.0, depth=0.5):
    """Create simple engraved text using basic rectangular letter forms."""
    # Simple block font - each character is defined as a set of rectangles
    # relative to a char_width x char_height bounding box
    char_width = char_height * 0.6
    spacing = char_height * 0.2
    
    # Define simplified block letters as list of (x, z, w, h) rectangles
    # Coordinates relative to character origin (bottom-left)
    cw, ch = char_width, char_height
    sw = cw * 0.2  # stroke width
    
    font = {
        'D': [(0,0,sw,ch), (0,ch-sw,cw*0.7,sw), (0,0,cw*0.7,sw), (cw*0.7,sw,sw,ch-2*sw)],
        'e': [(0,0,sw,ch*0.6), (0,ch*0.6-sw,cw,sw), (0,0,cw,sw), (0,ch*0.3-sw/2,cw*0.8,sw), (cw-sw,ch*0.3,sw,ch*0.3-sw)],
        's': [(0,0,cw,sw), (cw-sw,0,sw,ch*0.3), (0,ch*0.3-sw/2,cw,sw), (0,ch*0.3,sw,ch*0.3-sw), (0,ch*0.6-sw,cw,sw)],
        'i': [(cw*0.35,0,sw,ch*0.6), (cw*0.35,ch*0.7,sw,sw)],
        'g': [(0,0,cw,sw), (cw-sw,-ch*0.2,sw,ch*0.2), (0,-ch*0.2,cw,sw), (0,0,sw,ch*0.6), (0,ch*0.6-sw,cw,sw), (cw-sw,ch*0.3,sw,ch*0.3-sw)],
        'n': [(0,0,sw,ch*0.6), (0,ch*0.6-sw,cw*0.8,sw), (cw-sw,0,sw,ch*0.6)],
        ' ': [],
        'b': [(0,0,sw,ch), (0,ch*0.6-sw,cw*0.8,sw), (0,0,cw*0.8,sw), (cw*0.8-sw,0,sw,ch*0.6)],
        'y': [(0,ch*0.3,sw,ch*0.3), (cw-sw,0,sw,ch*0.6), (0,0,cw,sw), (0,-ch*0.2,cw,sw), (0,-ch*0.2,sw,ch*0.2)],
        'A': [(0,0,sw,ch), (cw-sw,0,sw,ch), (0,ch-sw,cw,sw), (0,ch*0.5,cw,sw)],
        'W': [(0,0,sw,ch), (cw-sw,0,sw,ch), (cw*0.5-sw/2,0,sw,ch*0.6), (0,0,cw,sw)],
        'S': [(0,0,cw,sw), (cw-sw,0,sw,ch*0.5), (0,ch*0.5-sw/2,cw,sw), (0,ch*0.5,sw,ch*0.5-sw), (0,ch-sw,cw,sw)],
        'K': [(0,0,sw,ch), (sw,ch*0.5-sw/2,cw*0.3,sw), (cw*0.5,ch*0.5,sw,ch*0.5), (cw*0.5,0,sw,ch*0.5)],
        'r': [(0,0,sw,ch*0.6), (0,ch*0.6-sw,cw*0.7,sw), (cw*0.7-sw,ch*0.3,sw,ch*0.3)],
        'o': [(0,0,sw,ch*0.6), (cw-sw,0,sw,ch*0.6), (0,0,cw,sw), (0,ch*0.6-sw,cw,sw)],
    }
    
    meshes = []
    x_offset = 0
    
    for char in text:
        rects = font.get(char, font.get(char.lower(), []))
        for rx, rz, rw, rh in rects:
            # Create a small box for each stroke
            box = trimesh.primitives.Box(extents=[rw, depth, rh])
            box.apply_translation([x_offset + rx + rw/2, depth/2, rz + rh/2])
            meshes.append(box)
        x_offset += char_width + spacing
    
    if meshes:
        combined = trimesh.util.concatenate(meshes)
        return combined, x_offset - spacing
    return None, 0


def main():
    print("Kiro MagLev - Rear Cover Generator")
    print("=" * 40)
    
    # --- Cover dimensions ---
    cavity_w = 62.0  # cavity width (X)
    cavity_h = 12.0  # cavity height (Z)
    
    plug_w = 61.0    # plug slightly smaller for fit (0.5mm gap each side)
    plug_h = 11.0    # plug height
    plug_depth = 5.0  # how far plug goes into cavity
    
    flange_w = 66.0  # flange wider than cavity (2mm lip each side)
    flange_h = 16.0  # flange taller (2mm lip top and bottom)
    flange_depth = 2.5  # flange thickness
    
    text_str = "Design by AWS Kiro"
    text_depth = 0.8  # engraving depth
    
    print(f"  Cavity opening: {cavity_w}x{cavity_h}mm")
    print(f"  Plug: {plug_w}x{plug_h}x{plug_depth}mm")
    print(f"  Flange: {flange_w}x{flange_h}x{flange_depth}mm")
    print(f"  Text: '{text_str}' engraved {text_depth}mm deep")
    
    # --- Create plug (goes inside cavity) ---
    plug = trimesh.primitives.Box(extents=[plug_w, plug_depth, plug_h])
    plug.apply_translation([0, -plug_depth/2, 0])  # plug extends in -Y direction
    
    # --- Create flange (sits on outside surface) ---
    flange = trimesh.primitives.Box(extents=[flange_w, flange_depth, flange_h])
    flange.apply_translation([0, flange_depth/2, 0])  # flange extends in +Y direction
    
    # --- Combine plug and flange ---
    cover = trimesh.util.concatenate([plug, flange])
    cover.fix_normals()
    
    # --- Create text for engraving ---
    text_mesh, text_width = create_block_text(text_str, char_height=4.0, depth=text_depth + 0.5)
    
    if text_mesh is not None:
        # Center text on flange outer face
        # Text is currently at origin, needs to be moved to flange outer face
        text_bounds = text_mesh.bounds
        text_center_x = (text_bounds[0][0] + text_bounds[1][0]) / 2
        text_center_z = (text_bounds[0][2] + text_bounds[1][2]) / 2
        
        # Move text to center of flange, on outer face (Y = flange_depth)
        text_mesh.apply_translation([
            -text_center_x,  # center X
            flange_depth - text_depth/2,  # on outer face
            -text_center_z   # center Z
        ])
        
        # Boolean subtract text from cover
        print("  Engraving text...")
        try:
            cover = trimesh.boolean.difference([cover, text_mesh], engine='manifold')
            print("  Text engraved successfully")
        except Exception as e:
            print(f"  Text engraving failed: {e}")
            print("  Saving cover without text engraving")
    
    # --- Save ---
    cover.export('kiro_cover.stl')
    
    print(f"\n  SUMMARY:")
    print(f"  Cover: {flange_w}x{flange_h}mm flange + {plug_w}x{plug_h}x{plug_depth}mm plug")
    print(f"  Total depth: {plug_depth + flange_depth}mm")
    print(f"  Faces: {len(cover.faces)}")
    print(f"  Saved: kiro_cover.stl")


if __name__ == '__main__':
    main()
