"""
STL Viewer - Renders the ghost STL from multiple angles for comparison
with the plushie reference images. Uses matplotlib for 3D rendering.
Saves renders as PNG images for visual comparison.
"""

import numpy as np
from stl import mesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import os


def load_stl(filepath):
    """Load STL and return the mesh."""
    return mesh.Mesh.from_file(filepath)


def render_stl(stl_mesh, elevation, azimuth, title, output_path, figsize=(6, 6)):
    """Render STL from a given viewpoint and save as image."""
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection='3d')
    
    # Get all triangles
    vectors = stl_mesh.vectors
    
    # Create polygon collection
    poly = Poly3DCollection(vectors, alpha=0.9)
    poly.set_facecolor([0.85, 0.85, 0.9])  # light gray-blue
    poly.set_edgecolor([0.5, 0.5, 0.6])
    poly.set_linewidth(0.1)
    ax.add_collection3d(poly)
    
    # Auto-scale
    all_points = vectors.reshape(-1, 3)
    mins = all_points.min(axis=0)
    maxs = all_points.max(axis=0)
    center = (mins + maxs) / 2
    max_range = (maxs - mins).max() / 2
    
    ax.set_xlim(center[0] - max_range, center[0] + max_range)
    ax.set_ylim(center[1] - max_range, center[1] + max_range)
    ax.set_zlim(center[2] - max_range, center[2] + max_range)
    
    ax.view_init(elev=elevation, azim=azimuth)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_axis_off()
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"  Saved: {output_path}")


def main():
    stl_path = 'kiro_ghost.stl'
    output_dir = 'stl_renders'
    os.makedirs(output_dir, exist_ok=True)
    
    print("Loading STL...")
    stl_mesh = load_stl(stl_path)
    
    print(f"Mesh: {len(stl_mesh.vectors)} triangles")
    
    # Render from multiple angles matching the plushie photos
    views = [
        # (elevation, azimuth, name) - matching plushie image angles
        (10, -90, "front_view"),          # Front (eyes facing us)
        (10, 90, "rear_view"),            # Rear
        (10, -45, "right_45deg"),         # Right 45°
        (10, -135, "left_45deg"),         # Left 45°
        (45, -90, "top_45deg"),           # Top-down at 45°
        (-30, -90, "bottom_45deg"),       # Bottom up at 45°
        (10, 0, "side_right"),            # Pure side (right)
        (10, 180, "side_left"),           # Pure side (left)
        (20, -60, "isometric_right"),     # Isometric right
        (20, -120, "isometric_left"),     # Isometric left
    ]
    
    print(f"\nRendering {len(views)} views...")
    for elev, azim, name in views:
        title = name.replace('_', ' ').title()
        out_path = os.path.join(output_dir, f"{name}.png")
        render_stl(stl_mesh, elev, azim, title, out_path)
    
    print(f"\nAll renders saved to '{output_dir}/' folder.")
    print("Compare these with kiro_plushie_images/ to identify shape differences.")


if __name__ == '__main__':
    main()
