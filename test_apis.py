import os
import re
from dotenv import load_dotenv
load_dotenv()

TEST_PROMPT = "Say exactly: API connection successful"
results     = {}

# ── Agent 1 — Groq Llama 3.3 70B ─────────
print("\nTesting Agent 1 — Groq Llama 3.3 70B...")
try:
    from groq import Groq
    client   = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model      = "llama-3.3-70b-versatile",
        messages   = [{"role": "user", "content": TEST_PROMPT}],
        max_tokens = 20
    )
    print(f"✅ Groq 70B: {response.choices[0].message.content}")
    results["agent1_groq_70b"] = True
except Exception as e:
    print(f"❌ Groq 70B: {e}")
    results["agent1_groq_70b"] = False


# ── Agent 2 — Gemini Flash ────────────────
print("\nTesting Agent 2 — Gemini 2.5 Flash...")
try:
    from google import genai
    client   = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    response = client.models.generate_content(
        model    = "gemini-2.5-flash",
        contents = TEST_PROMPT
    )
    print(f"✅ Gemini Flash: {response.text.strip()}")
    results["agent2_gemini_flash"] = True
except Exception as e:
    print(f"❌ Gemini Flash: {e}")
    results["agent2_gemini_flash"] = False


# ── Agent 3 — Mistral ─────────────────────
print("\nTesting Agent 3 — Mistral Small...")
try:
    from mistralai import Mistral
    client   = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
    response = client.chat.complete(
        model    = "mistral-small-latest",
        messages = [{"role": "user", "content": TEST_PROMPT}]
    )
    print(f"✅ Mistral: {response.choices[0].message.content}")
    results["agent3_mistral"] = True
except Exception as e:
    print(f"❌ Mistral: {e}")
    results["agent3_mistral"] = False


# ── Agent 4 — Groq Llama 3.3 70B ─────────
print("\nTesting Agent 4 — Groq Llama 3.3 70B...")
try:
    from groq import Groq
    client   = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model      = "llama-3.3-70b-versatile",
        messages   = [{"role": "user", "content": TEST_PROMPT}],
        max_tokens = 20
    )
    print(f"✅ Groq 70B: {response.choices[0].message.content}")
    results["agent4_groq_70b"] = True
except Exception as e:
    print(f"❌ Groq 70B: {e}")
    results["agent4_groq_70b"] = False


# ── Agent 5 — Groq Fast (Fallback) ───────
print("\nTesting Agent 5 — Groq Fast Fallback...")
try:
    from groq import Groq
    client   = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model      = "llama-3.1-8b-instant",
        messages   = [{"role": "user", "content": TEST_PROMPT}],
        max_tokens = 20
    )
    print(f"✅ Groq Fast: {response.choices[0].message.content}")
    results["agent5_groq_fast"] = True
except Exception as e:
    print(f"❌ Groq Fast: {e}")
    results["agent5_groq_fast"] = False


# ── Summary ───────────────────────────────
print("\n" + "="*55)
print("  FINAL AGENT READINESS")
print("="*55)

agents = {
    "Agent 1 — Orchestrator    (Groq 70B)":     results.get("agent1_groq_70b",      False),
    "Agent 2 — Route Analyst   (Gemini Flash)": results.get("agent2_gemini_flash",  False),
    "Agent 3 — Risk Assessor   (Mistral)":      results.get("agent3_mistral",       False),
    "Agent 4 — Playbook Writer (Groq 70B)":     results.get("agent4_groq_70b",      False),
    "Agent 5 — Fallback        (Groq Fast)":    results.get("agent5_groq_fast",     False),
}

for agent, ready in agents.items():
    print(f"  {'✅' if ready else '❌'} {agent}")

all_ready = all(agents.values())
working   = sum(agents.values())

print(f"\n  {working}/5 agents ready")
print(f"  {'🚀 All agents ready — build can proceed' if all_ready else '⚠️  Check failing agents'}")
print("="*55)