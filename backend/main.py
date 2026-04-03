import os
import asyncio
import json
import uuid
import queue
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List
from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend import schemas
from backend.simulation.websocket import manager
from backend.simulation.engine import SimulationEngine
from backend.simulation.track_generator import generate_random_track, save_track

# In-memory storage for active simulations
active_simulations = {}
tracks_cache = {}

TRACKS_DIR = os.path.join(os.path.dirname(__file__), "data", "tracks")


def load_tracks():
    tracks_cache.clear()
    if not os.path.exists(TRACKS_DIR):
        os.makedirs(TRACKS_DIR, exist_ok=True)
    
    for filename in os.listdir(TRACKS_DIR):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(TRACKS_DIR, filename), "r") as f:
                    data = json.load(f)
                    track_id = filename.replace(".json", "")
                    tracks_cache[track_id] = {
                        "id": track_id,
                        "name": data.get("name", track_id),
                        "json_data": data
                    }
            except Exception as e:
                print(f"[!] Failed to load track {filename}: {e}")


async def broadcast_updates():
    """Background task that broadcasts simulation state to WebSocket clients."""
    while True:
        for sim_id in list(active_simulations.keys()):
            if sim_id not in active_simulations:
                continue
            q = active_simulations[sim_id]["queue"]
            
            # Flush queue and broadcast latest state
            latest_state = None
            while not q.empty():
                try:
                    latest_state = q.get_nowait()
                except:
                    break
            
            # Only broadcast the most recent state (skip intermediate frames)
            if latest_state is not None:
                try:
                    await manager.broadcast(json.dumps(latest_state))
                except Exception as e:
                    print(f"[!] Broadcast error for {sim_id}: {e}")
        
        await asyncio.sleep(0.033)  # ~30 fps broadcast rate


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    load_tracks()
    broadcast_task = asyncio.create_task(broadcast_updates())
    print(f"[*] Loaded {len(tracks_cache)} tracks from {TRACKS_DIR}")
    yield
    # Shutdown: stop all simulations
    broadcast_task.cancel()
    for sim_id in list(active_simulations.keys()):
        try:
            active_simulations[sim_id]["engine"].stop()
        except:
            pass
    print("[*] All simulations stopped")


app = FastAPI(title="Autonomous Vehicle Simulation API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health & Status ──────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "Autonomous Vehicle Simulation API is running",
        "tracks": len(tracks_cache),
        "active_simulations": len(active_simulations)
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "tracks_loaded": len(tracks_cache),
        "active_simulations": len(active_simulations),
        "ws_connections": len(manager.active_connections)
    }


# ─── WebSocket ────────────────────────────────────────────────────

@app.websocket("/ws/{simulation_id}")
async def websocket_endpoint(websocket: WebSocket, simulation_id: str):
    await manager.connect(websocket)
    try:
        while True:
            try:
                # Use a timeout so the loop doesn't block forever
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)
                cmd_type = message.get("type")
                
                if simulation_id in active_simulations:
                    engine = active_simulations[simulation_id]["engine"]
                    if cmd_type == "set_mode":
                        engine.mode = message.get("value")
                    elif cmd_type == "set_recording":
                        engine.recording = message.get("value")
                    elif cmd_type == "stop":
                        engine.stop()
                    elif cmd_type == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                # Send a ping to keep connection alive
                try:
                    await websocket.send_text(json.dumps({"type": "heartbeat"}))
                except:
                    break
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.disconnect(websocket)


# ─── Tracks ───────────────────────────────────────────────────────

@app.get("/tracks/", response_model=List[schemas.Track])
def read_tracks():
    load_tracks()
    return list(tracks_cache.values())


@app.get("/tracks/{track_id}")
def get_track(track_id: str):
    if track_id not in tracks_cache:
        load_tracks()  # Retry
    if track_id not in tracks_cache:
        raise HTTPException(status_code=404, detail="Track not found")
    return tracks_cache[track_id]


@app.post("/tracks/generate", response_model=schemas.Track)
def generate_track():
    """Generate a random procedural track."""
    track_data = generate_random_track()
    track_id, saved_data = save_track(track_data, TRACKS_DIR)
    
    track_entry = {
        "id": track_id,
        "name": saved_data.get("name", track_id),
        "json_data": saved_data
    }
    tracks_cache[track_id] = track_entry
    
    return track_entry


# ─── Simulations ──────────────────────────────────────────────────

@app.post("/simulations/start", response_model=schemas.SimulationRun)
def start_simulation(run: schemas.SimulationRunCreate):
    tid = str(run.track_id)
    if tid not in tracks_cache:
        load_tracks()  # Retry loading
    if tid not in tracks_cache:
        raise HTTPException(status_code=404, detail=f"Track '{tid}' not found. Available: {list(tracks_cache.keys())}")
    
    sim_id = str(uuid.uuid4())
    track_data = tracks_cache[tid]["json_data"]
    
    # State queue for broadcasting updates
    state_queue = queue.Queue(maxsize=100)
    
    # Start the simulation engine in a separate thread
    sim_mode = getattr(run, 'mode', 'ga') or 'ga'
    print(f"[*] [Engine] Starting simulation '{sim_id}' on track '{tid}' with mode: {sim_mode}")
    engine = SimulationEngine(sim_id, track_data, state_queue)
    engine.mode = sim_mode
    engine.start()
    
    db_run = schemas.SimulationRun(
        id=sim_id,
        track_id=tid,
        start_time=datetime.utcnow(),
        status="running"
    )
    
    active_simulations[sim_id] = {
        "engine": engine,
        "queue": state_queue,
        "data": db_run
    }
    
    return db_run


@app.post("/simulations/{simulation_id}/stop")
def stop_simulation(simulation_id: str):
    if simulation_id in active_simulations:
        active_simulations[simulation_id]["engine"].stop()
        active_simulations[simulation_id]["data"].status = "stopped"
        # Clean up after a short delay
        return {"status": "stopped", "simulation_id": simulation_id}
    raise HTTPException(status_code=404, detail="Simulation not found")


@app.get("/simulations/{simulation_id}/state")
def get_simulation_state(simulation_id: str):
    """Get the latest state of a simulation (polling fallback)."""
    if simulation_id not in active_simulations:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    q = active_simulations[simulation_id]["queue"]
    latest = None
    while not q.empty():
        try:
            latest = q.get_nowait()
        except:
            break
    
    if latest:
        return latest
    return {"status": "waiting", "simulation_id": simulation_id}


@app.post("/simulations/reset")
def reset_all_simulations():
    """Stop and clear all active simulations."""
    stopped = []
    for sim_id in list(active_simulations.keys()):
        try:
            active_simulations[sim_id]["engine"].stop()
            stopped.append(sim_id)
        except:
            pass
    active_simulations.clear()
    return {"status": "reset", "stopped_simulations": stopped}


@app.post("/simulations/config", response_model=schemas.DLStatus)
def update_config(config: schemas.DLConfig):
    """Update configuration of the most recent simulation."""
    if not active_simulations:
        raise HTTPException(status_code=404, detail="No active simulation")
    
    sim_id = list(active_simulations.keys())[-1]
    engine = active_simulations[sim_id]["engine"]
    
    engine.mode = config.mode
    engine.recording = config.recording
    
    return schemas.DLStatus(
        is_recording=engine.recording,
        current_mode=engine.mode,
        model_loaded=os.path.exists("backend/models/steering_model.pth")
    )


# ─── Deep Learning ────────────────────────────────────────────────

@app.post("/dl/train")
async def train_model():
    try:
        from backend.dl.train import train
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, train)
        return {"status": "success", "message": "Training complete"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
