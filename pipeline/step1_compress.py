"""
local-ai-v5 — Step 1: Prompt Compression
Reads:  grounded_context.json
Writes: compressed_intent.txt

Compresses the raw intent into one clean sentence, informed by the
web-grounded context from Step 0. Result is used by all downstream steps.

Stateless: reads one file, writes one file, exits.
"""
import json
from ollama_client import ask, check_model

check_model()

with open("grounded_context.json", "r", encoding="utf-8") as f:
    ctx = json.load(f)

raw = ctx.get("raw_intent", "")
grounded = ctx.get("grounded", {})
stack = grounded.get("current_stack", [])
grounded_intent = grounded.get("grounded_intent", raw)

print("[1/7] Compressing intent (grounding-aware)...")

prompt = (
    "Compress this build description into ONE clean, precise sentence. "
    "Incorporate the grounded intent and current stack if relevant. "
    "Same language as input. Return the sentence only — no quotes, no punctuation wrapping.\n\n"
    f"Raw intent: {raw}\n"
    f"Grounded intent: {grounded_intent}\n"
    f"Current stack hint: {', '.join(stack) if stack else 'none'}"
)

result = ask(1, "prompt_compression", prompt, budget_tokens=128).strip()

# Strip any quotes the model adds
result = result.strip('"').strip("'").strip()

with open("compressed_intent.txt", "w", encoding="utf-8") as f:
    f.write(result)

print(f"[1/7] Done → {result}")
