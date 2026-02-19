"""
Temporal Worker for batch job processing.

Run this separately from the FastAPI server:
    python worker.py

Or with environment variable for Temporal server:
    TEMPORAL_HOST=localhost:7233 python worker.py
"""

import asyncio
import os
from temporalio.client import Client
from temporalio.worker import Worker

from workflows import (
    ProcessJobWorkflow,
    init_job_activity,
    process_chunk_activity,
    complete_job_activity
)

# Task queue name - must match what FastAPI uses when starting workflows
TASK_QUEUE = "job-processing-queue"

# Temporal server address
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")


async def main():
    """Start the Temporal worker"""
    
    print(f"Connecting to Temporal server at {TEMPORAL_HOST}...")
    
    # Connect to Temporal server
    client = await Client.connect(TEMPORAL_HOST)
    
    print(f"Connected! Starting worker on task queue: {TASK_QUEUE}")
    
    # Create worker with workflow and activities
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[ProcessJobWorkflow],
        activities=[
            init_job_activity,
            process_chunk_activity,
            complete_job_activity
        ]
    )
    
    print("Worker started. Waiting for jobs...")
    print("Press Ctrl+C to stop")
    
    # Run the worker (blocks until interrupted)
    await worker.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nWorker stopped.")
