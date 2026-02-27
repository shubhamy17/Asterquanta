from fastapi import FastAPI, UploadFile, File, Depends, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, select
from sqlalchemy import desc
from database import engine, get_session, create_db_and_tables
from models import Job, Transaction, User
from sqlmodel import Session
from pydantic import BaseModel, EmailStr
import pandas as pd
import os
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

# Temporal imports
from temporalio.client import Client as TemporalClient

# WebSocket manager
from websocket_manager import manager as ws_manager

# Temporal configuration
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE = "job-processing-queue"

# Global Temporal client (initialized at startup)
temporal_client: TemporalClient = None

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    global temporal_client
    create_db_and_tables()
    
    # Connect to Temporal server
    try:
        temporal_client = await TemporalClient.connect(TEMPORAL_HOST)
        print(f"Connected to Temporal server at {TEMPORAL_HOST}")
    except Exception as e:
        print(f"Warning: Could not connect to Temporal server: {e}")
        print("Job processing will fall back to BackgroundTasks")
    
    yield  # App runs here
    
    # Shutdown logic (if needed)
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class UserCreate(BaseModel):
    name: str
    email: EmailStr

class ProgressBroadcast(BaseModel):
    """Model for internal progress broadcast from worker to FastAPI"""
    user_id: int
    job_id: int
    status: str
    progress_percent: int
    processed_records: int
    total_records: int
    valid_records: int
    invalid_records: int
    suspicious_records: int
    batch_completed: int
    total_batches: int

# ==============================
# USER ENDPOINTS
# ==============================

@app.post("/users")
def create_user(user_data: UserCreate, session: Session = Depends(get_session)):
    # Check if email already exists
    existing_user = session.exec(select(User).where(User.email == user_data.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(name=user_data.name, email=user_data.email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@app.get("/users")
def get_all_users(session: Session = Depends(get_session)):
    # Use ORM query with ordering
    users = session.exec(select(User).order_by(desc(User.created_at))).all()
    return users

@app.get("/users/{user_id}")
def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users/{user_id}/jobs")
def get_user_jobs(user_id: int, session: Session = Depends(get_session)):
    # Use ORM relationship instead of query builder
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Access jobs through relationship and sort in Python
    return sorted(user.jobs, key=lambda j: j.created_at, reverse=True)

# ==============================
# 1️⃣ UPLOAD CSV → POST /jobs
# ==============================

@app.post("/jobs")
async def create_job(user_id: int, file: UploadFile = File(...), session: Session = Depends(get_session)):
    # Use ORM to get user
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create job using ORM
    job = Job(user_id=user_id, status="UPLOADED")
    session.add(job)
    session.commit()
    session.refresh(job)

    # Save file
    path = f"{UPLOAD_DIR}/job_{job.id}.csv"
    with open(path, "wb") as f:
        f.write(await file.read())

    return {"job_id": job.id}


# ==============================
# BATCH WORKER
# ==============================

def process_job(job_id: int):

    with Session(engine) as session:

        job = session.get(Job, job_id)

        if job.status == "RUNNING":
            return

        job.status = "RUNNING"
        session.commit()

        df = pd.read_csv(f"uploads/job_{job_id}.csv")

        job.total_records = len(df)
        session.commit()

        BATCH = 100

        for i in range(0, len(df), BATCH):

            batch = df.iloc[i:i+BATCH]

            for _, row in batch.iterrows():

                error = None
                valid = True

                try:
                    ts = datetime.fromisoformat(str(row["timestamp"]))
                except:
                    error = "Invalid timestamp"
                    valid = False

                if not isinstance(row["amount"], (int,float)):
                    error = "Invalid amount"
                    valid = False

                suspicious = False
                if float(row["amount"]) < 0 or float(row["amount"]) > 50000:
                    suspicious = True

                t = Transaction(
                    job_id=job_id,
                    transaction_id=str(row["transaction_id"]),
                    user_id=str(row["user_id"]),
                    amount=float(row["amount"]),
                    timestamp=ts if valid else datetime.now(),
                    is_valid=valid,
                    is_suspicious=suspicious,
                    error_message=error
                )

                session.add(t)

                job.processed_records += 1
                if valid:
                    job.valid_records += 1
                else:
                    job.invalid_records += 1
                
                if suspicious:
                    job.suspicious_records += 1

            session.commit()   # commit per batch (REQUIRED)

        job.status = "COMPLETED"
        session.commit()


# ==============================
# 2️⃣ START JOB → POST /jobs/{id}/start
# ==============================

@app.post("/jobs/{job_id}/start")
async def start_job(job_id: int, bg: BackgroundTasks, session: Session = Depends(get_session)):
    
    job = session.get(Job, job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status == "RUNNING":
        raise HTTPException(status_code=400, detail="Already running")
    
    # Use Temporal workflow if connected, otherwise fall back to BackgroundTasks
    if temporal_client:
        from workflows import ProcessJobWorkflow
        
        # Start workflow with job_id as workflow ID for idempotency
        await temporal_client.start_workflow(
            ProcessJobWorkflow.run,
            job_id,
            id=f"job-{job_id}",
            task_queue=TASK_QUEUE
        )
        return {"message": "started", "mode": "temporal"}
    else:
        # Fallback to BackgroundTasks if Temporal is not available
        bg.add_task(process_job, job_id)
        return {"message": "started", "mode": "background"}

# ==============================
# 3️⃣ JOB STATUS → GET /jobs/{id}
# ==============================

@app.get("/jobs/{job_id}")
def job_status(job_id:int, session:Session=Depends(get_session)):

    job = session.get(Job, job_id)

    percent = 0
    if job.total_records:
        percent = int(job.processed_records/job.total_records*100)

    return {
        "id":job.id,
        "status":job.status,
        "total_records":job.total_records,
        "processed_records":job.processed_records,
        "valid_records":job.valid_records,
        "invalid_records":job.invalid_records,
        "suspicious_records":job.suspicious_records,
        "progress_percent":percent,
        "created_at":job.created_at
    }


# ==============================
# 4️⃣ VIEW RESULTS → GET /jobs/{id}/transactions
# ==============================

@app.get("/jobs/{job_id}/transactions")
def transactions(
        job_id:int,
        page:int=1,
        size:int=20,
        filter:str=None,
        session:Session=Depends(get_session)
):

    q = select(Transaction).where(Transaction.job_id==job_id)

    if filter=="valid":
        q=q.where(Transaction.is_valid==True)

    if filter=="invalid":
        q=q.where(Transaction.is_valid==False)

    if filter=="suspicious":
        q=q.where(Transaction.is_suspicious==True)

    rows=session.exec(q.offset((page-1)*size).limit(size)).all()

    return rows


# ==============================
# 5️⃣ WEBSOCKET → /ws/{user_id}
# ==============================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """
    WebSocket endpoint for real-time job progress updates.
    
    Connect: ws://localhost:8000/ws/{user_id}
    
    Receives JSON messages with job progress:
    {
        "type": "job_progress",
        "job_id": 123,
        "status": "RUNNING",
        "progress_percent": 45,
        "processed_records": 450,
        "total_records": 1000,
        "valid_records": 440,
        "invalid_records": 10,
        "suspicious_records": 5,
        "batch_completed": 5,
        "total_batches": 10
    }
    """
    await ws_manager.connect(user_id, websocket)
    
    try:
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for ping/pong or client messages
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # Ping timeout
                )
                
                # Handle ping from client
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_text("ping")
                except Exception:
                    break
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error for user {user_id}: {e}")
    finally:
        await ws_manager.disconnect(user_id, websocket)


# ==============================
# 6️⃣ INTERNAL BROADCAST → POST /internal/broadcast
# ==============================

@app.post("/internal/broadcast")
async def internal_broadcast(data: ProgressBroadcast):
    """
    Internal endpoint for Temporal worker to broadcast progress updates.
    The worker calls this via HTTP since it runs in a separate process
    and doesn't have access to the FastAPI WebSocket connections.
    """
    progress_data = {
        "type": "job_progress",
        "job_id": data.job_id,
        "status": data.status,
        "progress_percent": data.progress_percent,
        "processed_records": data.processed_records,
        "total_records": data.total_records,
        "valid_records": data.valid_records,
        "invalid_records": data.invalid_records,
        "suspicious_records": data.suspicious_records,
        "batch_completed": data.batch_completed,
        "total_batches": data.total_batches
    }
    
    await ws_manager.broadcast_to_user(data.user_id, progress_data)
    
    return {"status": "broadcast_sent", "user_id": data.user_id}

