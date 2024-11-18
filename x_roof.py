import numpy as np
import rasterio
import geopandas as gpd
from shapely.geometry import LineString, Polygon, MultiPolygon
from rasterio.transform import Affine
import gdal

# ============================
# 1. Fungsi Menghitung Aspect
# ============================
def calculate_aspect(dem_path, output_path):
    """
    Menghitung aspek dari file raster input (DEM).
    
    Args:
        dem_path (str): Path ke file raster input (TIF).
        output_path (str): Path untuk menyimpan file raster aspek.
    """
    # Membuka raster input
    with rasterio.open(dem_path) as src:
        dem = src.read(1).astype(float)  # Membaca DEM
        transform = src.transform
        crs = src.crs
        profile = src.profile

    # Mengatasi nilai NoData
    dem[dem == src.nodata] = np.nan

    # Perhitungan aspek
    xres = transform.a
    yres = -transform.e
    gy, gx = np.gradient(dem, yres, xres)
    aspect = np.arctan2(-gy, gx)
    aspect_deg = np.degrees(aspect)
    aspect_deg = (aspect_deg + 360) % 360
    aspect_deg[np.isnan(dem)] = np.nan

    # Menyimpan raster aspek
    profile.update(
        dtype=rasterio.float32,
        count=1,
        compress="lzw",
        nodata=np.nan,
    )
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(aspect_deg.astype(np.float32), 1)
    
    print(f"Aspek berhasil dihitung dan disimpan di: {output_path}")

# ============================
# 2. Membuat Struktur Atap
# ============================
def shrink_polygon(polygon, shrink_factor=0.05):
    """Fungsi untuk mengecilkan poligon."""
    return polygon.buffer(-shrink_factor, resolution=16)  # Mengecilkan poligon

def create_edges(polygon):
    """Fungsi untuk membuat garis antar-vertex dari poligon."""
    if polygon.is_empty:
        return None
    if isinstance(polygon, Polygon):
        coords = list(polygon.exterior.coords)
    elif isinstance(polygon, MultiPolygon):
        coords = [list(poly.exterior.coords) for poly in polygon.geoms]
        coords = [c for sublist in coords for c in sublist]

    edges = []
    for i in range(len(coords) - 1):
        edges.append(LineString([coords[i], coords[i + 1]]))
    return edges

def triangulate(polygon):
    """Fungsi untuk membagi poligon menjadi segitiga (triangulasi)."""
    from shapely.ops import triangulate
    return triangulate(polygon)

def process_roof_structure(building_outline_path, output_edges_path, output_triangles_path):
    """
    Membuat struktur atap dari outline gedung.

    Args:
        building_outline_path (str): Path ke file SHP outline gedung.
        output_edges_path (str): Path untuk menyimpan garis antar-vertex (SHP).
        output_triangles_path (str): Path untuk menyimpan hasil triangulasi atap (SHP).
    """
    building_outline = gpd.read_file(building_outline_path)

    # Mengecilkan poligon
    building_outline['shrunk'] = building_outline.geometry.apply(shrink_polygon)

    # Membuat garis antar-vertex
    building_outline['edges'] = building_outline['shrunk'].apply(create_edges)
    all_edges = []
    for edges in building_outline['edges']:
        all_edges.extend(edges)
    edges_gdf = gpd.GeoDataFrame(geometry=all_edges, crs=building_outline.crs)

    # Membuat triangulasi
    building_outline['triangles'] = building_outline['shrunk'].apply(triangulate)
    triangles = []
    for triangle_list in building_outline['triangles']:
        triangles.extend(triangle_list)
    triangles_gdf = gpd.GeoDataFrame(geometry=triangles, crs=building_outline.crs)

    # Menyimpan hasil ke file SHP
    edges_gdf.to_file(output_edges_path)
    triangles_gdf.to_file(output_triangles_path)

    print(f"Struktur atap selesai dibuat:")
    print(f"  - Garis antar-vertex disimpan di: {output_edges_path}")
    print(f"  - Triangulasi atap disimpan di: {output_triangles_path}")

# ============================
# 3. Jalankan Proses
# ============================
if __name__ == "__main__":
    # Path input
    input_dem = "ohm.tif"               # Input DEM (OHM)
    input_building_outline = "building_outline.shp"  # Input SHP outline gedung

    # Path output
    output_aspect = "aspect.tif"        # Output file aspect (TIF)
    output_edges = "roof_edges.shp"     # Output garis antar-vertex (SHP)
    output_triangles = "roof_triangles.shp"  # Output triangulasi atap (SHP)

    # Langkah 1: Hitung Aspect
    calculate_aspect(input_dem, output_aspect)

    # Langkah 2: Buat Struktur Atap
    process_roof_structure(input_building_outline, output_edges, output_triangles)
