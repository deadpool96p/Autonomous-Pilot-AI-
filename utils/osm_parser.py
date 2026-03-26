import osmnx as ox
import json
from shapely.geometry import Polygon, mapping
import os

def fetch_osm_track(location_name, road_width=10):
    """
    Fetches OSM road data and converts it to our JSON track format.
    Example: fetch_osm_track("Times Square, New York, USA")
    """
    print(f"Fetching road network for: {location_name}")
    try:
        graph = ox.graph_from_address(location_name, dist=500, network_type='drive')
    except Exception as e:
        print(f"Error fetching OSM data: {e}")
        return None

    # Get road geometries
    gdf_edges = ox.graph_to_gdfs(graph, nodes=False, edges=True)
    
    # Create road boundaries
    # We'll take the first major road or a set of connected roads
    all_roads = gdf_edges.geometry.tolist()
    
    # Simplify for our simulation: buffer road centerlines
    combined_road = ox.utils_geo.unary_union(all_roads)
    buffered_road = combined_road.buffer(road_width / 2.0)
    
    # Convert to polygons (outer boundaries and holes)
    road_boundaries = []
    if buffered_road.geom_type == 'Polygon':
        road_boundaries.append(list(buffered_road.exterior.coords))
        for hole in buffered_road.interiors:
            road_boundaries.append(list(hole.coords))
    elif buffered_road.geom_type == 'MultiPolygon':
        # Pick the largest one for a single track or handle all
        main_poly = max(buffered_road.geoms, key=lambda p: p.area)
        road_boundaries.append(list(main_poly.exterior.coords))
        for hole in main_poly.interiors:
            road_boundaries.append(list(hole.coords))

    # Find a good spawn point (pick first node or start of first edge)
    first_edge = all_roads[0]
    spawn_point = {"x": first_edge.coords[0][0], "y": first_edge.coords[0][1], "angle": 0}

    track_data = {
        "name": location_name,
        "spawn_point": spawn_point,
        "road_boundaries": road_boundaries,
        "obstacles": [],
        "checkpoints": []
    }

    return track_data

def save_track(track_data, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        json.dump(track_data, f, indent=4)
    print(f"Track saved to {filename}")

if __name__ == "__main__":
    # Test fetch
    track = fetch_osm_track("Central Park, New York")
    if track:
        save_track(track, "environment/tracks/central_park.json")
