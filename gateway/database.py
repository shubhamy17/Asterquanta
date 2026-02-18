import os
from pathlib import Path
from dotenv import load_dotenv
from sqlmodel import create_engine, Session

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL)

def get_session():
    with Session(engine) as session:
        yield session
