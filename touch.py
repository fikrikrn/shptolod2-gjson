import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import unary_union

def filter_vertices_with_two_connections(input_shapefile, output_shapefile):
    """
    Menyederhanakan geometri MultiPolygon dengan hanya mempertahankan vertex 
    yang memiliki minimal 2 hubungan (terhubung dengan 2 vertex lain).

    Parameters:
    - input_shapefile: str, path ke file shapefile input.
    - output_shapefile: str, path untuk menyimpan shapefile hasil.
    """
    # Baca shapefile menggunakan GeoPandas
    gdf = gpd.read_file(input_shapefile)

    # Gabungkan semua geometri untuk pemeriksaan hubungan
    all_geometries = unary_union(gdf.geometry)

    # Fungsi untuk memeriksa hubungan antar vertex
    def get_connected_vertices(geometry):
        """
        Mengembalikan daftar vertex yang memiliki minimal 2 koneksi.
        """
        coords = list(geometry.exterior.coords)
        connections = {coord: 0 for coord in coords}  # Simpan jumlah koneksi per vertex
        
        # Hitung koneksi antar vertex
        for i, coord in enumerate(coords):
            prev_vertex = coords[i - 1] if i > 0 else coords[-1]  # Vertex sebelumnya
            next_vertex = coords[i + 1] if i < len(coords) - 1 else coords[0]  # Vertex berikutnya
            connections[coord] += 1  # Tambah koneksi saat ini
            connections[prev_vertex] += 1  # Koneksi ke vertex sebelumnya
            connections[next_vertex] += 1  # Koneksi ke vertex berikutnya

        # Pilih hanya vertex dengan minimal 2 koneksi
        return [coord for coord, count in connections.items() if count >= 2]

    # Fungsi untuk menyaring vertex pada Polygon
    def filter_polygon_vertices(polygon):
        # Dapatkan vertex yang terhubung dengan minimal 2 koneksi
        valid_coords = get_connected_vertices(polygon)

        # Buat ulang poligon jika valid_coords cukup membentuk geometri
        if len(valid_coords) > 2:
            return Polygon(valid_coords)
        return None

    # Proses setiap geometri dalam GeoDataFrame
    filtered_polygons = []
    for geom in gdf.geometry:
        if geom.geom_type == "Polygon":
            filtered_polygon = filter_polygon_vertices(geom)
            if filtered_polygon:
                filtered_polygons.append(filtered_polygon)
        elif geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                filtered_polygon = filter_polygon_vertices(poly)
                if filtered_polygon:
                    filtered_polygons.append(filtered_polygon)

    # Buat geometri MultiPolygon dari hasil
    filtered_multipolygon = MultiPolygon(filtered_polygons)

    # Simpan ke GeoDataFrame dan file shapefile
    result_gdf = gpd.GeoDataFrame(geometry=[filtered_multipolygon], crs=gdf.crs)
    result_gdf.to_file(output_shapefile)
    print(f"Hasil disimpan di: {output_shapefile}")
