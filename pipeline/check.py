"""
local-ai-v5 — Pre-flight Check
Run this first: python3 check.py

Verifies:
  - Ollama reachable at WSL endpoint
  - gemma4 model is pulled
  - Auto-patches ollama_client.py with exact model tag found
  - Python deps present
"""
import requests
import sys
import re

OLLAMA_HOST = "http://172.30.80.1:11434"
REQUIRED_MODEL = "gemma4"

print("local-ai-v5 — Pre-flight Check")
print("=" * 40)

# 1. Ollama reachable
try:
    r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=8)
    r.raise_for_status()
    print(f"✓ Ollama reachable at {OLLAMA_HOST}")
except Exception as e:
    print(f"✗ Ollama unreachable: {e}")
    print(f"  Fix: run 'ollama serve' in WSL")
    print(f"  Test: curl {OLLAMA_HOST}/api/tags")
    sys.exit(1)

# 2. Model present
models = r.json().get("models", [])
names = [m["name"] for m in models]
matched = [n for n in names if REQUIRED_MODEL in n]

if matched:
    best = matched[0]
    print(f"✓ Model found: {matched}  →  using {best}")
    with open("ollama_client.py", "r") as f:
        src = f.read()
    patched = re.sub(r'MODEL = ".*?"', f'MODEL = "{best}"', src)
    with open("ollama_client.py", "w") as f:
        f.write(patched)
    print(f"  ✓ ollama_client.py patched: MODEL = \"{best}\"")
else:
    print(f"✗ gemma4 not found. Available: {names}")
    print(f"  Fix: ollama pull gemma4:26b")
    sys.exit(1)

# 3. Python deps
missing = []
for pkg, imp in [("requests", "requests"), ("bs4", "bs4")]:
    try:
        __import__(imp)
    except ImportError:
        missing.append(pkg)

if missing:
    print(f"✗ Missing packages: {missing}")
    print(f"  Fix: pip3 install {' '.join(missing)} --break-system-packages")
    sys.exit(1)
else:
    print(f"✓ Python deps OK (requests, beautifulsoup4)")

# 4. Network check for Step 0 web grounding
try:
    import urllib.request
    urllib.request.urlopen("https://api.duckduckgo.com", timeout=5)
    print(f"✓ Web search reachable (DuckDuckGo) — Step 0 grounding will use live data")
except Exception:
    print(f"⚠ Web search unreachable — Step 0 will use fallback (offline mode)")
    print(f"  Pipeline will still run, grounding confidence will be 'low'")

print()
print("All checks passed.")
print()
print("Run the pipeline:")
print('  python3 run.py "describe what you want to build"')
print()
