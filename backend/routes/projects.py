from fastapi import APIRouter
from db import get_connection

router = APIRouter()


# READ
@router.get("/projects")
def get_projects():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM projects;")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    conn.close()

    return {
        "data": [dict(zip(columns, row)) for row in rows]
    }


# CREATE (CRUD TOOL)
@router.post("/projects")
def create_project(project: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO projects (name, description, status, priority)
        VALUES (%s, %s, %s, %s)
    """, (
        project["name"],
        project.get("description", ""),
        project.get("status", "planned"),
        project.get("priority", 1)
    ))

    conn.commit()
    conn.close()

    return {"status": "created"}


# UPDATE (CRUD TOOL)
@router.patch("/projects/{id}")
def update_project(id: int, data: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE projects
        SET status = %s
        WHERE id = %s
    """, (data["status"], id))

    conn.commit()
    conn.close()

    return {"status": "updated"}