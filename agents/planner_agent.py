import json
import os
from typing import Any

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv is optional at runtime; environment variables still work without it.
    pass

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


def _enhance_plan_with_groq(plan: dict[str, Any]) -> dict[str, Any]:
    """Optionally refine summary and final decision using Groq.

    The deterministic planner output is always produced first; this only rewrites
    text fields when GROQ_API_KEY is configured and the API call succeeds.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return plan

    prompt_payload = {
        "summary": plan.get("summary", ""),
        "critical_issues": plan.get("critical_issues", []),
        "actions": plan.get("actions", []),
        "final_decision": plan.get("final_decision", ""),
    }

    messages = [
        {
            "role": "system",
            "content": (
                "You are an operations planning assistant. "
                "Rewrite only summary and final_decision to be clear and concise. "
                "Return valid JSON with keys: summary, final_decision."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(prompt_payload, ensure_ascii=True),
        },
    ]

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": messages,
                "temperature": 0.2,
            },
            timeout=12,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        if isinstance(parsed, dict):
            summary = parsed.get("summary")
            final_decision = parsed.get("final_decision")
            if isinstance(summary, str) and summary.strip():
                plan["summary"] = summary.strip()
            if isinstance(final_decision, str) and final_decision.strip():
                plan["final_decision"] = final_decision.strip()
    except Exception:
        # Keep deterministic output if LLM call fails or returns invalid JSON.
        return plan

    return plan


def _severity_for_inventory(item: dict[str, Any]) -> str:
    shortfall = item.get("shortfall", 0)
    min_req = item.get("min_required", 1)
    ratio = shortfall / max(min_req, 1)
    if ratio >= 1.0:
        return "high"
    if ratio >= 0.5:
        return "medium"
    return "low"


def _severity_for_project(issue: dict[str, Any]) -> str:
    if issue.get("status") == "failed":
        return "high"
    if issue.get("blockers"):
        return "medium"
    return "low"


def run_planner_agent(
    inventory_issues: list[dict[str, Any]],
    research_issues: list[dict[str, Any]],
) -> dict[str, Any]:
    """Combine inventory and research outputs into a structured decision plan."""
    critical_issues = []
    actions = []
    priority = 1

    for item in inventory_issues:
        severity = _severity_for_inventory(item)
        critical_issues.append({
            "type": "inventory",
            "description": (
                f"{item['item_name']} is under stock: "
                f"{item['quantity']} available, {item['min_required']} required "
                f"(shortfall: {item['shortfall']} {item['unit']})"
            ),
            "severity": severity,
        })
        actions.append({
            "priority": priority,
            "action": f"Restock {item['item_name']} by {item['shortfall']} {item['unit']}",
            "reason": f"Current quantity ({item['quantity']}) is below minimum required ({item['min_required']})",
        })
        priority += 1

    for issue in research_issues:
        severity = _severity_for_project(issue)
        blocker_text = (
            "; ".join(issue["blockers"]) if issue["blockers"] else "no specific blocker recorded"
        )
        critical_issues.append({
            "type": "research",
            "description": (
                f"Project '{issue['project_name']}' is {issue['status']} "
                f"(team: {issue['team']}, deadline: {issue['deadline']}). "
                f"Blockers: {blocker_text}"
            ),
            "severity": severity,
        })
        actions.append({
            "priority": priority,
            "action": f"Review and unblock project '{issue['project_name']}'",
            "reason": f"Project status is '{issue['status']}' with blockers: {blocker_text}",
        })
        priority += 1

    high_count = sum(1 for ci in critical_issues if ci["severity"] == "high")
    medium_count = sum(1 for ci in critical_issues if ci["severity"] == "medium")

    if high_count > 0:
        final_decision = (
            f"IMMEDIATE ACTION REQUIRED: {high_count} high-severity issue(s) detected. "
            "Address critical inventory shortages and failed projects before proceeding."
        )
    elif medium_count > 0:
        final_decision = (
            f"CAUTION: {medium_count} medium-severity issue(s) need attention. "
            "Schedule restocking and project reviews within the next sprint."
        )
    elif critical_issues:
        final_decision = "LOW RISK: Minor issues detected. Monitor and address during regular operations."
    else:
        final_decision = "ALL CLEAR: No critical issues detected. Lab operations are running smoothly."

    inv_names = [
    i.get("item_name") or i.get("name")
    for i in inventory_issues
    if i.get("item_name") or i.get("name")
    ]

    proj_names = [
    i.get("project_name") or i.get("project")
    for i in research_issues
    if i.get("project_name") or i.get("project")
    ]
    summary_parts = []
    if inv_names:
        summary_parts.append(f"{len(inv_names)} low-stock item(s): {', '.join(inv_names)}")
    if proj_names:
        summary_parts.append(f"{len(proj_names)} at-risk project(s): {', '.join(proj_names)}")
    summary = (
        "Sandy AI Lab status — " + "; ".join(summary_parts)
        if summary_parts
        else "Sandy AI Lab status — all systems nominal"
    )

    plan = {
        "summary": summary,
        "critical_issues": critical_issues,
        "actions": sorted(actions, key=lambda a: a["priority"]),
        "final_decision": final_decision,
    }

    return _enhance_plan_with_groq(plan)
