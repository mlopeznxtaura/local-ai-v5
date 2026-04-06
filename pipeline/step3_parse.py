"""
local-ai-v5 — Step 3: Feature Parsing
Reads:  mock_ui.html
Writes: features.json

Deterministic HTML parse first (no tokens wasted on what BeautifulSoup handles).
Model adds semantic feature descriptions on top of the parsed elements.

Stateless: reads one file, writes one file, exits.
"""
import json
from bs4 import BeautifulSoup
from ollama_client import ask, check_model, safe_json

check_model()

with open("mock_ui.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
elements = []

for btn in soup.find_all("button"):
    t = btn.get_text(strip=True)
    if t:
        elements.append({"type": "button", "label": t})

for inp in soup.find_all("input"):
    label = inp.get("placeholder") or inp.get("name") or inp.get("type", "input")
    elements.append({"type": "input", "label": label})

for form in soup.find_all("form"):
    elements.append({"type": "form", "label": form.get("id") or "form"})

for h in soup.find_all(["h1", "h2", "h3"]):
    t = h.get_text(strip=True)
    if t:
        elements.append({"type": "section", "label": t})

print(f"[3/7] Parsed {len(elements)} UI elements. Extracting features...")

compact = json.dumps(elements, separators=(',', ':'))

prompt = (
    "Given this UI element list, return a JSON array of app features. "
    'Each: {"name":"...","description":"...","inputs":[],"outputs":[]}. '
    "Return ONLY valid minified JSON array. No explanation.\n\n"
    + compact
)

raw = ask(3, "feature_parsing", prompt, budget_tokens=1024)
features = safe_json(raw, [
    {"name": e["label"], "description": e["type"], "inputs": [], "outputs": []}
    for e in elements
])

output = {"parsed_elements": elements, "features": features}

with open("features.json", "w", encoding="utf-8") as f:
    json.dump(output, f, separators=(',', ':'))

print(f"[3/7] Done → features.json ({len(features)} features)")
