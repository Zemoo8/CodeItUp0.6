from fastapi import APIRouter
from pydantic import BaseModel
from db import get_connection

router = APIRouter()


class PlanRequest(BaseModel):
    task: str
    context: str | None = None


@router.post("/plan")
def generate_plan(request: PlanRequest):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM projects;")
    projects_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM inventory;")
    inventory_count = cur.fetchone()[0]

    conn.close()

    task = request.task.lower()

    if "inventory" in task:
        action = "read_inventory"
    elif "project" in task:
        action = "read_projects"
    elif "create" in task:
        action = "create_project"
    else:
        action = "general_plan"

    return {
        "status": "success",
        "task": request.task,
        "context": request.context,
        "system_snapshot": {
            "projects": projects_count,
            "inventory": inventory_count
        },
        "suggested_action": action,
        "tool_example": {
            "tool": action,
            "args": {}
        },
        "next_step": "Send tool call to Database Agent (/agent/execute)"
    }