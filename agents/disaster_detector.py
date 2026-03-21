import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

# ─────────────────────────────────────────
# 1. PORT LOCATIONS TO MONITOR
# ─────────────────────────────────────────
# These are the real ports we watch for
# dangerous weather conditions

MONITORED_PORTS = {
    "Shanghai_Port":     {"lat": 31.2304,  "lon": 121.5000, "country": "China"},
    "Singapore_Port":    {"lat": 1.2655,   "lon": 103.8200, "country": "Singapore"},
    "Busan_Port":        {"lat": 35.1028,  "lon": 129.0400, "country": "South Korea"},
    "Los_Angeles_Port":  {"lat": 33.7395,  "lon": -118.262, "country": "USA"},
    "Long_Beach_Port":   {"lat": 33.7542,  "lon": -118.216, "country": "USA"},
    "Rotterdam_Port":    {"lat": 51.9225,  "lon": 4.4792,   "country": "Netherlands"},
    "Hamburg_Port":      {"lat": 53.5753,  "lon": 9.9200,   "country": "Germany"},
    "Houston_Port":      {"lat": 29.7283,  "lon": -95.000,  "country": "USA"},
    "New_York_Port":     {"lat": 40.6840,  "lon": -74.044,  "country": "USA"},
    "Mumbai_Port":       {"lat": 18.9300,  "lon": 72.8400,  "country": "India"},
    "Jebel_Ali":         {"lat": 25.0118,  "lon": 55.0694,  "country": "UAE"},
    "Port_Said":         {"lat": 31.2565,  "lon": 32.2841,  "country": "Egypt"},
}

# ─────────────────────────────────────────
# 2. RISK THRESHOLDS
# What weather conditions count as dangerous
# ─────────────────────────────────────────

RISK_THRESHOLDS = {
    "wind_speed_ms":    15,    # metres/second (54 km/h = strong gale)
    "visibility_m":     1000,  # metres (below 1km = dangerous for ships)
    "rain_1h_mm":       50,    # mm per hour (heavy rain)
    "snow_1h_mm":       10,    # mm per hour (heavy snow)
}

DANGEROUS_CONDITIONS = [
    "Thunderstorm",
    "Tornado",
    "Hurricane",
    "Tropical Storm",
    "Blizzard",
    "Heavy Snow",
    "Dense Fog",
]


# ─────────────────────────────────────────
# 3. FETCH WEATHER FOR ONE PORT
# ─────────────────────────────────────────

def get_port_weather(port_name, lat, lon):
    """
    Fetch current weather for a port location
    using OpenWeatherMap API.
    """
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}"
        f"&appid={API_KEY}"
        f"&units=metric"
    )

    try:
        response = requests.get(url, timeout=10)
        data     = response.json()

        if response.status_code != 200:
            return None

        weather = {
            "port":        port_name,
            "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M"),
            "condition":   data["weather"][0]["main"],
            "description": data["weather"][0]["description"],
            "temp_c":      round(data["main"]["temp"], 1),
            "wind_ms":     round(data["wind"]["speed"], 1),
            "wind_kmh":    round(data["wind"]["speed"] * 3.6, 1),
            "humidity":    data["main"]["humidity"],
            "visibility_m":data.get("visibility", 10000),
            "rain_1h":     data.get("rain", {}).get("1h", 0),
            "snow_1h":     data.get("snow", {}).get("1h", 0),
        }

        return weather

    except Exception as e:
        print(f"  ⚠️  Could not fetch weather for {port_name}: {e}")
        return None


# ─────────────────────────────────────────
# 4. ASSESS RISK FOR ONE PORT
# ─────────────────────────────────────────

def assess_risk(weather):
    """
    Given weather data for a port,
    return risk level and reasons.
    """
    if not weather:
        return "UNKNOWN", []

    risks  = []
    level  = "LOW"

    # Check wind speed
    if weather["wind_ms"] >= RISK_THRESHOLDS["wind_speed_ms"]:
        risks.append(
            f"High winds: {weather['wind_kmh']} km/h "
            f"(threshold: {RISK_THRESHOLDS['wind_speed_ms']*3.6} km/h)"
        )
        level = "HIGH"

    # Check visibility
    if weather["visibility_m"] < RISK_THRESHOLDS["visibility_m"]:
        risks.append(
            f"Low visibility: {weather['visibility_m']}m "
            f"(threshold: {RISK_THRESHOLDS['visibility_m']}m)"
        )
        level = "HIGH"

    # Check rain
    if weather["rain_1h"] >= RISK_THRESHOLDS["rain_1h_mm"]:
        risks.append(
            f"Heavy rain: {weather['rain_1h']}mm/hr"
        )
        level = "HIGH" if level != "HIGH" else "HIGH"

    # Check snow
    if weather["snow_1h"] >= RISK_THRESHOLDS["snow_1h_mm"]:
        risks.append(
            f"Heavy snow: {weather['snow_1h']}mm/hr"
        )
        level = "HIGH"

    # Check dangerous conditions
    for condition in DANGEROUS_CONDITIONS:
        if condition.lower() in weather["condition"].lower():
            risks.append(f"Dangerous condition: {weather['condition']}")
            level = "CRITICAL"
            break

    # Medium risk — elevated wind or rain
    if not risks:
        if weather["wind_ms"] >= 10:
            risks.append(
                f"Elevated winds: {weather['wind_kmh']} km/h"
            )
            level = "MEDIUM"
        elif weather["rain_1h"] > 0:
            risks.append(
                f"Light rain: {weather['rain_1h']}mm/hr"
            )
            level = "LOW"

    return level, risks


# ─────────────────────────────────────────
# 5. SCAN ALL PORTS
# ─────────────────────────────────────────

def scan_all_ports():
    """
    Check weather at every monitored port.
    Return a full report and list of
    at-risk ports.
    """

    print("\n" + "="*55)
    print("  🌍 SCANNING ALL PORTS FOR WEATHER RISKS")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*55 + "\n")

    all_weather  = {}
    at_risk      = []
    critical     = []

    for port_name, coords in MONITORED_PORTS.items():

        weather = get_port_weather(
            port_name,
            coords["lat"],
            coords["lon"]
        )

        if not weather:
            continue

        risk_level, risk_reasons = assess_risk(weather)
        weather["risk_level"]    = risk_level
        weather["risk_reasons"]  = risk_reasons
        all_weather[port_name]   = weather

        # Print status
        emoji = {
            "LOW":      "🟢",
            "MEDIUM":   "🟡",
            "HIGH":     "🔴",
            "CRITICAL": "🚨",
            "UNKNOWN":  "⚪"
        }.get(risk_level, "⚪")

        print(f"{emoji} {port_name}")
        print(f"   Condition : {weather['condition']} — {weather['description']}")
        print(f"   Wind      : {weather['wind_kmh']} km/h")
        print(f"   Temp      : {weather['temp_c']}°C")
        print(f"   Risk      : {risk_level}")
        if risk_reasons:
            for r in risk_reasons:
                print(f"   ⚠️  {r}")
        print()

        if risk_level in ["HIGH", "CRITICAL"]:
            at_risk.append(port_name)
        if risk_level == "CRITICAL":
            critical.append(port_name)

    # ── Summary ───────────────────────────
    print("="*55)
    print(f"  📊 SCAN COMPLETE")
    print(f"  Total ports scanned : {len(all_weather)}")
    print(f"  At-risk ports       : {len(at_risk)}")
    print(f"  Critical ports      : {len(critical)}")

    if critical:
        print(f"\n  🚨 CRITICAL ALERTS:")
        for p in critical:
            print(f"     → {p}")
    elif at_risk:
        print(f"\n  🔴 HIGH RISK PORTS:")
        for p in at_risk:
            print(f"     → {p}")
    else:
        print(f"\n  ✅ No severe weather detected")

    print("="*55)

    # ── Save results ──────────────────────
    output = {
        "timestamp":   datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ports":       all_weather,
        "at_risk":     at_risk,
        "critical":    critical,
        "total_scanned": len(all_weather)
    }

    with open("data/weather_report.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Weather report saved to data/weather_report.json")

    return output


# ─────────────────────────────────────────
# 6. AUTO TRIGGER CHECK
# Call this to check if simulation should
# be triggered automatically
# ─────────────────────────────────────────

def check_auto_trigger():
    """
    Returns a list of ports that should
    trigger an automatic simulation
    due to dangerous weather.
    """
    report = scan_all_ports()

    triggers = []

    for port in report["at_risk"]:
        triggers.append({
            "port":   port,
            "reason": report["ports"][port]["risk_reasons"],
            "level":  report["ports"][port]["risk_level"],
        })

    return triggers


# ─────────────────────────────────────────
# 7. RUN IT
# ─────────────────────────────────────────

if __name__ == "__main__":
    triggers = check_auto_trigger()

    if triggers:
        print(f"\n🚨 AUTO-TRIGGER: {len(triggers)} port(s) need simulation")
        for t in triggers:
            print(f"   → {t['port']} ({t['level']})")
            for r in t['reason']:
                print(f"     {r}")
    else:
        print("\n✅ No ports need auto-triggered simulation right now")