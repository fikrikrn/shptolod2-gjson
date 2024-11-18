import time
import shutil
import os
from file1 import process_aspect
from file2_new import process_raster
from file4 import process_union_clip
from cleann import runnn
from full_building import generate_complete_building_model
from separate_obj import split_obj_by_shapefile
from make_solid import make_obj_solid
from tocityjson import obj_to_cityjson

# UBAH BAGIAN INI
ohm_path = './input/OHM_FT_Fix.tif'
building_outline_path = './input/BO_FT.shp'
epsg = 32749
output_cityjson = './output/Teknik-with-remove-ver.json'

# FILE TEMPORARY JANGAN DIUBAH
temp_folder = './temp'
output_path = os.path.join(temp_folder, 'output.tif')
output_shp = os.path.join(temp_folder, 'shp_output.shp')
output_shapefile_bersihh = os.path.join(temp_folder, 'bersihh.shp')
output_union_path = os.path.join(temp_folder, 'union.shp')
sip = os.path.join(temp_folder, './sip.shp')
output_folder = os.path.join(temp_folder, 'lod2')
output_lod2 = os.path.join(temp_folder, 'full_building.obj')
output_solid_lod2 = os.path.join(temp_folder, 'lod2.obj')
smooth_obj = (temp_folder, 'halus.obj')


def create_temp_folder(folder_path):
    """Membuat folder temporary jika belum ada."""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Folder temporary '{folder_path}' berhasil dibuat.")

def clear_temp_folder(folder_path):
    """Menghapus semua file dan subfolder dalam folder temporary."""
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        print(f"Folder temporary '{folder_path}' berhasil dihapus.")

def main():
    create_temp_folder(temp_folder)

    try:
        start = time.time()
        process_aspect(ohm_path, building_outline_path, output_path)
        print(f"Pembuatan Aspect selesai dalam {time.time() - start:.2f} detik")

        start = time.time()
        process_raster(output_path, output_shp, 4)
        print(f"Pembuatan shp dari Aspect selesai dalam {time.time() - start:.2f} detik")

        # start = time.time()
        # runnn(output_shp, output_shapefile_bersihh, 0.1, 1)
        # print(f"Pembersihan geometry selesai dalam {time.time() - start:.2f} detik")

        start = time.time()
        # process_union_clip(output_shapefile_bersihh, building_outline_path, output_union_path)
        process_union_clip(output_shp, building_outline_path, output_union_path)
        print(f"Perapihan geometry selesai dalam {time.time() - start:.2f} detik")

        start = time.time()
        # process_union_clip(output_shapefile_bersihh, building_outline_path, output_union_path)
        process_union_clip(output_shp, building_outline_path, output_union_path)
        print(f"Perapihan geometry selesai dalam {time.time() - start:.2f} detik")       

        start = time.time()
        generate_complete_building_model(output_union_path, ohm_path, output_lod2, base_height=0)
        print(f"Pembuatan model obj LOD 2 selesai dalam {time.time() - start:.2f} detik")

        start = time.time()
        make_obj_solid(output_lod2, output_solid_lod2, False)
        print(f"Membuat LOD 2 menjadi solid selesai dalam {time.time() - start:.2f} detik")

        start = time.time()
        split_obj_by_shapefile(output_solid_lod2, building_outline_path, output_folder)
        print(f"Pemisahan per ID LOD 2 selesai dalam {time.time() - start:.2f} detik")

        start = time.time()
        obj_to_cityjson(output_folder, output_cityjson, epsg)
        print(f"Pembuatan CityJSON selesai dalam {time.time() - start:.2f} detik")
    
    # except Exception as e:
    #     print(f"salah : {e}")
    finally:
        clear_temp_folder(temp_folder)

if __name__ == "__main__":
    main()
