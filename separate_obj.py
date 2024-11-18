import shapefile
import trimesh
import numpy as np
import os
from shapely.geometry import shape, Point
from tqdm import tqdm


def is_point_in_polygon(point, polygon, tolerance=0):
    """
    Check if a 2D point is within a polygon with optional buffering.
    """
    if len(point) < 2:
        return False  # Skip invalid points
    if tolerance > 0:
        polygon = polygon.buffer(tolerance)
    return polygon.contains(Point(point[0], point[1]))


def split_obj_by_shapefile(obj_file, shapefile_path, output_folder, tolerance=0.001):
    """
    Split an OBJ file into smaller OBJ files based on the polygons in a shapefile.
    """
    os.makedirs(output_folder, exist_ok=True)

    # Load the shapefile
    sf = shapefile.Reader(shapefile_path)
    print(f"Loaded shapefile with {len(sf)} features.")

    # Load the OBJ file
    mesh = trimesh.load(obj_file)
    vertices = np.array(mesh.vertices)

    # Check vertices dimensions
    if vertices.size == 0 or vertices.shape[1] < 2:
        print("Error: Vertices are empty or do not have enough dimensions.")
        return

    for feature in tqdm(sf.shapeRecords(), desc="Processing shapes", unit="feature", total=len(sf.shapeRecords())):
        polygon_shape = shape(feature.shape.__geo_interface__)
        building_id = feature.record['id']

        # Filter vertices that are valid for processing
        vertex_mask = np.array([
            is_point_in_polygon(vertex, polygon_shape, tolerance)
            for vertex in vertices
        ])

        # Determine which faces should be included based on vertex_mask
        face_mask = np.any(vertex_mask[mesh.faces], axis=1)

        if np.any(face_mask):  # Only process if there are relevant faces
            sub_meshes = mesh.submesh([face_mask], only_watertight=False)
            combined_mesh = trimesh.util.concatenate(sub_meshes) if len(sub_meshes) > 1 else sub_meshes[0]

            # Save the resulting mesh
            output_file = os.path.join(output_folder, f"{building_id}.obj")
            combined_mesh.export(output_file)

    print("All OBJ files have been saved based on the shapefile.")
