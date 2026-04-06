"""
local-ai-v5 — Step 2: Mock UI Generation
Reads:  compressed_intent.txt, grounded_context.json
Writes: mock_ui.html

Generates an HTML mock of what the app should look like.
Uses grounded stack context so components match current real-world patterns.

Stateless: reads input files, writes one file, exits.
"""
import json
from ollama_client import ask, check_model

check_model()

with open("compressed_intent.txt", "r", encoding="utf-8") as f:
    intent = f.read().strip()

with open("grounded_context.json", "r", encoding="utf-8") as f:
    ctx = json.load(f)

stack = ctx.get("grounded", {}).get("current_stack", [])
stack_hint = f"Preferred stack: {', '.join(stack)}. " if stack else ""

print("[2/7] Generating mock UI...")

prompt = (
    "You are a UI designer. Return a single complete HTML file showing what this app looks like. "
    f"{stack_hint}"
    "Use clean HTML and inline CSS. Include all buttons, forms, inputs, and sections the app needs. "
    "Make it look real. Label every element clearly. "
    "Return ONLY raw HTML starting with <!DOCTYPE html>. No explanation. No markdown."
    f"\n\nApp: {intent}"
)

result = ask(2, "mock_ui_generation", prompt, budget_tokens=2048)

r = result.strip()
if "```html" in r:
    r = r.split("```html")[1].split("```")[0]
elif "```" in r:
    r = r.split("```")[1].split("```")[0]

if not (r.strip().startswith("<!DOCTYPE") or r.strip().startswith("<html")):
    r = f"<!DOCTYPE html><html><body>{r}</body></html>"

with open("mock_ui.html", "w", encoding="utf-8") as f:
    f.write(r.strip())

print("[2/7] Done → mock_ui.html  (open in browser to preview)")
