import json
import ollama
import time

# ─────────────────────────────────────────
# MULTI-AGENT SYSTEM
# 4 specialized agents working together
# ─────────────────────────────────────────


# ─────────────────────────────────────────
# HELPER — CALL LOCAL AI
# ─────────────────────────────────────────

def ask_ai(model, system_prompt, user_prompt):
    """Send a prompt to Ollama and get response."""
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ]
    )
    return response['message']['content']


# ─────────────────────────────────────────
# LOAD SIMULATION RESULTS
# ─────────────────────────────────────────

def load_results():
    with open("data/results.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────
# AGENT 1 — ORCHESTRATOR
# Reads the disaster, understands the
# situation, delegates to other agents
# ─────────────────────────────────────────

def agent_orchestrator(disaster_node, source, target, model):

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
    response = ask_ai(model, system_prompt, user_prompt)
    print(f"\n{response}")

    # Save output
    with open("data/agent1_orchestrator.txt", "w", encoding="utf-8") as f:
        f.write(response)

    print("\n✅ Orchestrator complete")
    return response


# ─────────────────────────────────────────
# AGENT 2 — ROUTE ANALYST
# Deeply analyzes every surviving route
# Scores and ranks them
# ─────────────────────────────────────────

def agent_route_analyst(model):

    print("\n" + "="*55)
    print("  📊 AGENT 2: ROUTE ANALYST")
    print("="*55)

    results        = load_results()
    orchestrator   = open("data/agent1_orchestrator.txt", encoding="utf-8").read()

    # Format all routes for analysis
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
   1000 simulations, which route is most consistent?
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
# Flags risks on each surviving route
# Warns about congestion, geopolitics,
# seasonal issues
# ─────────────────────────────────────────

def agent_risk_assessor(model):

    print("\n" + "="*55)
    print("  ⚠️  AGENT 3: RISK ASSESSOR")
    print("="*55)

    results      = load_results()
    orchestrator = open("data/agent1_orchestrator.txt", encoding="utf-8").read()
    route_analysis = open("data/agent2_route_analyst.txt", encoding="utf-8").read()

    # Get top routes for risk assessment
    top_routes = list(results['route_summary'].keys())[:5]
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

For each of the top 3 routes, assess:
1. CONGESTION RISK — is this port/route known
   for congestion? When is it worst?
2. GEOPOLITICAL RISK — any political tensions
   along this route?
3. SEASONAL RISK — weather or seasonal patterns
   that could affect this route?
4. CAPACITY RISK — can the alternative ports
   handle the redirected volume?
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
# Reads all 3 agent outputs
# Writes the final recovery playbook
# ─────────────────────────────────────────

def agent_playbook_writer(model):

    print("\n" + "="*55)
    print("  📋 AGENT 4: PLAYBOOK WRITER")
    print("="*55)

    results        = load_results()
    orchestrator   = open("data/agent1_orchestrator.txt",  encoding="utf-8").read()
    route_analysis = open("data/agent2_route_analyst.txt", encoding="utf-8").read()
    risk_report    = open("data/agent3_risk_assessor.txt", encoding="utf-8").read()

    system_prompt = """
You are the Playbook Writer Agent. You are an expert
at turning complex logistics data into clear,
actionable emergency response plans.
You have received briefings from three specialist
agents. Your job is to synthesize everything into
one clear prescriptive playbook that a logistics
manager can act on immediately.
Write clearly. Be specific. Use numbers.
Structure your output with clear sections.
"""

    user_prompt = f"""
You have received the following expert briefings:

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
   What happened, how bad is it, how long to recover

2. IMMEDIATE ACTIONS (Hours 1-24)
   Exact steps, who does what, which route to activate

3. SHORT TERM ACTIONS (Days 2-7)
   Monitoring, adjustments, backup plans

4. ROUTES RANKED
   Top 3 routes with pros cons and risk level

5. RISKS TO WATCH
   Top 3 risks from the risk assessor with
   mitigation strategy for each

6. WHO TO NOTIFY
   Specific stakeholders, what to tell each one,
   in what order

7. SUCCESS METRICS
   How will you know the recovery is working?
   What numbers to watch?

Be specific. Use actual route names and numbers.
This playbook will be used by real decision makers.
"""

    print("⚙️  Playbook Writer synthesizing all agent outputs...")
    response = ask_ai(model, system_prompt, user_prompt)
    print(f"\n{response}")

    # Save final playbook
    with open("data/playbook.txt", "w", encoding="utf-8") as f:
        f.write("MULTI-AGENT SUPPLY CHAIN RECOVERY PLAYBOOK\n")
        f.write("="*55 + "\n\n")
        f.write(f"Disaster : {results['disaster']}\n")
        f.write(f"Generated by: 4-Agent AI System ({model})\n\n")
        f.write("="*55 + "\n\n")
        f.write(response)

    print("\n✅ Playbook Writer complete")
    return response


# ─────────────────────────────────────────
# MASTER FUNCTION — RUN ALL 4 AGENTS
# ─────────────────────────────────────────

def run_multi_agent_system(
    disaster_node,
    source,
    target,
    model = "mistral"
):

    print("\n" + "="*55)
    print("  🚀 MULTI-AGENT SYSTEM STARTING")
    print(f"  Disaster : {disaster_node}")
    print(f"  Model    : {model}")
    print("="*55)

    start_time = time.time()

    # Run all 4 agents in sequence
    # Each agent reads the previous agent's output
    orchestrator_output  = agent_orchestrator(
        disaster_node, source, target, model
    )
    route_output         = agent_route_analyst(model)
    risk_output          = agent_risk_assessor(model)
    playbook_output      = agent_playbook_writer(model)

    elapsed = round(time.time() - start_time, 1)

    print("\n" + "="*55)
    print(f"  ✅ ALL 4 AGENTS COMPLETE in {elapsed}s")
    print("="*55)

    return {
        "orchestrator":   orchestrator_output,
        "route_analyst":  route_output,
        "risk_assessor":  risk_output,
        "playbook":       playbook_output,
        "time_taken":     elapsed
    }


# ─────────────────────────────────────────
# RUN IT
# ─────────────────────────────────────────

if __name__ == "__main__":

    # Make sure simulation has been run first
    results = run_multi_agent_system(
        disaster_node = "Shanghai_Port",
        source        = "Factory_Shanghai",
        target        = "Customer_NewYork",
        model         = "mistral"
    )