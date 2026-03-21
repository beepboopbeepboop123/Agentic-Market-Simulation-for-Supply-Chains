import json
import ollama
import time
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.hardware_detector import (
    scan_hardware,
    get_ollama_options,
    TIER_CONFIG,
    print_hardware_report
)

# ─────────────────────────────────────────
# DETECT HARDWARE AT STARTUP
# ─────────────────────────────────────────

HARDWARE   = scan_hardware()
TIER       = HARDWARE["tier"]
OPTIONS    = get_ollama_options(TIER)
AUTO_MODEL = HARDWARE["config"]["recommended_model"]

print(f"\n{HARDWARE['config']['emoji']} Hardware Tier  : {TIER}")
print(f"   GPU             : {HARDWARE['gpu']['gpu_name']}")
print(f"   VRAM            : {HARDWARE['gpu']['vram_gb']} GB")
print(f"   Recommended     : {AUTO_MODEL}")
print(f"   Context length  : {OPTIONS['num_ctx']} tokens")
print(f"   GPU layers      : {OPTIONS['num_gpu']}")


# ─────────────────────────────────────────
# LOAD SIMULATION RESULTS
# ─────────────────────────────────────────

def load_results():
    with open("data/results.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────
# HELPER — CALL LOCAL AI WITH HW LIMITS
# ─────────────────────────────────────────

def ask_ai(model, system_prompt, user_prompt):
    """
    Send a prompt to Ollama with hardware
    appropriate limits to prevent OOM errors.
    Automatically falls back to smaller model
    if the requested model is too large.
    """

    tier_config = TIER_CONFIG[TIER]
    safe_model  = model

    # Override model if too large for hardware
    if TIER in ["TIER_1", "TIER_2"]:
        if model in ["mistral", "llama2", "llama3"]:
            safe_model = tier_config["recommended_model"]
            print(
                f"  ⚠️  {model} too large for {TIER}. "
                f"Switching to {safe_model}"
            )

    # First attempt with hardware tuned options
    try:
        response = ollama.chat(
            model    = safe_model,
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            options  = OPTIONS
        )
        return response['message']['content']

    except Exception as e:
        print(f"  ⚠️  {safe_model} failed: {str(e)[:80]}")

        # Second attempt — try fallback model
        fallback = tier_config["fallback_model"]
        print(f"  🔄 Trying fallback: {fallback}...")

        try:
            response = ollama.chat(
                model    = fallback,
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt}
                ],
                options  = {
                    "num_gpu":     0,
                    "num_ctx":     1024,
                    "num_predict": 500,
                }
            )
            return response['message']['content']

        except Exception as e2:
            print(f"  ❌ Fallback also failed: {str(e2)[:80]}")

            # Third attempt — CPU only with tinyllama
            print(f"  🔄 Last resort: tinyllama on CPU...")
            try:
                response = ollama.chat(
                    model    = "tinyllama",
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_prompt}
                    ],
                    options  = {
                        "num_gpu":     0,
                        "num_ctx":     512,
                        "num_predict": 300,
                    }
                )
                return response['message']['content']

            except Exception as e3:
                return (
                    f"AI unavailable on this hardware.\n"
                    f"Error: {str(e3)[:100]}\n"
                    f"Try: ollama pull {fallback}"
                )


# ─────────────────────────────────────────
# AGENT 1 — ORCHESTRATOR
# ─────────────────────────────────────────

def agent_orchestrator(disaster_node, source, target, model):

    print("\n" + "="*55)
    print("  🧠 AGENT 1: ORCHESTRATOR")
    print(f"  Running on: {TIER} with {safe_model_name(model)}")
    print("="*55)

    results = load_results()

    system_prompt = """
You are the Orchestrator Agent in a supply chain
emergency response system. Your job is to:
1. Assess the severity of the disaster
2. Summarize what data is available
3. Give clear instructions to your team
Be concise, professional, and direct.
"""

    user_prompt = f"""
EMERGENCY SITUATION:
- Disaster     : {disaster_node} is CLOSED
- Route From   : {source}
- Route To     : {target}
- Simulations  : {results['total_runs']} stress tests completed
- Routes found : {len(results['route_summary'])} surviving routes
- Best option  : {results['best_route']}
- Best avg time: {results['best_avg_days']} days
- Best avg cost: ${results['best_avg_cost']}

Your job:
1. Assess how serious this disruption is
2. State what the Route Analyst should focus on
3. State what the Risk Assessor should watch for
4. State what the Playbook Writer should emphasize
Keep your response under 200 words.
"""

    print("⚙️  Orchestrator analyzing situation...")
    response = ask_ai(model, system_prompt, user_prompt)
    print(f"\n{response}")

    with open("data/agent1_orchestrator.txt", "w", encoding="utf-8") as f:
        f.write(response)

    print("\n✅ Orchestrator complete")
    return response


# ─────────────────────────────────────────
# AGENT 2 — ROUTE ANALYST
# ─────────────────────────────────────────

def agent_route_analyst(model):

    print("\n" + "="*55)
    print("  📊 AGENT 2: ROUTE ANALYST")
    print(f"  Running on: {TIER} with {safe_model_name(model)}")
    print("="*55)

    results        = load_results()
    orchestrator   = open(
        "data/agent1_orchestrator.txt", encoding="utf-8"
    ).read()

    routes_text = ""
    for i, (route, stats) in enumerate(results['route_summary'].items()):
        routes_text += f"""
Route {i+1}: {route}
  - Times chosen : {stats['times_chosen']} / {results['total_runs']}
  - Success rate : {stats['success_rate']}
  - Avg days     : {stats['avg_days']}
  - Avg cost     : ${stats['avg_cost']}
"""

    system_prompt = """
You are the Route Analyst Agent. You are an expert
in global shipping routes and logistics optimization.
Your job is to deeply analyze surviving routes after
a supply chain disruption and rank them clearly.
Be specific with numbers. Think like a logistics expert.
"""

    user_prompt = f"""
ORCHESTRATOR BRIEFING:
{orchestrator}

SURVIVING ROUTES DATA:
{routes_text}

BEST ROUTE IDENTIFIED: {results['best_route']}
Average: {results['best_avg_days']} days | ${results['best_avg_cost']}

Your analysis should include:
1. TOP 3 ROUTES — rank the best 3 with reasons
2. SPEED vs COST TRADEOFF — which route is fastest,
   which is cheapest, are they the same?
3. RELIABILITY SCORE — based on success rate across
   simulations, which route is most consistent?
4. YOUR RECOMMENDATION — one clear route with
   specific reasoning using the actual numbers

Be specific. Use route names and actual numbers.
Keep response under 300 words.
"""

    print("⚙️  Route Analyst ranking all surviving routes...")
    response = ask_ai(model, system_prompt, user_prompt)
    print(f"\n{response}")

    with open("data/agent2_route_analyst.txt", "w", encoding="utf-8") as f:
        f.write(response)

    print("\n✅ Route Analyst complete")
    return response


# ─────────────────────────────────────────
# AGENT 3 — RISK ASSESSOR
# ─────────────────────────────────────────

def agent_risk_assessor(model):

    print("\n" + "="*55)
    print("  ⚠️  AGENT 3: RISK ASSESSOR")
    print(f"  Running on: {TIER} with {safe_model_name(model)}")
    print("="*55)

    results        = load_results()
    orchestrator   = open(
        "data/agent1_orchestrator.txt", encoding="utf-8"
    ).read()
    route_analysis = open(
        "data/agent2_route_analyst.txt", encoding="utf-8"
    ).read()

    top_routes      = list(results['route_summary'].keys())[:5]
    top_routes_text = "\n".join([f"- {r}" for r in top_routes])

    system_prompt = """
You are the Risk Assessor Agent. You are an expert
in global supply chain risks including:
- Port congestion patterns
- Geopolitical risks by region
- Seasonal weather patterns affecting shipping
- Port capacity and infrastructure limits
Your job is to flag real risks on each route so
decision makers can plan accordingly.
"""

    user_prompt = f"""
ORCHESTRATOR BRIEFING:
{orchestrator}

ROUTE ANALYST RECOMMENDATION:
{route_analysis}

TOP ROUTES TO ASSESS:
{top_routes_text}

DISASTER: {results['disaster']} is closed

For each of the top 3 routes assess:
1. CONGESTION RISK
2. GEOPOLITICAL RISK
3. SEASONAL RISK
4. CAPACITY RISK
5. OVERALL RISK LEVEL — Low / Medium / High

End with: SAFEST ROUTE OVERALL and why.
Keep response under 300 words.
"""

    print("⚙️  Risk Assessor evaluating route dangers...")
    response = ask_ai(model, system_prompt, user_prompt)
    print(f"\n{response}")

    with open("data/agent3_risk_assessor.txt", "w", encoding="utf-8") as f:
        f.write(response)

    print("\n✅ Risk Assessor complete")
    return response


# ─────────────────────────────────────────
# AGENT 4 — PLAYBOOK WRITER
# ─────────────────────────────────────────

def agent_playbook_writer(model):

    print("\n" + "="*55)
    print("  📋 AGENT 4: PLAYBOOK WRITER")
    print(f"  Running on: {TIER} with {safe_model_name(model)}")
    print("="*55)

    results        = load_results()
    orchestrator   = open(
        "data/agent1_orchestrator.txt",  encoding="utf-8"
    ).read()
    route_analysis = open(
        "data/agent2_route_analyst.txt", encoding="utf-8"
    ).read()
    risk_report    = open(
        "data/agent3_risk_assessor.txt", encoding="utf-8"
    ).read()

    system_prompt = """
You are the Playbook Writer Agent. You are an expert
at turning complex logistics data into clear,
actionable emergency response plans.
You have received briefings from three specialist
agents. Synthesize everything into one clear
prescriptive playbook a logistics manager can
act on immediately.
Write clearly. Be specific. Use numbers.
"""

    user_prompt = f"""
ORCHESTRATOR ASSESSMENT:
{orchestrator}

ROUTE ANALYST FINDINGS:
{route_analysis}

RISK ASSESSOR WARNINGS:
{risk_report}

RAW SIMULATION DATA:
- Disaster    : {results['disaster']}
- Total runs  : {results['total_runs']}
- Best route  : {results['best_route']}
- Best days   : {results['best_avg_days']}
- Best cost   : ${results['best_avg_cost']}

Write a PRESCRIPTIVE RECOVERY PLAYBOOK with:
1. SITUATION SUMMARY
2. IMMEDIATE ACTIONS (Hours 1-24)
3. SHORT TERM ACTIONS (Days 2-7)
4. ROUTES RANKED (top 3 with pros/cons)
5. RISKS TO WATCH (top 3 with mitigation)
6. WHO TO NOTIFY (specific stakeholders)
7. SUCCESS METRICS (what numbers to watch)

Use actual route names and numbers throughout.
"""

    print("⚙️  Playbook Writer synthesizing all agent outputs...")
    response = ask_ai(model, system_prompt, user_prompt)
    print(f"\n{response}")

    with open("data/playbook.txt", "w", encoding="utf-8") as f:
        f.write("MULTI-AGENT SUPPLY CHAIN RECOVERY PLAYBOOK\n")
        f.write("="*55 + "\n\n")
        f.write(f"Disaster     : {results['disaster']}\n")
        f.write(f"Generated by : 4-Agent AI System ({model})\n")
        f.write(f"Hardware     : {TIER} — {HARDWARE['gpu']['gpu_name']}\n\n")
        f.write("="*55 + "\n\n")
        f.write(response)

    print("\n✅ Playbook Writer complete")
    return response


# ─────────────────────────────────────────
# HELPER — SAFE MODEL NAME
# ─────────────────────────────────────────

def safe_model_name(requested_model):
    """
    Returns the model that will actually run
    given hardware constraints.
    """
    if TIER in ["TIER_1", "TIER_2"]:
        if requested_model in ["mistral", "llama2", "llama3"]:
            return TIER_CONFIG[TIER]["recommended_model"] + " (auto-switched)"
    return requested_model


# ─────────────────────────────────────────
# MASTER FUNCTION — RUN ALL 4 AGENTS
# ─────────────────────────────────────────

def run_multi_agent_system(
    disaster_node,
    source,
    target,
    model = None
):
    # Auto select model if not specified
    if model is None or model == "auto":
        model = AUTO_MODEL
        print(f"\n🤖 Auto-selected model: {model} for {TIER}")

    print("\n" + "="*55)
    print("  🚀 MULTI-AGENT SYSTEM STARTING")
    print(f"  Disaster  : {disaster_node}")
    print(f"  Model     : {model}")
    print(f"  Hardware  : {TIER}")
    print(f"  GPU       : {HARDWARE['gpu']['gpu_name']}")
    print(f"  VRAM      : {HARDWARE['gpu']['vram_gb']} GB")
    print("="*55)

    start_time = time.time()

    orchestrator_output = agent_orchestrator(
        disaster_node, source, target, model
    )
    route_output        = agent_route_analyst(model)
    risk_output         = agent_risk_assessor(model)
    playbook_output     = agent_playbook_writer(model)

    elapsed = round(time.time() - start_time, 1)

    print("\n" + "="*55)
    print(f"  ✅ ALL 4 AGENTS COMPLETE in {elapsed}s")
    print(f"  Hardware used : {TIER}")
    print(f"  Model used    : {safe_model_name(model)}")
    print("="*55)

    # Save hardware info with results
    with open("data/hardware_config.json", "w") as f:
        json.dump(HARDWARE, f, indent=2)

    return {
        "orchestrator":  orchestrator_output,
        "route_analyst": route_output,
        "risk_assessor": risk_output,
        "playbook":      playbook_output,
        "time_taken":    elapsed,
        "hardware_tier": TIER,
        "model_used":    safe_model_name(model),
    }


# ─────────────────────────────────────────
# RUN IT
# ─────────────────────────────────────────

if __name__ == "__main__":

    print_hardware_report()

    results = run_multi_agent_system(
        disaster_node = "Shanghai_Port",
        source        = "Factory_Shanghai",
        target        = "Customer_NewYork",
        model         = "auto"
    )