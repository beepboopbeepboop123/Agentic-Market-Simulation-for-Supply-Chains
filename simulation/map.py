import networkx as nx
import random
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simulation.real_ports import build_real_supply_chain, REAL_PORTS

# ─────────────────────────────────────────
# 1. BUILD SUPPLY CHAIN FROM REAL DATA
# ─────────────────────────────────────────

supply_chain = build_real_supply_chain()


# ─────────────────────────────────────────
# 2. HELPER FUNCTIONS
# ─────────────────────────────────────────

def get_total_days(graph, path):
    total = 0
    for i in range(len(path) - 1):
        total += graph[path[i]][path[i+1]]['days']
    return round(total, 1)

def get_total_cost(graph, path):
    total = 0
    for i in range(len(path) - 1):
        total += graph[path[i]][path[i+1]]['cost']
    return total

def find_all_paths(graph, source, target):
    try:
        return list(nx.all_simple_paths(graph, source, target, cutoff=8))
    except:
        return []


# ─────────────────────────────────────────
# 3. SIMULATE A DISASTER
# ─────────────────────────────────────────

def simulate_disruption(closed_node, source, target):

    print(f"\n{'='*55}")
    print(f"  DISASTER: {closed_node} is CLOSED")
    print(f"{'='*55}")

    # Paths BEFORE disaster
    paths_before = find_all_paths(supply_chain, source, target)
    print(f"\n✅ Routes BEFORE disaster: {len(paths_before)}")
    for p in paths_before:
        print(f"   {'→'.join(p)}")
        print(f"   {get_total_days(supply_chain, p)} days | ${get_total_cost(supply_chain, p):,}")

    # Remove the disaster node
    temp_graph = supply_chain.copy()
    temp_graph.remove_node(closed_node)

    # Paths AFTER disaster
    paths_after = find_all_paths(temp_graph, source, target)
    print(f"\n❌ Routes AFTER disaster: {len(paths_after)}")

    if not paths_after:
        print("   ⚠️  NO ROUTES AVAILABLE. Complete breakdown.")
        return

    for p in paths_after:
        print(f"   {'→'.join(p)}")
        print(f"   {get_total_days(temp_graph, p)} days | ${get_total_cost(temp_graph, p):,}")

    # Best recovery route
    best = min(paths_after, key=lambda p: get_total_days(temp_graph, p))

    print(f"\n🏆 BEST RECOVERY ROUTE:")
    print(f"   {'→'.join(best)}")
    print(f"   {get_total_days(temp_graph, best)} days | ${get_total_cost(temp_graph, best):,}")


# ─────────────────────────────────────────
# 4. MONTE CARLO STRESS TEST
# ─────────────────────────────────────────

def run_monte_carlo(closed_node, source, target, runs=1000):

    print(f"\n{'='*55}")
    print(f"  STRESS TEST: Running {runs} simulations...")
    print(f"  Disaster: {closed_node} closed")
    print(f"{'='*55}\n")

    # Remove disaster node once
    temp_graph = supply_chain.copy()
    temp_graph.remove_node(closed_node)

    # Find all surviving paths
    surviving_paths = find_all_paths(temp_graph, source, target)

    if not surviving_paths:
        print("⚠️  No routes survive this disaster.")
        return

    route_scores = {}
    all_results  = []

    for run in range(runs):

        path        = random.choice(surviving_paths)
        path_key    = " → ".join(path)
        congestion  = random.uniform(0, 5)  # 0-5 days random delay

        base_days   = get_total_days(temp_graph, path)
        base_cost   = get_total_cost(temp_graph, path)
        total_days  = round(base_days + congestion, 1)
        total_cost  = round(base_cost + (congestion * 150))

        all_results.append({
            "run":        run + 1,
            "path":       path_key,
            "days":       total_days,
            "cost":       total_cost,
            "congestion": round(congestion, 1)
        })

        if path_key not in route_scores:
            route_scores[path_key] = {
                "times_chosen": 0,
                "total_days":   0,
                "total_cost":   0
            }

        route_scores[path_key]["times_chosen"] += 1
        route_scores[path_key]["total_days"]   += total_days
        route_scores[path_key]["total_cost"]   += total_cost

    # Summary
    print("📊 RESULTS ACROSS ALL RUNS:\n")
    for route, stats in route_scores.items():
        count    = stats["times_chosen"]
        avg_days = round(stats["total_days"] / count, 1)
        avg_cost = round(stats["total_cost"] / count)
        success  = round((count / runs) * 100, 1)
        print(f"  Route : {route}")
        print(f"  Chosen: {count} times ({success}%)")
        print(f"  Avg   : {avg_days} days | ${avg_cost:,}")
        print()

    # Best route
    best_route = min(
        route_scores.items(),
        key=lambda x: x[1]["total_days"] / x[1]["times_chosen"]
    )

    best_name     = best_route[0]
    best_avg_days = round(best_route[1]["total_days"] / best_route[1]["times_chosen"], 1)
    best_avg_cost = round(best_route[1]["total_cost"] / best_route[1]["times_chosen"])

    print(f"🏆 BEST ROUTE ACROSS ALL {runs} SIMULATIONS:")
    print(f"   {best_name}")
    print(f"   Average: {best_avg_days} days | ${best_avg_cost:,}")

    # Save results
    output = {
        "disaster":      closed_node,
        "source":        source,
        "target":        target,
        "total_runs":    runs,
        "route_summary": {
            route: {
                "times_chosen": stats["times_chosen"],
                "success_rate": f"{round((stats['times_chosen']/runs)*100, 1)}%",
                "avg_days":     round(stats["total_days"] / stats["times_chosen"], 1),
                "avg_cost":     round(stats["total_cost"] / stats["times_chosen"])
            }
            for route, stats in route_scores.items()
        },
        "best_route":     best_name,
        "best_avg_days":  best_avg_days,
        "best_avg_cost":  best_avg_cost,
        "all_runs":       all_results
    }

    with open("data/results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Results saved to data/results.json")
    return output


# ─────────────────────────────────────────
# 5. RUN IT
# ─────────────────────────────────────────

if __name__ == "__main__":

    simulate_disruption(
        closed_node = "Shanghai_Port",
        source      = "Factory_Shanghai",
        target      = "Customer_NewYork"
    )

    run_monte_carlo(
        closed_node = "Shanghai_Port",
        source      = "Factory_Shanghai",
        target      = "Customer_NewYork",
        runs        = 1000
    )