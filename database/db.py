import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# ─────────────────────────────────────────
# 1. CONNECT TO SUPABASE
# ─────────────────────────────────────────

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ─────────────────────────────────────────
# 2. AUTH FUNCTIONS
# ─────────────────────────────────────────

def sign_up(email, password, full_name, company_name, industry):
    """
    Register a new user and create their
    company in one step.
    """
    try:
        # Step 1 — Create auth user
        auth_response = supabase.auth.sign_up({
            "email":    email,
            "password": password,
        })

        if not auth_response.user:
            return False, "Signup failed. Try again."

        user_id = auth_response.user.id

        # Step 2 — Create company
        company_response = supabase.table("companies").insert({
            "name":     company_name,
            "industry": industry,
        }).execute()

        company_id = company_response.data[0]["id"]

        # Step 3 — Create profile
        supabase.table("profiles").insert({
            "id":         user_id,
            "company_id": company_id,
            "full_name":  full_name,
            "role":       "admin",
        }).execute()

        return True, "Account created successfully."

    except Exception as e:
        return False, str(e)


def sign_in(email, password):
    """Log in an existing user."""
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email":    email,
            "password": password,
        })

        if not auth_response.user:
            return False, None, "Login failed."

        return True, auth_response, "Login successful."

    except Exception as e:
        return False, None, str(e)


def sign_out():
    """Log out current user."""
    try:
        supabase.auth.sign_out()
        return True
    except:
        return False


def get_current_user():
    """Get currently logged in user."""
    try:
        return supabase.auth.get_user()
    except:
        return None


# ─────────────────────────────────────────
# 3. COMPANY FUNCTIONS
# ─────────────────────────────────────────

def get_company(user_id):
    """Get company details for a user."""
    try:
        profile = supabase.table("profiles")\
            .select("*, companies(*)")\
            .eq("id", user_id)\
            .single()\
            .execute()

        return profile.data
    except:
        return None


# ─────────────────────────────────────────
# 4. SIMULATION HISTORY FUNCTIONS
# ─────────────────────────────────────────

def save_simulation(
    user_id,
    company_id,
    disaster_node,
    source_node,
    target_node,
    num_runs,
    results,
    playbook,
    ai_model,
    hardware_tier,
    normal_days = 0
):
    """Save a simulation run to the database."""
    try:
        delay = round(
            results["best_avg_days"] - normal_days, 1
        )

        data = {
            "company_id":    company_id,
            "user_id":       user_id,
            "disaster_node": disaster_node,
            "source_node":   source_node,
            "target_node":   target_node,
            "num_runs":      num_runs,
            "best_route":    results["best_route"],
            "best_avg_days": results["best_avg_days"],
            "best_avg_cost": results["best_avg_cost"],
            "normal_days":   normal_days,
            "delay_days":    delay,
            "ai_model":      ai_model,
            "hardware_tier": hardware_tier,
            "playbook":      playbook,
            "results_json":  results,
        }

        response = supabase.table("simulations")\
            .insert(data)\
            .execute()

        return True, response.data[0]["id"]

    except Exception as e:
        return False, str(e)


def get_simulation_history(company_id, limit=20):
    """
    Get past simulations for a company.
    Most recent first.
    """
    try:
        response = supabase.table("simulations")\
            .select("*")\
            .eq("company_id", company_id)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()

        return response.data

    except Exception as e:
        print(f"History fetch error: {e}")
        return []


def get_simulation_by_id(simulation_id):
    """Get a single simulation by ID."""
    try:
        response = supabase.table("simulations")\
            .select("*")\
            .eq("id", simulation_id)\
            .single()\
            .execute()

        return response.data

    except:
        return None


def get_company_stats(company_id):
    """
    Get aggregate stats for a company.
    Used for the cost savings calculator.
    """
    try:
        response = supabase.table("simulations")\
            .select("*")\
            .eq("company_id", company_id)\
            .execute()

        sims = response.data
        if not sims:
            return None

        total_sims  = len(sims)
        avg_delay   = round(
            sum(s["delay_days"] or 0 for s in sims) / total_sims, 1
        )
        avg_cost    = round(
            sum(s["best_avg_cost"] or 0 for s in sims) / total_sims
        )
        disasters   = list(set(s["disaster_node"] for s in sims))
        total_runs  = sum(s["num_runs"] or 0 for s in sims)

        return {
            "total_simulations": total_sims,
            "total_runs":        total_runs,
            "avg_delay_days":    avg_delay,
            "avg_recovery_cost": avg_cost,
            "disasters_tested":  disasters,
            "first_simulation":  sims[-1]["created_at"],
            "last_simulation":   sims[0]["created_at"],
        }

    except Exception as e:
        print(f"Stats error: {e}")
        return None


# ─────────────────────────────────────────
# 5. TEST CONNECTION
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("Testing Supabase connection...")

    try:
        response = supabase.table("companies")\
            .select("count")\
            .execute()
        print("✅ Connected to Supabase successfully")
        print("✅ Companies table accessible")

    except Exception as e:
        print(f"❌ Connection failed: {e}")