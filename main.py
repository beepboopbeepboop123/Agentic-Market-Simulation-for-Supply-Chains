from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

war_room_data = {
    "activeShipments": 142,
    "criticalAlerts": 3,
    "inventoryHealth": 94,
    "pendingOrders": 28,
    "aiInsight": "System initializing...",
    "requiresAction": False
}

@app.get("/api/dashboard")
def get_dashboard_data():
    # 1. Update the base numbers
    war_room_data["activeShipments"] += random.randint(-2, 2)
    war_room_data["pendingOrders"] += random.randint(-1, 1)
    
    war_room_data["inventoryHealth"] += random.randint(-1, 1)
    war_room_data["inventoryHealth"] = max(80, min(100, war_room_data["inventoryHealth"]))

    if random.random() > 0.9:
        war_room_data["criticalAlerts"] += 1
    elif war_room_data["criticalAlerts"] > 0 and random.random() > 0.8:
        war_room_data["criticalAlerts"] -= 1

    # 2. THE NEW AI INSIGHT ENGINE
    # Calculate a simple risk score: if orders outpace inventory health by too much
    risk_score = (war_room_data["pendingOrders"] / max(1, war_room_data["inventoryHealth"])) * 100
    
    if risk_score > 35 or war_room_data["criticalAlerts"] > 4:
        war_room_data["aiInsight"] = "High bottleneck probability. Recommend rerouting incoming shipments to secondary warehouses."
        war_room_data["requiresAction"] = True
    elif war_room_data["inventoryHealth"] < 85:
        war_room_data["aiInsight"] = "Inventory dipping below optimal threshold. Prepare automated re-order protocols."
        war_room_data["requiresAction"] = True
    else:
        war_room_data["aiInsight"] = "Supply chain operating within optimal parameters. No immediate action required."
        war_room_data["requiresAction"] = False

    return war_room_data