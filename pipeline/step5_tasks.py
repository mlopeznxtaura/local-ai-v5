"""
local-ai-v5 — Step 5: Task & Test Generation + Immediate Validation
Reads:  dag.json, compressed_intent.txt, grounded_context.json
Writes: tasks.json, tests.json

KEY BEHAVIOR:
- Generates each task's test immediately after generating the task itself.
- Each task+test pair is validated as a stateless sub-step before moving on.
- Tasks that fail validation are flagged before build ever starts.
- Only the compressed task spec passes forward — descriptions stay in tasks.json.

Stateless: reads input files, writes two files, exits.
"""
import json
from ollama_client import ask, check_model, safe_json

check_model()

with open("dag.json", "r", encoding="utf-8") as f:
    dag = json.load(f)

with open("compressed_intent.txt", "r", encoding="utf-8") as f:
    intent = f.read().strip()

with open("grounded_context.json", "r", encoding="utf-8") as f:
    ctx = json.load(f)

stack = ctx.get("grounded", {}).get("current_stack", [])
build_order = dag.get("build_order", [])

print(f"[5/7] Generating tasks + immediate validation for {len(build_order)} items...")

tasks = []
tests = []
task_counter = 1

for feature_name in build_order:
    tid = f"T{str(task_counter).zfill(3)}"

    # --- Sub-step A: Generate task spec (stateless call) ---
    task_prompt = (
        f"Generate ONE atomic build task for: {feature_name}\n"
        f"App intent: {intent}\n"
        f"Stack: {', '.join(stack) if stack else 'any'}\n\n"
        'Return ONLY: {"id":"' + tid + '","title":"...","file":"output/path/file.ext",'
        '"description":"exact complete spec for what this file must contain and do",'
        '"depends_on":[],"status":"pending"}'
    )

    raw_task = ask(5, "task_generation", task_prompt, budget_tokens=384)
    task = safe_json(raw_task, {
        "id": tid,
        "title": feature_name,
        "file": f"output/{feature_name.lower().replace(' ', '_')}.py",
        "description": f"Implement {feature_name}",
        "depends_on": [],
        "status": "pending"
    })
    task["id"] = tid  # enforce correct ID

    # --- Sub-step B: Generate test for this task immediately (stateless call) ---
    test_prompt = (
        f"Write a Python test for this task. "
        f"Test must verify: (1) file exists, (2) contains correct logic for the feature. "
        f"Return ONLY: "
        '{"task_id":"' + tid + '","test_code":"import os\\nassert os.path.exists(\'...\')..."}'
        f"\n\nTask: {json.dumps(task, separators=(',',':'))}"
    )

    raw_test = ask(5, "test_generation", test_prompt, budget_tokens=256)
    test = safe_json(raw_test, {
        "task_id": tid,
        "test_code": f"import os\nassert os.path.exists('{task.get('file', '')}'), 'Missing: {task.get(\"file\", \"\")}'"
    })
    test["task_id"] = tid  # enforce

    # --- Sub-step C: Validate task+test pair (stateless) ---
    # Check test code is syntactically valid before writing
    test_code = test.get("test_code", "pass")
    try:
        compile(test_code, "<validate>", "exec")
        validation = "ok"
    except SyntaxError as e:
        validation = f"syntax_error: {e}"
        # Fallback to existence check
        test["test_code"] = f"import os\nassert os.path.exists('{task.get('file', '')}'), 'File missing'"
        test["validation_warning"] = validation

    tasks.append(task)
    tests.append(test)
    print(f"  {tid} — {feature_name[:40]} [{validation}]")
    task_counter += 1

with open("tasks.json", "w", encoding="utf-8") as f:
    json.dump(tasks, f, indent=2)

with open("tests.json", "w", encoding="utf-8") as f:
    json.dump(tests, f, indent=2)

print(f"[5/7] Done → {len(tasks)} tasks, {len(tests)} tests (all validated before build)")
