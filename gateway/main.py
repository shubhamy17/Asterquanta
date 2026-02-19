from fastapi import FastAPI, UploadFile, File, Depends, BackgroundTasks, HTTPException
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

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Pydantic models for request/response
class UserCreate(BaseModel):
    name: str
    email: EmailStr

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

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
def start_job(job_id:int, bg:BackgroundTasks, session: Session = Depends(get_session)):

    job = session.get(Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == "RUNNING":
        raise HTTPException(status_code=400, detail="Already running")

    bg.add_task(process_job, job_id)

    return {"message":"started"}

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
