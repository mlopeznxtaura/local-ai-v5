"""
local-ai-v5 — Step 0: Web Grounding
Reads:  user_prompt.txt
Writes: grounded_context.json

Purpose: Validate the user's intent against live web data BEFORE the model
touches it with training data. Pulls current best practices, common patterns,
and relevant libraries as of today. This context feeds into Step 1 so the
entire pipeline is grounded in real-world current usage, not just training data.

Stateless: reads one file, writes one file, exits.
"""
import json
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from ollama_client import ask, check_model, safe_json, strip_fences

check_model()

with open("user_prompt.txt", "r", encoding="utf-8") as f:
    raw = f.read().strip()

print("[0/7] Web grounding — extracting search queries from intent...")

# --- Phase A: Ask model to extract 2-3 targeted search queries ---
# Small, cheap call. Model extracts what to search for, not the answer.
query_prompt = (
    "Extract 2-3 web search queries that would ground this build intent in "
    "current real-world best practices and relevant libraries. "
    "Return ONLY a JSON array of strings. No explanation.\n\n"
    f"Intent: {raw}"
)

raw_queries = ask(0, "query_extraction", query_prompt, budget_tokens=128)
queries = safe_json(raw_queries, [])

# Fallback: derive simple query from raw prompt
if not isinstance(queries, list) or len(queries) == 0:
    words = raw.split()[:8]
    queries = [" ".join(words) + " best practices " + str(datetime.now().year)]

queries = queries[:3]  # hard cap
print(f"[0/7] Queries: {queries}")

# --- Phase B: DuckDuckGo Instant Answer API (no key, no auth) ---
search_results = []
for q in queries:
    encoded = urllib.parse.quote_plus(q)
    url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "local-ai-v5/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        abstract = data.get("AbstractText", "")
        related = [r.get("Text", "") for r in data.get("RelatedTopics", [])[:3] if isinstance(r, dict)]
        result_text = abstract or " | ".join(related) or "no results"
        search_results.append({"query": q, "result": result_text[:600]})
        print(f"[0/7] ✓ {q[:50]}...")
    except Exception as e:
        search_results.append({"query": q, "result": f"search_unavailable: {str(e)}"})
        print(f"[0/7] ✗ search failed for: {q} ({e})")

# --- Phase C: Model synthesizes grounding context ---
# Feed raw intent + search results → compressed grounding context
# This is what separates live-grounded builds from pure training-data hallucination.
synthesis_prompt = (
    "Synthesize these web search results with the user's build intent. "
    "Identify: current best libraries, common patterns as of today, and any "
    "constraints or gotchas the search results reveal. "
    "Return ONLY minified JSON: "
    '{"grounded_intent":"<one sentence>","current_stack":["lib1","lib2"],'
    '"patterns":["pattern1"],"gotchas":["gotcha1"],"search_confidence":"high|medium|low"}\n\n'
    f"Intent: {raw}\n\nSearch results: {json.dumps(search_results, separators=(',',':'))}"
)

raw_context = ask(0, "grounding_synthesis", synthesis_prompt, budget_tokens=512)
grounded = safe_json(raw_context, {
    "grounded_intent": raw,
    "current_stack": [],
    "patterns": [],
    "gotchas": [],
    "search_confidence": "low"
})

output = {
    "raw_intent": raw,
    "search_results": search_results,
    "grounded": grounded,
    "grounded_at": datetime.utcnow().isoformat() + "Z"
}

with open("grounded_context.json", "w", encoding="utf-8") as f:
    json.dump(output, f, separators=(',', ':'))

print(f"[0/7] Done → grounded_context.json")
print(f"       Confidence: {grounded.get('search_confidence','?')} | Stack: {grounded.get('current_stack',[])}")
