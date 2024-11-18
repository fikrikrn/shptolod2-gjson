from tqdm import tqdm
import geopandas as gpd
import rasterio
import numpy as np
from shapely.geometry import Polygon

def save_obj(vertices, faces, filename="output.obj"):
    with open(filename, 'w') as f:
        # Tulis vertices
        for v in vertices:
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")
        # Tulis faces
        for face in faces:
            face_indices = ' '.join(str(idx + 1) for idx in face)
            f.write(f"f {face_indices}\n")
    print(f"File saved as {filename}")

def generate_polygon_3d_model(shapefile_path: str, ohm_tif_path: str, output_obj_path: str):
    # Baca shapefile polygon
    gdf = gpd.read_file(shapefile_path)

    # Buka file raster OHM
    with rasterio.open(ohm_tif_path) as ohm:
        vertices = []
        faces = []
        vertex_index = 0

        # Tambahkan progress bar untuk iterasi setiap polygon
        with tqdm(total=len(gdf), desc="Processing Polygons", unit="polygon") as pbar:
            for polygon in gdf.geometry:
                if isinstance(polygon, Polygon):
                    poly_vertices = []
                    
                    # Tambahkan progress bar untuk setiap koordinat pada polygon
                    for x, y in tqdm(polygon.exterior.coords, desc="Processing Coordinates", leave=False):
                        # Ambil nilai tinggi dari OHM pada titik (x, y)
                        row, col = ohm.index(x, y)
                        z = ohm.read(1)[row, col]  # Asumsi nilai ketinggian diambil dari band pertama
                        vertices.append((x, y, z))
                        poly_vertices.append(vertex_index)
                        vertex_index += 1
                    
                    # Tambahkan polygon sebagai face
                    faces.append(poly_vertices)
                
                # Perbarui progress bar setelah setiap polygon selesai diproses
                pbar.update(1)

        # Simpan hasil sebagai file OBJ
        save_obj(vertices, faces, output_obj_path)
