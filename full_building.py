import logging
from tqdm import tqdm
import geopandas as gpd
import rasterio
from shapely.geometry import Polygon, MultiPolygon

def save_obj(vertices, faces, filename="output.obj"):
    """Simpan model dalam format OBJ."""
    with open(filename, 'w') as f:
        # Tulis vertices
        for v in vertices:
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")
        # Tulis faces
        for face in faces:
            face_indices = ' '.join(str(idx + 1) for idx in face)
            f.write(f"f {face_indices}\n")
    print(f"File saved as {filename}")

def generate_complete_building_model(shapefile_path, ohm_tif_path, output_obj_path, base_height=0):
    """Buat model bangunan dengan dinding dan atap dari shapefile dan raster elevasi."""
    # Inisialisasi logging
    logging.basicConfig(level=logging.INFO)
    
    # Load shapefile
    gdf = gpd.read_file(shapefile_path)

    # Load raster dan pastikan CRS shapefile cocok dengan CRS raster
    with rasterio.open(ohm_tif_path) as ohm:
        gdf = gdf.to_crs(ohm.crs)
        raster_bounds = ohm.bounds  # Batas raster

        # Filter geometri yang berada dalam domain raster
        gdf = gdf.cx[raster_bounds[0]:raster_bounds[2], raster_bounds[1]:raster_bounds[3]]
        gdf = gdf[gdf.is_valid]  # Hapus geometri yang tidak valid

        vertices = []
        faces = []
        vertex_index = 0

        # Progress bar untuk setiap bangunan
        for _, row in tqdm(gdf.iterrows(), total=len(gdf), desc="Processing Buildings", unit="building"):
            geom = row.geometry
            
            # Tangani Polygon dan MultiPolygon
            polygons = [geom] if geom.geom_type == 'Polygon' else geom.geoms if geom.geom_type == 'MultiPolygon' else []

            for polygon in polygons:
                poly_vertices = []  # Vertices atap
                wall_faces = []     # Faces dinding

                # Proses koordinat atap
                for x, y in tqdm(polygon.exterior.coords, desc="Processing Coordinates", leave=False):
                    try:
                        row, col = ohm.index(x, y)
                        # Pastikan koordinat berada dalam domain raster
                        if not (0 <= row < ohm.height and 0 <= col < ohm.width):
                            logging.warning(f"Coordinate {(x, y)} out of bounds for raster.")
                            continue
                        z = ohm.read(1)[row, col]  # Baca elevasi
                        vertices.append((x, y, z))
                        poly_vertices.append(vertex_index)
                        vertex_index += 1
                    except Exception as e:
                        logging.error(f"Error processing coordinate {(x, y)}: {e}")
                        continue

                # Tambahkan face untuk atap jika memiliki setidaknya 3 vertex
                if len(poly_vertices) >= 3:
                    faces.append(poly_vertices)

                # Buat dinding dengan menghubungkan base dan top face
                for i in range(len(poly_vertices) - 1):
                    v0 = poly_vertices[i]
                    v1 = poly_vertices[i + 1]

                    # Vertices untuk dinding
                    x0, y0, _ = vertices[v0]
                    x1, y1, _ = vertices[v1]
                    vertices.append((x0, y0, base_height))
                    vertices.append((x1, y1, base_height))
                    
                    # Indeks vertices dinding
                    base_v0 = vertex_index
                    base_v1 = vertex_index + 1
                    vertex_index += 2
                    
                    # Tambahkan dua triangular face untuk dinding
                    wall_faces.append([v0, v1, base_v1])  # Segitiga 1
                    wall_faces.append([v0, base_v0, base_v1])  # Segitiga 2
                
                # Tambahkan semua face dinding ke daftar utama
                faces.extend(wall_faces)

    # Simpan model ke file OBJ
    save_obj(vertices, faces, output_obj_path)
