import networkx as nx
import random
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simulation.real_ports import build_real_supply_chain

# Build the base graph
supply_chain = build_real_supply_chain()

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

def run_monte_carlo(closed_node, source, target, runs=1000):
    # Remove disaster node
    temp_graph = supply_chain.copy()
    if closed_node in temp_graph:
        temp_graph.remove_node(closed_node)

    surviving_paths = find_all_paths(temp_graph, source, target)

    if not surviving_paths:
        return None # No routes survive

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

    # Find the best route based on average days
    best_route = min(
        route_scores.items(),
        key=lambda x: x[1]["total_days"] / x[1]["times_chosen"]
    )

    best_name     = best_route[0]
    best_avg_days = round(best_route[1]["total_days"] / best_route[1]["times_chosen"], 1)
    best_avg_cost = round(best_route[1]["total_cost"] / best_route[1]["times_chosen"])

    # Format the output for the API and frontend
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
        "best_route":    best_name,
        "best_avg_days": best_avg_days,
        "best_avg_cost": best_avg_cost,
    }

    # Save to file just in case it's needed locally
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "data"), exist_ok=True)
    with open(os.path.join(os.path.dirname(__file__), "..", "data", "results.json"), "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    return output