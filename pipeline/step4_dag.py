"""
local-ai-v5 — Step 4: DAG Construction
Reads:  features.json
Writes: dag.json

Builds a dependency graph and topological build order from the feature list.
Only passes feature names to the model — descriptions already consumed.

Stateless: reads one file, writes one file, exits.
"""
import json
from ollama_client import ask, check_model, safe_json

check_model()

with open("features.json", "r", encoding="utf-8") as f:
    data = json.load(f)

features = data.get("features", [])
names = [f.get("name", "") for f in features if f.get("name")]
compact = json.dumps(names, separators=(',', ':'))

print(f"[4/7] Building DAG for {len(names)} features...")

prompt = (
    "Given this feature list, return a build dependency DAG. "
    'Format: {"nodes":[{"id":"...","depends_on":[]}],"build_order":["..."]}. '
    "Work backwards from most complex to most primitive. "
    "build_order must be topologically sorted — dependencies first. "
    "Return ONLY valid minified JSON. No explanation.\n\n"
    + compact
)

raw = ask(4, "dag_construction", prompt, budget_tokens=1024)
dag = safe_json(raw, None)

if not dag or "nodes" not in dag or "build_order" not in dag:
    print("[4/7] WARNING: Invalid DAG from model — building linear fallback.")
    dag = {
        "nodes": [{"id": n, "depends_on": []} for n in names],
        "build_order": names
    }

with open("dag.json", "w", encoding="utf-8") as f:
    json.dump(dag, f, separators=(',', ':'))

order_preview = dag["build_order"][:5]
suffix = "..." if len(dag["build_order"]) > 5 else ""
print(f"[4/7] Done → dag.json  order: {order_preview}{suffix}")
