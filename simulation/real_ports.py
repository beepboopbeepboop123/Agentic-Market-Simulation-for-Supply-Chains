import networkx as nx
from geopy.distance import geodesic
import json

# ─────────────────────────────────────────
# 1. REAL WORLD NODES WITH COORDINATES
# ─────────────────────────────────────────

REAL_PORTS = {

    # ── RAW MATERIAL SUPPLIERS ────────────
    "RawMaterial_Australia":    {"lat": -33.8688, "lon": 151.2093, "type": "raw_supplier",  "country": "Australia",    "product": "iron_ore",      "capacity": 10000},
    "RawMaterial_Brazil":       {"lat": -19.9191, "lon": -43.9386, "type": "raw_supplier",  "country": "Brazil",       "product": "iron_ore",      "capacity": 8000},
    "RawMaterial_Chile":        {"lat": -33.4569, "lon": -70.6483, "type": "raw_supplier",  "country": "Chile",        "product": "copper",        "capacity": 6000},
    "RawMaterial_DRCongo":      {"lat": -4.3217,  "lon": 15.3222,  "type": "raw_supplier",  "country": "DR Congo",     "product": "cobalt",        "capacity": 5000},

    # ── PRIMARY FACTORIES ─────────────────
    "Factory_Shanghai":         {"lat": 31.2304,  "lon": 121.4737, "type": "factory",       "country": "China",        "product": "electronics",   "capacity": 8000,  "backup_for": []},
    "Factory_Shenzhen":         {"lat": 22.5431,  "lon": 114.0579, "type": "factory",       "country": "China",        "product": "electronics",   "capacity": 7000,  "backup_for": ["Factory_Shanghai"]},
    "Factory_Guangzhou":        {"lat": 23.1291,  "lon": 113.2644, "type": "factory",       "country": "China",        "product": "electronics",   "capacity": 6000,  "backup_for": ["Factory_Shanghai"]},

    # ── BACKUP FACTORIES ──────────────────
    "Factory_Vietnam":          {"lat": 10.8231,  "lon": 106.6297, "type": "factory",       "country": "Vietnam",      "product": "electronics",   "capacity": 5000,  "backup_for": ["Factory_Shanghai", "Factory_Shenzhen"]},
    "Factory_India_Chennai":    {"lat": 13.0827,  "lon": 80.2707,  "type": "factory",       "country": "India",        "product": "electronics",   "capacity": 4000,  "backup_for": ["Factory_Shanghai"]},
    "Factory_India_Mumbai":     {"lat": 19.0760,  "lon": 72.8777,  "type": "factory",       "country": "India",        "product": "textiles",      "capacity": 5000,  "backup_for": []},
    "Factory_Bangladesh":       {"lat": 23.8103,  "lon": 90.4125,  "type": "factory",       "country": "Bangladesh",   "product": "textiles",      "capacity": 4000,  "backup_for": ["Factory_India_Mumbai"]},
    "Factory_Mexico":           {"lat": 19.4326,  "lon": -99.1332, "type": "factory",       "country": "Mexico",       "product": "auto_parts",    "capacity": 5000,  "backup_for": []},
    "Factory_EasternEurope":    {"lat": 52.2297,  "lon": 21.0122,  "type": "factory",       "country": "Poland",       "product": "auto_parts",    "capacity": 4000,  "backup_for": ["Factory_Mexico"]},
    "Factory_Malaysia":         {"lat": 3.1390,   "lon": 101.6869, "type": "factory",       "country": "Malaysia",     "product": "electronics",   "capacity": 4500,  "backup_for": ["Factory_Vietnam"]},
    "Factory_Indonesia":        {"lat": -6.2088,  "lon": 106.8456, "type": "factory",       "country": "Indonesia",    "product": "textiles",      "capacity": 3500,  "backup_for": ["Factory_Bangladesh"]},

    # ── ASIAN PORTS ───────────────────────
    "Shanghai_Port":            {"lat": 31.2304,  "lon": 121.5000, "type": "port",          "country": "China"},
    "Shenzhen_Yantian":         {"lat": 22.5600,  "lon": 114.2700, "type": "port",          "country": "China"},
    "Hong_Kong_Port":           {"lat": 22.3193,  "lon": 114.1694, "type": "port",          "country": "China"},
    "Singapore_Port":           {"lat": 1.2655,   "lon": 103.8200, "type": "port",          "country": "Singapore"},
    "Busan_Port":               {"lat": 35.1028,  "lon": 129.0400, "type": "port",          "country": "South Korea"},
    "Port_Klang":               {"lat": 3.0000,   "lon": 101.4000, "type": "port",          "country": "Malaysia"},
    "Colombo_Port":             {"lat": 6.9271,   "lon": 79.8612,  "type": "port",          "country": "Sri Lanka"},
    "Mumbai_Port":              {"lat": 18.9300,  "lon": 72.8400,  "type": "port",          "country": "India"},
    "Chennai_Port":             {"lat": 13.0827,  "lon": 80.2707,  "type": "port",          "country": "India"},
    "Jakarta_Port":             {"lat": -6.1751,  "lon": 106.8650, "type": "port",          "country": "Indonesia"},
    "Ho_Chi_Minh_Port":         {"lat": 10.7769,  "lon": 106.7009, "type": "port",          "country": "Vietnam"},

    # ── MIDDLE EASTERN PORTS ──────────────
    "Jebel_Ali":                {"lat": 25.0118,  "lon": 55.0694,  "type": "port",          "country": "UAE"},
    "Port_Said":                {"lat": 31.2565,  "lon": 32.2841,  "type": "port",          "country": "Egypt"},

    # ── EUROPEAN PORTS ────────────────────
    "Rotterdam_Port":           {"lat": 51.9225,  "lon": 4.4792,   "type": "port",          "country": "Netherlands"},
    "Hamburg_Port":             {"lat": 53.5753,  "lon": 9.9200,   "type": "port",          "country": "Germany"},
    "Felixstowe_Port":          {"lat": 51.9539,  "lon": 1.3518,   "type": "port",          "country": "UK"},

    # ── US WEST COAST PORTS ───────────────
    "Los_Angeles_Port":         {"lat": 33.7395,  "lon": -118.2620,"type": "port",          "country": "USA"},
    "Long_Beach_Port":          {"lat": 33.7542,  "lon": -118.2165,"type": "port",          "country": "USA"},
    "Seattle_Port":             {"lat": 47.6062,  "lon": -122.3321,"type": "port",          "country": "USA"},

    # ── US EAST COAST PORTS ───────────────
    "New_York_Port":            {"lat": 40.6840,  "lon": -74.0440, "type": "port",          "country": "USA"},
    "Houston_Port":             {"lat": 29.7283,  "lon": -95.0000, "type": "port",          "country": "USA"},
    "Savannah_Port":            {"lat": 32.0835,  "lon": -81.0998, "type": "port",          "country": "USA"},

    # ── AIR FREIGHT HUBS ─────────────────
    "AirHub_HongKong":          {"lat": 22.3080,  "lon": 113.9185, "type": "air_hub",       "country": "China",        "speed_multiplier": 0.1,   "cost_multiplier": 8.0},
    "AirHub_Dubai":             {"lat": 25.2528,  "lon": 55.3644,  "type": "air_hub",       "country": "UAE",          "speed_multiplier": 0.1,   "cost_multiplier": 8.0},
    "AirHub_Frankfurt":         {"lat": 50.0379,  "lon": 8.5622,   "type": "air_hub",       "country": "Germany",      "speed_multiplier": 0.1,   "cost_multiplier": 8.0},
    "AirHub_Chicago":           {"lat": 41.9742,  "lon": -87.9073, "type": "air_hub",       "country": "USA",          "speed_multiplier": 0.1,   "cost_multiplier": 8.0},

    # ── REGIONAL WAREHOUSES ───────────────
    "Warehouse_LA":             {"lat": 34.0522,  "lon": -118.2437,"type": "warehouse",     "country": "USA",          "capacity": 50000},
    "Warehouse_Chicago":        {"lat": 41.8781,  "lon": -87.6298, "type": "warehouse",     "country": "USA",          "capacity": 40000},
    "Warehouse_NewYork":        {"lat": 40.7128,  "lon": -74.0060, "type": "warehouse",     "country": "USA",          "capacity": 45000},
    "Warehouse_Houston":        {"lat": 29.7604,  "lon": -95.3698, "type": "warehouse",     "country": "USA",          "capacity": 35000},
    "Warehouse_Rotterdam":      {"lat": 51.9000,  "lon": 4.4500,   "type": "warehouse",     "country": "Netherlands",  "capacity": 60000},
    "Warehouse_Singapore":      {"lat": 1.3521,   "lon": 103.8198, "type": "warehouse",     "country": "Singapore",    "capacity": 40000},
    "Warehouse_Dubai":          {"lat": 25.2048,  "lon": 55.2708,  "type": "warehouse",     "country": "UAE",          "capacity": 35000},

    # ── DISTRIBUTION CENTERS ─────────────
    "DC_Dallas":                {"lat": 32.7767,  "lon": -96.7970, "type": "distribution",  "country": "USA"},
    "DC_Atlanta":               {"lat": 33.7490,  "lon": -84.3880, "type": "distribution",  "country": "USA"},
    "DC_London":                {"lat": 51.5074,  "lon": -0.1278,  "type": "distribution",  "country": "UK"},
    "DC_Paris":                 {"lat": 48.8566,  "lon": 2.3522,   "type": "distribution",  "country": "France"},

    # ── CUSTOMERS ─────────────────────────
    "Customer_NewYork":         {"lat": 40.7128,  "lon": -74.0060, "type": "customer",      "country": "USA"},
    "Customer_Chicago":         {"lat": 41.8781,  "lon": -87.6298, "type": "customer",      "country": "USA"},
    "Customer_LA":              {"lat": 34.0522,  "lon": -118.2437,"type": "customer",      "country": "USA"},
    "Customer_London":          {"lat": 51.5074,  "lon": -0.1278,  "type": "customer",      "country": "UK"},
    "Customer_Paris":           {"lat": 48.8566,  "lon": 2.3522,   "type": "customer",      "country": "France"},
    "Customer_Dubai":           {"lat": 25.2048,  "lon": 55.2708,  "type": "customer",      "country": "UAE"},
}


# ─────────────────────────────────────────
# 2. REAL ROUTES
# ─────────────────────────────────────────

REAL_ROUTES = [

    # ── Raw Materials → Factories ─────────
    ("RawMaterial_Australia",   "Factory_Shanghai"),
    ("RawMaterial_Australia",   "Factory_Shenzhen"),
    ("RawMaterial_Brazil",      "Factory_Shanghai"),
    ("RawMaterial_Chile",       "Factory_Mexico"),
    ("RawMaterial_DRCongo",     "Factory_EasternEurope"),

    # ── Primary Factories → Ports ─────────
    ("Factory_Shanghai",        "Shanghai_Port"),
    ("Factory_Shanghai",        "Busan_Port"),
    ("Factory_Shanghai",        "AirHub_HongKong"),
    ("Factory_Shenzhen",        "Shenzhen_Yantian"),
    ("Factory_Shenzhen",        "Hong_Kong_Port"),
    ("Factory_Shenzhen",        "AirHub_HongKong"),
    ("Factory_Guangzhou",       "Hong_Kong_Port"),
    ("Factory_Guangzhou",       "Shanghai_Port"),

    # ── Backup Factories → Ports ──────────
    ("Factory_Vietnam",         "Ho_Chi_Minh_Port"),
    ("Factory_Vietnam",         "Singapore_Port"),
    ("Factory_Vietnam",         "AirHub_HongKong"),
    ("Factory_India_Chennai",   "Chennai_Port"),
    ("Factory_India_Chennai",   "Colombo_Port"),
    ("Factory_India_Mumbai",    "Mumbai_Port"),
    ("Factory_Bangladesh",      "Colombo_Port"),
    ("Factory_Bangladesh",      "Singapore_Port"),
    ("Factory_Malaysia",        "Port_Klang"),
    ("Factory_Malaysia",        "Singapore_Port"),
    ("Factory_Indonesia",       "Jakarta_Port"),
    ("Factory_Indonesia",       "Singapore_Port"),
    ("Factory_Mexico",          "Houston_Port"),
    ("Factory_Mexico",          "Los_Angeles_Port"),
    ("Factory_EasternEurope",   "Hamburg_Port"),
    ("Factory_EasternEurope",   "Rotterdam_Port"),

    # ── Trans-Pacific (Asia → US West) ────
    ("Shanghai_Port",           "Los_Angeles_Port"),
    ("Shanghai_Port",           "Long_Beach_Port"),
    ("Shanghai_Port",           "Seattle_Port"),
    ("Shenzhen_Yantian",        "Los_Angeles_Port"),
    ("Shenzhen_Yantian",        "Long_Beach_Port"),
    ("Hong_Kong_Port",          "Los_Angeles_Port"),
    ("Hong_Kong_Port",          "Long_Beach_Port"),
    ("Busan_Port",              "Los_Angeles_Port"),
    ("Busan_Port",              "Long_Beach_Port"),
    ("Busan_Port",              "Seattle_Port"),
    ("Singapore_Port",          "Los_Angeles_Port"),
    ("Port_Klang",              "Los_Angeles_Port"),
    ("Ho_Chi_Minh_Port",        "Los_Angeles_Port"),
    ("Jakarta_Port",            "Los_Angeles_Port"),

    # ── Asia → US East Coast ─────────────
    ("Shanghai_Port",           "New_York_Port"),
    ("Shanghai_Port",           "Houston_Port"),
    ("Busan_Port",              "New_York_Port"),
    ("Singapore_Port",          "New_York_Port"),
    ("Singapore_Port",          "Houston_Port"),
    ("Shenzhen_Yantian",        "New_York_Port"),
    ("Hong_Kong_Port",          "New_York_Port"),
    ("Ho_Chi_Minh_Port",        "New_York_Port"),

    # ── Asia → Europe (via Suez) ──────────
    ("Shanghai_Port",           "Singapore_Port"),
    ("Busan_Port",              "Singapore_Port"),
    ("Singapore_Port",          "Colombo_Port"),
    ("Ho_Chi_Minh_Port",        "Colombo_Port"),
    ("Colombo_Port",            "Jebel_Ali"),
    ("Mumbai_Port",             "Jebel_Ali"),
    ("Chennai_Port",            "Jebel_Ali"),
    ("Jebel_Ali",               "Port_Said"),
    ("Port_Said",               "Rotterdam_Port"),
    ("Port_Said",               "Felixstowe_Port"),
    ("Rotterdam_Port",          "Hamburg_Port"),
    ("Rotterdam_Port",          "Felixstowe_Port"),

    # ── Air Freight Routes ────────────────
    ("AirHub_HongKong",         "AirHub_Chicago"),
    ("AirHub_HongKong",         "AirHub_Frankfurt"),
    ("AirHub_HongKong",         "AirHub_Dubai"),
    ("AirHub_Dubai",            "AirHub_Chicago"),
    ("AirHub_Frankfurt",        "AirHub_Chicago"),

    # ── US West Coast → Warehouses ────────
    ("Los_Angeles_Port",        "Warehouse_LA"),
    ("Long_Beach_Port",         "Warehouse_LA"),
    ("Seattle_Port",            "Warehouse_Chicago"),

    # ── US East/Gulf → Warehouses ─────────
    ("New_York_Port",           "Warehouse_NewYork"),
    ("Houston_Port",            "Warehouse_Houston"),
    ("Savannah_Port",           "Warehouse_Chicago"),

    # ── Europe → Warehouses ───────────────
    ("Rotterdam_Port",          "Warehouse_Rotterdam"),
    ("Hamburg_Port",            "Warehouse_Rotterdam"),
    ("Felixstowe_Port",         "DC_London"),
    ("Jebel_Ali",               "Warehouse_Dubai"),

    # ── Air Hubs → Warehouses ────────────
    ("AirHub_Chicago",          "Warehouse_Chicago"),
    ("AirHub_Frankfurt",        "Warehouse_Rotterdam"),
    ("AirHub_Dubai",            "Warehouse_Dubai"),

    # ── Singapore Regional Hub ────────────
    ("Singapore_Port",          "Warehouse_Singapore"),
    ("Warehouse_Singapore",     "Warehouse_LA"),

    # ── Warehouse → Distribution ──────────
    ("Warehouse_LA",            "DC_Dallas"),
    ("Warehouse_LA",            "DC_Atlanta"),
    ("Warehouse_Chicago",       "Warehouse_NewYork"),
    ("Warehouse_Houston",       "Warehouse_Chicago"),
    ("Warehouse_Rotterdam",     "DC_London"),
    ("Warehouse_Rotterdam",     "DC_Paris"),

    # ── Distribution → Customers ──────────
    ("Warehouse_NewYork",       "Customer_NewYork"),
    ("Warehouse_Chicago",       "Customer_Chicago"),
    ("Warehouse_LA",            "Customer_LA"),
    ("DC_Dallas",               "Customer_Chicago"),
    ("DC_Atlanta",              "Customer_NewYork"),
    ("DC_London",               "Customer_London"),
    ("DC_Paris",                "Customer_Paris"),
    ("Warehouse_Rotterdam",     "Customer_London"),
    ("Warehouse_Rotterdam",     "Customer_Paris"),
    ("Warehouse_Dubai",         "Customer_Dubai"),
    ("Jebel_Ali",               "Customer_Dubai"),
]


# ─────────────────────────────────────────
# 3. TRANSIT TIME AND COST CALCULATION
# ─────────────────────────────────────────

SHIP_SPEED_KNOTS    = 14
KNOTS_TO_KMH        = 1.852
PORT_HANDLING_DAYS  = 1

# Type-specific speed and cost multipliers
TYPE_MULTIPLIERS = {
    "air_hub":      {"speed": 0.08, "cost": 9.0},
    "factory":      {"speed": 1.0,  "cost": 0.5},
    "raw_supplier": {"speed": 1.0,  "cost": 0.3},
    "port":         {"speed": 1.0,  "cost": 1.0},
    "warehouse":    {"speed": 1.2,  "cost": 0.2},
    "distribution": {"speed": 1.0,  "cost": 0.3},
    "customer":     {"speed": 1.0,  "cost": 0.2},
}


def calculate_transit_days(node_a, node_b):
    coord_a = (REAL_PORTS[node_a]["lat"], REAL_PORTS[node_a]["lon"])
    coord_b = (REAL_PORTS[node_b]["lat"], REAL_PORTS[node_b]["lon"])

    distance_km  = geodesic(coord_a, coord_b).kilometers

    # Use air speed if either node is an air hub
    type_a = REAL_PORTS[node_a]["type"]
    type_b = REAL_PORTS[node_b]["type"]

    if type_a == "air_hub" or type_b == "air_hub":
        speed_mult   = 0.08
        transit_days = (distance_km / 900) / 24
    else:
        speed_kmh    = SHIP_SPEED_KNOTS * KNOTS_TO_KMH
        transit_days = (distance_km / speed_kmh) / 24

    total_days = round(transit_days + PORT_HANDLING_DAYS, 1)
    return total_days, round(distance_km)


def calculate_cost(distance_km, node_a, node_b):
    type_a     = REAL_PORTS[node_a]["type"]
    type_b     = REAL_PORTS[node_b]["type"]

    # Air freight costs much more
    if type_a == "air_hub" or type_b == "air_hub":
        return round(distance_km * 1.2)
    else:
        return round(distance_km * 0.12)


# ─────────────────────────────────────────
# 4. BUILD THE GRAPH
# ─────────────────────────────────────────

def build_real_supply_chain():
    graph = nx.DiGraph()

    for node, attrs in REAL_PORTS.items():
        graph.add_node(node, **attrs)

    for from_node, to_node in REAL_ROUTES:
        days, distance = calculate_transit_days(from_node, to_node)
        cost           = calculate_cost(distance, from_node, to_node)
        graph.add_edge(
            from_node, to_node,
            days     = days,
            cost     = cost,
            distance = distance
        )

    return graph


# ─────────────────────────────────────────
# 5. FIND BACKUP SUPPLIERS
# This is the new key function
# ─────────────────────────────────────────

def find_backup_suppliers(graph, closed_node):
    """
    If a factory closes find all other factories
    that can produce the same product and are
    not affected by the disruption.
    """
    if closed_node not in REAL_PORTS:
        return []

    closed_info = REAL_PORTS.get(closed_node, {})
    if closed_info.get("type") not in ["factory", "raw_supplier"]:
        return []

    closed_product = closed_info.get("product", "unknown")

    backups = []
    for node, attrs in REAL_PORTS.items():
        if node == closed_node:
            continue
        if attrs["type"] not in ["factory", "raw_supplier"]:
            continue
        if attrs.get("product") != closed_product:
            continue
        if node not in graph.nodes():
            continue

        backups.append({
            "node":        node,
            "country":     attrs["country"],
            "capacity":    attrs.get("capacity", 0),
            "product":     attrs.get("product", "unknown"),
            "backup_for":  attrs.get("backup_for", []),
            "is_designated": closed_node in attrs.get("backup_for", [])
        })

    # Sort by designated backups first then by capacity
    backups.sort(
        key=lambda x: (not x["is_designated"], -x["capacity"])
    )

    return backups


# ─────────────────────────────────────────
# 6. TEST IT
# ─────────────────────────────────────────

if __name__ == "__main__":

    print("Building real supply chain graph...")
    graph = build_real_supply_chain()

    print(f"\n✅ Total nodes    : {graph.number_of_nodes()}")
    print(f"✅ Total routes   : {graph.number_of_edges()}")

    # Count by type
    type_counts = {}
    for node, attrs in REAL_PORTS.items():
        t = attrs["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    print(f"\n📊 Node breakdown:")
    for t, count in sorted(type_counts.items()):
        print(f"   {t:20} : {count}")

    print(f"\n📦 SAMPLE TRANSIT TIMES:")
    samples = [
        ("Shanghai_Port",       "Los_Angeles_Port"),
        ("Factory_Vietnam",     "Ho_Chi_Minh_Port"),
        ("AirHub_HongKong",     "AirHub_Chicago"),
        ("Factory_Mexico",      "Houston_Port"),
        ("Rotterdam_Port",      "Hamburg_Port"),
    ]
    for a, b in samples:
        if graph.has_edge(a, b):
            d = graph[a][b]
            print(f"   {a} → {b}")
            print(f"   {d['distance']:,} km | {d['days']} days | ${d['cost']:,}")
            print()

    # Test backup supplier finder
    print("🔄 BACKUP SUPPLIER TEST:")
    print("   If Factory_Shanghai closes...")
    backups = find_backup_suppliers(graph, "Factory_Shanghai")
    for b in backups:
        tag = " ← DESIGNATED BACKUP" if b["is_designated"] else ""
        print(f"   → {b['node']} ({b['country']}) capacity:{b['capacity']}{tag}")

    # Save port data
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

    print(f"\n✅ Port data saved to data/ports.json")