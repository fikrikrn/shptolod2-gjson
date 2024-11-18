from tqdm import tqdm
import geopandas as gpd

def filter_shapefile_by_area(input_raw_path, output_new_path, min_area):
    
    with tqdm(total=3, desc="Filtering Shapefile by Area", unit="step") as pbar:
        
        # Langkah 1: Membaca shapefile
        gdf = gpd.read_file(input_raw_path)
        pbar.update(1)  # Update setelah membaca shapefile
        
        # Langkah 2: Menambahkan kolom luas dan melakukan filter
        gdf["area"] = gdf.geometry.area.astype(int)
        gdf_filtered = gdf[gdf["area"] >= min_area]
        pbar.update(1)  # Update setelah filter area
        
        # Langkah 3: Menyimpan shapefile hasil filter
        gdf_filtered.to_file(output_new_path)
        pbar.update(1)  # Update setelah penyimpanan shapefile

    print(f"Proses seleksi selesai. Shapefile yang telah difilter disimpan sebagai: {output_new_path}")
