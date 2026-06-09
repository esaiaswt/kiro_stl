"""
Analyze the STL geometry to understand the current shape profile.
Prints width at various heights to help identify shape issues.
"""
import numpy as np
from stl import mesh

m = mesh.Mesh.from_file('kiro_ghost.stl')
pts = m.vectors.reshape(-1, 3)

print("=== STL Bounding Box ===")
mins = pts.min(axis=0)
maxs = pts.max(axis=0)
print(f"X range: {mins[0]:.1f} to {maxs[0]:.1f} (width: {maxs[0]-mins[0]:.1f}mm)")
print(f"Y range: {mins[1]:.1f} to {maxs[1]:.1f} (depth: {maxs[1]-mins[1]:.1f}mm)")
print(f"Z range: {mins[2]:.1f} to {maxs[2]:.1f} (height: {maxs[2]-mins[2]:.1f}mm)")

# Analyze ghost body only (above z=12, which is base+pillar)
ghost_pts = pts[pts[:, 2] > 14]  # ghost body points only
if len(ghost_pts) > 0:
    g_mins = ghost_pts.min(axis=0)
    g_maxs = ghost_pts.max(axis=0)
    print(f"\n=== Ghost Body Only ===")
    print(f"X: {g_mins[0]:.1f} to {g_maxs[0]:.1f} (W: {g_maxs[0]-g_mins[0]:.1f}mm)")
    print(f"Y: {g_mins[1]:.1f} to {g_maxs[1]:.1f} (D: {g_maxs[1]-g_mins[1]:.1f}mm)")
    print(f"Z: {g_mins[2]:.1f} to {g_maxs[2]:.1f} (H: {g_maxs[2]-g_mins[2]:.1f}mm)")
    
    # Profile: width at different heights
    print(f"\n=== Front-View Profile (Width at each height) ===")
    print(f"{'Height':>8} {'Width':>8} {'Depth':>8}  Bar")
    z_range = g_maxs[2] - g_mins[2]
    for pct in [0, 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 95, 100]:
        z = g_mins[2] + z_range * pct / 100
        # Points near this height (±0.5mm)
        slice_pts = ghost_pts[np.abs(ghost_pts[:, 2] - z) < 0.5]
        if len(slice_pts) > 5:
            w = slice_pts[:, 0].max() - slice_pts[:, 0].min()
            d = slice_pts[:, 1].max() - slice_pts[:, 1].min()
            bar = '█' * int(w / 2)
            print(f"{pct:>6}% {w:>7.1f}mm {d:>7.1f}mm  {bar}")
        else:
            print(f"{pct:>6}%   (no data)")
