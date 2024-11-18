from tqdm import tqdm
import geopandas as gpd
import rasterio
import numpy as np
import pyvista as pv

def generate_building_walls_obj(shapefile_path, ohm_tif_path, output_path, base_height=0):
    # Baca shapefile dan TIF
    shapefile = gpd.read_file(shapefile_path)
    raster = rasterio.open(ohm_tif_path)
    
    # Persiapkan daftar untuk menyimpan mesh bangunan
    walls = []

    # Iterasi melalui setiap geometri (contoh bangunan) dalam shapefile dengan progress bar
    for _, row in tqdm(shapefile.iterrows(), total=len(shapefile), desc="Processing Buildings", unit="building"):
        geom = row.geometry
        
        # Jika geometri adalah MultiPolygon, iterasi setiap Polygon di dalamnya
        if geom.geom_type == 'MultiPolygon':
            polygons = geom.geoms
        elif geom.geom_type == 'Polygon':
            polygons = [geom]  # Jika geometri adalah Polygon, masukkan ke dalam list
        
        # Iterasi melalui setiap Polygon
        for polygon in polygons:
            # Ambil koordinat dari tiap vertex
            coords = np.array(polygon.exterior.coords)
            
            # Ambil elevasi (Z) dari raster untuk setiap koordinat dengan progress bar
            heights = []
            for x, y in tqdm(coords, desc="Sampling Heights", leave=False):
                for val in raster.sample([(x, y)]):
                    heights.append(val[0])  # Ambil ketinggian pada titik tersebut
            
            # Pastikan jumlah ketinggian sama dengan jumlah titik
            if len(heights) != len(coords):
                continue  # Skip jika ada data yang tidak sesuai
            
            # Buat dinding untuk setiap sisi poligon
            for i in range(len(coords) - 1):
                x1, y1 = coords[i]
                x2, y2 = coords[i + 1]
                z1 = heights[i]
                z2 = heights[i + 1]
                
                # Definisikan empat titik sudut untuk dinding segitiga dari 0 ke ketinggian OHM
                points = np.array([
                    [x1, y1, base_height],  # Titik dasar 1
                    [x2, y2, base_height],  # Titik dasar 2
                    [x1, y1, z1],           # Titik tinggi 1
                    [x2, y2, z2]            # Titik tinggi 2
                ])
                
                # Buat mesh segitiga untuk dinding
                faces = [[3, 0, 1, 2], [3, 1, 2, 3]]  # Buat dua segitiga untuk setiap sisi
                walls.append((points, faces))

    # Buat objek mesh PyVista untuk visualisasi
    all_meshes = pv.PolyData()
    for points, faces in tqdm(walls, desc="Building Meshes", unit="wall"):
        mesh = pv.PolyData(points, faces)
        all_meshes = all_meshes + mesh

    # Simpan sebagai file OBJ
    all_meshes.save(output_path, binary=False)
    print(f"File OBJ disimpan ke {output_path}")
