from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    status: str = "uploaded"
    total_records: int = 0
    processed_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int
    transaction_id: str
    user_id: str
    amount: float
    timestamp: datetime
    is_valid: bool = True
    is_suspicious: bool = False
    error_message: Optional[str]
