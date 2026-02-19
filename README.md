# Full Stack Batch Processing Application

A complete full-stack application for batch CSV processing with real-time progress updates using WebSocket, Temporal workflows for durable execution, and a React frontend.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 Docker Network                              │
│                                                                             │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────────────┐  │
│   │ Frontend │────▶│ Backend  │────▶│    DB    │     │    Temporal      │  │
│   │  :3000   │     │  :8000   │     │  :5432   │     │  Server :7233    │  │
│   │  (Nginx) │     │ (FastAPI)│     │(Postgres)│     │  UI :8080        │  │
│   └──────────┘     └────┬─────┘     └──────────┘     └────────┬─────────┘  │
│        │                │                                     │            │
│        │    WebSocket   │                                     │            │
│        │◀───────────────┤                                     │            │
│        │                │                                     │            │
│        │                ▼                                     │            │
│        │           ┌──────────┐◀──────────────────────────────┘            │
│        │           │  Worker  │  (Temporal Activities)                     │
│        │           └──────────┘                                            │
│        │                                                                   │
└────────┴───────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React 19, Vite 7, TailwindCSS |
| Backend | FastAPI, SQLModel, Uvicorn |
| Database | PostgreSQL 15 |
| Workflow Engine | Temporal |
| Real-time | WebSocket |
| Container | Docker, Docker Compose |

## Features

- **User Management**: Create and manage users
- **CSV Upload**: Upload CSV files for batch processing
- **Real-time Progress**: WebSocket-based live progress updates
- **Durable Workflows**: Temporal-based fault-tolerant job processing
- **Transaction Validation**: Validates each row with business rules
- **Job Dashboard**: View job status, progress, and transaction details

---

## Quick Start with Docker (Recommended)

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- At least 4GB RAM available for Docker

### Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd FullStackProblem
   ```

2. **Start all services**
   ```bash
   docker-compose up --build -d
   ```

3. **Wait for services to be healthy** (about 30-60 seconds)
   ```bash
   docker-compose ps
   ```
   
   All services should show `Up` status:
   ```
   NAME                 STATUS
   fullstack_db         Up (healthy)
   temporal_server      Up
   temporal_ui          Up
   fullstack_backend    Up (healthy)
   fullstack_worker     Up
   fullstack_frontend   Up
   ```

4. **Access the application**
   - **Frontend**: http://localhost:3000
   - **Backend API Docs**: http://localhost:8000/docs
   - **Temporal UI**: http://localhost:8080

5. **Stop all services**
   ```bash
   docker-compose down
   ```

6. **Stop and remove all data (fresh start)**
   ```bash
   docker-compose down -v
   ```

### Docker Services

| Service | Container Name | Port | Description |
|---------|---------------|------|-------------|
| db | fullstack_db | 5432 | PostgreSQL database |
| temporal | temporal_server | 7233 | Temporal workflow server |
| temporal-ui | temporal_ui | 8080 | Temporal web dashboard |
| backend | fullstack_backend | 8000 | FastAPI backend |
| worker | fullstack_worker | - | Temporal worker |
| frontend | fullstack_frontend | 3000 | React frontend (Nginx) |

---

## Manual Setup (Development)

### Prerequisites

- **Node.js** 20+ (for frontend)
- **Python** 3.11+ (for backend)
- **PostgreSQL** 15+ (local installation)
- **Temporal CLI** (for workflow engine)

### Step 1: Database Setup

1. **Start PostgreSQL** (if not running)
   ```bash
   # macOS with Homebrew
   brew services start postgresql@15
   
   # Or start manually
   pg_ctl -D /usr/local/var/postgres start
   ```

2. **Create the database**
   ```bash
   psql postgres -c "CREATE DATABASE batchdb;"
   ```

### Step 2: Backend Setup

1. **Navigate to gateway folder**
   ```bash
   cd gateway
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # or: venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   
   Create or edit `.env` file in the project root:
   ```env
   # For local development
   DATABASE_URL="postgresql+psycopg2://YOUR_USERNAME@localhost:5432/batchdb"
   
   # Temporal (local dev server)
   TEMPORAL_HOST=localhost:7233
   ```

5. **Create database tables**
   ```bash
   python -c "from database import create_db_and_tables; create_db_and_tables()"
   ```

6. **Start the backend server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   Backend will be available at: http://localhost:8000

### Step 3: Temporal Setup

1. **Install Temporal CLI** (if not installed)
   ```bash
   # macOS
   brew install temporal
   
   # Or download from: https://github.com/temporalio/cli/releases
   ```

2. **Start Temporal dev server** (in a new terminal)
   ```bash
   temporal server start-dev --port 7233 --ui-port 8233
   ```

   - Temporal Server: localhost:7233
   - Temporal UI: http://localhost:8233

3. **Start the Temporal worker** (in a new terminal)
   ```bash
   cd gateway
   source venv/bin/activate
   python worker.py
   ```

### Step 4: Frontend Setup

1. **Navigate to frontend folder** (in a new terminal)
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

   Frontend will be available at: http://localhost:5173

---

## Usage Guide

### 1. Create a User

1. Open http://localhost:3000 (Docker) or http://localhost:5173 (manual)
2. Click "Create New User"
3. Enter name and email
4. Click "Create User"

### 2. Upload and Process a CSV File

1. Click on a user to open their dashboard
2. Click "Upload CSV" tab
3. Select a CSV file with the following format:
   ```csv
   transaction_id,amount,date,description
   TXN001,100.50,2024-01-15,Payment received
   TXN002,250.00,2024-01-16,Invoice payment
   ```
4. Click "Upload"
5. Click "Start Processing" on the uploaded job
6. Watch real-time progress via WebSocket updates

### 3. View Job Details

1. Click on a job to see details
2. View:
   - Job status (pending, processing, completed, failed)
   - Progress percentage
   - Total/valid/invalid record counts
   - Individual transaction validation results

### Sample CSV Format

```csv
transaction_id,amount,date,description
TXN001,150.00,2024-01-15,Monthly subscription
TXN002,75.50,2024-01-16,Service fee
TXN003,-50.00,2024-01-17,Refund
TXN004,1000.00,2024-01-18,Product purchase
```

**Validation Rules:**
- `transaction_id`: Required, must be unique
- `amount`: Required, must be a valid number
- `date`: Required, must be a valid date format
- `description`: Optional

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users` | Create a new user |
| GET | `/users` | List all users |
| GET | `/users/{id}` | Get user by ID |
| GET | `/users/{id}/jobs` | Get user's jobs |
| POST | `/jobs?user_id={id}` | Upload CSV file |
| POST | `/jobs/{id}/start` | Start job processing |
| GET | `/jobs/{id}` | Get job status |
| GET | `/jobs/{id}/transactions` | Get job transactions |
| WS | `/ws/{user_id}` | WebSocket for real-time updates |

**API Documentation**: http://localhost:8000/docs (Swagger UI)

---

## Troubleshooting

### Docker Issues

**Services not starting:**
```bash
# Check container logs
docker-compose logs -f

# Check specific service
docker logs fullstack_backend

# Restart with fresh state
docker-compose down -v && docker-compose up --build -d
```

**Port conflicts:**
```bash
# Check what's using a port
lsof -i :8000
lsof -i :3000

# Kill process on port
lsof -ti:8000 | xargs kill -9
```

**Worker keeps restarting:**
```bash
# Check worker logs
docker logs fullstack_worker -f

# Usually means Temporal isn't ready yet - wait 30 seconds
```

### Local Development Issues

**Database connection failed:**
```bash
# Check PostgreSQL is running
pg_isready

# Check database exists
psql postgres -c "\l" | grep batchdb
```

**Temporal connection failed:**
```bash
# Make sure Temporal server is running
temporal server start-dev --port 7233 --ui-port 8233

# Check Temporal is accessible
curl http://localhost:7233
```

**Module not found errors:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Environment Variables

### Backend (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `TEMPORAL_HOST` | Temporal server address | `localhost:7233` |
| `FASTAPI_URL` | Backend URL for worker callbacks | `http://localhost:8000` |

### Docker Compose

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | Database username | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `postgres` |
| `POSTGRES_DB` | Database name | `fullstack_db` |

---

## Project Structure

```
FullStackProblem/
├── docker-compose.yml      # Docker orchestration
├── init-temporal-db.sql    # Temporal database init
├── .env                    # Environment variables
├── README.md               # This file
│
├── frontend/               # React frontend
│   ├── Dockerfile
│   ├── nginx.conf          # Nginx config for SPA
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── components/     # React components
│       └── services/       # API and WebSocket services
│
└── gateway/                # FastAPI backend
    ├── Dockerfile
    ├── requirements.txt
    ├── main.py             # FastAPI application
    ├── database.py         # Database configuration
    ├── models.py           # SQLModel data models
    ├── workflows.py        # Temporal workflows
    ├── worker.py           # Temporal worker
    ├── websocket_manager.py # WebSocket handling
    └── uploads/            # Uploaded CSV files
```

---

## Development

### Running Tests

```bash
cd gateway
source venv/bin/activate
pytest test_api.py -v
```

### Building for Production

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build backend
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f worker
```

---

## License

MIT License