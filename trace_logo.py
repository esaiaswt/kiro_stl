"""
Extract outline from kiro_2D_logo_no_background.png using alpha channel.
Uses a COMBINED approach: right edge + bottom edge + left edge + top edge
to capture ALL concave toes including the rightmost one.

The key fix: use the BOTTOM EDGE (column scan) for the bottom portion
instead of relying on left/right row scans which miss concave areas.
"""
import numpy as np
from PIL import Image

# Load PNG with alpha
img = Image.open('kiro_2D_logo/kiro_2D_logo_no_background.png')
arr = np.array(img)
visible = arr[:, :, 3] > 128
h, w = visible.shape

body_rows = np.where(visible.any(axis=1))[0]
body_cols = np.where(visible.any(axis=0))[0]
y_min, y_max = body_rows[0], body_rows[-1]
x_min, x_max = body_cols[0], body_cols[-1]

cx = (x_min + x_max) / 2
cy = (y_min + y_max) / 2
target_width = 36.0
scale = target_width / (x_max - x_min)

print(f"Body: rows {y_min}-{y_max}, cols {x_min}-{x_max}")
print(f"Scale: {scale:.4f} mm/px")

def px_to_mm(col, row):
    x = (col - cx) * scale
    z = -(row - cy) * scale  # flip Y→Z
    return (x, z)

# === BUILD CLOCKWISE OUTLINE ===
# Strategy: Use right edge for TOP to BOTTOM-RIGHT transition,
# then BOTTOM EDGE (column scan) for the bottom including all toes,
# then left edge for BOTTOM-LEFT to TOP transition.

# Determine where bottom section starts (roughly bottom 45% of height)
bottom_threshold_row = y_min + int((y_max - y_min) * 0.55)

# 1. RIGHT EDGE: from top down to where bottom section begins
right_edge = []
for row in range(y_min, y_max + 1):
    cols = np.where(visible[row])[0]
    if len(cols) > 0:
        right_edge.append((cols[-1], row))

# Find where right edge reaches the bottom threshold
right_split = len(right_edge)
for i, (c, r) in enumerate(right_edge):
    if r >= bottom_threshold_row:
        right_split = i
        break

right_top = right_edge[:right_split]  # Top to transition

# 2. BOTTOM EDGE: column scan (rightmost col to leftmost col)
# This captures ALL toes including concave ones
bottom_edge = []
# Find the actual column range for the bottom section
# Scan from right to left
for col in range(x_max, x_min - 1, -1):
    rows = np.where(visible[:, col])[0]
    if len(rows) > 0:
        bot_row = rows[-1]
        if bot_row >= bottom_threshold_row:
            bottom_edge.append((col, bot_row))

# 3. LEFT EDGE: from bottom threshold back up to top
left_edge = []
for row in range(y_max, y_min - 1, -1):
    cols = np.where(visible[row])[0]
    if len(cols) > 0:
        left_edge.append((cols[0], row))

# Find where left edge reaches above the bottom threshold
left_split = 0
for i, (c, r) in enumerate(left_edge):
    if r <= bottom_threshold_row:
        left_split = i
        break

left_bottom_to_top = left_edge[left_split:]  # From transition back to top

# 4. TOP EDGE: not needed if right_top starts at top and left ends at top

# Combine: right_top → bottom_edge → left_bottom_to_top
all_points = right_top + bottom_edge + left_bottom_to_top

# Remove duplicates
cleaned = [all_points[0]]
for p in all_points[1:]:
    dx = p[0] - cleaned[-1][0]
    dy = p[1] - cleaned[-1][1]
    if dx*dx + dy*dy > 9:  # 3px minimum distance
        cleaned.append(p)

print(f"Combined outline: {len(cleaned)} points (after dedup)")

# Convert to mm
outline_mm = [px_to_mm(c, r) for c, r in cleaned]

# Downsample to ~250 points
n_target = 250
step = max(1, len(outline_mm) // n_target)
outline_sampled = outline_mm[::step]

# Ensure closed loop
first = outline_sampled[0]
last = outline_sampled[-1]
dist = ((first[0]-last[0])**2 + (first[1]-last[1])**2)**0.5
if dist > 0.5:
    outline_sampled.append(first)  # close the loop
    outline_sampled.pop()  # but don't duplicate

print(f"Final outline: {len(outline_sampled)} points")
print(f"X range: {min(p[0] for p in outline_sampled):.1f} to {max(p[0] for p in outline_sampled):.1f}")
print(f"Z range: {min(p[1] for p in outline_sampled):.1f} to {max(p[1] for p in outline_sampled):.1f}")

# === EXTRACT EYE POSITIONS ===
black = (arr[:,:,0] < 50) & (arr[:,:,1] < 50) & (arr[:,:,2] < 50) & visible
eye_cols = np.where(black.any(axis=0))[0]

le_mm = re_mm = (0, 0)
le_size_mm = re_size_mm = (3, 4)

if len(eye_cols) > 0:
    col_diffs = np.diff(eye_cols)
    gap_idx = np.argmax(col_diffs)
    
    left_eye_cols = eye_cols[:gap_idx+1]
    right_eye_cols = eye_cols[gap_idx+1:]
    
    le_mask = black.copy()
    le_mask[:, right_eye_cols[0]:] = False
    le_r = np.where(le_mask.any(axis=1))[0]
    le_c = np.where(le_mask.any(axis=0))[0]
    le_center = ((le_c[0]+le_c[-1])/2, (le_r[0]+le_r[-1])/2)
    le_size = (le_c[-1]-le_c[0], le_r[-1]-le_r[0])
    
    re_mask = black.copy()
    re_mask[:, :right_eye_cols[0]] = False
    re_r = np.where(re_mask.any(axis=1))[0]
    re_c = np.where(re_mask.any(axis=0))[0]
    re_center = ((re_c[0]+re_c[-1])/2, (re_r[0]+re_r[-1])/2)
    re_size = (re_c[-1]-re_c[0], re_r[-1]-re_r[0])
    
    le_mm = px_to_mm(*le_center)
    re_mm = px_to_mm(*re_center)
    le_size_mm = (le_size[0]*scale, le_size[1]*scale)
    re_size_mm = (re_size[0]*scale, re_size[1]*scale)
    
    print(f"\nLeft eye:  center=({le_mm[0]:.1f}, {le_mm[1]:.1f})mm, size=({le_size_mm[0]:.1f}x{le_size_mm[1]:.1f})mm")
    print(f"Right eye: center=({re_mm[0]:.1f}, {re_mm[1]:.1f})mm, size=({re_size_mm[0]:.1f}x{re_size_mm[1]:.1f})mm")

# === SAVE ===
with open('kiro_outline_data.py', 'w') as f:
    f.write("# Auto-generated from kiro_2D_logo_no_background.png\n")
    f.write("# Combined edge trace (right + bottom-column-scan + left)\n")
    f.write("# Captures all 3 toes including rightmost concave one\n")
    f.write(f"# {len(outline_sampled)} points, 36.0mm W x {max(p[1] for p in outline_sampled)-min(p[1] for p in outline_sampled):.1f}mm H\n\n")
    f.write("KIRO_OUTLINE = [\n")
    for x, z in outline_sampled:
        f.write(f"    ({x:.2f}, {z:.2f}),\n")
    f.write("]\n\n")
    f.write(f"LEFT_EYE = ({le_mm[0]:.2f}, {le_mm[1]:.2f})\n")
    f.write(f"RIGHT_EYE = ({re_mm[0]:.2f}, {re_mm[1]:.2f})\n")
    f.write(f"LEFT_EYE_SIZE = ({le_size_mm[0]:.2f}, {le_size_mm[1]:.2f})\n")
    f.write(f"RIGHT_EYE_SIZE = ({re_size_mm[0]:.2f}, {re_size_mm[1]:.2f})\n")

print(f"\nSaved: kiro_outline_data.py")
