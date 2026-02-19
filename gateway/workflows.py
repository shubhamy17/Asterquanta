"""
Temporal Workflow for batch job processing with dynamic batch sizing and WebSocket progress updates.

Architecture:
    Frontend → FastAPI Upload → Start Temporal Workflow → Workflow:
        → init_job_activity (set RUNNING, calculate batches)
        → process_chunk_activity (validate, bulk insert, broadcast progress) × N batches
        → complete_job_activity (set COMPLETED, final broadcast)
"""

from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional
import math

# NOTE: Do NOT import pandas, sqlmodel, or models at module level
# These imports happen inside activities to avoid sandbox restrictions


# ==============================
# DATA CLASSES FOR WORKFLOW I/O
# ==============================

@dataclass
class JobInfo:
    """Information about a job for workflow processing"""
    job_id: int
    user_id: int
    total_records: int
    batch_size: int
    total_batches: int
    csv_path: str


@dataclass
class ChunkResult:
    """Result of processing a single chunk"""
    processed: int
    valid: int
    invalid: int
    suspicious: int


@dataclass
class ProgressUpdate:
    """Progress update to broadcast via WebSocket"""
    job_id: int
    user_id: int
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
# ACTIVITIES
# ==============================

@activity.defn
async def init_job_activity(job_id: int) -> JobInfo:
    """
    Initialize job processing:
    - Set status to RUNNING
    - Count total records in CSV
    - Calculate dynamic batch size based on file size
    - Return job info for workflow
    """
    import os
    import pandas as pd
    from sqlmodel import Session
    from database import engine
    from models import Job
    
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        if job.status == "RUNNING":
            raise ValueError(f"Job {job_id} is already running")
        
        csv_path = f"uploads/job_{job_id}.csv"
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        # Read CSV to get total records
        df = pd.read_csv(csv_path)
        total_records = len(df)
        
        # Dynamic batch size calculation based on file size
        file_size_bytes = os.path.getsize(csv_path)
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        # Formula: ~500 bytes per row estimate, target 2MB chunks for memory efficiency
        # Clamp between 100 (minimum for progress granularity) and 5000 (maximum for memory)
        estimated_rows_per_mb = 2000  # ~500 bytes per row
        target_chunk_mb = 2  # Target chunk size in MB
        
        if file_size_mb > 0:
            # Calculate based on actual file density
            actual_rows_per_mb = total_records / file_size_mb if file_size_mb > 0 else estimated_rows_per_mb
            batch_size = int(target_chunk_mb * actual_rows_per_mb)
        else:
            batch_size = int(target_chunk_mb * estimated_rows_per_mb)
        
        # Clamp batch size
        batch_size = max(100, min(batch_size, 5000))
        
        # Calculate total batches
        total_batches = math.ceil(total_records / batch_size)
        
        # Update job status
        job.status = "RUNNING"
        job.total_records = total_records
        job.processed_records = 0
        job.valid_records = 0
        job.invalid_records = 0
        job.suspicious_records = 0
        session.commit()
        
        activity.logger.info(
            f"Job {job_id}: {total_records} records, {file_size_mb:.2f}MB, "
            f"batch_size={batch_size}, total_batches={total_batches}"
        )
        
        return JobInfo(
            job_id=job_id,
            user_id=job.user_id,
            total_records=total_records,
            batch_size=batch_size,
            total_batches=total_batches,
            csv_path=csv_path
        )


@activity.defn
async def process_chunk_activity(
    job_id: int,
    user_id: int,
    csv_path: str,
    chunk_index: int,
    batch_size: int,
    total_batches: int,
    total_records: int
) -> ChunkResult:
    """
    Process a single chunk of the CSV:
    - Read chunk from CSV
    - Validate each record
    - Bulk insert transactions using SQLAlchemy
    - Update job progress counters
    - Broadcast progress via WebSocket
    """
    import pandas as pd
    from datetime import datetime
    from sqlmodel import Session
    from database import engine
    from models import Job, Transaction
    import httpx
    import os
    
    # Get FastAPI URL from environment or default
    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
    
    with Session(engine) as session:
        # Calculate chunk bounds
        start_row = chunk_index * batch_size
        end_row = min(start_row + batch_size, total_records)
        
        # Read specific chunk from CSV
        df = pd.read_csv(csv_path, skiprows=range(1, start_row + 1), nrows=(end_row - start_row))
        
        # If we skipped rows, we need to read headers separately
        if start_row > 0:
            headers = pd.read_csv(csv_path, nrows=0).columns
            df.columns = headers
        
        transactions_to_insert = []
        valid_count = 0
        invalid_count = 0
        suspicious_count = 0
        
        for _, row in df.iterrows():
            error = None
            valid = True
            ts = datetime.now()
            
            # Validate timestamp
            try:
                ts = datetime.fromisoformat(str(row["timestamp"]))
            except Exception:
                error = "Invalid timestamp"
                valid = False
            
            # Validate amount
            try:
                amount = float(row["amount"])
                if not isinstance(row["amount"], (int, float)) and not valid:
                    # Already invalid from timestamp, keep that error
                    pass
            except (ValueError, TypeError):
                if valid:  # Only set error if not already invalid
                    error = "Invalid amount"
                    valid = False
                amount = 0.0
            
            # Check suspicious
            suspicious = False
            try:
                if float(row["amount"]) < 0 or float(row["amount"]) > 50000:
                    suspicious = True
            except (ValueError, TypeError):
                pass
            
            # Create transaction object
            transaction = Transaction(
                job_id=job_id,
                transaction_id=str(row["transaction_id"]),
                user_id=str(row["user_id"]),
                amount=amount,
                timestamp=ts,
                is_valid=valid,
                is_suspicious=suspicious,
                error_message=error
            )
            transactions_to_insert.append(transaction)
            
            if valid:
                valid_count += 1
            else:
                invalid_count += 1
            
            if suspicious:
                suspicious_count += 1
        
        # Bulk insert all transactions in this chunk
        session.bulk_save_objects(transactions_to_insert)
        
        # Update job counters
        job = session.get(Job, job_id)
        job.processed_records += len(transactions_to_insert)
        job.valid_records += valid_count
        job.invalid_records += invalid_count
        job.suspicious_records += suspicious_count
        
        session.commit()
        
        # Calculate progress
        progress_percent = int((job.processed_records / total_records) * 100) if total_records > 0 else 0
        
        # Broadcast progress via HTTP to FastAPI (which has the WebSocket connections)
        broadcast_payload = {
            "user_id": user_id,
            "job_id": job_id,
            "status": "RUNNING",
            "progress_percent": progress_percent,
            "processed_records": job.processed_records,
            "total_records": total_records,
            "valid_records": job.valid_records,
            "invalid_records": job.invalid_records,
            "suspicious_records": job.suspicious_records,
            "batch_completed": chunk_index + 1,
            "total_batches": total_batches
        }
        
        # Call FastAPI internal endpoint to broadcast via WebSocket
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{FASTAPI_URL}/internal/broadcast", json=broadcast_payload)
        except Exception as e:
            activity.logger.warning(f"Failed to broadcast progress: {e}")
        
        activity.logger.info(
            f"Job {job_id}: Batch {chunk_index + 1}/{total_batches} completed. "
            f"Progress: {progress_percent}%"
        )
        
        return ChunkResult(
            processed=len(transactions_to_insert),
            valid=valid_count,
            invalid=invalid_count,
            suspicious=suspicious_count
        )


@activity.defn
async def complete_job_activity(job_id: int, user_id: int, total_batches: int) -> None:
    """
    Mark job as completed and send final WebSocket broadcast.
    """
    from sqlmodel import Session
    from database import engine
    from models import Job
    import httpx
    import os
    
    # Get FastAPI URL from environment or default
    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
    
    with Session(engine) as session:
        job = session.get(Job, job_id)
        job.status = "COMPLETED"
        session.commit()
        
        # Final broadcast via HTTP to FastAPI
        broadcast_payload = {
            "user_id": user_id,
            "job_id": job_id,
            "status": "COMPLETED",
            "progress_percent": 100,
            "processed_records": job.processed_records,
            "total_records": job.total_records,
            "valid_records": job.valid_records,
            "invalid_records": job.invalid_records,
            "suspicious_records": job.suspicious_records,
            "batch_completed": total_batches,
            "total_batches": total_batches
        }
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{FASTAPI_URL}/internal/broadcast", json=broadcast_payload)
        except Exception as e:
            activity.logger.warning(f"Failed to broadcast completion: {e}")
        
        activity.logger.info(f"Job {job_id}: COMPLETED")


# ==============================
# WORKFLOW DEFINITION
# ==============================

@workflow.defn
class ProcessJobWorkflow:
    """
    Temporal workflow for processing batch jobs.
    
    Orchestrates:
    1. Job initialization (set RUNNING, calculate batches)
    2. Process each chunk sequentially (validate, bulk insert, broadcast)
    3. Mark job as completed
    
    Benefits over BackgroundTasks:
    - Durable execution: survives server restarts
    - Automatic retries with configurable policy
    - Visibility into workflow state via Temporal UI
    - Easy to add timeouts, heartbeats, signals
    """
    
    @workflow.run
    async def run(self, job_id: int) -> dict:
        """Execute the job processing workflow"""
        
        # Retry policy for activities
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3
        )
        
        # Step 1: Initialize job and get batch configuration
        job_info = await workflow.execute_activity(
            init_job_activity,
            job_id,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy
        )
        
        workflow.logger.info(
            f"Job {job_id}: Starting processing with {job_info.total_batches} batches "
            f"of {job_info.batch_size} records each"
        )
        
        # Step 2: Process each chunk sequentially
        total_processed = 0
        total_valid = 0
        total_invalid = 0
        total_suspicious = 0
        
        for chunk_index in range(job_info.total_batches):
            result = await workflow.execute_activity(
                process_chunk_activity,
                args=[
                    job_id,
                    job_info.user_id,
                    job_info.csv_path,
                    chunk_index,
                    job_info.batch_size,
                    job_info.total_batches,
                    job_info.total_records
                ],
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=retry_policy,
                heartbeat_timeout=timedelta(minutes=2)
            )
            
            total_processed += result.processed
            total_valid += result.valid
            total_invalid += result.invalid
            total_suspicious += result.suspicious
        
        # Step 3: Mark job as completed
        await workflow.execute_activity(
            complete_job_activity,
            args=[job_id, job_info.user_id, job_info.total_batches],
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry_policy
        )
        
        return {
            "job_id": job_id,
            "status": "COMPLETED",
            "total_processed": total_processed,
            "valid_records": total_valid,
            "invalid_records": total_invalid,
            "suspicious_records": total_suspicious,
            "batch_size": job_info.batch_size,
            "total_batches": job_info.total_batches
        }
