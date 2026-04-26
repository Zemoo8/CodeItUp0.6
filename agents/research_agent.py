from typing import Any

PROBLEM_STATUSES = {"delayed", "failed", "blocked"}


def run_research_agent(
    projects: list[dict[str, Any]],
    experiments_log: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    blockers_by_project: dict[Any, list[str]] = {}

    for exp in experiments_log:
        if exp.get("status") == "failed":
            pid = exp.get("project_id") or exp.get("project")

            if pid:
                blockers_by_project.setdefault(pid, []).append(
                    exp.get("notes", "Unknown issue")
                )

    issues = []

    for project in projects:
        status = project.get("status", "")

        if status in PROBLEM_STATUSES:
            pid = project.get("id") or project.get("project_name")

            issues.append({
                "project_id": pid,
                "project_name": project.get("project_name") or project.get("name") or "Unknown Project",
                "status": status,
                "team": project.get("team"),
                "deadline": project.get("deadline"),
                "blockers": blockers_by_project.get(pid, []),
            })

    return issues