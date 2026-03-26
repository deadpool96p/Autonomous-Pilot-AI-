from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class Track(BaseModel):
    id: str
    name: str
    json_data: Dict[str, Any]

class TrackCreate(BaseModel):
    name: str
    json_data: Dict[str, Any]

class SimulationRun(BaseModel):
    id: str
    track_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str # "running", "completed", "stopped"

class SimulationRunCreate(BaseModel):
    track_id: str
    status: str

class DLConfig(BaseModel):
    mode: str # "ga", "dl", "manual"
    recording: bool

class DLStatus(BaseModel):
    is_recording: bool
    current_mode: str
    model_loaded: bool
    last_log: Optional[str] = None
