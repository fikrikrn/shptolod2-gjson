import trimesh

def make_obj_solid(input_file, output_file, use_convex_hull):
    # Memuat mesh dari file input
    scene_or_mesh = trimesh.load(input_file)
    
    # Jika hasilnya adalah Scene, gabungkan semua mesh menjadi satu
    if isinstance(scene_or_mesh, trimesh.Scene):
        print("File berisi beberapa mesh. Menggabungkan menjadi satu mesh.")
        meshes = [geometry for geometry in scene_or_mesh.geometry.values()]
        mesh = trimesh.util.concatenate(meshes)
    else:
        mesh = scene_or_mesh  # Sudah berupa Trimesh

    # Mengecek apakah mesh sudah solid
    if not mesh.is_watertight:
        print("Mesh tidak solid. Mencoba menutup lubang...")
        mesh.fill_holes()
        
        # Jika mesh masih tidak solid, gunakan convex hull jika diizinkan
        if not mesh.is_watertight and use_convex_hull:
            print("Menggunakan convex hull untuk membuat model solid.")
            mesh = mesh.convex_hull  # Membuat mesh baru yang solid berbentuk convex

    # Menyimpan mesh solid ke file output
    mesh.export(output_file)
    print(f"File {output_file} telah disimpan dengan mesh yang solid.")
