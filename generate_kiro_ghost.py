"""
Kiro Ghost 3D STL Generator - v13 (Logo-traced outline)
========================================================
Uses the EXACT 2D outline extracted from kiro_2D_logo.jpg.
No more hand-drawn Bezier approximations.
The outline is inflated into a 3D pillow shape.
"""

import numpy as np
from stl import mesh
import math
from kiro_outline_data import KIRO_OUTLINE


def make_pillow(outline, thickness, n_slices=32):
    """
    Inflate 2D outline into 3D pillow using centroid scaling.
    Scale tapers to near-zero at front/back edges for smooth rounding.
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
        # Pillow profile: full at center, tapers at edges
        s = math.sin(t * math.pi) ** 0.55
        s = max(s, 0.12)
        
        for i in range(n):
            px, pz = outline[i]
            verts.append([cx + (px-cx)*s, y, cz + (pz-cz)*s])
    
    # Front/back cap points
    fi = len(verts); verts.append([cx, -half_t, cz])
    bi = len(verts); verts.append([cx, half_t, cz])
    
    # Side faces
    for j in range(n_slices):
        for i in range(n):
            ni = (i+1) % n
            p1, p2 = j*n+i, j*n+ni
            p3, p4 = (j+1)*n+i, (j+1)*n+ni
            faces.append([p1, p2, p4])
            faces.append([p1, p4, p3])
    
    # Front cap
    for i in range(n):
        ni = (i+1) % n
        faces.append([fi, ni, i])
    
    # Back cap
    ls = n_slices * n
    for i in range(n):
        ni = (i+1) % n
        faces.append([bi, ls+i, ls+ni])
    
    return np.array(verts, dtype=np.float64), np.array(faces)


def make_eye(cx, cy, cz, rx, rz, depth, su=24):
    """
    Eye as an oval cylinder pushed INTO the surface (toward +Y).
    Creates an elliptical cylinder with:
    - An outer rim ring at the surface (y = cy)
    - A back face ring pushed inward (y = cy + depth)
    - Side walls connecting them
    - A flat back cap
    Normals point inward (concave indent).
    """
    verts, faces = [], []
    
    # Ring at surface (front rim)
    for j in range(su):
        theta = 2 * math.pi * j / su
        x = cx + rx * math.cos(theta)
        z = cz + rz * math.sin(theta)
        verts.append([x, cy, z])  # indices 0..su-1
    
    # Ring at depth (back of cylinder)
    for j in range(su):
        theta = 2 * math.pi * j / su
        x = cx + rx * math.cos(theta)
        z = cz + rz * math.sin(theta)
        verts.append([x, cy + depth, z])  # indices su..2*su-1
    
    # Back cap center
    ci = len(verts)
    verts.append([cx, cy + depth, cz])  # index 2*su
    
    # Side walls (connecting front ring to back ring)
    # Winding reversed so normals point inward (into the hole)
    for j in range(su):
        nj = (j + 1) % su
        p1 = j          # front ring
        p2 = nj         # front ring next
        p3 = su + j     # back ring
        p4 = su + nj    # back ring next
        faces.append([p1, p4, p2])
        faces.append([p1, p3, p4])
    
    # Back cap (flat ellipse at depth)
    # Winding so normal points toward -Y (facing outward from inside the hole)
    for j in range(su):
        nj = (j + 1) % su
        faces.append([ci, su + j, su + nj])
    
    return np.array(verts, dtype=np.float64), np.array(faces)


def make_base(w, h, cr=3.0, steps=8):
    """Rounded base plate."""
    hw = w/2
    verts, faces, ol = [], [], []
    for ccx, ccy, sa, ea in [
        (-hw+cr,-hw+cr,math.pi,1.5*math.pi),
        (hw-cr,-hw+cr,1.5*math.pi,2*math.pi),
        (hw-cr,hw-cr,0,0.5*math.pi),
        (-hw+cr,hw-cr,0.5*math.pi,math.pi),
    ]:
        for i in range(steps):
            a = sa+(ea-sa)*i/steps
            ol.append([ccx+cr*math.cos(a), ccy+cr*math.sin(a)])
    nn = len(ol)
    for p in ol: verts.append([p[0],p[1],0])
    for p in ol: verts.append([p[0],p[1],h])
    bc=len(verts); verts.append([0,0,0])
    tc=len(verts); verts.append([0,0,h])
    for i in range(nn):
        ni=(i+1)%nn
        faces.append([bc,ni,i])
        faces.append([tc,nn+i,nn+ni])
        faces.append([i,ni,nn+ni])
        faces.append([i,nn+ni,nn+i])
    return np.array(verts, dtype=np.float64), np.array(faces)


def make_cyl(cx, cy, zb, zt, r, steps=16):
    """Cylinder for pillar."""
    verts, faces = [], []
    verts.append([cx,cy,zb]); verts.append([cx,cy,zt])
    for i in range(steps):
        a=2*math.pi*i/steps
        verts.append([cx+r*math.cos(a),cy+r*math.sin(a),zb])
    for i in range(steps):
        a=2*math.pi*i/steps
        verts.append([cx+r*math.cos(a),cy+r*math.sin(a),zt])
    for i in range(steps):
        ni=(i+1)%steps
        faces.append([0,2+ni,2+i])
        faces.append([1,2+steps+i,2+steps+ni])
        faces.append([2+i,2+ni,2+steps+i])
        faces.append([2+ni,2+steps+ni,2+steps+i])
    return np.array(verts, dtype=np.float64), np.array(faces)


def make_chamfer(cx, cy, z_bottom, z_top, r_bottom, r_top, steps=24):
    """
    Conical chamfer/fillet to strengthen the joint between stem and base.
    r_bottom is the wider radius (at the base), r_top is the stem radius.
    """
    verts, faces = [], []
    # Bottom ring (wide, sits on base)
    for i in range(steps):
        a = 2 * math.pi * i / steps
        verts.append([cx + r_bottom * math.cos(a), cy + r_bottom * math.sin(a), z_bottom])
    # Top ring (matches stem radius)
    for i in range(steps):
        a = 2 * math.pi * i / steps
        verts.append([cx + r_top * math.cos(a), cy + r_top * math.sin(a), z_top])
    # Bottom center
    bc = len(verts); verts.append([cx, cy, z_bottom])
    # Side faces connecting bottom ring to top ring
    for i in range(steps):
        ni = (i + 1) % steps
        # Bottom ring = indices 0..steps-1, Top ring = steps..2*steps-1
        faces.append([i, ni, steps + ni])
        faces.append([i, steps + ni, steps + i])
    # Bottom cap (flat disc at z_bottom)
    for i in range(steps):
        ni = (i + 1) % steps
        faces.append([bc, ni, i])
    return np.array(verts, dtype=np.float64), np.array(faces)


def combine(parts):
    """Combine meshes into one STL."""
    av, af = [], []
    off = 0
    for v, f in parts:
        av.append(v); af.append(f+off); off+=len(v)
    av=np.vstack(av); af=np.vstack(af)
    m=mesh.Mesh(np.zeros(len(af), dtype=mesh.Mesh.dtype))
    for i,f in enumerate(af):
        for j in range(3): m.vectors[i][j]=av[f[j]]
    return m


def main():
    print("Kiro Ghost v15 - Oval cylinder eyes pushed into surface")
    
    # Use the traced outline directly
    outline = list(KIRO_OUTLINE)
    thickness = 22.0
    
    print(f"  Outline: {len(outline)} pts from logo trace")
    print(f"  Size: {max(p[0] for p in outline)-min(p[0] for p in outline):.1f}mm W x "
          f"{max(p[1] for p in outline)-min(p[1] for p in outline):.1f}mm H")
    
    # Position above pillar
    base_h, pillar_h = 4.0, 8.0
    pillar_top = base_h + pillar_h
    min_z = min(p[1] for p in outline)
    z_off = pillar_top - min_z
    outline = [(x, z + z_off) for x, z in outline]
    
    # Build ghost
    ghost_v, ghost_f = make_pillow(outline, thickness, n_slices=40)
    
    # Base (same width as ghost)
    max_x = max(abs(p[0]) for p in outline)
    base_w = max_x * 2 + 2
    base_v, base_f = make_base(base_w, base_h)
    
    # Pillar (penetrates into ghost) - doubled diameter (radius 4.0mm)
    pillar_r = 4.0
    pil_v, pil_f = make_cyl(0, 0, base_h, pillar_top + 4, pillar_r)
    
    # Chamfer at stem-base joint (cone from 2.5x pillar radius down to pillar radius)
    # Made prominent so it's clearly visible as a structural reinforcement
    chamfer_h = 4.0  # 4mm tall chamfer
    chamfer_r_bottom = pillar_r * 2.5  # 10mm radius at base for visible reinforcement
    chamfer_v, chamfer_f = make_chamfer(0, 0, base_h, base_h + chamfer_h, chamfer_r_bottom, pillar_r)
    
    # Eyes (from logo trace - exact positions)
    from kiro_outline_data import LEFT_EYE, RIGHT_EYE, LEFT_EYE_SIZE, RIGHT_EYE_SIZE
    ghost_min_z = min(p[1] for p in outline)
    ghost_max_z = max(p[1] for p in outline)
    ghost_h = ghost_max_z - ghost_min_z
    
    # Eye Z positions from traced logo (already in mm relative to center, offset by z_off)
    le_x, le_z = LEFT_EYE[0], LEFT_EYE[1] + z_off
    re_x, re_z = RIGHT_EYE[0], RIGHT_EYE[1] + z_off
    le_w, le_h = LEFT_EYE_SIZE[0] / 2, LEFT_EYE_SIZE[1] / 2
    re_w, re_h = RIGHT_EYE_SIZE[0] / 2, RIGHT_EYE_SIZE[1] / 2
    # Eyes: need to be flush with the front surface of the pillow body.
    # The pillow front surface Y depends on the scale factor at that slice.
    # At the very front (j=0), scale s = sin(0)^0.55 clamped to 0.12, so the
    # front-most Y where the outline reaches full scale is found by solving
    # for the slice where the eye's (x,z) point lies ON the scaled outline.
    # 
    # Approximation: find what fraction of the centroid-to-outline distance
    # the eye center is at, then find the front Y where that scale applies.
    half_t = thickness / 2
    n_slices_build = 40  # must match what we built the pillow with
    cx_body = sum(p[0] for p in outline) / len(outline)
    cz_body = sum(p[1] for p in outline) / len(outline)
    
    def find_surface_y(ex, ez):
        """Find the Y of the front surface at point (ex, ez) by checking pillow geometry."""
        # Distance from centroid to eye point
        dx = ex - cx_body
        dz = ez - cz_body
        dist_eye = math.sqrt(dx*dx + dz*dz)
        # Find the outline point closest in angle to the eye
        angle_eye = math.atan2(dz, dx)
        best_dist = 0
        for px, pz in outline:
            a = math.atan2(pz - cz_body, px - cx_body)
            if abs(a - angle_eye) < 0.05 or abs(a - angle_eye) > 2*math.pi - 0.05:
                d = math.sqrt((px-cx_body)**2 + (pz-cz_body)**2)
                if d > best_dist:
                    best_dist = d
        if best_dist == 0:
            best_dist = dist_eye * 1.2
        # The eye needs scale s such that s * best_dist >= dist_eye
        # i.e. s >= dist_eye / best_dist
        s_needed = dist_eye / best_dist
        s_needed = max(s_needed, 0.12)
        # Find the front-most slice (smallest j) where s >= s_needed
        # s = sin(j/n_slices * pi) ^ 0.55, and we want the FRONT side (j < n_slices/2)
        # Solve: sin(t*pi)^0.55 = s_needed => t = arcsin(s_needed^(1/0.55)) / pi
        inner = min(s_needed ** (1.0/0.55), 1.0)
        t = math.asin(inner) / math.pi
        y_surface = -half_t + thickness * t
        return y_surface
    
    le_surface_y = find_surface_y(le_x, le_z)
    re_surface_y = find_surface_y(re_x, re_z)
    
    eye_depth = 10.0  # oval cylinder pushed 10mm into the surface for visible 3D print
    left_eye_v, left_eye_f = make_eye(le_x, le_surface_y, le_z, le_w, le_h, eye_depth)
    right_eye_v, right_eye_f = make_eye(re_x, re_surface_y, re_z, re_w, re_h, eye_depth)
    
    # Combine and save
    parts = [
        (base_v, base_f), (pil_v, pil_f), (chamfer_v, chamfer_f), (ghost_v, ghost_f),
        (left_eye_v, left_eye_f), (right_eye_v, right_eye_f),
    ]
    m = combine(parts)
    m.save('kiro_ghost.stl')
    
    total_h = base_h + pillar_h + ghost_h
    print(f"  Total height: ~{total_h:.0f}mm")
    print(f"  Pillar: diameter {pillar_r*2:.0f}mm (doubled), chamfer {chamfer_r_bottom*2:.0f}mm base")
    print(f"  Saved: kiro_ghost.stl")
    print(f"\n  v15: Oval cylinder eyes pushed into body surface")


if __name__ == '__main__':
    main()
