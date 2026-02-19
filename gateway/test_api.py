import time
import pytest
import os

# Set test database URL BEFORE importing app modules
os.environ["DATABASE_URL"] = "postgresql+psycopg2://shubham@localhost:5432/batchdb"

from sqlmodel import SQLModel
from fastapi.testclient import TestClient
from database import engine
from main import app

# Create test client
client = TestClient(app)


# ==============================
# TEST FIXTURES
# ==============================

@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and clean up after"""
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


# ==============================
# HELPER FUNCTIONS
# ==============================

def create_user(name: str = "Test User", email: str = None):
    """Create a user and return user_id"""
    if email is None:
        email = f"test_{time.time_ns()}@example.com"
    r = client.post("/users", json={"name": name, "email": email})
    assert r.status_code == 200
    return r.json()["id"]


def create_job(user_id: int, csv_text: str):
    """Create a job for a user and return job_id"""
    r = client.post(
        f"/jobs?user_id={user_id}",
        files={"file": ("test.csv", csv_text, "text/csv")}
    )
    assert r.status_code == 200
    return r.json()["job_id"]


def wait_for_completion(job_id: int, timeout: int = 10):
    """Wait until job completes or times out"""
    start = time.time()
    while time.time() - start < timeout:
        r = client.get(f"/jobs/{job_id}")
        status = r.json()["status"]
        if status == "COMPLETED":
            return True
        if status == "FAILED":
            return False
        time.sleep(0.3)
    return False


# ==============================
# USER ENDPOINTS TESTS
# ==============================

def test_create_user():
    """Test creating a new user"""
    email = f"user_{time.time_ns()}@test.com"
    r = client.post("/users", json={"name": "John Doe", "email": email})
    
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "John Doe"
    assert data["email"] == email
    assert "id" in data
    assert "created_at" in data


def test_create_user_duplicate_email():
    """Test creating user with duplicate email fails"""
    email = f"duplicate_{time.time_ns()}@test.com"
    
    # First creation should succeed
    r1 = client.post("/users", json={"name": "User 1", "email": email})
    assert r1.status_code == 200
    
    # Second creation with same email should fail
    r2 = client.post("/users", json={"name": "User 2", "email": email})
    assert r2.status_code == 400
    assert "already registered" in r2.json()["detail"].lower()


def test_create_user_invalid_email():
    """Test creating user with invalid email fails"""
    r = client.post("/users", json={"name": "User", "email": "invalid-email"})
    assert r.status_code == 422  # Validation error


def test_get_all_users():
    """Test retrieving all users"""
    # Create a user first
    create_user()
    
    r = client.get("/users")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_user_by_id():
    """Test retrieving a specific user by ID"""
    user_id = create_user(name="Specific User")
    
    r = client.get(f"/users/{user_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == user_id
    assert data["name"] == "Specific User"


def test_get_user_not_found():
    """Test retrieving a non-existent user returns 404"""
    r = client.get("/users/999999")
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


def test_get_user_jobs():
    """Test retrieving jobs for a specific user"""
    user_id = create_user()
    
    # Create a job for the user
    csv_data = """transaction_id,user_id,amount,timestamp
T1,U1,100.00,2025-01-01T10:00:00
"""
    job_id = create_job(user_id, csv_data)
    
    r = client.get(f"/users/{user_id}/jobs")
    assert r.status_code == 200
    jobs = r.json()
    assert isinstance(jobs, list)
    assert len(jobs) >= 1
    assert any(job["id"] == job_id for job in jobs)


def test_get_user_jobs_not_found():
    """Test getting jobs for non-existent user returns 404"""
    r = client.get("/users/999999/jobs")
    assert r.status_code == 404


# ==============================
# JOB CREATION TESTS
# ==============================

def test_create_job():
    """Test creating a job with valid CSV"""
    user_id = create_user()
    csv_data = """transaction_id,user_id,amount,timestamp
T1,U1,120.50,2025-01-01T10:00:00
"""
    job_id = create_job(user_id, csv_data)
    assert isinstance(job_id, int)


def test_create_job_user_not_found():
    """Test creating job for non-existent user returns 404"""
    csv_data = """transaction_id,user_id,amount,timestamp
T1,U1,100,2025-01-01T10:00:00
"""
    r = client.post(
        "/jobs?user_id=999999",
        files={"file": ("test.csv", csv_data, "text/csv")}
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


# ==============================
# JOB START TESTS
# ==============================

def test_start_job():
    """Test starting a job"""
    user_id = create_user()
    csv_data = """transaction_id,user_id,amount,timestamp
T1,U1,120.50,2025-01-01T10:00:00
"""
    job_id = create_job(user_id, csv_data)
    
    r = client.post(f"/jobs/{job_id}/start")
    assert r.status_code == 200
    assert r.json()["message"] == "started"


def test_start_job_not_found():
    """Test starting non-existent job returns 404"""
    r = client.post("/jobs/999999/start")
    assert r.status_code == 404
    assert r.json()["detail"] == "Job not found"


# ==============================
# JOB STATUS TESTS
# ==============================

def test_job_status():
    """Test getting job status"""
    user_id = create_user()
    csv_data = """transaction_id,user_id,amount,timestamp
T1,U1,120.50,2025-01-01T10:00:00
"""
    job_id = create_job(user_id, csv_data)
    
    r = client.get(f"/jobs/{job_id}")
    data = r.json()
    
    assert r.status_code == 200
    assert "id" in data
    assert "status" in data
    assert "total_records" in data
    assert "processed_records" in data
    assert "valid_records" in data
    assert "invalid_records" in data
    assert "suspicious_records" in data
    assert "progress_percent" in data
    assert "created_at" in data


def test_job_status_after_completion():
    """Test job status after processing completes"""
    user_id = create_user()
    csv_data = """transaction_id,user_id,amount,timestamp
T1,U1,100.00,2025-01-01T10:00:00
T2,U2,200.00,2025-01-01T10:05:00
"""
    job_id = create_job(user_id, csv_data)
    
    client.post(f"/jobs/{job_id}/start")
    wait_for_completion(job_id)
    
    r = client.get(f"/jobs/{job_id}")
    data = r.json()
    
    assert data["status"] == "COMPLETED"
    assert data["total_records"] == 2
    assert data["processed_records"] == 2
    assert data["progress_percent"] == 100


# ==============================
# TRANSACTION TESTS
# ==============================

def test_transactions():
    """Test getting transactions for a completed job"""
    user_id = create_user()
    csv_data = """transaction_id,user_id,amount,timestamp
T1,U1,120.50,2025-01-01T10:00:00
T2,U2,60000,2025-01-01T10:05:00
"""
    job_id = create_job(user_id, csv_data)
    
    client.post(f"/jobs/{job_id}/start")
    wait_for_completion(job_id)
    
    r = client.get(f"/jobs/{job_id}/transactions?page=1&size=10")
    
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) == 2


def test_transactions_pagination():
    """Test transaction pagination"""
    user_id = create_user()
    # Create CSV with 25 transactions
    rows = [f"T{i},U1,100,2025-01-01T10:00:00" for i in range(25)]
    csv_data = "transaction_id,user_id,amount,timestamp\n" + "\n".join(rows)
    
    job_id = create_job(user_id, csv_data)
    
    client.post(f"/jobs/{job_id}/start")
    wait_for_completion(job_id)
    
    # Get first page
    r1 = client.get(f"/jobs/{job_id}/transactions?page=1&size=10")
    assert r1.status_code == 200
    assert len(r1.json()) == 10
    
    # Get second page
    r2 = client.get(f"/jobs/{job_id}/transactions?page=2&size=10")
    assert r2.status_code == 200
    assert len(r2.json()) == 10
    
    # Get third page (partial)
    r3 = client.get(f"/jobs/{job_id}/transactions?page=3&size=10")
    assert r3.status_code == 200
    assert len(r3.json()) == 5


def test_transactions_filter_valid():
    """Test filtering valid transactions"""
    user_id = create_user()
    csv_data = """transaction_id,user_id,amount,timestamp
T1,U1,100.00,2025-01-01T10:00:00
T2,U2,200.00,invalid_timestamp
"""
    job_id = create_job(user_id, csv_data)
    
    client.post(f"/jobs/{job_id}/start")
    wait_for_completion(job_id)
    
    r = client.get(f"/jobs/{job_id}/transactions?filter=valid")
    data = r.json()
    
    assert r.status_code == 200
    assert all(t["is_valid"] is True for t in data)


def test_transactions_filter_invalid():
    """Test filtering invalid transactions"""
    user_id = create_user()
    csv_data = """transaction_id,user_id,amount,timestamp
T1,U1,100.00,2025-01-01T10:00:00
T2,U2,200.00,invalid_timestamp
"""
    job_id = create_job(user_id, csv_data)
    
    client.post(f"/jobs/{job_id}/start")
    wait_for_completion(job_id)
    
    r = client.get(f"/jobs/{job_id}/transactions?filter=invalid")
    data = r.json()
    
    assert r.status_code == 200
    assert len(data) >= 1
    assert all(t["is_valid"] is False for t in data)


def test_suspicious_flag():
    """Test suspicious transaction filtering (amount > 50000)"""
    user_id = create_user()
    csv_data = """transaction_id,user_id,amount,timestamp
T1,U1,70000,2025-01-01T10:00:00
T2,U2,100,2025-01-01T10:05:00
"""
    job_id = create_job(user_id, csv_data)
    
    client.post(f"/jobs/{job_id}/start")
    wait_for_completion(job_id)
    
    r = client.get(f"/jobs/{job_id}/transactions?filter=suspicious")
    
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert all(t["is_suspicious"] is True for t in data)


def test_suspicious_flag_negative_amount():
    """Test that negative amounts are flagged as suspicious"""
    user_id = create_user()
    csv_data = """transaction_id,user_id,amount,timestamp
T1,U1,-100,2025-01-01T10:00:00
"""
    job_id = create_job(user_id, csv_data)
    
    client.post(f"/jobs/{job_id}/start")
    wait_for_completion(job_id)
    
    r = client.get(f"/jobs/{job_id}/transactions?filter=suspicious")
    
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["is_suspicious"] is True
    assert data[0]["amount"] == -100


# ==============================
# INTERNAL BROADCAST TESTS
# ==============================

def test_internal_broadcast():
    """Test internal broadcast endpoint for worker progress updates"""
    user_id = create_user()
    csv_data = """transaction_id,user_id,amount,timestamp
T1,U1,100,2025-01-01T10:00:00
"""
    job_id = create_job(user_id, csv_data)
    
    broadcast_data = {
        "user_id": user_id,
        "job_id": job_id,
        "status": "RUNNING",
        "progress_percent": 50,
        "processed_records": 500,
        "total_records": 1000,
        "valid_records": 480,
        "invalid_records": 20,
        "suspicious_records": 5,
        "batch_completed": 5,
        "total_batches": 10
    }
    
    r = client.post("/internal/broadcast", json=broadcast_data)
    
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "broadcast_sent"
    assert data["user_id"] == user_id
