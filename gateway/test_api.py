import time
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# -----------------------------
# HELPER → create CSV job
# -----------------------------
def create_job(csv_text: str):
    r = client.post(
        "/jobs",
        files={"file": ("test.csv", csv_text, "text/csv")}
    )
    assert r.status_code == 200
    return r.json()["job_id"]


# -----------------------------
# HELPER → wait until job completes
# -----------------------------
def wait_for_completion(job_id, timeout=5):
    start = time.time()
    while time.time() - start < timeout:
        r = client.get(f"/jobs/{job_id}")
        if r.json()["status"] == "completed":
            return
        time.sleep(0.3)


# -----------------------------
# 1️⃣ TEST CREATE JOB
# -----------------------------
def test_create_job():

    csv_data = """transaction_id,user_id,amount,timestamp
T1,U1,120.50,2025-01-01T10:00:00
"""

    job_id = create_job(csv_data)

    assert isinstance(job_id, int)


# -----------------------------
# 2️⃣ TEST START JOB
# -----------------------------
def test_start_job():

    csv_data = """transaction_id,user_id,amount,timestamp
T1,U1,120.50,2025-01-01T10:00:00
"""

    job_id = create_job(csv_data)

    r = client.post(f"/jobs/{job_id}/start")
    assert r.status_code == 200


# -----------------------------
# 3️⃣ TEST JOB STATUS
# -----------------------------
def test_job_status():

    csv_data = """transaction_id,user_id,amount,timestamp
T1,U1,120.50,2025-01-01T10:00:00
"""

    job_id = create_job(csv_data)

    r = client.get(f"/jobs/{job_id}")
    data = r.json()

    assert "status" in data
    assert "processed_records" in data


# -----------------------------
# 4️⃣ TEST TRANSACTIONS + PAGINATION
# -----------------------------
def test_transactions():

    csv_data = """transaction_id,user_id,amount,timestamp
T1,U1,120.50,2025-01-01T10:00:00
T2,U2,60000,2025-01-01T10:05:00
"""

    job_id = create_job(csv_data)

    client.post(f"/jobs/{job_id}/start")

    wait_for_completion(job_id)

    r = client.get(f"/jobs/{job_id}/transactions?page=1&size=10")

    assert r.status_code == 200
    assert isinstance(r.json(), list)


# -----------------------------
# 5️⃣ TEST SUSPICIOUS FILTER
# -----------------------------
def test_suspicious_flag():

    csv_data = """transaction_id,user_id,amount,timestamp
T1,U1,70000,2025-01-01T10:00:00
"""

    job_id = create_job(csv_data)

    client.post(f"/jobs/{job_id}/start")

    wait_for_completion(job_id)

    r = client.get(f"/jobs/{job_id}/transactions?filter=suspicious")

    assert r.status_code == 200

    data = r.json()
    assert len(data) >= 1
    assert data[0]["is_suspicious"] is True
