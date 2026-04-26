import sys
import json
import requests

sys.path.insert(0, ".")
from agents.inventory_agent import run_inventory_agent
from agents.research_agent import run_research_agent
from agents.planner_agent import run_planner_agent

BASE_URL = "http://192.168.1.118:8000"

# Allow users to paste a docs URL without breaking endpoint requests.
if BASE_URL.rstrip("/").endswith("/docs"):
    BASE_URL = BASE_URL.rstrip("/")[:-5]

# ── Helpers ────────────────────────────────────────────────────────────────────

def _get(path: str) -> list[dict]:
    """GET BASE_URL/path and return the list under the 'data' key."""
    url = f"{BASE_URL}{path}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json().get("data") or []
    except requests.ConnectionError:
        print(f"  [ERROR] Cannot connect to {url} — is the backend running?")
        sys.exit(1)
    except requests.HTTPError as e:
        print(f"  [ERROR] {url} returned {e.response.status_code}")
        sys.exit(1)
    except Exception as e:
        print(f"  [ERROR] Unexpected error fetching {url}: {e}")
        sys.exit(1)


def _normalize_inventory(rows: list[dict]) -> list[dict]:
    """Map DB field 'name' → 'item_name' so agents don't crash."""
    out = []
    for row in rows:
        item = dict(row)
        if "item_name" not in item and "name" in item:
            item["item_name"] = item["name"]
        item.setdefault("item_name", "Unknown")
        item.setdefault("quantity", 0)
        item.setdefault("min_required", 0)
        item.setdefault("unit", "")
        out.append(item)
    return out


def _normalize_projects(rows: list[dict]) -> list[dict]:
    """Map DB field 'name' → 'project_name' so agents don't crash."""
    out = []
    for row in rows:
        proj = dict(row)
        if "project_name" not in proj and "name" in proj:
            proj["project_name"] = proj["name"]
        proj.setdefault("project_name", "Unknown Project")
        proj.setdefault("status", "unknown")
        proj.setdefault("team", None)
        proj.setdefault("deadline", None)
        out.append(proj)
    return out


def _section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


# ── Fetch ──────────────────────────────────────────────────────────────────────

def fetch_inventory() -> list[dict]:
    print("  Fetching GET /inventory …")
    raw = _get("/inventory")
    print(f"  Got {len(raw)} row(s)")
    return raw


def fetch_projects() -> list[dict]:
    print("  Fetching GET /projects …")
    raw = _get("/projects")
    print(f"  Got {len(raw)} row(s)")
    return raw


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    _section("STEP 1 — Fetch raw data from backend")

    raw_inventory = fetch_inventory()
    raw_projects  = fetch_projects()

    _section("STEP 2 — Raw inventory data")
    print(json.dumps(raw_inventory, indent=2, default=str))

    _section("STEP 3 — Raw project data")
    print(json.dumps(raw_projects, indent=2, default=str))

    # Normalize field names before passing to agents
    inventory  = _normalize_inventory(raw_inventory)
    projects   = _normalize_projects(raw_projects)
    experiments: list[dict] = []   # no /experiments endpoint exposed by this backend

    _section("STEP 4 — Inventory Agent")
    inventory_issues = run_inventory_agent(inventory)
    print(f"  Low-stock items detected: {len(inventory_issues)}")
    print(json.dumps(inventory_issues, indent=2, default=str))

    _section("STEP 5 — Research Agent")
    if not experiments:
        print("  [NOTE] No experiments endpoint available — blockers will not be populated")
    research_issues = run_research_agent(projects, experiments)
    print(f"  At-risk projects detected: {len(research_issues)}")
    print(json.dumps(research_issues, indent=2, default=str))

    _section("STEP 6 — Planner Agent (final decision)")
    plan = run_planner_agent(inventory_issues, research_issues)
    print(json.dumps(plan, indent=2, default=str))

    _section("RESULT")
    print(f"  {plan['final_decision']}")
    print()


if __name__ == "__main__":
    main()
