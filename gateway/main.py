from fastapi import FastAPI, UploadFile, File, Depends, BackgroundTasks, HTTPException
from sqlmodel import SQLModel, select
from database import engine, get_session
from models import Job, Transaction
from sqlmodel import Session
import pandas as pd
import os
from datetime import datetime

app = FastAPI()

SQLModel.metadata.create_all(engine)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# ==============================
# 1️⃣ UPLOAD CSV → POST /jobs
# ==============================

@app.post("/jobs")
async def create_job(file: UploadFile = File(...), session: Session = Depends(get_session)):

    job = Job(status="uploaded")
    session.add(job)
    session.commit()
    session.refresh(job)

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

        if job.status == "running":
            return

        job.status = "running"
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

            session.commit()   # commit per batch (REQUIRED)

        job.status = "completed"
        session.commit()


# ==============================
# 2️⃣ START JOB → POST /jobs/{id}/start
# ==============================

@app.post("/jobs/{job_id}/start")
def start_job(job_id:int, bg:BackgroundTasks, session: Session = Depends(get_session)):

    job = session.get(Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == "running":
        raise HTTPException(status_code=400, detail="Already running")

    bg.add_task(process_job, job_id)

    return {"message":"started"}
