# Sandy AI Lab

A hackathon-built AI lab assistant themed around Sandy Cheeks from SpongeBob. Ask it anything about the lab in plain English — it fetches live data and answers using an LLM.

---

## What it does

You type (or speak) a question like *"show me inventory status"* or *"what should I work on today?"*. The backend fetches real data from the lab database, passes it to a Groq LLM as context, and streams back a natural-language answer. No hardcoded responses — every answer comes from the actual data.

---

## Architecture

```
Browser (React + TanStack Start)
    │
    │  POST /chat  { message: "..." }
    ▼
FastAPI backend (main.py)
    ├── db/connection.py  ──►  external lab API  (or mock fallback)
    ├── agents/rag_agent.py  ──►  Groq LLM  (llama-3.3-70b-versatile)
    └── agents/ (inventory · research · planner)  ──►  POST /run pipeline
```

**Backend — Python / FastAPI**
- `POST /chat` — RAG endpoint: fetches live inventory + projects, builds context, calls Groq LLM, returns natural-language answer
- `POST /run` — deterministic 3-agent pipeline (Inventory → Research → Planner) for structured output
- `db/connection.py` — hits the external API first, falls back to local DB, then mock data
- `agents/rag_agent.py` — context builder + Groq chat completion
- `agents/inventory_agent.py` — flags items below minimum stock
- `agents/research_agent.py` — flags delayed/blocked projects
- `agents/planner_agent.py` — produces prioritized action plan

**Frontend — React 19 / TypeScript / TanStack Start**
- Sandy-themed cartoon UI (Spongebob design system, Tailwind CSS v4)
- Word-by-word streaming effect on replies
- Web Speech API — voice input (mic button) and TTS output (toggle in sidebar)
- 20-second request timeout with clear error messages
- Hydration-safe (no `Math.random()` or `typeof window` at module level)

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 19, TypeScript, TanStack Start (SSR), TanStack Router, Tailwind CSS v4, Radix UI, shadcn/ui |
| Backend | Python 3.11+, FastAPI, Pydantic v2, Uvicorn |
| LLM | Groq API — `llama-3.3-70b-versatile` |
| Data | External REST API + PostgreSQL fallback + mock fallback |
| Dev | Vite 7, ESLint, Prettier |

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- A [Groq API key](https://console.groq.com)

### Backend

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

Copy `.env` and fill in your values:

```env
DATABASE_API_URL=http://your-lab-api:8000
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
```

Start the backend:

```bash
uvicorn main:app --reload
# Swagger UI at http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
VITE_API_URL=http://localhost:8000
```

Start the dev server:

```bash
npm run dev
# Opens at http://localhost:8080
```

---

## Usage

With both servers running, open `http://localhost:8080` and ask anything:

- *"Show me inventory status"*
- *"Are there any low stock items?"*
- *"Tell me about the current projects"*
- *"What should I work on today?"*
- *"What can I run an experiment on with current supplies?"*

Click the mic button to use voice input. Toggle voice output in the sidebar.

---

## API

### `POST /chat`
RAG-based natural language answer.

```json
// Request
{ "message": "show me inventory status" }

// Response
{
  "reply": "We've got Copper Wire (50 pcs), Sensor Kit (8 sets)...",
  "data_source": "api"
}
```

### `POST /run`
Structured 3-agent pipeline output.

```json
// Response
{
  "data_source": "api",
  "execution_mode": "deterministic",
  "execution_trace": [...],
  "inventory_issues": [...],
  "research_issues": [...],
  "plan": { "summary": "...", "actions": [...], "final_decision": "..." }
}
```

---

## Data fallback chain

```
External API (DATABASE_API_URL)
    → PostgreSQL (DATABASE_URL)
        → Mock data (hardcoded in db/connection.py)
```

If the external API is unreachable, the system falls back silently. The `data_source` field in the response tells you which source was used.

---

## Project structure

```
sandy-ai-lab/
├── main.py                    # FastAPI app — /chat and /run endpoints
├── requirements.txt
├── .env                       # backend env vars (do not commit secrets)
├── agents/
│   ├── rag_agent.py           # fetches data + calls Groq LLM
│   ├── inventory_agent.py     # low-stock detection
│   ├── research_agent.py      # at-risk project detection
│   ├── planner_agent.py       # action plan generation
│   └── deepagents_orchestrator.py
├── db/
│   └── connection.py          # data fetching with fallback chain
├── frontend/
│   ├── src/
│   │   ├── routes/index.tsx   # main chat UI
│   │   ├── components/
│   │   │   ├── SpongeLayout.tsx
│   │   │   └── Bubbles.tsx
│   │   └── styles.css         # Spongebob design system
│   ├── .env.local             # VITE_API_URL (not committed)
│   └── vite.config.ts
└── test_pipeline.py           # standalone pipeline test script
```

---

## License

MIT
