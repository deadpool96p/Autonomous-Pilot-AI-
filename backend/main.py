import os
import multiprocessing
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import uuid
from datetime import datetime
from typing import List
from backend import schemas

app = FastAPI(title="Autonomous Vehicle Simulation API (Simplified)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session data (or use backend/data/simulations.json for persistence)
active_simulations = {}
tracks_cache = {}

TRACKS_DIR = os.path.join(os.path.dirname(__file__), "core", "environment", "tracks")

def load_tracks():
    tracks_cache.clear()
    if not os.path.exists(TRACKS_DIR):
        os.makedirs(TRACKS_DIR, exist_ok=True)
    
    for filename in os.listdir(TRACKS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(TRACKS_DIR, filename), "r") as f:
                data = json.load(f)
                track_id = filename.replace(".json", "")
                tracks_cache[track_id] = {
                    "id": track_id,
                    "name": data.get("name", track_id),
                    "json_data": data
                }

# Initial load
load_tracks()

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"message": "Autonomous Vehicle Simulation API is running (Lite Mode)"}

@app.websocket("/ws/{simulation_id}")
async def websocket_endpoint(websocket: WebSocket, simulation_id: str):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        pass
    finally:
        manager.disconnect(websocket)

@app.get("/tracks/", response_model=List[schemas.Track])
def read_tracks():
    load_tracks() # Reload to pick up new files
    return list(tracks_cache.values())

@app.post("/tracks/generate", response_model=schemas.Track)
def generate_track():
    from backend.core.environment.track_generator import generate_random_track
    track_data = generate_random_track()
    track_id = f"random_{uuid.uuid4().hex[:8]}"
    
    # Save to file
    file_path = os.path.join(TRACKS_DIR, f"{track_id}.json")
    with open(file_path, "w") as f:
        json.dump(track_data, f)
    
    new_track = {
        "id": track_id,
        "name": track_data["name"],
        "json_data": track_data
    }
    tracks_cache[track_id] = new_track
    return new_track

@app.post("/simulations/start", response_model=schemas.SimulationRun)
def start_simulation(run: schemas.SimulationRunCreate):
    tid = str(run.track_id)
    if tid not in tracks_cache:
        load_tracks()
    if tid not in tracks_cache:
        raise HTTPException(status_code=404, detail="Track not found")
    
    sim_id = str(uuid.uuid4())
    db_run = schemas.SimulationRun(
        id=sim_id,
        track_id=tid,
        start_time=datetime.utcnow(),
        status="running"
    )
    
    # Start background process
    from backend.simulation_runner import SimulationEngine
    track_data = tracks_cache[tid]["json_data"]
    
    queue = multiprocessing.Queue()
    engine = SimulationEngine(sim_id, track_data, queue=queue)
    engine.start()
    active_simulations[sim_id] = {"engine": engine, "queue": queue, "data": db_run}
    print(f"Started simulation {sim_id} for track {tid}")
    
    return db_run

@app.post("/simulations/{simulation_id}/stop")
def stop_simulation(simulation_id: str):
    if simulation_id in active_simulations:
        active_simulations[simulation_id]["engine"].stop()
        active_simulations[simulation_id]["engine"].join()
        active_simulations[simulation_id]["data"].status = "stopped"
        active_simulations[simulation_id]["data"].end_time = datetime.utcnow()
        # Keep in memory for a bit or save to backend/data/history.json
        return {"status": "stopped"}
    raise HTTPException(status_code=404, detail="Simulation not running")

@app.post("/simulations/reset")
def reset_all_simulations():
    for sim_id in list(active_simulations.keys()):
        active_simulations[sim_id]["engine"].stop()
        active_simulations[sim_id]["engine"].join()
        del active_simulations[sim_id]
    
    if os.path.exists("saved_genome.pkl"):
        os.remove("saved_genome.pkl")
    return {"status": "reset"}

async def broadcast_updates():
    while True:
        # Create a list of keys to avoid modification issues during iteration
        for sim_id in list(active_simulations.keys()):
            if sim_id not in active_simulations: continue
            queue = active_simulations[sim_id]["queue"]
            try:
                # Process up to 10 messages per simulation per tick to avoid flooding but stay real-time
                for _ in range(10):
                    if queue.empty(): break
                    try:
                        state = queue.get_nowait()
                        await manager.broadcast(json.dumps(state))
                    except:
                        break
            except Exception as e:
                print(f"Error broadcasting updates for {sim_id}: {e}")
        await asyncio.sleep(0.05)

@app.post("/simulations/save-best")
def save_best_genome():
    if os.path.exists("saved_genome.pkl"):
        # Copy to a timestamped file as well
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import shutil
        shutil.copy("saved_genome.pkl", f"backend/data/genome_{timestamp}.pkl")
        return {"status": "saved", "file": f"genome_{timestamp}.pkl"}
    raise HTTPException(status_code=404, detail="No best genome found yet")

@app.post("/simulations/load-best")
def load_best_genome():
    if os.path.exists("saved_genome.pkl"):
        # In a real app we'd load it into the active population
        return {"status": "loaded"}
    raise HTTPException(status_code=404, detail="No saved genome found")

@app.post("/simulations/config", response_model=schemas.DLStatus)
def update_config(config: schemas.DLConfig):
    # This acts on the most recently started active simulation
    if not active_simulations:
        raise HTTPException(status_code=404, detail="No active simulation")
    
    sim_id = list(active_simulations.keys())[-1]
    cmd_q = active_simulations[sim_id]["command_queue"]
    
    cmd_q.put({"type": "mode", "value": config.mode})
    cmd_q.put({"type": "recording", "value": config.recording})
    
    return schemas.DLStatus(
        is_recording=config.recording,
        current_mode=config.mode,
        model_loaded=os.path.exists("backend/data/best_model.pth")
    )

@app.post("/dl/train")
async def train_model():
    # Behavioral Cloning training from the latest log
    data_dir = "backend/data"
    logs = [f for f in os.listdir(data_dir) if f.startswith("driving_log_") and f.endswith(".csv")]
    if not logs:
        raise HTTPException(status_code=404, detail="No driving logs found")
    
    logs.sort(reverse=True)
    latest_log = os.path.join(data_dir, logs[0])
    
    from backend.core.dl.trainer import train_bc
    try:
        model_path = train_bc(latest_log)
        return {"status": "trained", "model": model_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_updates())
