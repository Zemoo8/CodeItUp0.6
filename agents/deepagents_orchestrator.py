import json
import os
import re
from typing import Any

from agents.inventory_agent import run_inventory_agent
from agents.planner_agent import run_planner_agent
from agents.research_agent import run_research_agent


def _debug_enabled() -> bool:
    return os.getenv("DEEPAGENTS_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}


def _debug_log(message: str) -> None:
    if _debug_enabled():
        print(f"[deepagents] {message}")

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def deepagents_enabled() -> bool:
    value = os.getenv("USE_DEEPAGENTS", "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _extract_message_content(result: Any) -> str:
    if isinstance(result, dict):
        messages = result.get("messages")
        if isinstance(messages, list) and messages:
            last = messages[-1]
            content = getattr(last, "content", None)
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts: list[str] = []
                for block in content:
                    if isinstance(block, dict):
                        text = block.get("text")
                        if isinstance(text, str):
                            parts.append(text)
                if parts:
                    return "\n".join(parts)
            if isinstance(last, dict):
                last_content = last.get("content")
                if isinstance(last_content, str):
                    return last_content
                if isinstance(last_content, list):
                    parts: list[str] = []
                    for block in last_content:
                        if isinstance(block, dict):
                            text = block.get("text")
                            if isinstance(text, str):
                                parts.append(text)
                    if parts:
                        return "\n".join(parts)
    return ""


def _parse_json_from_text(content: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # Strip markdown code fences if present.
    fenced = content.strip()
    if fenced.startswith("```"):
        fenced = re.sub(r"^```[a-zA-Z0-9_\-]*\n?", "", fenced)
        fenced = re.sub(r"\n?```$", "", fenced)
        try:
            parsed = json.loads(fenced)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    # Fallback: extract the first JSON object from mixed text.
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = content[start : end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return None

    return None


def run_deepagents_pipeline(
    inventory: list[dict[str, Any]],
    projects: list[dict[str, Any]],
    experiments: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Run a Deep Agents orchestrated version of the same 3-agent workflow.

    Returns None if deepagents is unavailable or the result is invalid.
    """
    try:
        from deepagents import create_deep_agent
    except Exception as e:
        _debug_log(f"import failure: {e}")
        return None

    # Deep Agents expects OpenAI-compatible env vars for openai:* models.
    # If user only configured Groq-style vars, bridge them automatically.
    if not os.getenv("OPENAI_API_KEY") and os.getenv("GROQ_API_KEY"):
        os.environ["OPENAI_API_KEY"] = os.getenv("GROQ_API_KEY", "")
    if not os.getenv("OPENAI_BASE_URL"):
        if os.getenv("GROQ_API_URL"):
            os.environ["OPENAI_BASE_URL"] = os.getenv("GROQ_API_URL", "")
        elif os.getenv("GROQ_API_KEY"):
            os.environ["OPENAI_BASE_URL"] = "https://api.groq.com/openai/v1"

    model = os.getenv("DEEPAGENTS_MODEL", "openai:llama-3.1-8b-instant")

    def inventory_tool() -> str:
        """Analyze inventory and return JSON list of low-stock issues."""
        return json.dumps(run_inventory_agent(inventory), ensure_ascii=True)

    def research_tool() -> str:
        """Analyze projects and experiments and return JSON list of at-risk projects."""
        return json.dumps(run_research_agent(projects, experiments), ensure_ascii=True)

    def planner_tool(inventory_issues_json: str, research_issues_json: str) -> str:
        """Build final plan from JSON strings of inventory and research issues."""
        inventory_issues = json.loads(inventory_issues_json)
        research_issues = json.loads(research_issues_json)
        plan = run_planner_agent(inventory_issues, research_issues)
        return json.dumps(plan, ensure_ascii=True)

    system_prompt = (
        "You are an orchestration agent for Sandy AI Lab. "
        "Use tools in order: inventory_tool, research_tool, planner_tool. "
        "Return strict JSON with keys: inventory_issues, research_issues, plan. "
        "Do not include markdown fences."
    )

    try:
        agent = create_deep_agent(
            model=model,
            tools=[inventory_tool, research_tool, planner_tool],
            system_prompt=system_prompt,
            subagents=[],
            skills=[],
            memory=[],
            permissions=[],
        )
    except Exception as e:
        _debug_log(f"create_deep_agent failure: {e}")
        return None

    try:
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Run the full lab pipeline now and return strict JSON output "
                            "with inventory_issues, research_issues, and plan."
                        ),
                    }
                ]
            }
        )
    except Exception as e:
        _debug_log(f"invoke failure: {e}")
        return None

    content = _extract_message_content(result)
    if not content:
        _debug_log("no message content in deepagents result")
        return None

    parsed = _parse_json_from_text(content)
    if parsed is None:
        _debug_log("unable to parse JSON from deepagents response")
        return None

    inventory_issues = parsed.get("inventory_issues")
    research_issues = parsed.get("research_issues")
    plan = parsed.get("plan")

    if not isinstance(inventory_issues, list):
        _debug_log("inventory_issues is not a list")
        return None
    if not isinstance(research_issues, list):
        _debug_log("research_issues is not a list")
        return None
    if not isinstance(plan, dict):
        _debug_log("plan is not a dict")
        return None

    return {
        "inventory_issues": inventory_issues,
        "research_issues": research_issues,
        "plan": plan,
    }
