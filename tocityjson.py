import os
import json
import uuid
from tqdm import tqdm

def parse_obj(file_path):
    """Parse OBJ file and extract vertices and faces."""
    vertices = []
    faces = []
    
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split()
            if not parts:
                continue
            if parts[0] == 'v':
                # Vertex line
                vertices.append([float(coord) for coord in parts[1:]])
            elif parts[0] == 'f':
                # Face line
                face_indices = [int(index.split('/')[0]) - 1 for index in parts[1:]]
                faces.append(face_indices)
    
    return vertices, faces

def create_cityjson_structure(geographical_extent, epsg):
    """Create the base CityJSON structure with specified extent."""
    return {
        "type": "CityJSON",
        "version": "1.0",
        "metadata": {
            "referenceSystem": f"urn:ogc:def:crs:EPSG::{epsg}",
            "geographicalExtent": geographical_extent
        },
        "CityObjects": {},
        "vertices": [],
        "appearance": {
            "materials": [
                {
                    "name": "roofandground",
                    "ambientIntensity": 0.2,
                    "diffuseColor": [0.9, 0.1, 0.75],
                    "transparency": 0.0,
                    "isSmooth": False
                },
                {
                    "name": "wall",
                    "ambientIntensity": 0.4,
                    "diffuseColor": [0.1, 0.1, 0.9],
                    "transparency": 0.0,
                    "isSmooth": False
                }
            ]
        }
    }

def add_building_to_cityjson(cityjson, building_id, vertices, faces, building_index):
    """Add building geometry, semantics, and materials to CityJSON structure."""
    vertex_offset = len(cityjson["vertices"])
    cityjson["vertices"].extend(vertices)  # Append vertices to the global list
    
    # Format faces and add to geometry
    solid_geometry = [[[[vertex_offset + idx for idx in face]] for face in faces]]
    
    # Prepare semantics and materials arrays with the correct number of elements
    num_faces = len(faces)
    semantics_values = [[0] * 1 + [1] * 1 + [2] * (num_faces - 2)]
    material_values = [[0] * 1 + [0] * 1 + [1] * (num_faces - 2)]
    
    semantics = {
        "values": semantics_values,
        "surfaces": [
            {"type": "RoofSurface"},
            {"type": "GroundSurface"},
            {"type": "WallSurface"}
        ]
    }
    
    material = {"": {"values": material_values}}
    
    # Define building object
    cityjson["CityObjects"][building_id] = {
        "type": "Building",
        "attributes": {
            "level_0": building_index,
            "level_1": 0,
            "Id": building_index + 1,
            "uuid_bgn": building_id
        },
        "geometry": [{
            "type": "Solid",
            "lod": 1,
            "boundaries": solid_geometry,
            "semantics": semantics,
            "material": material
        }]
    }

def save_cityjson(cityjson, output_path):
    """Save CityJSON data to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(cityjson, f, indent=2)

def obj_to_cityjson(input_folder, output_file, epsg):
    """Menggabungkan kumpulan file OBJ ke satu file CityJSON dengan ID unik."""
    # Membuat struktur dasar CityJSON
    cityjson = create_cityjson_structure([0, 0, 0, 0, 0, 0], epsg)  # Extent bisa diatur sesuai shapefile jika perlu

    obj_files = [f for f in os.listdir(input_folder) if f.endswith('.obj')]
    
    # Iterasi file OBJ di folder input dengan tqdm
    for index, obj_file in enumerate(tqdm(obj_files, desc="Processing OBJ files", unit="file")):
        obj_path = os.path.join(input_folder, obj_file)
        vertices, faces = parse_obj(obj_path)
        
        # Membuat ID unik untuk setiap building berdasarkan nama file atau UUID
        building_id = obj_file.split('.')[0] if obj_file else str(uuid.uuid4())
        
        # Menambahkan bangunan ke CityJSON
        add_building_to_cityjson(
            cityjson,
            building_id,
            vertices,
            faces,
            index
        )

    # Menyimpan hasil CityJSON
    save_cityjson(cityjson, output_file)
    print(f"CityJSON saved to {output_file}")
