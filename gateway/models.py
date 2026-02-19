from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship: One user has many jobs
    jobs: List["Job"] = Relationship(back_populates="user")


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    status: str = "UPLOADED"
    total_records: int = 0
    processed_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    suspicious_records: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: Optional["User"] = Relationship(back_populates="jobs")
    transactions: List["Transaction"] = Relationship(back_populates="job")


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    transaction_id: str
    user_id: str
    amount: float
    timestamp: datetime
    is_valid: bool = True
    is_suspicious: bool = False
    error_message: Optional[str]
    
    # Relationship: Each transaction belongs to a job
    job: Optional["Job"] = Relationship(back_populates="transactions")
