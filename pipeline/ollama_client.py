"""
local-ai-v5 — Shared Ollama client
All pipeline steps import this. Nothing else is shared between steps.
"""
import requests
import json
import re

OLLAMA_HOST = "http://172.30.80.1:11434"
MODEL = "gemma4:26b"  # auto-patched by check.py if tag differs

STATELESS_SYSTEM = """You are a stateless build execution unit in a software generation pipeline.

HARD RULES:
- You have NO memory of previous steps
- Output is consumed by a machine — no prose, no explanation, no markdown fences
- JSON output ONLY unless told otherwise
- Always compress next_input — target 40% smaller than input
- Never exceed your token budget — truncate and set truncated:true if needed
- No stubs, no placeholders, no TODOs in any generated code

ERROR: if input is malformed emit exactly:
{"error":"malformed_input","step":<N>}
Then stop."""

def ask(step_num: int, step_name: str, user_content: str, budget_tokens: int = 1024) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": STATELESS_SYSTEM},
            {
                "role": "user",
                "content": json.dumps({
                    "step": step_num,
                    "step_name": step_name,
                    "input": user_content,
                    "budget_tokens": budget_tokens
                })
            }
        ],
        "stream": False,
        "options": {
            "num_predict": budget_tokens,
            "temperature": 0.15
        }
    }
    try:
        r = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json=payload,
            timeout=600
        )
        r.raise_for_status()
        return r.json()["message"]["content"]
    except requests.exceptions.ConnectionError:
        raise SystemExit(
            f"\n[local-ai-v5] Cannot reach Ollama at {OLLAMA_HOST}\n"
            f"  Fix: make sure 'ollama serve' is running in WSL\n"
            f"  Test: curl {OLLAMA_HOST}/api/tags\n"
        )
    except Exception as e:
        raise SystemExit(f"\n[local-ai-v5] Ollama error at step {step_num}: {e}\n")


def strip_fences(text: str) -> str:
    """Remove markdown code fences — model sometimes wraps output anyway."""
    t = text.strip()
    t = re.sub(r'^```[a-z]*\n?', '', t)
    t = re.sub(r'\n?```$', '', t)
    return t.strip()


def safe_json(raw: str, fallback):
    """Parse JSON safely, return fallback on failure."""
    try:
        return json.loads(strip_fences(raw))
    except (json.JSONDecodeError, ValueError):
        return fallback


def check_model():
    """Verify Ollama is up and model is available. Called at top of each step."""
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        if not any("gemma4" in m for m in models):
            print(f"[local-ai-v5] WARNING: gemma4 not found. Available: {models}")
            print(f"  Run: ollama pull gemma4:26b")
    except Exception as e:
        raise SystemExit(f"\n[local-ai-v5] Ollama unreachable: {e}\n")
