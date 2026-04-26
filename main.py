from dotenv import load_dotenv
load_dotenv()

import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from groq import Groq

from db.connection import fetch_inventory, fetch_projects, fetch_experiments_log
from agents.deepagents_orchestrator import deepagents_enabled, run_deepagents_pipeline
from agents.inventory_agent import run_inventory_agent
from agents.research_agent import run_research_agent
from agents.planner_agent import run_planner_agent

app = FastAPI(
    title="Sandy AI Lab",
    version="1.0.0",
    description="3-agent pipeline: Inventory → Research → Planner",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Agent output models ────────────────────────────────────────────────────────

class InventoryIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    quantity: int
    min_required: int
    shortfall: int


class ResearchIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project: str
    status: str
    blockers: list[str]
    notes: str


class CriticalIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["inventory", "research"]
    description: str
    severity: Literal["low", "medium", "high"]


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid")
    priority: int
    action: str
    reason: str


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str
    critical_issues: list[CriticalIssue]
    actions: list[Action]
    final_decision: str


# ── Execution trace models ─────────────────────────────────────────────────────

class TraceStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent: str
    input_summary: str
    output_summary: str


# ── Top-level response ─────────────────────────────────────────────────────────

class RunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data_source: Literal["mock", "database", "api", "mixed"]
    execution_mode: Literal["deterministic", "deepagents"]
    execution_trace: list[TraceStep]
    inventory_issues: list[InventoryIssue]
    research_issues: list[ResearchIssue]
    plan: Plan


# ── Routes ─────────────────────────────────────────────────────────────────────

app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")

@app.get("/")
def root():
    return RedirectResponse(url="/ui")


@app.post("/run", response_model=RunResponse)
def run_pipeline():
    trace: list[TraceStep] = []
    execution_mode: Literal["deterministic", "deepagents"] = "deterministic"

    # Load data
    inventory, inv_source = fetch_inventory()
    projects, proj_source = fetch_projects()
    experiments, exp_source = fetch_experiments_log()

    sources = {inv_source, proj_source, exp_source}
    if len(sources) == 1:
        data_source: Literal["mock", "database", "api", "mixed"] = next(iter(sources))
    else:
        data_source = "mixed"

    # Normalize DB field names → agent-expected field names
    inventory = [
        {"item_name": i["name"], "quantity": i["quantity"], "min_required": i["min_required"], "unit": i["unit"]}
        if "name" in i else i
        for i in inventory
    ]
    projects = [
        {"project_name": p["name"], "status": p.get("status", "unknown"), "team": p.get("team", "Unknown"), "deadline": p.get("deadline")}
        if "name" in p else p
        for p in projects
    ]
    experiments = [
        {
            "project_id": e.get("project_id") or e.get("project"),
            "status": e.get("status") or e.get("result") or ("failed" if e.get("success") is False else "success"),
            "notes": e.get("notes") or e.get("blocker") or "Unknown issue",
        }
        for e in experiments
    ]

    raw_inventory: list[dict]
    raw_research: list[dict]
    raw_plan: dict

    deep_result = None
    if deepagents_enabled():
        deep_result = run_deepagents_pipeline(inventory, projects, experiments)

    if deep_result is not None:
        execution_mode = "deepagents"
        raw_inventory = deep_result["inventory_issues"]
        raw_research = deep_result["research_issues"]
        raw_plan = deep_result["plan"]
        trace.append(TraceStep(
            agent="deepagents_orchestrator",
            input_summary=(
                f"{len(inventory)} inventory item(s), {len(projects)} project(s), "
                f"{len(experiments)} experiment log(s)"
            ),
            output_summary=(
                f"Generated {len(raw_inventory)} inventory issue(s), "
                f"{len(raw_research)} research issue(s), {len(raw_plan.get('actions', []))} action(s)"
            ),
        ))
    else:
        # Inventory agent
        raw_inventory = run_inventory_agent(inventory)
        trace.append(TraceStep(
            agent="inventory_agent",
            input_summary=f"{len(inventory)} inventory item(s) scanned",
            output_summary=f"{len(raw_inventory)} low-stock item(s) detected",
        ))

        # Research agent
        raw_research = run_research_agent(projects, experiments)
        trace.append(TraceStep(
            agent="research_agent",
            input_summary=f"{len(projects)} project(s) and {len(experiments)} experiment log(s) analysed",
            output_summary=f"{len(raw_research)} at-risk project(s) found",
        ))

        # Planner agent
        raw_plan = run_planner_agent(raw_inventory, raw_research)
        trace.append(TraceStep(
            agent="planner_agent",
            input_summary=f"{len(raw_inventory)} inventory issue(s), {len(raw_research)} research issue(s) received",
            output_summary=f"{len(raw_plan['actions'])} action(s) generated — {raw_plan['final_decision'][:60]}…",
        ))

    # Map raw agent dicts → strict Pydantic models
    inventory_issues = [
        InventoryIssue(
            name=item["item_name"],
            quantity=item["quantity"],
            min_required=item["min_required"],
            shortfall=item["shortfall"],
        )
        for item in raw_inventory
    ]

    research_issues = [
        ResearchIssue(
            project=issue["project_name"],
            status=issue["status"],
            blockers=issue["blockers"],
            notes="; ".join(issue["blockers"]) if issue["blockers"] else "No blockers recorded",
        )
        for issue in raw_research
    ]

    return RunResponse(
        data_source=data_source,
        execution_mode=execution_mode,
        execution_trace=trace,
        inventory_issues=inventory_issues,
        research_issues=research_issues,
        plan=Plan(**raw_plan),
    )


# ── Individual Agent Endpoints (for chat-based frontend) ─────────────────────

def _normalize_inventory(inventory: list[dict]) -> list[dict]:
    """Normalize inventory field names."""
    return [
        {"item_name": i.get("item_name") or i.get("name"), "quantity": i.get("quantity", 0), 
         "min_required": i.get("min_required", 0), "unit": i.get("unit", "")}
        for i in inventory
    ]


def _normalize_projects(projects: list[dict]) -> list[dict]:
    """Normalize project field names."""
    return [
        {"project_name": p.get("project_name") or p.get("name"), "status": p.get("status", "unknown"), 
         "team": p.get("team", "Unknown"), "deadline": p.get("deadline")}
        for p in projects
    ]


@app.post("/agent/inventory")
def get_inventory_issues():
    """Run inventory agent and return low-stock items."""
    inventory, _ = fetch_inventory()
    inventory = _normalize_inventory(inventory)
    issues = run_inventory_agent(inventory)
    return {
        "agent": "inventory_agent",
        "low_stock_items": [
            {"name": item["item_name"], "quantity": item["quantity"], "min_required": item["min_required"], "shortfall": item["shortfall"], "unit": item.get("unit", "")}
            for item in issues
        ]
    }


@app.post("/agent/research")
def get_research_issues():
    """Run research agent and return at-risk projects."""
    projects, _ = fetch_projects()
    experiments, _ = fetch_experiments_log()
    projects = _normalize_projects(projects)
    experiments = [
        {"project_id": e.get("project_id") or e.get("project"),
         "status": e.get("status") or e.get("result") or ("failed" if e.get("success") is False else "success"),
         "notes": e.get("notes") or e.get("blocker") or "Unknown issue"}
        for e in experiments
    ]
    issues = run_research_agent(projects, experiments)
    return {
        "agent": "research_agent",
        "at_risk_projects": [
            {"project": issue["project_name"], "status": issue["status"], "team": issue.get("team"), "deadline": issue.get("deadline"), "blockers": issue.get("blockers", []), "notes": issue.get("notes", "")}
            for issue in issues
        ]
    }


@app.post("/agent/planner")
def get_plan(request: dict = None):
    """Run planner agent and return action plan."""
    if not request:
        inv_response = get_inventory_issues()
        res_response = get_research_issues()
        inventory_issues = [
            {"item_name": item["name"], "quantity": item["quantity"], "min_required": item["min_required"], "shortfall": item["shortfall"]}
            for item in inv_response["low_stock_items"]
        ]
        research_issues = [
            {"project_name": issue["project"], "status": issue["status"], "team": issue.get("team"), "deadline": issue.get("deadline"), "blockers": issue.get("blockers", []), "notes": issue.get("notes", "")}
            for issue in res_response["at_risk_projects"]
        ]
    else:
        inventory_issues = request.get("inventory_issues", [])
        research_issues = request.get("research_issues", [])
    plan = run_planner_agent(inventory_issues or [], research_issues or [])
    return {
        "agent": "planner_agent",
        "plan": {"summary": plan["summary"], "critical_issues": plan.get("critical_issues", []), "actions": plan.get("actions", []), "final_decision": plan["final_decision"]}
    }


# ── Chat models ────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: list[dict[str, str]] = Field(default_factory=list)

class ChatResponse(BaseModel):
    reply: str
    data_source: str

    agent_used: str | None = None
    error: bool = False


def _normalize_rag_inventory(inventory: list[dict]) -> list[dict]:
    return [
        {
            "name": item.get("item_name") or item.get("name") or "Unknown item",
            "quantity": item.get("quantity", 0),
            "min_required": item.get("min_required", 0),
            "unit": item.get("unit", ""),
        }
        for item in inventory
    ]


def _normalize_rag_projects(projects: list[dict]) -> list[dict]:
    return [
        {
            "name": project.get("project_name") or project.get("name") or "Unknown project",
            "status": project.get("status", "unknown"),
            "team": project.get("team", "Unknown"),
            "deadline": project.get("deadline"),
        }
        for project in projects
    ]


def _normalize_rag_experiments(experiments: list[dict]) -> list[dict]:
    return [
        {
            "project_id": exp.get("project_id") or exp.get("project"),
            "status": exp.get("status") or exp.get("result") or "unknown",
            "notes": exp.get("notes") or exp.get("blocker") or "",
        }
        for exp in experiments
    ]


def _strip_json_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    return cleaned.strip()


def _run_strict_rag_chat(message: str, history: list[dict[str, str]]) -> tuple[str, bool]:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return "ERROR: GROQ_API_KEY is missing, so strict RAG chat cannot run.", True

    inventory, _ = fetch_inventory()
    projects, _ = fetch_projects()
    experiments, _ = fetch_experiments_log()

    inventory_norm = _normalize_rag_inventory(inventory)
    projects_norm = _normalize_rag_projects(projects)
    experiments_norm = _normalize_rag_experiments(experiments)

    inventory_issues = run_inventory_agent([
        {
            "item_name": item["name"],
            "quantity": item["quantity"],
            "min_required": item["min_required"],
            "unit": item["unit"],
        }
        for item in inventory_norm
    ])
    research_issues = run_research_agent([
        {
            "project_name": project["name"],
            "status": project["status"],
            "team": project["team"],
            "deadline": project["deadline"],
        }
        for project in projects_norm
    ], experiments_norm)
    plan = run_planner_agent([
        {
            "item_name": item["item_name"],
            "quantity": item["quantity"],
            "min_required": item["min_required"],
            "shortfall": item["shortfall"],
            "unit": item.get("unit", ""),
        }
        for item in inventory_issues
    ], [
        {
            "project_name": issue["project_name"],
            "status": issue["status"],
            "team": issue.get("team"),
            "deadline": issue.get("deadline"),
            "blockers": issue.get("blockers", []),
        }
        for issue in research_issues
    ])

    context = {
        "inventory": inventory_norm,
        "projects": projects_norm,
        "experiments": experiments_norm,
        "inventory_issues": inventory_issues,
        "research_issues": research_issues,
        "plan": plan,
        "history": history[-8:],
    }

    system_prompt = (
        "You are Sandy AI. Answer ONLY from the provided context. "
        "No keyword rules, no fallback phrasing, no invented facts. "
        "Use the recent conversation history to resolve short follow-up questions like 'for real?' or 'what about that?'. "
        "If the data does not contain the answer, return JSON with status='error' and answer beginning with 'ERROR:'. "
        "If you can answer, return JSON with status='ok' and a concise answer grounded in the context. "
        "Always output valid JSON only, with keys: status, answer."
    )

    user_prompt = (
        f"Question: {message}\n\n"
        f"Grounded context:\n{json.dumps(context, ensure_ascii=True)}\n\n"
        "Rules:\n"
        "- Use only the grounded context above.\n"
        "- If the question is a short follow-up, use the recent conversation history to resolve what it refers to.\n"
        "- If asked about inventory, mention exact low-stock items only if they exist.\n"
        "- If asked about projects, mention exact at-risk projects only if they exist.\n"
        "- If asked what to work on, use the plan and current active projects.\n"
        "- If asked about experiments and there is no experiment catalog, return error.\n"
        "- Do not mention unsupported data as if it exists.\n"
    )

    client = Groq(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=500,
        )
        raw = response.choices[0].message.content or ""
        parsed = json.loads(_strip_json_fences(raw))
        status = str(parsed.get("status", "error")).lower()
        answer = str(parsed.get("answer", "")).strip()
        if status != "ok" or not answer:
            return (answer if answer.startswith("ERROR:") else "ERROR: The model could not answer from the available data."), True
        if answer.lower().startswith("i don't know") or answer.lower().startswith("i do not know"):
            return "ERROR: The model could not answer from the available data.", True
        return answer, False
    except Exception as exc:
        return f"ERROR: The chat model failed with {exc.__class__.__name__}.", True


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Strict RAG chat endpoint - no keyword matching or fallback replies."""
    inventory, inv_source = fetch_inventory()
    projects, proj_source = fetch_projects()
    experiments, exp_source = fetch_experiments_log()
    sources = {inv_source, proj_source, exp_source}
    data_source = next(iter(sources)) if len(sources) == 1 else "mixed"

    reply, is_error = _run_strict_rag_chat(req.message, req.history)

    return ChatResponse(
        reply=reply,
        data_source=data_source,
        agent_used="rag_agent",
        error=is_error,
    )


if __name__ == "__main__":
    import json

    print("=== Sandy AI Lab — Local Pipeline Test ===\n")

    inventory, inv_source = fetch_inventory()
    projects, proj_source = fetch_projects()
    experiments, exp_source = fetch_experiments_log()

    inventory = [
        {"item_name": i.get("item_name") or i.get("name"), "quantity": i.get("quantity", 0), "min_required": i.get("min_required", 0), "unit": i.get("unit", "")}
        for i in inventory
    ]
    projects = [
        {"project_name": p.get("project_name") or p.get("name"), "status": p.get("status", "unknown"), "team": p.get("team", "Unknown"), "deadline": p.get("deadline")}
        for p in projects
    ]
    experiments = [
        {
            "project_id": e.get("project_id") or e.get("project"),
            "status": e.get("status") or e.get("result") or ("failed" if e.get("success") is False else "success"),
            "notes": e.get("notes") or e.get("blocker") or "Unknown issue",
        }
        for e in experiments
    ]

    print(f"[data_source]      inventory={inv_source}, projects={proj_source}, experiments={exp_source}\n")

    raw_inventory = run_inventory_agent(inventory)
    print(f"[inventory_agent]  input : {len(inventory)} item(s)")
    print(f"[inventory_agent]  output: {len(raw_inventory)} low-stock item(s)\n")

    raw_research = run_research_agent(projects, experiments)
    print(f"[research_agent]   input : {len(projects)} project(s), {len(experiments)} experiment log(s)")
    print(f"[research_agent]   output: {len(raw_research)} at-risk project(s)\n")

    raw_plan = run_planner_agent(raw_inventory, raw_research)
    print(f"[planner_agent]    input : {len(raw_inventory)} inventory issue(s), {len(raw_research)} research issue(s)")
    print(f"[planner_agent]    output: {len(raw_plan['actions'])} action(s)\n")

    print("=== Final Plan ===")
    print(json.dumps(raw_plan, indent=2))
