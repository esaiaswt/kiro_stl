"""
Kiro Ghost 3D STL Generator - Magnetic Levitation Version
==========================================================
- Scaled ~3x to fit 62x62x12mm magnetic box inside body
- No base/stem - ghost floats via magnetic levitation
- Magnetic box cavity accessible from bottom
- 15mm clearance from bottom of ghost to platform
- 4x 8mm diameter LED light tubes at box corners, open top to bottom
"""

import numpy as np
from stl import mesh
import math
from kiro_outline_data import KIRO_OUTLINE


def make_pillow(outline, thickness, n_slices=32, min_scale=0.12, profile="pillow", flat_fraction=0.75):
    """
    Inflate 2D outline into 3D shape using centroid scaling.
    
    profile options:
    - "pillow": sin^0.55 taper (egg/oval from side)
    - "capsule": flat middle with rounded caps at front/back (stadium from side)
    """
    n = len(outline)
    half_t = thickness / 2
    cx = sum(p[0] for p in outline) / n
    cz = sum(p[1] for p in outline) / n

    verts = []
    faces = []

    for j in range(n_slices + 1):
        t = j / n_slices
        y = -half_t + thickness * t

        if profile == "capsule":
            cap_size = (1.0 - flat_fraction) / 2
            if t < cap_size:
                # Front cap rounding
                t_in_cap = t / cap_size
                s = math.sin(t_in_cap * math.pi / 2) ** 0.55
                s = max(s, min_scale)
            elif t > 1.0 - cap_size:
                # Rear cap rounding
                t_in_cap = (1.0 - t) / cap_size
                s = math.sin(t_in_cap * math.pi / 2) ** 0.55
                s = max(s, min_scale)
            else:
                s = 1.0
        else:
            # Original pillow profile
            s = math.sin(t * math.pi) ** 0.55
            s = max(s, min_scale)

        for i in range(n):
            px, pz = outline[i]
            verts.append([cx + (px - cx) * s, y, cz + (pz - cz) * s])

    # Front/back cap points
    fi = len(verts); verts.append([cx, -half_t, cz])
    bi = len(verts); verts.append([cx, half_t, cz])

    # Side faces
    for j in range(n_slices):
        for i in range(n):
            ni = (i + 1) % n
            p1, p2 = j * n + i, j * n + ni
            p3, p4 = (j + 1) * n + i, (j + 1) * n + ni
            faces.append([p1, p2, p4])
            faces.append([p1, p4, p3])

    # Front cap
    for i in range(n):
        ni = (i + 1) % n
        faces.append([fi, ni, i])

    # Back cap
    ls = n_slices * n
    for i in range(n):
        ni = (i + 1) % n
        faces.append([bi, ls + i, ls + ni])

    return np.array(verts, dtype=np.float64), np.array(faces)


def make_eye(cx, cy, cz, rx, rz, depth, su=24):
    """
    Eye as an oval cylinder pushed INTO the surface (toward +Y).
    """
    verts, faces = [], []

    # Ring at surface (front rim)
    for j in range(su):
        theta = 2 * math.pi * j / su
        x = cx + rx * math.cos(theta)
        z = cz + rz * math.sin(theta)
        verts.append([x, cy, z])

    # Ring at depth (back of cylinder)
    for j in range(su):
        theta = 2 * math.pi * j / su
        x = cx + rx * math.cos(theta)
        z = cz + rz * math.sin(theta)
        verts.append([x, cy + depth, z])

    # Back cap center
    ci = len(verts)
    verts.append([cx, cy + depth, cz])

    # Side walls
    for j in range(su):
        nj = (j + 1) % su
        p1, p2, p3, p4 = j, nj, su + j, su + nj
        faces.append([p1, p4, p2])
        faces.append([p1, p3, p4])

    # Back cap
    for j in range(su):
        nj = (j + 1) % su
        faces.append([ci, su + j, su + nj])

    return np.array(verts, dtype=np.float64), np.array(faces)


def make_box_cavity(cx, cy, z_bottom, box_w, box_l, box_h, open_face="bottom"):
    """
    Rectangular cavity open at one face.
    Box is centered at (cx, cy) in XY plane.
    box_w = X dimension, box_l = Y dimension, box_h = Z dimension
    open_face: "bottom" (open at z_bottom), "rear" (open at cy + box_l/2)
    Normals point INWARD (concave cavity).
    """
    hw = box_w / 2
    hl = box_l / 2
    z_top = z_bottom + box_h

    # 8 corners of the box
    verts = [
        [cx - hw, cy - hl, z_bottom],  # 0: bottom-left-front
        [cx + hw, cy - hl, z_bottom],  # 1: bottom-right-front
        [cx + hw, cy + hl, z_bottom],  # 2: bottom-right-back
        [cx - hw, cy + hl, z_bottom],  # 3: bottom-left-back
        [cx - hw, cy - hl, z_top],     # 4: top-left-front
        [cx + hw, cy - hl, z_top],     # 5: top-right-front
        [cx + hw, cy + hl, z_top],     # 6: top-right-back
        [cx - hw, cy + hl, z_top],     # 7: top-left-back
    ]

    faces = []

    if open_face == "bottom":
        # All walls except bottom face
        faces.append([0, 4, 1]); faces.append([1, 4, 5])
        faces.append([1, 5, 2]); faces.append([2, 5, 6])
        faces.append([2, 6, 3]); faces.append([3, 6, 7])
        faces.append([3, 7, 0]); faces.append([0, 7, 4])
        faces.append([4, 7, 5]); faces.append([5, 7, 6])

    elif open_face == "rear":
        # All walls except rear face (y = cy + hl is open)
        faces.append([0, 4, 1]); faces.append([1, 4, 5])  # front
        faces.append([1, 5, 2]); faces.append([2, 5, 6])  # right
        faces.append([3, 7, 0]); faces.append([0, 7, 4])  # left
        faces.append([4, 7, 5]); faces.append([5, 7, 6])  # top
        faces.append([0, 1, 3]); faces.append([1, 2, 3])  # bottom

    return np.array(verts, dtype=np.float64), np.array(faces)


def make_insertion_channel(cx, y_start, y_end, z_bottom, channel_w, channel_h):
    """
    Rectangular channel for box insertion from rear.
    Runs from y_start to y_end, open at y_end (rear face).
    channel_w = X width, channel_h = Z height.
    """
    hw = channel_w / 2
    z_top = z_bottom + channel_h

    verts = [
        [cx - hw, y_start, z_bottom],  # 0
        [cx + hw, y_start, z_bottom],  # 1
        [cx + hw, y_end, z_bottom],    # 2
        [cx - hw, y_end, z_bottom],    # 3
        [cx - hw, y_start, z_top],     # 4
        [cx + hw, y_start, z_top],     # 5
        [cx + hw, y_end, z_top],       # 6
        [cx - hw, y_end, z_top],       # 7
    ]

    faces = []
    # Front wall (y = y_start) - closed
    faces.append([0, 4, 1]); faces.append([1, 4, 5])
    # Right wall
    faces.append([1, 5, 2]); faces.append([2, 5, 6])
    # Left wall
    faces.append([3, 7, 0]); faces.append([0, 7, 4])
    # Top
    faces.append([4, 7, 5]); faces.append([5, 7, 6])
    # Bottom
    faces.append([0, 1, 3]); faces.append([1, 2, 3])
    # Rear (y = y_end) is OPEN

    return np.array(verts, dtype=np.float64), np.array(faces)


def make_tube(cx, cy, z_bottom, z_top, radius, steps=24):
    """
    Vertical hollow tube (open at both ends).
    Creates cylinder wall only (no caps) - normals point inward.
    """
    verts, faces = [], []

    # Bottom ring
    for i in range(steps):
        a = 2 * math.pi * i / steps
        verts.append([cx + radius * math.cos(a), cy + radius * math.sin(a), z_bottom])

    # Top ring
    for i in range(steps):
        a = 2 * math.pi * i / steps
        verts.append([cx + radius * math.cos(a), cy + radius * math.sin(a), z_top])

    # Side walls (normals pointing inward - reversed winding for concave)
    for i in range(steps):
        ni = (i + 1) % steps
        b1, b2 = i, ni  # bottom ring
        t1, t2 = steps + i, steps + ni  # top ring
        faces.append([b1, t2, b2])
        faces.append([b1, t1, t2])

    return np.array(verts, dtype=np.float64), np.array(faces)


def combine(parts):
    """Combine meshes into one STL."""
    av, af = [], []
    off = 0
    for v, f in parts:
        av.append(v)
        af.append(f + off)
        off += len(v)
    av = np.vstack(av)
    af = np.vstack(af)
    m = mesh.Mesh(np.zeros(len(af), dtype=mesh.Mesh.dtype))
    for i, f in enumerate(af):
        for j in range(3):
            m.vectors[i][j] = av[f[j]]
    return m


def main():
    print("Kiro Ghost - Magnetic Levitation Version")
    print("=" * 50)

    # --- Configuration ---
    box_w, box_l, box_h = 62.0, 62.0, 12.0  # magnetic box dimensions
    clearance = 15.0  # mm from bottom of ghost to platform
    wall_min = 5.0  # minimum wall thickness around box
    led_tube_r = 4.0  # 8mm diameter / 2
    eye_depth = 10.0  # eye cylinder depth

    # --- Calculate scale factor ---
    outline_orig = list(KIRO_OUTLINE)
    orig_w = max(p[0] for p in outline_orig) - min(p[0] for p in outline_orig)
    orig_h = max(p[1] for p in outline_orig) - min(p[1] for p in outline_orig)
    orig_thickness = 22.0  # original Y thickness

    # Need both X and Y to accommodate 62mm + walls
    needed_xy = box_w + 2 * wall_min  # 72mm
    scale_x = needed_xy / orig_w
    scale_y = needed_xy / orig_thickness
    # Use scale 2.4x - minimum that fits box with adequate wall thickness
    scale = 2.4

    print(f"  Original: {orig_w:.1f}mm W x {orig_h:.1f}mm H x {orig_thickness:.1f}mm thick")
    print(f"  Scale factor: {scale:.2f}x (to fit {box_w}x{box_l}mm box + {wall_min}mm walls)")

    # Scaled dimensions
    # Use capsule profile: flat middle (full width) with rounded front/back caps
    # Thickness 73mm - minimum to contain 62mm box with capsule rounding
    thickness = 73.0  # capsule thickness
    pillow_min_scale = 0.12
    flat_fraction = 0.92  # 92% flat region = 67.2mm (covers box 62mm with margin)
    scaled_w = orig_w * scale
    scaled_h = orig_h * scale

    print(f"  Scaled: {scaled_w:.1f}mm W x {scaled_h:.1f}mm H x {thickness:.1f}mm thick")

    # --- Scale the outline ---
    # Center the outline at origin, then scale
    cx_orig = sum(p[0] for p in outline_orig) / len(outline_orig)
    cz_orig = sum(p[1] for p in outline_orig) / len(outline_orig)
    outline = [((x - cx_orig) * scale, (z - cz_orig) * scale) for x, z in outline_orig]

    # --- Position ghost so bottom is at Z=15mm (clearance above platform) ---
    # The outline Z values represent height. Find the min Z of the scaled outline.
    min_z_outline = min(p[1] for p in outline)
    # Shift outline up so the bottom of the ghost is at z = clearance
    z_shift = clearance - min_z_outline
    outline = [(x, z + z_shift) for x, z in outline]

    # Keep original outline WITH TOES (signature Kiro curls).
    # The box is positioned above the toe area (Z=30+) where the body is solid.

    ghost_min_z = min(p[1] for p in outline)
    ghost_max_z = max(p[1] for p in outline)
    print(f"  Ghost Z range: {ghost_min_z:.1f}mm to {ghost_max_z:.1f}mm")
    print(f"  Clearance above platform: {clearance}mm")

    # --- Build ghost body (no base/stem) ---
    ghost_v, ghost_f = make_pillow(outline, thickness, n_slices=40,
                                   min_scale=pillow_min_scale,
                                   profile="capsule", flat_fraction=flat_fraction)

    # --- Magnetic box cavity ---
    # Single cavity extending from box position to rear surface.
    # This creates a slot accessible from the rear - the box slides in from behind.
    # Cavity: 62mm(X) x depth(Y) x 12mm(Z), open at rear face.
    cx_ghost = sum(p[0] for p in outline) / len(outline)

    box_z_bottom = clearance + 13.5  # 28.5mm (13.5mm gap from body bottom)
    # Shift box X-center to match outline center at box Z level (asymmetric outline)
    # This balances wall thickness on both sides
    pts_at_box_z = [(x, z) for x, z in outline if box_z_bottom - 2 <= z <= box_z_bottom + box_h + 2]
    if pts_at_box_z:
        cx_ghost = (max(p[0] for p in pts_at_box_z) + min(p[0] for p in pts_at_box_z)) / 2
    box_cy_front = -box_l / 2  # -31mm (where box front face sits)
    half_t_body = thickness / 2  # 42.5mm (rear surface)

    # The cavity extends from box front (Y=-31) to rear surface (Y=42.5)
    # Centered in X at cx_ghost, open at rear (+Y face)
    cavity_depth_y = half_t_body - box_cy_front  # 73.5mm total depth
    cavity_cy = (box_cy_front + half_t_body) / 2  # center of cavity in Y

    print(f"  Box cavity: {box_w}x{cavity_depth_y:.1f}x{box_h}mm slot, open at rear")
    print(f"  Slot Y range: {box_cy_front:.1f} to {half_t_body:.1f}mm")
    print(f"  Box slides in from rear, sits at Y=[{box_cy_front:.1f}, {box_cy_front + box_l:.1f}]")
    print(f"  Z range: [{box_z_bottom:.1f}, {box_z_bottom + box_h:.1f}]mm")

    cavity_v, cavity_f = make_box_cavity(
        cx_ghost, cavity_cy, box_z_bottom,
        box_w, cavity_depth_y, box_h, open_face="rear")

    # --- LED tubes at box corners ---
    # LED tubes at the 4 corners of where the box sits (Y=-31 to Y=+31)
    half_box_x = box_w / 2
    led_inset = led_tube_r + 2.0  # 6mm inset from box edge
    led_positions = [
        (cx_ghost - half_box_x + led_inset, box_cy_front + led_inset),
        (cx_ghost + half_box_x - led_inset, box_cy_front + led_inset),
        (cx_ghost + half_box_x - led_inset, box_cy_front + box_l - led_inset),
        (cx_ghost - half_box_x + led_inset, box_cy_front + box_l - led_inset),
    ]

    # Tubes go from box bottom up to where the body surface is at that XY position.
    # The pillow tapers in Y, so at Y=±25mm the body is shorter than at center.
    # Calculate the actual body top Z at each tube's Y position using point-in-polygon
    # check for the full tube cross-section (8mm diameter circle).
    half_t = thickness / 2
    cx_body = sum(p[0] for p in outline) / len(outline)
    cz_body = sum(p[1] for p in outline) / len(outline)

    def point_in_polygon(px, pz, polygon):
        """Ray casting algorithm to check if point is inside polygon."""
        n = len(polygon)
        inside = False
        j = n - 1
        for i in range(n):
            xi, zi = polygon[i]
            xj, zj = polygon[j]
            if ((zi > pz) != (zj > pz)) and (px < (xj - xi) * (pz - zi) / (zj - zi) + xi):
                inside = not inside
            j = i
        return inside

    def get_tube_max_z(tx, ty, tube_radius):
        """Find max Z where full tube circle is inside the pillow body at (tx, ty)."""
        # Get the capsule scale at this Y position
        t_slice = (ty + half_t) / thickness
        t_slice = max(0.0, min(1.0, t_slice))
        cap_size = (1.0 - flat_fraction) / 2
        if t_slice < cap_size:
            t_in_cap = t_slice / cap_size
            s = math.sin(t_in_cap * math.pi / 2) ** 0.55
            s = max(s, pillow_min_scale)
        elif t_slice > 1.0 - cap_size:
            t_in_cap = (1.0 - t_slice) / cap_size
            s = math.sin(t_in_cap * math.pi / 2) ** 0.55
            s = max(s, pillow_min_scale)
        else:
            s = 1.0
        # Compute the scaled outline at this Y slice
        scaled_outline = [(cx_body + (px - cx_body) * s, cz_body + (pz - cz_body) * s)
                          for px, pz in outline]
        # Binary search for max Z where full tube cross-section is inside
        z_low = int(box_z_bottom + box_h)
        z_high = int(ghost_max_z)
        max_safe_z = z_low
        for z_test in range(z_low, z_high):
            all_inside = True
            # Check 8 points around tube circumference
            for angle_i in range(8):
                a = 2 * math.pi * angle_i / 8
                check_x = tx + tube_radius * math.cos(a)
                check_z = z_test + tube_radius * math.sin(a)
                if not point_in_polygon(check_x, check_z, scaled_outline):
                    all_inside = False
                    break
            if all_inside:
                max_safe_z = z_test
            elif max_safe_z > z_low:
                break
        return max_safe_z

    tube_z_bottom = clearance - 1.0  # start 1mm below body bottom for clean opening

    print(f"  LED tubes: 4x {led_tube_r * 2:.0f}mm diameter")

    tube_parts = []
    for i, (lx, ly) in enumerate(led_positions):
        tube_z_top = get_tube_max_z(lx, ly, led_tube_r)
        # Pull back 3mm extra margin to ensure fully concealed
        tube_z_top -= 3.0
        tv, tf = make_tube(lx, ly, tube_z_bottom, tube_z_top, led_tube_r, steps=24)
        tube_parts.append((tv, tf))
        print(f"    Tube {i + 1}: x={lx:.1f}, y={ly:.1f}, z={tube_z_bottom:.1f} to {tube_z_top:.1f}mm")

    # --- Eyes (scaled positions) ---
    from kiro_outline_data import LEFT_EYE, RIGHT_EYE, LEFT_EYE_SIZE, RIGHT_EYE_SIZE

    le_x = (LEFT_EYE[0] - cx_orig) * scale
    le_z = (LEFT_EYE[1] - cz_orig) * scale + z_shift
    re_x = (RIGHT_EYE[0] - cx_orig) * scale
    re_z = (RIGHT_EYE[1] - cz_orig) * scale + z_shift
    le_w = LEFT_EYE_SIZE[0] / 2 * scale
    le_h = LEFT_EYE_SIZE[1] / 2 * scale
    re_w = RIGHT_EYE_SIZE[0] / 2 * scale
    re_h = RIGHT_EYE_SIZE[1] / 2 * scale

    # Find front surface Y for each eye (reusing half_t, cx_body, cz_body from above)

    def find_surface_y(ex, ez):
        """Find the Y of the front surface at point (ex, ez) for capsule profile."""
        dx = ex - cx_body
        dz = ez - cz_body
        dist_eye = math.sqrt(dx * dx + dz * dz)
        angle_eye = math.atan2(dz, dx)
        best_dist = 0
        for px, pz in outline:
            a = math.atan2(pz - cz_body, px - cx_body)
            if abs(a - angle_eye) < 0.05 or abs(a - angle_eye) > 2 * math.pi - 0.05:
                d = math.sqrt((px - cx_body) ** 2 + (pz - cz_body) ** 2)
                if d > best_dist:
                    best_dist = d
        if best_dist == 0:
            best_dist = dist_eye * 1.2
        s_needed = dist_eye / best_dist
        s_needed = max(s_needed, pillow_min_scale)
        # For capsule: if s_needed <= 1.0, the point is in the flat region
        # The front surface is at the start of the flat region
        cap_size = (1.0 - flat_fraction) / 2
        if s_needed >= 1.0:
            # Point is at full scale - surface is at start of flat region
            t = cap_size
        else:
            # Point needs some taper - it's in the front cap
            inner = min(s_needed ** (1.0 / 0.55), 1.0)
            t_in_cap = math.asin(inner) / (math.pi / 2)
            t = t_in_cap * cap_size
        y_surface = -half_t + thickness * t
        return y_surface

    le_surface_y = find_surface_y(le_x, le_z)
    re_surface_y = find_surface_y(re_x, re_z)

    # Scale eye depth proportionally
    scaled_eye_depth = eye_depth * scale
    left_eye_v, left_eye_f = make_eye(le_x, le_surface_y, le_z, le_w, le_h, scaled_eye_depth)
    right_eye_v, right_eye_f = make_eye(re_x, re_surface_y, re_z, re_w, re_h, scaled_eye_depth)

    print(f"  Eyes: {le_w * 2:.1f}x{le_h * 2:.1f}mm oval, {scaled_eye_depth:.1f}mm deep")

    # --- Combine body, then boolean subtract cavities ---
    import trimesh

    # Build the solid body
    body_mesh = combine([(ghost_v, ghost_f)])
    body_trimesh = trimesh.Trimesh(
        vertices=np.array([[v[0], v[1], v[2]] for f in body_mesh.vectors for v in f]).reshape(-1, 3),
        faces=np.arange(len(body_mesh.vectors) * 3).reshape(-1, 3)
    )
    body_trimesh.merge_vertices()
    body_trimesh.fix_normals()

    # Create the cavity box for boolean subtraction (solid box to subtract)
    # Cavity: 62mm(X) x 73.5mm(Y) x 12mm(Z), from Y=-31 to Y=42.5, Z=30-42
    cavity_box = trimesh.primitives.Box(
        extents=[box_w, cavity_depth_y, box_h],
        transform=trimesh.transformations.translation_matrix([
            cx_ghost, (box_cy_front + half_t_body) / 2, box_z_bottom + box_h / 2
        ])
    )

    # Create LED tube cylinders to subtract
    tube_meshes = []
    for i, (lx, ly) in enumerate(led_positions):
        tube_z_top_val = get_tube_max_z(lx, ly, led_tube_r)
        tube_z_top_val -= 3.0
        tube_height = tube_z_top_val - tube_z_bottom
        if tube_height > 0:
            cyl = trimesh.primitives.Cylinder(
                radius=led_tube_r,
                height=tube_height,
                transform=trimesh.transformations.translation_matrix([
                    lx, ly, tube_z_bottom + tube_height / 2
                ])
            )
            tube_meshes.append(cyl)
            print(f"    Tube {i + 1}: x={lx:.1f}, y={ly:.1f}, z={tube_z_bottom:.1f} to {tube_z_top_val:.1f}mm")

    # Create eye cylinders to subtract
    le_surface_y_val = find_surface_y(le_x, le_z)
    re_surface_y_val = find_surface_y(re_x, re_z)
    scaled_eye_depth = eye_depth * scale

    # Boolean subtraction: body - cavity - tubes - eyes
    print("\n  Performing boolean subtraction...")
    result = trimesh.boolean.difference([body_trimesh, cavity_box], engine='manifold')

    for tube_m in tube_meshes:
        result = trimesh.boolean.difference([result, tube_m], engine='manifold')

    # Subtract eye cavities (proper oval cylinders, 7mm depth)
    # Start eyes OUTSIDE the front surface to punch cleanly through the front cap
    eye_depth_fixed = 7.0  # 7mm depth as requested
    eye_start_y = -half_t - 1.0  # start 1mm outside front surface
    for eye_x, eye_z, eye_rx, eye_rz in [
        (le_x, le_z, le_w, le_h),
        (re_x, re_z, re_w, re_h),
    ]:
        # Build oval cylinder manually with proper elliptical cross-section
        n_seg = 48  # smooth oval
        # Create an elliptical prism (oval cylinder) along Y axis
        oval_verts = []
        oval_faces = []
        # Front ring (outside front surface)
        for i in range(n_seg):
            angle = 2 * math.pi * i / n_seg
            x = eye_x + eye_rx * math.cos(angle)
            z = eye_z + eye_rz * math.sin(angle)
            oval_verts.append([x, eye_start_y, z])
        # Back ring (7mm + extra into body)
        eye_end_y = eye_start_y + eye_depth_fixed + 2.0  # extra 2mm to ensure clean cut
        for i in range(n_seg):
            angle = 2 * math.pi * i / n_seg
            x = eye_x + eye_rx * math.cos(angle)
            z = eye_z + eye_rz * math.sin(angle)
            oval_verts.append([x, eye_end_y, z])
        # Front cap center
        fc = len(oval_verts)
        oval_verts.append([eye_x, eye_start_y, eye_z])
        # Back cap center
        bc = len(oval_verts)
        oval_verts.append([eye_x, eye_end_y, eye_z])
        # Side faces
        for i in range(n_seg):
            ni = (i + 1) % n_seg
            oval_faces.append([i, ni, n_seg + ni])
            oval_faces.append([i, n_seg + ni, n_seg + i])
        # Front cap
        for i in range(n_seg):
            ni = (i + 1) % n_seg
            oval_faces.append([fc, i, ni])
        # Back cap
        for i in range(n_seg):
            ni = (i + 1) % n_seg
            oval_faces.append([bc, n_seg + ni, n_seg + i])

        eye_mesh = trimesh.Trimesh(
            vertices=np.array(oval_verts),
            faces=np.array(oval_faces)
        )
        eye_mesh.fix_normals()
        try:
            result = trimesh.boolean.difference([result, eye_mesh], engine='manifold')
        except Exception as e:
            print(f"    Eye subtraction failed: {e}")

    # Save result
    result.export('kiro_ghost_maglev.stl')

    print(f"\n  SUMMARY:")
    print(f"  Total height: {ghost_max_z:.1f}mm (top of ghost)")
    print(f"  Width: {scaled_w:.1f}mm, Thickness: {thickness:.1f}mm")
    print(f"  Platform clearance: {clearance}mm")
    print(f"  Magnetic box: {box_w}x{box_l}x{box_h}mm cavity (rear access, boolean cut)")
    print(f"  LED tubes: 4x 8mm diameter (boolean cut)")
    print(f"  Saved: kiro_ghost_maglev.stl ({len(result.faces)} faces)")


if __name__ == '__main__':
    main()
