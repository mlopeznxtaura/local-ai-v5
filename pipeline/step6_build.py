"""
local-ai-v5 — Step 6: Build Execution
Reads:  tasks.json, tests.json
Writes: output/<files>, output.zip

- One stateless Ollama call per task
- Test runs immediately after each file is written
- Up to 3 retries per task — each retry is a fresh stateless call
- tasks.json updated after every task (crash-safe resume)
- output.zip auto-generated at end regardless of partial failures
- Optional GitHub push if git remote is configured

Stateless per task: each build call receives only that task's spec.
"""
import json
import os
import zipfile
import subprocess
from ollama_client import ask, check_model, strip_fences

check_model()

BUILD_INSTRUCTION = (
    "You are a senior software engineer. Write complete working code for the task. "
    "No stubs. No placeholders. No TODOs. No comments. Complete implementation only. "
    "Return ONLY the raw code. No explanation. No markdown fences."
)

def run_test(test_code: str) -> tuple:
    try:
        exec(compile(test_code, "<test>", "exec"), {})
        return True, None
    except Exception as e:
        return False, str(e)

def build_one_task(task: dict, test_code: str, max_retries: int = 3) -> bool:
    file_path = task.get("file", "")
    if not file_path.startswith("output/"):
        file_path = os.path.join("output", file_path)

    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else "output", exist_ok=True)

    for attempt in range(1, max_retries + 1):
        print(f"    attempt {attempt}/{max_retries}...")

        # Fresh stateless call — only this task's spec
        prompt = (
            BUILD_INSTRUCTION + "\n\n"
            f"Task: {task.get('title', '')}\n"
            f"File: {file_path}\n"
            f"Description: {task.get('description', '')}"
        )

        code = ask(6, "build_execution", prompt, budget_tokens=2048)
        code = strip_fences(code)
        if code.startswith("python\n"):
            code = code[7:]

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        passed, err = run_test(test_code)
        if passed:
            print(f"    ✓ passed")
            return True
        else:
            print(f"    ✗ {err}")

    print(f"    ✗ failed after {max_retries} attempts")
    return False

def zip_output(output_dir: str = "output", zip_path: str = "output.zip") -> str:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(output_dir):
            for fname in files:
                full = os.path.join(root, fname)
                arcname = os.path.relpath(full, start=os.path.dirname(output_dir))
                zf.write(full, arcname)
    return os.path.abspath(zip_path)

def try_github_push():
    """Optional — only runs if git remote is configured. Never blocks on failure."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            print("[6/7] No git remote — skipping GitHub push.")
            return
        remote = result.stdout.strip()
        subprocess.run(["git", "add", "output/"], timeout=10)
        subprocess.run(
            ["git", "commit", "-m", "local-ai-v5: build output"],
            timeout=10
        )
        push = subprocess.run(["git", "push"], capture_output=True, text=True, timeout=30)
        if push.returncode == 0:
            print(f"[6/7] ✓ Pushed to {remote}")
        else:
            print(f"[6/7] Push failed (non-fatal): {push.stderr.strip()}")
    except Exception as e:
        print(f"[6/7] GitHub push skipped: {e}")

# --- Main ---
with open("tasks.json", "r", encoding="utf-8") as f:
    tasks = json.load(f)

with open("tests.json", "r", encoding="utf-8") as f:
    tests = json.load(f)

test_lookup = {t["task_id"]: t.get("test_code", "pass") for t in tests}
os.makedirs("output", exist_ok=True)

results = []
for task in tasks:
    if task.get("status") == "done":
        print(f"  Skipping {task['id']} (already done)")
        continue

    print(f"\n[6/7] {task['id']} — {task.get('title', '')}")
    success = build_one_task(task, test_lookup.get(task["id"], "pass"))

    task["status"] = "done" if success else "failed"
    results.append({"id": task["id"], "success": success})

    # Write after every task — crash-safe resume
    with open("tasks.json", "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)

done = sum(1 for r in results if r["success"])
failed = len(results) - done

print(f"\n{'='*44}")
print(f"  Build: {done}/{len(results)} tasks succeeded  |  {failed} failed")

# Mandatory zip export
zip_path = zip_output()
print(f"  Zip:   {zip_path}")

# Optional GitHub push
try_github_push()

print(f"{'='*44}\n")
