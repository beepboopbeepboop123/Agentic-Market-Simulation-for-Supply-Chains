import networkx as nx

# ─────────────────────────────────────────
# 1. BUILD THE SUPPLY CHAIN MAP
# ─────────────────────────────────────────

supply_chain = nx.DiGraph()

# --- NODES ---
nodes = {
    "Supplier_China":       {"type": "supplier"},
    "Supplier_Vietnam":     {"type": "supplier"},
    "Supplier_India":       {"type": "supplier"},

    "Shanghai_Port":        {"type": "port"},
    "Singapore_Port":       {"type": "port"},
    "Mumbai_Port":          {"type": "port"},

    "LA_Port":              {"type": "port"},
    "Houston_Port":         {"type": "port"},

    "Warehouse_California": {"type": "warehouse"},
    "Warehouse_Texas":      {"type": "warehouse"},

    "Customer_NewYork":     {"type": "customer"},
    "Customer_Chicago":     {"type": "customer"},
}

for node, attrs in nodes.items():
    supply_chain.add_node(node, **attrs)

# --- EDGES (From, To, days, cost) ---
routes = [
    ("Supplier_China",       "Shanghai_Port",        2,  500),
    ("Supplier_China",       "Singapore_Port",        4,  600),
    ("Supplier_Vietnam",     "Singapore_Port",        3,  400),
    ("Supplier_India",       "Mumbai_Port",           2,  300),

    ("Shanghai_Port",        "LA_Port",              14, 2000),
    ("Shanghai_Port",        "Houston_Port",         18, 2200),
    ("Singapore_Port",       "LA_Port",              16, 1800),
    ("Singapore_Port",       "Houston_Port",         20, 2000),
    ("Mumbai_Port",          "Houston_Port",         22, 1900),

    ("LA_Port",              "Warehouse_California",  1,  200),
    ("LA_Port",              "Warehouse_Texas",       3,  400),
    ("Houston_Port",         "Warehouse_Texas",       1,  150),

    ("Warehouse_California", "Customer_NewYork",      5,  500),
    ("Warehouse_California", "Customer_Chicago",      4,  450),
    ("Warehouse_Texas",      "Customer_NewYork",      3,  350),
    ("Warehouse_Texas",      "Customer_Chicago",      2,  250),
]

for from_node, to_node, days, cost in routes:
    supply_chain.add_edge(from_node, to_node, days=days, cost=cost)


# ─────────────────────────────────────────
# 2. HELPER FUNCTIONS
# ─────────────────────────────────────────

def get_total_days(path):
    total = 0
    for i in range(len(path) - 1):
        total += supply_chain[path[i]][path[i+1]]['days']
    return total

def get_total_cost(path):
    total = 0
    for i in range(len(path) - 1):
        total += supply_chain[path[i]][path[i+1]]['cost']
    return total

def find_all_paths(source, target):
    try:
        return list(nx.all_simple_paths(supply_chain, source, target))
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
    paths_before = find_all_paths(source, target)
    print(f"\n✅ Routes BEFORE disaster: {len(paths_before)}")
    for p in paths_before:
        print(f"   {'→'.join(p)}")
        print(f"   {get_total_days(p)} days | ${get_total_cost(p)}")

    # Remove the disaster node
    temp_graph = supply_chain.copy()
    temp_graph.remove_node(closed_node)

    # Paths AFTER disaster
    try:
        paths_after = list(nx.all_simple_paths(temp_graph, source, target))
    except:
        paths_after = []

    print(f"\n❌ Routes AFTER disaster: {len(paths_after)}")

    if not paths_after:
        print("   ⚠️  NO ROUTES AVAILABLE. Complete breakdown.")
        return

    for p in paths_after:
        days = sum(temp_graph[p[i]][p[i+1]]['days'] for i in range(len(p)-1))
        cost = sum(temp_graph[p[i]][p[i+1]]['cost'] for i in range(len(p)-1))
        print(f"   {'→'.join(p)}")
        print(f"   {days} days | ${cost}")

    # Best recovery route
    best = min(paths_after, key=lambda p: sum(
        temp_graph[p[i]][p[i+1]]['days'] for i in range(len(p)-1)
    ))
    best_days = sum(temp_graph[best[i]][best[i+1]]['days'] for i in range(len(best)-1))
    best_cost = sum(temp_graph[best[i]][best[i+1]]['cost'] for i in range(len(best)-1))

    print(f"\n🏆 BEST RECOVERY ROUTE:")
    print(f"   {'→'.join(best)}")
    print(f"   {best_days} days | ${best_cost}")


# ─────────────────────────────────────────
# 4. RUN IT
# ─────────────────────────────────────────

if __name__ == "__main__":
    simulate_disruption(
        closed_node = "Shanghai_Port",
        source      = "Supplier_China",
        target      = "Customer_NewYork"
    )

import random
import json

# ─────────────────────────────────────────
# 5. MONTE CARLO STRESS TEST
# ─────────────────────────────────────────

def run_monte_carlo(closed_node, source, target, runs=1000):

    print(f"\n{'='*55}")
    print(f"  STRESS TEST: Running {runs} simulations...")
    print(f"  Disaster: {closed_node} closed")
    print(f"{'='*55}\n")

    # Remove the disaster node once
    temp_graph = supply_chain.copy()
    temp_graph.remove_node(closed_node)

    # Find all surviving paths
    try:
        surviving_paths = list(nx.all_simple_paths(temp_graph, source, target))
    except:
        surviving_paths = []

    if not surviving_paths:
        print("⚠️  No routes survive this disaster.")
        return

    # Track results across all runs
    route_scores = {}
    all_results  = []

    for run in range(runs):

        # Pick a random surviving path
        path = random.choice(surviving_paths)
        path_key = " → ".join(path)

        # Add random congestion delay (0 to 7 extra days)
        congestion = random.randint(0, 7)

        # Calculate days and cost with congestion
        base_days = sum(
            temp_graph[path[i]][path[i+1]]['days']
            for i in range(len(path)-1)
        )
        base_cost = sum(
            temp_graph[path[i]][path[i+1]]['cost']
            for i in range(len(path)-1)
        )

        total_days = base_days + congestion
        total_cost = base_cost + (congestion * 100)

        # Store result
        all_results.append({
            "run":        run + 1,
            "path":       path_key,
            "days":       total_days,
            "cost":       total_cost,
            "congestion": congestion
        })

        # Track how many times each route was best
        if path_key not in route_scores:
            route_scores[path_key] = {
                "times_chosen": 0,
                "total_days":   0,
                "total_cost":   0
            }

        route_scores[path_key]["times_chosen"] += 1
        route_scores[path_key]["total_days"]   += total_days
        route_scores[path_key]["total_cost"]   += total_cost

    # ── Summary ──────────────────────────────
    print("📊 RESULTS ACROSS 1000 RUNS:\n")

    for route, stats in route_scores.items():
        count    = stats["times_chosen"]
        avg_days = stats["total_days"] / count
        avg_cost = stats["total_cost"] / count
        success  = round((count / runs) * 100, 1)

        print(f"  Route : {route}")
        print(f"  Chosen: {count} times ({success}%)")
        print(f"  Avg   : {avg_days:.1f} days | ${avg_cost:.0f}")
        print()

    # ── Best Route Overall ────────────────────
    best_route = min(
        route_scores.items(),
        key=lambda x: x[1]["total_days"] / x[1]["times_chosen"]
    )

    best_name     = best_route[0]
    best_avg_days = best_route[1]["total_days"] / best_route[1]["times_chosen"]
    best_avg_cost = best_route[1]["total_cost"] / best_route[1]["times_chosen"]

    print(f"🏆 BEST ROUTE ACROSS ALL 1000 SIMULATIONS:")
    print(f"   {best_name}")
    print(f"   Average: {best_avg_days:.1f} days | ${best_avg_cost:.0f}")

    # ── Save to JSON ──────────────────────────
    output = {
        "disaster":       closed_node,
        "source":         source,
        "target":         target,
        "total_runs":     runs,
        "route_summary":  {
            route: {
                "times_chosen": stats["times_chosen"],
                "success_rate": f"{round((stats['times_chosen']/runs)*100, 1)}%",
                "avg_days":     round(stats["total_days"] / stats["times_chosen"], 1),
                "avg_cost":     round(stats["total_cost"] / stats["times_chosen"], 1)
            }
            for route, stats in route_scores.items()
        },
        "best_route":     best_name,
        "best_avg_days":  round(best_avg_days, 1),
        "best_avg_cost":  round(best_avg_cost, 1),
        "all_runs":       all_results
    }

    with open("data/results.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Full results saved to data/results.json")


# ─────────────────────────────────────────
# 6. RUN BOTH
# ─────────────────────────────────────────

if __name__ == "__main__":

    # Single disruption check
    simulate_disruption(
        closed_node = "Shanghai_Port",
        source      = "Supplier_China",
        target      = "Customer_NewYork"
    )

    # 1000 run stress test
    run_monte_carlo(
        closed_node = "Shanghai_Port",
        source      = "Supplier_China",
        target      = "Customer_NewYork",
        runs        = 1000
    )