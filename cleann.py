import geopandas as gpd
from tqdm import tqdm
from shapely.ops import unary_union
import numpy as np


def runnn(input:str, output:str, thres:float, iter:float):
    # Read GeoJSON file into GeoDataFrame with error handling
    THRESHOLD = thres
    ITER = iter

    for iteration in range(ITER):
        try:
            if iteration == 0:
                building_gdf = gpd.read_file(input)
            else:
                building_gdf = gpd.read_file(output)

            # Fix invalid geometries
            building_gdf['geometry'] = building_gdf['geometry'].buffer(0)

            # Create a spatial index for faster intersection checks
            building_gdf = building_gdf.dropna(subset=['geometry'])  # Drop rows with invalid geometries
            if not building_gdf.empty:
                spatial_index = building_gdf.sindex
            else:
                print("GeoDataFrame is empty after dropping rows with invalid geometries.")
                continue  # Skip to the next iteration if GeoDataFrame is empty

        except ValueError as e:
            print(f"Error reading GeoJSON file: {e}")
            # continue  # Skip to the next iteration if there's an error reading the GeoJSON file

        # List to store merged features
        merged_features = []

        # Set to keep track of processed features
        processed_features = set()

        # Iterate over each feature
        for i, geom_a in tqdm(building_gdf.iterrows(), total=len(building_gdf), desc="Processing features"):            
            # Get potential intersecting features using spatial index
            if spatial_index:
                possible_matches_index = list(spatial_index.intersection(geom_a['geometry'].bounds))
            else:
                possible_matches_index = []

            # List to store geometries of intersecting features
            intersecting_geometries = []

            # Check intersection with other features
            for j in possible_matches_index:
                if i != j and i < j:
                    geom_b = building_gdf.loc[j, 'geometry']

                    # Check if the features intersect
                    if geom_a['geometry'].intersects(geom_b):
                        # Calculate the intersection area relative to each feature's area
                        intersection_area_a = geom_a['geometry'].intersection(geom_b).area / geom_a['geometry'].area
                        intersection_area_b = geom_a['geometry'].intersection(geom_b).area / geom_b.area

                        # Check if either feature has an intersection area greater than threshold value
                        if intersection_area_a > THRESHOLD or intersection_area_b > THRESHOLD:
                            intersecting_geometries.append(geom_b) 
                            processed_features.add(j)  # Mark as processed

            
            # Merge intersecting features
            if intersecting_geometries:
                # Apply the difference function to the intersecting geometries
                for intersecting_geometry in intersecting_geometries:
                    geom_a['geometry'] = geom_a['geometry'].difference(intersecting_geometry)
                
                # Store the updated geometry
                merged_features.append({'id': f"{i}_merged", 'geometry': geom_a['geometry']})
            else:
                # If no intersection found, add the original feature
                merged_features.append({'id': f"{i}_asli", 'geometry': geom_a['geometry']})
            
        # Create a GeoDataFrame with the merged features
        merged_features_gdf = gpd.GeoDataFrame(merged_features, crs=building_gdf.crs)

        # Save the updated GeoDataFrame to a new GeoJSON file
        merged_features_gdf.to_file(output, driver='GeoJSON')