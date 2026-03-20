import networkx as nx
from geopy.distance import geodesic
import json

# ─────────────────────────────────────────
# 1. REAL WORLD PORTS WITH COORDINATES
# ─────────────────────────────────────────

REAL_PORTS = {
    # SUPPLIERS
    "Factory_Shanghai":     {"lat": 31.2304,  "lon": 121.4737, "type": "supplier",  "country": "China"},
    "Factory_Shenzhen":     {"lat": 22.5431,  "lon": 114.0579, "type": "supplier",  "country": "China"},
    "Factory_Ho_Chi_Minh":  {"lat": 10.8231,  "lon": 106.6297, "type": "supplier",  "country": "Vietnam"},
    "Factory_Mumbai":       {"lat": 19.0760,  "lon": 72.8777,  "type": "supplier",  "country": "India"},

    # ASIAN PORTS
    "Shanghai_Port":        {"lat": 31.2304,  "lon": 121.5000, "type": "port",      "country": "China"},
    "Shenzhen_Yantian":     {"lat": 22.5600,  "lon": 114.2700, "type": "port",      "country": "China"},
    "Hong_Kong_Port":       {"lat": 22.3193,  "lon": 114.1694, "type": "port",      "country": "China"},
    "Singapore_Port":       {"lat": 1.2655,   "lon": 103.8200, "type": "port",      "country": "Singapore"},
    "Busan_Port":           {"lat": 35.1028,  "lon": 129.0400, "type": "port",      "country": "South Korea"},
    "Port_Klang":           {"lat": 3.0000,   "lon": 101.4000, "type": "port",      "country": "Malaysia"},
    "Colombo_Port":         {"lat": 6.9271,   "lon": 79.8612,  "type": "port",      "country": "Sri Lanka"},
    "Mumbai_Port":          {"lat": 18.9300,  "lon": 72.8400,  "type": "port",      "country": "India"},

    # MIDDLE EASTERN PORTS
    "Jebel_Ali":            {"lat": 25.0118,  "lon": 55.0694,  "type": "port",      "country": "UAE"},
    "Port_Said":            {"lat": 31.2565,  "lon": 32.2841,  "type": "port",      "country": "Egypt"},

    # EUROPEAN PORTS
    "Rotterdam_Port":       {"lat": 51.9225,  "lon": 4.4792,   "type": "port",      "country": "Netherlands"},
    "Hamburg_Port":         {"lat": 53.5753,  "lon": 9.9200,   "type": "port",      "country": "Germany"},

    # US WEST COAST
    "Los_Angeles_Port":     {"lat": 33.7395,  "lon": -118.2620,"type": "port",      "country": "USA"},
    "Long_Beach_Port":      {"lat": 33.7542,  "lon": -118.2165,"type": "port",      "country": "USA"},
    "Seattle_Port":         {"lat": 47.6062,  "lon": -122.3321,"type": "port",      "country": "USA"},

    # US EAST COAST
    "New_York_Port":        {"lat": 40.6840,  "lon": -74.0440, "type": "port",      "country": "USA"},
    "Houston_Port":         {"lat": 29.7283,  "lon": -95.0000, "type": "port",      "country": "USA"},
    "Savannah_Port":        {"lat": 32.0835,  "lon": -81.0998, "type": "port",      "country": "USA"},

    # WAREHOUSES
    "Warehouse_LA":         {"lat": 34.0522,  "lon": -118.2437,"type": "warehouse", "country": "USA"},
    "Warehouse_Chicago":    {"lat": 41.8781,  "lon": -87.6298, "type": "warehouse", "country": "USA"},
    "Warehouse_NewYork":    {"lat": 40.7128,  "lon": -74.0060, "type": "warehouse", "country": "USA"},
    "Warehouse_Houston":    {"lat": 29.7604,  "lon": -95.3698, "type": "warehouse", "country": "USA"},

    # CUSTOMERS
    "Customer_NewYork":     {"lat": 40.7128,  "lon": -74.0060, "type": "customer",  "country": "USA"},
    "Customer_Chicago":     {"lat": 41.8781,  "lon": -87.6298, "type": "customer",  "country": "USA"},
    "Customer_LA":          {"lat": 34.0522,  "lon": -118.2437,"type": "customer",  "country": "USA"},
    "Customer_London":      {"lat": 51.5074,  "lon": -0.1278,  "type": "customer",  "country": "UK"},
}


# ─────────────────────────────────────────
# 2. REAL ROUTES
# ─────────────────────────────────────────

REAL_ROUTES = [
    # Factory → Multiple Asian Ports
    ("Factory_Shanghai",    "Shanghai_Port"),
    ("Factory_Shanghai",    "Busan_Port"),
    ("Factory_Shanghai",    "Shenzhen_Yantian"),
    ("Factory_Shenzhen",    "Shenzhen_Yantian"),
    ("Factory_Shenzhen",    "Hong_Kong_Port"),
    ("Factory_Ho_Chi_Minh", "Singapore_Port"),
    ("Factory_Ho_Chi_Minh", "Port_Klang"),
    ("Factory_Mumbai",      "Mumbai_Port"),
    ("Factory_Mumbai",      "Colombo_Port"),

    # Trans-Pacific (Asia → US West Coast)
    ("Shanghai_Port",       "Los_Angeles_Port"),
    ("Shanghai_Port",       "Long_Beach_Port"),
    ("Shanghai_Port",       "Seattle_Port"),
    ("Shenzhen_Yantian",    "Los_Angeles_Port"),
    ("Shenzhen_Yantian",    "Long_Beach_Port"),
    ("Busan_Port",          "Los_Angeles_Port"),
    ("Busan_Port",          "Long_Beach_Port"),
    ("Busan_Port",          "Seattle_Port"),
    ("Singapore_Port",      "Los_Angeles_Port"),
    ("Port_Klang",          "Los_Angeles_Port"),
    ("Hong_Kong_Port",      "Los_Angeles_Port"),
    ("Hong_Kong_Port",      "Long_Beach_Port"),

    # Asia → US East Coast
    ("Shanghai_Port",       "New_York_Port"),
    ("Shanghai_Port",       "Houston_Port"),
    ("Busan_Port",          "New_York_Port"),
    ("Singapore_Port",      "New_York_Port"),
    ("Singapore_Port",      "Houston_Port"),
    ("Shenzhen_Yantian",    "New_York_Port"),
    ("Hong_Kong_Port",      "New_York_Port"),

    # Asia → Europe via Suez
    ("Shanghai_Port",       "Singapore_Port"),
    ("Busan_Port",          "Singapore_Port"),
    ("Singapore_Port",      "Colombo_Port"),
    ("Colombo_Port",        "Jebel_Ali"),
    ("Jebel_Ali",           "Port_Said"),
    ("Port_Said",           "Rotterdam_Port"),
    ("Rotterdam_Port",      "Hamburg_Port"),

    # US West Coast → Warehouses
    ("Los_Angeles_Port",    "Warehouse_LA"),
    ("Long_Beach_Port",     "Warehouse_LA"),
    ("Seattle_Port",        "Warehouse_Chicago"),

    # US East/Gulf → Warehouses
    ("New_York_Port",       "Warehouse_NewYork"),
    ("Houston_Port",        "Warehouse_Houston"),
    ("Savannah_Port",       "Warehouse_Chicago"),

    # Warehouse → Warehouse inland
    ("Warehouse_LA",        "Warehouse_Chicago"),
    ("Warehouse_Chicago",   "Warehouse_NewYork"),
    ("Warehouse_Houston",   "Warehouse_Chicago"),

    # Warehouses → Customers
    ("Warehouse_LA",        "Customer_LA"),
    ("Warehouse_LA",        "Customer_Chicago"),
    ("Warehouse_NewYork",   "Customer_NewYork"),
    ("Warehouse_NewYork",   "Customer_Chicago"),
    ("Warehouse_Chicago",   "Customer_Chicago"),
    ("Warehouse_Chicago",   "Customer_NewYork"),
    ("Warehouse_Houston",   "Customer_Chicago"),

    # Europe → Customers
    ("Rotterdam_Port",      "Customer_London"),
    ("Hamburg_Port",        "Customer_London"),
]


# ─────────────────────────────────────────
# 3. CALCULATE TRANSIT TIME AND COST
# ─────────────────────────────────────────

SHIP_SPEED_KNOTS   = 14
KNOTS_TO_KMH       = 1.852
PORT_HANDLING_DAYS = 1

def calculate_transit_days(port_a, port_b):
    coord_a      = (REAL_PORTS[port_a]["lat"], REAL_PORTS[port_a]["lon"])
    coord_b      = (REAL_PORTS[port_b]["lat"], REAL_PORTS[port_b]["lon"])
    distance_km  = geodesic(coord_a, coord_b).kilometers
    speed_kmh    = SHIP_SPEED_KNOTS * KNOTS_TO_KMH
    transit_days = (distance_km / speed_kmh) / 24
    total_days   = round(transit_days + PORT_HANDLING_DAYS, 1)
    return total_days, round(distance_km)

def calculate_cost(distance_km):
    return round(distance_km * 0.12)


# ─────────────────────────────────────────
# 4. BUILD THE GRAPH
# ─────────────────────────────────────────

def build_real_supply_chain():

    graph = nx.DiGraph()

    for port, attrs in REAL_PORTS.items():
        graph.add_node(port, **attrs)

    for from_port, to_port in REAL_ROUTES:
        days, distance = calculate_transit_days(from_port, to_port)
        cost           = calculate_cost(distance)
        graph.add_edge(
            from_port, to_port,
            days     = days,
            cost     = cost,
            distance = distance
        )

    return graph


# ─────────────────────────────────────────
# 5. TEST IT
# ─────────────────────────────────────────

if __name__ == "__main__":

    print("Building real supply chain graph...")
    graph = build_real_supply_chain()

    print(f"\n✅ Total ports/locations : {graph.number_of_nodes()}")
    print(f"✅ Total shipping routes : {graph.number_of_edges()}")

    print("\n📦 SAMPLE REAL TRANSIT TIMES:")
    sample_routes = [
        ("Shanghai_Port",  "Los_Angeles_Port"),
        ("Singapore_Port", "Rotterdam_Port"),
        ("Shanghai_Port",  "New_York_Port"),
        ("Colombo_Port",   "Jebel_Ali"),
        ("Rotterdam_Port", "Hamburg_Port"),
    ]

    for a, b in sample_routes:
        if graph.has_edge(a, b):
            days = graph[a][b]['days']
            dist = graph[a][b]['distance']
            cost = graph[a][b]['cost']
            print(f"  {a} → {b}")
            print(f"  {dist:,} km | {days} days | ${cost:,}")
            print()

    port_data = {
        port: {
            "lat":     attrs["lat"],
            "lon":     attrs["lon"],
            "type":    attrs["type"],
            "country": attrs["country"]
        }
        for port, attrs in REAL_PORTS.items()
    }

    with open("data/ports.json", "w") as f:
        json.dump(port_data, f, indent=2)

    print("✅ Port coordinates saved to data/ports.json")