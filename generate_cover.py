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


def create_text_mesh(text, target_width=60.0, depth=2.0):
    """Create 3D text mesh using matplotlib font rendering."""
    from shapely.geometry import Polygon
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    from trimesh.creation import extrude_polygon
    import matplotlib.path as mpath

    fp = FontProperties(family='sans-serif', weight='bold')
    tp = TextPath((0, 0), text, size=10, prop=fp)

    verts = tp.vertices
    codes = tp.codes

    # Convert matplotlib path to shapely polygons
    polygons = []
    current_poly = []
    for v, c in zip(verts, codes):
        if c == mpath.Path.MOVETO:
            if len(current_poly) > 2:
                try:
                    p = Polygon(current_poly)
                    if p.is_valid and p.area > 0.1:
                        polygons.append(p)
                except:
                    pass
            current_poly = [v.tolist()]
        elif c in (mpath.Path.LINETO, mpath.Path.CURVE3, mpath.Path.CURVE4):
            current_poly.append(v.tolist())
        elif c == mpath.Path.CLOSEPOLY:
            if len(current_poly) > 2:
                try:
                    p = Polygon(current_poly)
                    if p.is_valid and p.area > 0.1:
                        polygons.append(p)
                except:
                    pass
            current_poly = []

    if len(current_poly) > 2:
        try:
            p = Polygon(current_poly)
            if p.is_valid and p.area > 0.1:
                polygons.append(p)
        except:
            pass

    # Extrude each polygon and combine
    meshes = []
    for poly in polygons:
        try:
            m = extrude_polygon(poly, height=depth)
            meshes.append(m)
        except:
            pass

    if not meshes:
        return None

    text_3d = trimesh.util.concatenate(meshes)

    # Scale to fit target width
    bounds = text_3d.bounds
    text_w = bounds[1][0] - bounds[0][0]
    scale_factor = target_width / text_w

    text_3d.apply_scale(scale_factor)

    # Center at origin
    bounds = text_3d.bounds
    center = (bounds[0] + bounds[1]) / 2
    text_3d.apply_translation(-center)

    return text_3d


def create_block_text(text, char_height=5.0, depth=0.5):
    """Create simple engraved text using basic rectangular letter forms."""
    # Simple block font - each character is defined as a set of rectangles
    # relative to a char_width x char_height bounding box
    char_width = char_height * 0.6
    spacing = char_height * 0.2
    
    # Define simplified block letters as list of (x, z, w, h) rectangles
    # Coordinates relative to character origin (bottom-left)
    cw, ch = char_width, char_height
    sw = cw * 0.3  # stroke width (thicker for visibility)
    
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
    flange_depth = 3.0  # flange thickness (must be > text_depth)
    
    text_str = "Design by AWS Kiro"
    text_depth = 1.5  # deeper engraving for visibility
    
    print(f"  Cavity opening: {cavity_w}x{cavity_h}mm")
    print(f"  Plug: {plug_w}x{plug_h}x{plug_depth}mm")
    print(f"  Flange: {flange_w}x{flange_h}x{flange_depth}mm")
    print(f"  Text: '{text_str}' engraved {text_depth}mm deep")
    
    # --- Create plug (goes inside cavity) - with filleted leading edges ---
    # Use a slightly smaller box and subtract rounded edges using cylinders
    plug_mesh = trimesh.primitives.Box(extents=[plug_w, plug_depth, plug_h])
    plug_mesh.apply_translation([0, -plug_depth/2, 0])  # plug extends in -Y direction
    
    # Fillet the plug's leading edges (the 4 long edges at Y=-plug_depth end)
    # by subtracting rounded cylinders from the corners
    fillet_r = 1.5  # 1.5mm fillet radius
    # Create fillet by subtracting a "negative fillet" shape from corners
    # Easier: create the plug with rounded cross-section using convex hull approach
    # Actually, use boolean intersection with a rounded box
    # Simplest approach: subtract 4 corner strips from the plug
    plug_corners = []
    for sx in [-1, 1]:
        for sz in [-1, 1]:
            # Corner strip along Y axis at plug edges
            corner_box = trimesh.primitives.Box(extents=[fillet_r*2, plug_depth+1, fillet_r*2])
            corner_box.apply_translation([
                sx * (plug_w/2), 
                -plug_depth/2, 
                sz * (plug_h/2)
            ])
            # Cylinder to keep (the rounded part)
            corner_cyl = trimesh.primitives.Cylinder(
                radius=fillet_r, height=plug_depth+1, sections=16)
            rot = trimesh.transformations.rotation_matrix(math.pi/2, [1, 0, 0])
            corner_cyl.apply_transform(rot)
            corner_cyl.apply_translation([
                sx * (plug_w/2 - fillet_r),
                -plug_depth/2,
                sz * (plug_h/2 - fillet_r)
            ])
            # Subtract box, add cylinder back = fillet
            fillet_cut = trimesh.boolean.difference([corner_box, corner_cyl], engine='manifold')
            plug_corners.append(fillet_cut)
    
    for fc in plug_corners:
        plug_mesh = trimesh.boolean.difference([plug_mesh, fc], engine='manifold')
    
    # --- Create flange (sits on outside surface) - with filleted outer edges ---
    flange_mesh = trimesh.primitives.Box(extents=[flange_w, flange_depth, flange_h])
    flange_mesh.apply_translation([0, flange_depth/2, 0])  # flange extends in +Y direction
    
    # Fillet the flange's outer edges (4 edges on the +Y face)
    flange_fillet_r = 2.0  # 2mm fillet on flange
    flange_corners = []
    for sx in [-1, 1]:
        for sz in [-1, 1]:
            corner_box = trimesh.primitives.Box(extents=[flange_fillet_r*2, flange_depth+1, flange_fillet_r*2])
            corner_box.apply_translation([
                sx * (flange_w/2),
                flange_depth/2,
                sz * (flange_h/2)
            ])
            corner_cyl = trimesh.primitives.Cylinder(
                radius=flange_fillet_r, height=flange_depth+1, sections=16)
            rot = trimesh.transformations.rotation_matrix(math.pi/2, [1, 0, 0])
            corner_cyl.apply_transform(rot)
            corner_cyl.apply_translation([
                sx * (flange_w/2 - flange_fillet_r),
                flange_depth/2,
                sz * (flange_h/2 - flange_fillet_r)
            ])
            fillet_cut = trimesh.boolean.difference([corner_box, corner_cyl], engine='manifold')
            flange_corners.append(fillet_cut)
    
    for fc in flange_corners:
        flange_mesh = trimesh.boolean.difference([flange_mesh, fc], engine='manifold')
    
    # --- Combine plug and flange ---
    cover = trimesh.boolean.union([plug_mesh, flange_mesh], engine='manifold')
    cover.fix_normals()
    
    # --- Create text as RAISED/EMBOSSED letters (much more visible) ---
    text_mesh = create_text_mesh(text_str, target_width=58.0, depth=1.5)
    
    if text_mesh is not None:
        # Text mesh is in XY plane extruded along Z, centered at origin.
        # Rotate so text face is in XZ plane and extrusion goes along +Y (outward)
        rot = trimesh.transformations.rotation_matrix(-math.pi/2, [1, 0, 0])
        text_mesh.apply_transform(rot)
        
        # Position on outer face of flange (text protrudes outward from Y=flange_depth)
        text_mesh.apply_translation([0, flange_depth, 0])
        
        # UNION text with cover (raised text, not subtracted)
        print("  Adding raised text...")
        try:
            cover = trimesh.boolean.union([cover, text_mesh], engine='manifold')
            if not cover.is_watertight:
                trimesh.repair.fix_winding(cover)
                trimesh.repair.fill_holes(cover)
            print(f"  Raised text added (watertight: {cover.is_watertight})")
        except Exception as e:
            print(f"  Text union failed: {e}")
            print("  Saving cover without text")
    
    # --- Save ---
    cover.export('kiro_cover.stl')
    
    print(f"\n  SUMMARY:")
    print(f"  Cover: {flange_w}x{flange_h}mm flange + {plug_w}x{plug_h}x{plug_depth}mm plug")
    print(f"  Total depth: {plug_depth + flange_depth}mm")
    print(f"  Faces: {len(cover.faces)}")
    print(f"  Saved: kiro_cover.stl")


if __name__ == '__main__':
    main()
