import json
import time
import os
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from agents.ai_provider import ask_ai, get_available_providers

# ─────────────────────────────────────────
# SHOW PROVIDER STATUS AT STARTUP
# ─────────────────────────────────────────

print("\n🔌 AI Provider System")
for p, status in get_available_providers().items():
    print(f"   {status} — {p}")


# ─────────────────────────────────────────
# LOAD SIMULATION RESULTS
# ─────────────────────────────────────────

def load_results():
    with open("data/results.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────
# AGENT 1 — ORCHESTRATOR
# ─────────────────────────────────────────

def agent_orchestrator(disaster_node, source, target):

    print("\n" + "="*55)
    print("  🧠 AGENT 1: ORCHESTRATOR")
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
    response, provider = ask_ai(
        "orchestrator", system_prompt, user_prompt
    )
    print(f"\n{response}")

    with open("data/agent1_orchestrator.txt", "w", encoding="utf-8") as f:
        f.write(response)

    print(f"\n✅ Orchestrator complete (via {provider})")
    return response


# ─────────────────────────────────────────
# AGENT 2 — ROUTE ANALYST
# ─────────────────────────────────────────

def agent_route_analyst():

    print("\n" + "="*55)
    print("  📊 AGENT 2: ROUTE ANALYST")
    print("="*55)

    results      = load_results()
    orchestrator = open(
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
2. SPEED vs COST TRADEOFF — which is fastest, cheapest?
3. RELIABILITY SCORE — most consistent across simulations?
4. YOUR RECOMMENDATION — one clear route with reasoning

Be specific. Use route names and actual numbers.
Keep response under 300 words.
"""

    print("⚙️  Route Analyst ranking all surviving routes...")
    response, provider = ask_ai(
        "route_analyst", system_prompt, user_prompt
    )
    print(f"\n{response}")

    with open("data/agent2_route_analyst.txt", "w", encoding="utf-8") as f:
        f.write(response)

    print(f"\n✅ Route Analyst complete (via {provider})")
    return response


# ─────────────────────────────────────────
# AGENT 3 — RISK ASSESSOR
# ─────────────────────────────────────────

def agent_risk_assessor():

    print("\n" + "="*55)
    print("  ⚠️  AGENT 3: RISK ASSESSOR")
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
    response, provider = ask_ai(
        "risk_assessor", system_prompt, user_prompt
    )
    print(f"\n{response}")

    with open("data/agent3_risk_assessor.txt", "w", encoding="utf-8") as f:
        f.write(response)

    print(f"\n✅ Risk Assessor complete (via {provider})")
    return response


# ─────────────────────────────────────────
# AGENT 4 — PLAYBOOK WRITER
# ─────────────────────────────────────────

def agent_playbook_writer():

    print("\n" + "="*55)
    print("  📋 AGENT 4: PLAYBOOK WRITER")
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
    response, provider = ask_ai(
        "playbook_writer", system_prompt, user_prompt
    )
    print(f"\n{response}")

    with open("data/playbook.txt", "w", encoding="utf-8") as f:
        f.write("MULTI-AGENT SUPPLY CHAIN RECOVERY PLAYBOOK\n")
        f.write("="*55 + "\n\n")
        f.write(f"Disaster     : {results['disaster']}\n")
        f.write(f"Generated by : 4-Agent AI System\n\n")
        f.write("="*55 + "\n\n")
        f.write(response)

    print(f"\n✅ Playbook Writer complete (via {provider})")
    return response


# ─────────────────────────────────────────
# MASTER FUNCTION — RUN ALL 4 AGENTS
# ─────────────────────────────────────────

def run_multi_agent_system(
    disaster_node,
    source,
    target,
    model = None
):
    print("\n" + "="*55)
    print("  🚀 MULTI-AGENT SYSTEM STARTING")
    print(f"  Disaster  : {disaster_node}")
    print(f"  Providers : Groq + Gemini + Mistral")
    print("="*55)

    start_time = time.time()

    orchestrator_output = agent_orchestrator(
        disaster_node, source, target
    )
    route_output        = agent_route_analyst()
    risk_output         = agent_risk_assessor()
    playbook_output     = agent_playbook_writer()

    elapsed = round(time.time() - start_time, 1)

    print("\n" + "="*55)
    print(f"  ✅ ALL 4 AGENTS COMPLETE in {elapsed}s")
    print("="*55)

    return {
        "orchestrator":  orchestrator_output,
        "route_analyst": route_output,
        "risk_assessor": risk_output,
        "playbook":      playbook_output,
        "time_taken":    elapsed,
        "model_used":    "multi-provider",
    }


# ─────────────────────────────────────────
# RUN IT
# ─────────────────────────────────────────

if __name__ == "__main__":
    results = run_multi_agent_system(
        disaster_node = "Shanghai_Port",
        source        = "Factory_Shanghai",
        target        = "Customer_NewYork",
    )