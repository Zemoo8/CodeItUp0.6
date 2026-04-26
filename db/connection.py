import os
from typing import Any

import requests

DATABASE_URL = os.getenv("DATABASE_URL", "")
DATABASE_API_URL = os.getenv("DATABASE_API_URL", "").rstrip("/")

MOCK_INVENTORY = [
    {"id": 1, "item_name": "Lithium Cells", "quantity": 3, "min_required": 10, "unit": "pcs"},
    {"id": 2, "item_name": "Microcontrollers", "quantity": 25, "min_required": 20, "unit": "pcs"},
    {"id": 3, "item_name": "Sensor Array", "quantity": 1, "min_required": 5, "unit": "pcs"},
    {"id": 4, "item_name": "Coolant Fluid", "quantity": 0, "min_required": 3, "unit": "liters"},
    {"id": 5, "item_name": "PCB Boards", "quantity": 50, "min_required": 15, "unit": "pcs"},
]

MOCK_PROJECTS = [
    {"id": 1, "name": "Alpha Drone", "status": "delayed", "deadline": "2026-03-01", "team": "Hardware"},
    {"id": 2, "name": "Beta Sensor Suite", "status": "on_track", "deadline": "2026-05-15", "team": "Firmware"},
    {"id": 3, "name": "Gamma Control Board", "status": "failed", "deadline": "2026-02-10", "team": "Electronics"},
    {"id": 4, "name": "Delta Power Module", "status": "on_track", "deadline": "2026-06-01", "team": "Power"},
]

MOCK_EXPERIMENTS_LOG = [
    {"id": 1, "project_id": 1, "experiment": "Flight stability test", "result": "failed", "blocker": "Low battery capacity"},
    {"id": 2, "project_id": 1, "experiment": "Motor calibration", "result": "failed", "blocker": "Missing Lithium Cells"},
    {"id": 3, "project_id": 2, "experiment": "Sensor accuracy test", "result": "passed", "blocker": None},
    {"id": 4, "project_id": 3, "experiment": "PCB stress test", "result": "failed", "blocker": "Component overheating"},
    {"id": 5, "project_id": 3, "experiment": "Integration test", "result": "failed", "blocker": "Missing Coolant Fluid"},
]


def _fetch_from_api(path: str) -> list[dict[str, Any]] | None:
    """Fetch JSON rows from external API when DATABASE_API_URL is configured."""
    if not DATABASE_API_URL:
        return None

    try:
        response = requests.get(f"{DATABASE_API_URL}{path}", timeout=5)
        response.raise_for_status()
        payload = response.json()

        if isinstance(payload, dict) and isinstance(payload.get("data"), list):
            return payload["data"]
        if isinstance(payload, list):
            return payload
    except Exception:
        return None

    return None


def get_connection():
    if not DATABASE_URL:
        return None

    try:
        import psycopg2

        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception:
        return None


def fetch_inventory():
    api_rows = _fetch_from_api("/inventory")
    if api_rows is not None:
        return api_rows, "api"

    conn = get_connection()
    if conn is None:
        return MOCK_INVENTORY, "mock"

    try:
        import psycopg2.extras

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id, item_name, quantity, min_required, unit FROM inventory")
            return [dict(r) for r in cur.fetchall()], "database"
    except Exception:
        return MOCK_INVENTORY, "mock"
    finally:
        conn.close()


def fetch_projects():
    api_rows = _fetch_from_api("/projects")
    if api_rows is not None:
        return api_rows, "api"

    conn = get_connection()
    if conn is None:
        return MOCK_PROJECTS, "mock"

    try:
        import psycopg2.extras

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id, name, status, deadline, team FROM projects")
            return [dict(r) for r in cur.fetchall()], "database"
    except Exception:
        return MOCK_PROJECTS, "mock"
    finally:
        conn.close()


def fetch_experiments_log():
    if DATABASE_API_URL:
        # Some API deployments do not expose experiments. In API mode,
        # prefer an empty list over mock data to avoid mixing sources.
        for path in ("/experiments", "/experiments_log"):
            api_rows = _fetch_from_api(path)
            if api_rows is not None:
                return api_rows, "api"
        return [], "api"

    conn = get_connection()
    if conn is None:
        return MOCK_EXPERIMENTS_LOG, "mock"

    try:
        import psycopg2.extras

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id, project_id, experiment, result, blocker FROM experiments_log")
            return [dict(r) for r in cur.fetchall()], "database"
    except Exception:
        return MOCK_EXPERIMENTS_LOG, "mock"
    finally:
        conn.close()
