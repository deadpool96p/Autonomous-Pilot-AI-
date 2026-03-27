import osmnx as ox
import networkx as nx
import json
import os
import random
import numpy as np
from shapely.geometry import mapping, LineString, Polygon, MultiPolygon
from shapely.ops import unary_union

def import_osm_to_track(location_name="Montmartre, Paris, France", dist=500, output_file="city_track.json"):
    print(f"[*] Downloading OSM data for: {location_name}...")
    
    # 1. Get driving network
    try:
        G = ox.graph_from_address(location_name, dist=dist, network_type='drive')
        G_proj = ox.project_graph(G)
        nodes_proj, edges_proj = ox.graph_to_gdfs(G_proj)
    except Exception as e:
        print(f"[!] Error downloading roads: {e}")
        return

    # 2. Get buildings (optional but recommended for realism)
    buildings = None
    try:
        buildings_gdf = ox.features_from_address(location_name, tags={'building': True}, dist=dist)
        buildings = ox.project_gdf(buildings_gdf, to_crs=G_proj.graph['crs'])
    except Exception as e:
        print(f"[*] No buildings found or error: {e}")

    # 3. Coordinate Normalization
    # We want to fit the map into a localized coordinate system (e.g. 0-2000 units)
    minx, miny, maxx, maxy = nodes_proj.total_bounds
    width = maxx - minx
    height = maxy - miny
    
    # Scale to roughly 1500 units wide for visibility
    target_scale = 1500 / max(width, height)
    
    def transform_pt(x, y):
        return [
            float((x - minx) * target_scale + 100), # 100 padding
            float((maxy - y) * target_scale + 100)  # Invert Y for canvas
        ]

    track_data = {
        "id": "osm_" + location_name.lower().replace(" ", "_").split(",")[0],
        "name": f"City: {location_name.split(',')[0]}",
        "roads": [],
        "buildings": [],
        "graph": {"nodes": {}, "edges": []},
        "checkpoints": [],
        "start_pos": [0, 0],
        "start_angle": 0
    }

    # 4. Process Graph for NPC Navigation
    for node_id, data in G_proj.nodes(data=True):
        pt = transform_pt(data['x'], data['y'])
        track_data["graph"]["nodes"][str(node_id)] = pt
        
    for u, v, data in G_proj.edges(data=True):
        track_data["graph"]["edges"].append([str(u), str(v)])

    # 4. Process Roads
    # Each edge represents a road segment
    road_polygons = []
    track_data["lanes"] = []
    track_data["road_markings"] = []
    track_data["traffic_signs"] = []
    
    lane_counter = 0

    for _, edge in edges_proj.iterrows():
        # Buffer the centerline to create a road surface (approx 14m wide)
        line = edge.geometry
        buffered = line.buffer(7.0) # 7m radius = 14m width
        road_polygons.append(buffered)
        
        # Add to track as points
        coords = [transform_pt(x, y) for x, y in line.coords]
        track_data["roads"].append({
            "points": coords,
            "width": 14.0 * target_scale 
        })
        
        # Extract lanes info for HD Mapping
        try:
            # Parallel offset to create lane boundaries
            left_line = line.parallel_offset(3.5, 'left')
            right_line = line.parallel_offset(3.5, 'right')
            
            # Shapely parallel_offset can return MultiLineString; we handle simple LineStrings for now
            if isinstance(left_line, LineString) and isinstance(right_line, LineString):
                # Reverse right line so direction matches
                left_coords = [transform_pt(x, y) for x, y in left_line.coords]
                right_coords = [transform_pt(x, y) for x, y in list(right_line.coords)[::-1]]
                
                track_data["lanes"].append({
                    "lane_id": lane_counter,
                    "type": "driving",
                    "width": 7.0 * target_scale,
                    "center_line": coords,
                    "left_boundary": left_coords,
                    "right_boundary": right_coords,
                    "markings": ["solid_white", "dashed_yellow"]
                })
                lane_counter += 1
        except Exception as e:
            pass

    # Add random traffic signs near random nodes
    sign_types = ["stop", "speed_limit_30", "yield"]
    for i, (str_node_id, pt) in enumerate(track_data["graph"]["nodes"].items()):
        if i % 20 == 0:  # Sparse signs
            stype = random.choice(sign_types)
            track_data["traffic_signs"].append({
                "type": stype,
                "position": pt,
                "facing": random.randint(0, 360),
                "value": 30 if "speed" in stype else None
            })

    # 5. Process Buildings
    if buildings is not None:
        for _, b in buildings.iterrows():
            if isinstance(b.geometry, (Polygon, MultiPolygon)):
                geom = b.geometry
                if isinstance(geom, MultiPolygon):
                    geom = unary_union(geom)
                
                if isinstance(geom, Polygon):
                    coords = [transform_pt(x, y) for x, y in geom.exterior.coords]
                    track_data["buildings"].append({
                        "points": coords
                    })

    # 6. Set Start Position (first valid node)
    first_node = nodes_proj.iloc[0]
    track_data["start_pos"] = transform_pt(first_node.x, first_node.y)
    
    # 7. Add dummy checkpoints (nodes of the graph)
    sorted_nodes = nodes_proj.sort_values(by=['x', 'y'])
    for i, node in enumerate(sorted_nodes.itertuples()):
        if i % 10 == 0: # Sparse checkpoints
            pt = transform_pt(node.x, node.y)
            track_data["checkpoints"].append(pt)

    # 8. Seed Dynamic Objects
    track_data["dynamic_objects"] = []
    all_node_ids = list(track_data["graph"]["nodes"].keys())
    
    # Add random pedestrians along nodes
    for i in range(30):
        start_node = random.choice(all_node_ids)
        track_data["dynamic_objects"].append({
            "type": "pedestrian",
            "start_node": start_node,
            "speed": float(np.random.uniform(1.2, 1.8))
        })
            
    # Add random NPC cars
    for i in range(20):
        start_node = random.choice(all_node_ids)
        track_data["dynamic_objects"].append({
            "type": "npc_car",
            "start_node": start_node,
            "speed": float(np.random.uniform(5.0, 9.0))
        })

    # 9. Save to file
    output_dir = os.path.join(os.path.dirname(__file__), "../data/tracks")
    os.makedirs(output_dir, exist_ok=True)
    
    full_path = os.path.join(output_dir, output_file)
    with open(full_path, "w") as f:
        json.dump(track_data, f, indent=2)
        
    print(f"[+] Track saved to: {full_path}")
    return full_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--location", default="Montmartre, Paris, France")
    parser.add_argument("--dist", type=int, default=400)
    parser.add_argument("--out", default="paris_osm.json")
    args = parser.parse_args()
    
    import_osm_to_track(args.location, args.dist, args.out)
