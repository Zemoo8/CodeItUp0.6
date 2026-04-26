from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict
from typing import Literal

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
