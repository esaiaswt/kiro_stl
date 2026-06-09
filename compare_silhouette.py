"""
Compare STL outline at Y=0 (middle slice = the actual 2D profile)
with the Kiro 2D logo. This shows the TRUE silhouette including toes.
"""
import numpy as np
from stl import mesh
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Load STL
m = mesh.Mesh.from_file('kiro_ghost.stl')
pts = m.vectors.reshape(-1, 3)

# Get ghost-only points (above base+pillar)
ghost = pts[pts[:, 2] > 13]

# Get the MIDDLE Y-SLICE (Y ≈ 0, which is the center where outline is full-size)
# This is the actual 2D outline that defines the shape
mid_slice = ghost[np.abs(ghost[:, 1]) < 0.5]  # points near Y=0

print(f"Total ghost points: {len(ghost)}")
print(f"Middle slice (Y≈0) points: {len(mid_slice)}")

if len(mid_slice) < 10:
    # Try a wider band
    mid_slice = ghost[np.abs(ghost[:, 1]) < 1.5]
    print(f"Wider band (Y±1.5) points: {len(mid_slice)}")

# Extract the outline of this slice
# For each Z height, find min and max X
z_vals = mid_slice[:, 2]
z_min, z_max = z_vals.min(), z_vals.max()
z_range = np.linspace(z_min, z_max, 200)

left_pts = []
right_pts = []
for z in z_range:
    mask = np.abs(mid_slice[:, 2] - z) < 0.3
    if mask.sum() > 0:
        x_at_z = mid_slice[mask, 0]
        left_pts.append((x_at_z.min(), z))
        right_pts.append((x_at_z.max(), z))

# Load logo using alpha channel from PNG (no background version)
logo = Image.open('kiro_2D_logo/kiro_2D_logo_no_background.png')
logo_arr = np.array(logo)

# Extract logo white silhouette using alpha channel
white_mask = logo_arr[:, :, 3] > 128  # visible pixels from alpha

# Get logo outline using BOTH row-scan and column-scan
logo_h, logo_w = white_mask.shape
logo_left = []
logo_right = []
for row in range(logo_h):
    cols = np.where(white_mask[row])[0]
    if len(cols) > 0:
        logo_left.append((cols[0], row))
        logo_right.append((cols[-1], row))

# Also get bottom edge by column scan (captures concave toes)
logo_bottom = []
for col in range(logo_w):
    rows = np.where(white_mask[:, col])[0]
    if len(rows) > 0:
        logo_bottom.append((col, rows[-1]))

# Normalize logo to same coordinate space as STL
if logo_left:
    ll_x = [p[0] for p in logo_left]
    lr_x = [p[0] for p in logo_right]
    ll_z = [p[1] for p in logo_left]
    
    # Logo bounds
    logo_x_min = min(ll_x + lr_x)
    logo_x_max = max(ll_x + lr_x)
    logo_z_min = min(ll_z)
    logo_z_max = max(ll_z)
    
    # STL bounds
    stl_x_min = min(p[0] for p in left_pts) if left_pts else -18
    stl_x_max = max(p[0] for p in right_pts) if right_pts else 18
    stl_z_min = z_min
    stl_z_max = z_max
    
    # Scale logo to match STL size
    logo_width = logo_x_max - logo_x_min
    logo_height = logo_z_max - logo_z_min
    stl_width = stl_x_max - stl_x_min
    stl_height = stl_z_max - stl_z_min
    
    scale_x = stl_width / logo_width if logo_width > 0 else 1
    scale_z = stl_height / logo_height if logo_height > 0 else 1
    scale = min(scale_x, scale_z)  # uniform scale
    
    # Transform logo coords to STL space
    logo_cx = (logo_x_min + logo_x_max) / 2
    logo_cz = (logo_z_min + logo_z_max) / 2
    stl_cx = (stl_x_min + stl_x_max) / 2
    stl_cz = (stl_z_min + stl_z_max) / 2
    
    logo_left_norm = [(stl_cx + (x - logo_cx) * scale, stl_cz - (z - logo_cz) * scale) for x, z in logo_left]
    logo_right_norm = [(stl_cx + (x - logo_cx) * scale, stl_cz - (z - logo_cz) * scale) for x, z in logo_right]
    
    # Also transform bottom edge
    logo_bottom_norm = [(stl_cx + (x - logo_cx) * scale, stl_cz - (z - logo_cz) * scale) for x, z in logo_bottom]

# Plot overlay
fig, ax = plt.subplots(1, 1, figsize=(8, 10))

# Plot logo silhouette (green)
if logo_left:
    lx = [p[0] for p in logo_left_norm]
    lz = [p[1] for p in logo_left_norm]
    rx = [p[0] for p in logo_right_norm]
    rz = [p[1] for p in logo_right_norm]
    ax.fill_betweenx(lz, lx, rx, alpha=0.3, color='green', label='2D Logo')
    ax.plot(lx, lz, 'g-', linewidth=1.5)
    ax.plot(rx, rz, 'g-', linewidth=1.5)
    # Plot bottom edge to show toes clearly
    if logo_bottom_norm:
        bx = [p[0] for p in logo_bottom_norm]
        bz = [p[1] for p in logo_bottom_norm]
        ax.plot(bx, bz, 'g-', linewidth=2.5, label='2D Logo bottom edge')

# Plot STL silhouette (blue)
if left_pts:
    slx = [p[0] for p in left_pts]
    slz = [p[1] for p in left_pts]
    srx = [p[0] for p in right_pts]
    srz = [p[1] for p in right_pts]
    ax.fill_betweenx(slz, slx, srx, alpha=0.3, color='blue', label='STL (Y=0 slice)')
    ax.plot(slx, slz, 'b-', linewidth=1.5)
    ax.plot(srx, srz, 'b-', linewidth=1.5)

ax.set_aspect('equal')
ax.set_title('STL Middle Slice vs 2D Logo (Overlay)')
ax.legend(fontsize=12)
ax.grid(True, alpha=0.3)
ax.set_xlabel('X (mm)')
ax.set_ylabel('Z (mm)')

plt.tight_layout()
plt.savefig('silhouette_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("\nSaved: silhouette_comparison.png")
print("Green = 2D logo, Blue = STL middle slice")
print("Compare the bottom edges to see if toes match!")
