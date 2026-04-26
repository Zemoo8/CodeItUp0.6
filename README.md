# Sandy's Treedome Lab - AI Agent Pipeline

A FastAPI-based three-agent pipeline for inventory management, project research, and decision planning. Supports both deterministic execution and LLM-guided orchestration via LangChain Deep Agents.

## 🎯 Features

- **Three-Agent Pipeline**: Inventory → Research → Planner
- **Dual Execution Modes**:
  - **Deterministic**: Fast, rule-based Python agents (default)
  - **Deep Agents**: LLM-orchestrated via Groq API (optional)
- **Smart Data Sources**: API-first with fallback to PostgreSQL, then mock data
- **Modern Dashboard UI**: Real-time KPI display, agent status, console interface
- **Production-Ready**: Graceful error handling, comprehensive logging

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL (optional, if not using API backend)
- Groq API key (optional, for LLM enhancement)

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone or navigate to project
cd sandy-ai-lab

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate
# or (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with:
```
# Data source
DATABASE_API_URL=http://192.168.1.118:8000
# DATABASE_URL=postgresql://user:password@localhost/dbname  # Optional Postgres

# For Deep Agents + Groq LLM
GROQ_API_KEY=your_groq_api_key_here
DEEPAGENTS_MODEL=openai:llama-3.3-70b-versatile
USE_DEEPAGENTS=true

# Auto-bridging for OpenAI-compatible Groq
OPENAI_API_KEY=${GROQ_API_KEY}
OPENAI_BASE_URL=https://api.groq.com/openai/v1
```

### 3. Run the Application

**Development Mode** (with auto-reload):
```bash
python -m uvicorn main:app --reload
```

**Production Mode**:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

**Or use convenience scripts**:
- **Windows**: `run.bat`
- **Mac/Linux**: `./run.sh`

Server will be available at: **http://localhost:8000**
- Dashboard UI: http://localhost:8000/ui
- API Docs: http://localhost:8000/docs

## 📡 API Endpoints

### `POST /run`
Execute the full agent pipeline.

**Query Parameters**:
- `mode` (optional): `deterministic` or `deepagents` (overrides USE_DEEPAGENTS env var)

**Response**:
```json
{
  "execution_mode": "deterministic | deepagents",
  "data_source": "api | database | mock | mixed",
  "inventory_issues": [...],
  "research_issues": [...],
  "plan": {
    "summary": "...",
    "critical_issues": [...],
    "actions": [...],
    "final_decision": "..."
  },
  "execution_trace": {
    "start_time": "2026-04-26T...",
    "end_time": "2026-04-26T...",
    "agents": ["inventory_agent", "research_agent", "planner_agent"],
    "duration_ms": 234
  }
}
```

## 🧠 Understanding Execution Modes

### Deterministic Mode (Default)
Uses pure Python agent functions. Fast, predictable, no external LLM calls.

```bash
# Explicitly use deterministic mode
curl -X POST http://localhost:8000/run?mode=deterministic
```

### Deep Agents Mode
Uses LangChain Deep Agents framework with Groq LLM to orchestrate agent tool calls.
Requires: `GROQ_API_KEY` and `USE_DEEPAGENTS=true`

```bash
USE_DEEPAGENTS=true python -m uvicorn main:app --reload
```

## 🔧 Agent Details

### 1. Inventory Agent
Scans inventory for items below minimum stock levels.

**Input**: List of inventory items with `quantity` and `min_required`
**Output**: List of low-stock items with shortfall amounts

### 2. Research Agent
Identifies at-risk projects and associates blockers.

**Input**: List of projects with `status`, and experiments log for blockers
**Output**: List of problematic projects with their blockers and team info

### 3. Planner Agent
Combines inventory and research issues into actionable plan.
Optionally calls Groq LLM to refine summary and decision.

**Input**: Inventory issues, research issues
**Output**: Prioritized action plan with severity levels and recommendations

## 📦 Data Source Fallback Chain

The app intelligently selects data sources in this order:

1. **API** (if `DATABASE_API_URL` env var is set)
2. **PostgreSQL** (if `DATABASE_URL` env var is set and database is reachable)
3. **Mock Data** (built-in fallback)

Response includes `data_source` field showing which source was used.

## 🧪 Testing

Run the test pipeline:
```bash
python test_pipeline.py
```

Or run individual agent tests:
```bash
python test_agents.py
```

## 🌐 Website Integration & Deployment

### Option 1: Local/LAN Deployment
```bash
# Run on specific IP/port (accessible from other machines)
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Then access from other machines: `http://<your-ip>:8000/ui`

### Option 2: Docker Containerization

```bash
# Build image
docker build -t sandy-ai-lab:latest .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_API_URL=http://192.168.1.118:8000 \
  -e GROQ_API_KEY=your_key \
  -e USE_DEEPAGENTS=true \
  sandy-ai-lab:latest
```

### Option 3: Cloud Deployment (AWS/GCP/Azure)

**AWS ECS / Google Cloud Run**:
1. Push Docker image to container registry (ECR/Artifact Registry)
2. Deploy via ECS/Cloud Run console
3. Set environment variables in deployment config

**Heroku**:
```bash
# Install Heroku CLI, then:
heroku login
heroku create sandy-ai-lab
heroku config:set DATABASE_API_URL=...
heroku config:set GROQ_API_KEY=...
git push heroku main
```

### Option 4: Traditional VPS (DigitalOcean, Linode, AWS EC2)

```bash
# SSH into server
ssh root@your-vps-ip

# Install Python, PostgreSQL, nginx
apt update && apt install python3.9 python3-pip postgresql nginx -y

# Clone repo, setup venv, install deps
git clone https://github.com/youruser/sandy-ai-lab.git
cd sandy-ai-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start with gunicorn (behind nginx reverse proxy)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 127.0.0.1:8000
```

Configure nginx to reverse proxy to 127.0.0.1:8000.

## 🔐 Security Checklist for Production

- [ ] Use `.env` file with real API keys, never commit to git
- [ ] Enable HTTPS (use nginx/CloudFlare for TLS termination)
- [ ] Set `CORS_ORIGINS` to specific domains (whitelist frontend URLs)
- [ ] Use strong `OPENAI_API_KEY` / `GROQ_API_KEY` (rotate regularly)
- [ ] Enable database connection SSL if using remote PostgreSQL
- [ ] Set `USE_DEEPAGENTS=false` if no LLM calls needed (reduces latency)
- [ ] Monitor API rate limits for Groq (6000 TPM on free tier)

## 📊 Monitoring & Debugging

Enable detailed logging:
```bash
DEEPAGENTS_DEBUG=true python -m uvicorn main:app --reload
```

This will print debug info about Deep Agents execution, including:
- Tool calls made
- LLM response structure
- Fallback triggers

## 🤝 Contributing

For hackathon teams:
1. Test both `deterministic` and `deepagents` modes
2. Verify data loads from API (check `/run` response `data_source` field)
3. Monitor Groq API rate limits if using Deep Agents
4. Use `gunicorn` for production, not `uvicorn --reload`

## 📝 License

MIT

---

**Questions?** Check the `/docs` endpoint for full OpenAPI specification.
