# local-ai-v5
## Intent → Software. Offline. Stateless. Gemma 4.

---

## Architecture

```
user_prompt.txt
      ↓
step0_ground.py     → grounded_context.json   [LIVE WEB SEARCH — before any LLM]
      ↓
step1_compress.py   → compressed_intent.txt   [grounding-aware compression]
      ↓
step2_mockui.py     → mock_ui.html
      ↓
step3_parse.py      → features.json
      ↓
step4_dag.py        → dag.json
      ↓
step5_tasks.py      → tasks.json + tests.json [per-task immediate validation]
      ↓
step6_build.py      → output/ + output.zip    [crash-safe, auto zip, optional git push]
      ↓
ui/                 → Tauri desktop app        [build last]
```

**Stateless contract:** Every step reads exactly one input file, makes one or more
isolated Ollama calls (each call has zero memory of any other), writes one output
file, and exits. The orchestrator owns all state. The model owns nothing between calls.

**Step 0 grounding:** DuckDuckGo Instant Answer API — no key, no auth.
Pulls current best practices and library choices as of today's date.
Result feeds Step 1 so the entire pipeline is grounded in live data,
not training data alone.

**Step 5 per-task validation:** Each task's test is generated immediately after
the task itself, as a separate stateless call. Test syntax is validated before
build starts. No broken tests reach Step 6.

---

## Plug and Play — Your Environment

| | |
|---|---|
| WSL | Ubuntu 24.04 |
| Ollama endpoint | `http://172.30.80.1:11434` |
| Model | `gemma4:26b` |
| GPU | RTX 5090 |

---

## Setup

### 1. Pull the model
```bash
ollama pull gemma4:26b
```

### 2. Install Python deps
```bash
cd pipeline
pip3 install requests beautifulsoup4 --break-system-packages
```

### 3. Pre-flight check
```bash
python3 check.py
```
This confirms Ollama is reachable, gemma4 is available, auto-patches
`ollama_client.py` with the exact model tag, and checks web access for Step 0.

### 4. Run the pipeline
```bash
python3 run.py "describe what you want to build"
```

Examples:
```bash
python3 run.py "an expense tracker with charts and CSV export"
python3 run.py "a Tauri desktop app for monitoring cloud costs across AWS and IBM"
python3 run.py "a REST API with auth, rate limiting, and Swagger docs"
```

Output lands in `pipeline/output/` and `pipeline/output.zip`.

---

## Resume After Crash

Tasks already marked `"status":"done"` in `tasks.json` are skipped on re-run.
Just run `python3 run.py` again (no argument needed if `user_prompt.txt` exists).

---

## Optional: GitHub Push

Step 6 automatically attempts `git push` if a remote is configured.
It never blocks — if no remote or push fails, it logs and continues.

To set up:
```bash
cd pipeline
git init
git remote add origin https://github.com/1archit3ct1/your-repo.git
```

---

## Tauri UI (build last)

```bash
cd ui
npm install
npm run tauri dev
```

Requirements: Node 20.x, Rust stable, Tauri 2.x

The UI runs the same 7-step pipeline and shows output path + zip on completion.

---

## Troubleshooting

**Ollama unreachable:**
```bash
curl http://172.30.80.1:11434/api/tags
# If fails: check WSL IP
ip route show | grep default
# Update OLLAMA_HOST in ollama_client.py if IP changed
```

**Model not found:**
```bash
ollama list
ollama pull gemma4:26b
```

**Step 0 grounding offline:**
Pipeline still runs. Step 0 sets `search_confidence: "low"` in
`grounded_context.json` and Step 1 falls back to raw intent only.

**Bad JSON from model:**
Each step has a safe fallback. Re-running is always safe — completed
tasks are skipped via `tasks.json` status field.
