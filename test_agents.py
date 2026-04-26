from agents.inventory_agent import run_inventory_agent
from agents.research_agent import run_research_agent
from agents.planner_agent import run_planner_agent

# MOCK DATA
inventory = [
    {"item_name": "Lithium Cells", "quantity": 3, "min_required": 10, "unit": "pcs"},
    {"item_name": "Sensors", "quantity": 20, "min_required": 5, "unit": "pcs"},
]

projects = [
    {
        "project_name": "Sea pressure test",
        "status": "failed",
        "team": "Ocean Lab",
        "deadline": "2026-05-01",
        "blockers": []
    }
]

experiments_log = [
    {"project": "Sea pressure test", "status": "failed", "notes": "equipment failure"}
]

# RUN AGENTS
inv = run_inventory_agent(inventory)
res = run_research_agent(projects, experiments_log)
plan = run_planner_agent(inv, res)

print("INVENTORY ISSUES:", inv)
print("RESEARCH ISSUES:", res)
print("FINAL PLAN:", plan)