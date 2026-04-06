"""
local-ai-v5 — Pipeline Runner
Usage:
  python3 run.py "your intent here"
  python3 run.py                      (reads user_prompt.txt)

Pipeline:
  Step 0 — Web grounding (live search before any LLM compression)
  Step 1 — Prompt compression (grounding-aware)
  Step 2 — Mock UI generation
  Step 3 — Feature parsing
  Step 4 — DAG construction
  Step 5 — Task + test generation (per-task immediate validation)
  Step 6 — Build execution (crash-safe, auto zip, optional GitHub push)
"""
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    (0, "step0_ground.py",   "Web Grounding"),
    (1, "step1_compress.py", "Prompt Compression"),
    (2, "step2_mockui.py",   "Mock UI Generation"),
    (3, "step3_parse.py",    "Feature Parsing"),
    (4, "step4_dag.py",      "DAG Construction"),
    (5, "step5_tasks.py",    "Task & Test Generation"),
    (6, "step6_build.py",    "Build Execution"),
]

def main():
    os.chdir(HERE)

    if len(sys.argv) > 1:
        intent = " ".join(sys.argv[1:])
        with open("user_prompt.txt", "w", encoding="utf-8") as f:
            f.write(intent)
        print(f"\n[local-ai-v5] Intent: {intent}\n")
    elif not os.path.exists("user_prompt.txt"):
        print("[local-ai-v5] ERROR: No intent provided.")
        print('  Usage: python3 run.py "describe what you want to build"')
        sys.exit(1)

    for num, script, label in STEPS:
        print(f"\n{'='*48}")
        print(f"  STEP {num}/6 — {label}")
        print(f"{'='*48}")

        result = subprocess.run(
            [sys.executable, script],
            cwd=HERE
        )

        if result.returncode != 0:
            print(f"\n[local-ai-v5] FATAL: {script} failed. Pipeline halted.")
            print(f"  Tasks already marked 'done' in tasks.json will be skipped on re-run.")
            sys.exit(1)

    print(f"\n{'='*48}")
    print(f"  local-ai-v5 COMPLETE")
    print(f"  Output: {HERE}/output/")
    print(f"  Zip:    {HERE}/output.zip")
    print(f"{'='*48}\n")

if __name__ == "__main__":
    main()
