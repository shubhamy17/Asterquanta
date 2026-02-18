from fastapi import FastAPI, UploadFile, File, Depends
from database import engine, get_session
from models import Job
from sqlmodel import Session
import os

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
