import os
import time
import re
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
# API KEYS
# ─────────────────────────────────────────

GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MISTRAL_API_KEY= os.getenv("MISTRAL_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


# ─────────────────────────────────────────
# PROVIDER CONFIGS
# ─────────────────────────────────────────

PROVIDERS = {
    "groq_70b": {
        "name":       "Groq Llama 3.3 70B",
        "provider":   "groq",
        "model":      "llama-3.3-70b-versatile",
        "max_tokens": 2000,
        "best_for":   "speed, delegation, structured tasks",
    },
    "groq_8b": {
        "name":       "Groq Llama 3.1 8B",
        "provider":   "groq",
        "model":      "llama-3.1-8b-instant",
        "max_tokens": 1000,
        "best_for":   "fallback, fast simple tasks",
    },
    "gemini_flash": {
        "name":       "Gemini 2.5 Flash",
        "provider":   "gemini",
        "model":      "gemini-2.5-flash",
        "max_tokens": 2000,
        "best_for":   "structured data, numerical analysis",
    },
    "mistral": {
        "name":       "Mistral Small",
        "provider":   "mistral",
        "model":      "mistral-small-latest",
        "max_tokens": 2000,
        "best_for":   "risk analysis, reasoning",
    },
    "deepseek_r1": {
        "name":       "DeepSeek R1",
        "provider":   "deepseek",
        "model":      "deepseek-reasoner",
        "max_tokens": 2000,
        "best_for":   "chain of thought reasoning",
    },
    "deepseek_v3": {
        "name":       "DeepSeek V3",
        "provider":   "deepseek",
        "model":      "deepseek-chat",
        "max_tokens": 2000,
        "best_for":   "long form writing",
    },
}


# ─────────────────────────────────────────
# AGENT ASSIGNMENTS
# ─────────────────────────────────────────

AGENT_PROVIDERS = {
    "orchestrator":    "groq_70b",
    "route_analyst":   "gemini_flash",
    "risk_assessor":   "mistral",
    "playbook_writer": "groq_70b",
    "fallback":        "groq_8b",
}

FALLBACK_CHAINS = {
    "orchestrator":    ["groq_70b",     "gemini_flash", "mistral",  "groq_8b"],
    "route_analyst":   ["gemini_flash", "groq_70b",     "mistral",  "groq_8b"],
    "risk_assessor":   ["mistral",      "gemini_flash", "groq_70b", "groq_8b"],
    "playbook_writer": ["groq_70b",     "gemini_flash", "mistral",  "groq_8b"],
    "fallback":        ["groq_8b",      "groq_70b",     "mistral"],
}


# ─────────────────────────────────────────
# CALL FUNCTIONS
# ─────────────────────────────────────────

def call_groq(model, system_prompt, user_prompt, max_tokens):
    from groq import Groq
    client   = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model       = model,
        messages    = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        max_tokens  = max_tokens,
        temperature = 0.3,
    )
    return response.choices[0].message.content


def call_gemini(model, system_prompt, user_prompt, max_tokens):
    from google import genai
    from google.genai import types
    client   = genai.Client(api_key=GOOGLE_API_KEY)
    response = client.models.generate_content(
        model    = model,
        contents = f"{system_prompt}\n\n{user_prompt}",
        config   = types.GenerateContentConfig(
            max_output_tokens = max_tokens,
            temperature       = 0.3,
        )
    )
    return response.text


def call_mistral(model, system_prompt, user_prompt, max_tokens):
    from mistralai import Mistral
    client   = Mistral(api_key=MISTRAL_API_KEY)
    response = client.chat.complete(
        model    = model,
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        max_tokens  = max_tokens,
        temperature = 0.3,
    )
    return response.choices[0].message.content


def call_deepseek(model, system_prompt, user_prompt, max_tokens):
    from openai import OpenAI
    client   = OpenAI(
        api_key  = DEEPSEEK_API_KEY,
        base_url = "https://api.deepseek.com"
    )
    response = client.chat.completions.create(
        model       = model,
        messages    = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        max_tokens  = max_tokens,
        temperature = 0.3,
    )
    content = response.choices[0].message.content or ""
    if "<think>" in content:
        content = re.sub(
            r'<think>.*?</think>', '',
            content, flags=re.DOTALL
        ).strip()
    return content


def call_provider(provider_key, system_prompt, user_prompt):
    config     = PROVIDERS[provider_key]
    model      = config["model"]
    max_tokens = config["max_tokens"]
    provider   = config["provider"]

    if provider == "groq":
        return call_groq(model, system_prompt, user_prompt, max_tokens)
    elif provider == "gemini":
        return call_gemini(model, system_prompt, user_prompt, max_tokens)
    elif provider == "mistral":
        return call_mistral(model, system_prompt, user_prompt, max_tokens)
    elif provider == "deepseek":
        return call_deepseek(model, system_prompt, user_prompt, max_tokens)
    else:
        raise ValueError(f"Unknown provider: {provider}")


# ─────────────────────────────────────────
# MAIN FUNCTION — ASK AI
# ─────────────────────────────────────────

def ask_ai(agent_name, system_prompt, user_prompt, provider_override=None):
    """
    Call the best AI for this agent with
    automatic fallback chain.
    Returns: (response_text, provider_used)
    """

    if provider_override:
        chain = [provider_override] + FALLBACK_CHAINS.get(agent_name, ["groq_8b"])
        seen  = set()
        chain = [x for x in chain if not (x in seen or seen.add(x))]
    else:
        chain = FALLBACK_CHAINS.get(agent_name, ["groq_70b", "groq_8b"])

    for provider_key in chain:
        config = PROVIDERS.get(provider_key)
        if not config:
            continue

        # Skip if API key not configured
        p = config["provider"]
        if p == "groq"     and not GROQ_API_KEY:    continue
        if p == "gemini"   and not GOOGLE_API_KEY:   continue
        if p == "mistral"  and not MISTRAL_API_KEY:  continue
        if p == "deepseek" and not DEEPSEEK_API_KEY: continue

        try:
            print(f"  🤖 {agent_name} → {config['name']}")
            result = call_provider(provider_key, system_prompt, user_prompt)
            print(f"  ✅ {config['name']} responded")
            return result, provider_key

        except Exception as e:
            error_msg = str(e)[:80]
            print(f"  ⚠️  {config['name']} failed: {error_msg}")

            # Rate limit — wait and retry once
            if "429" in error_msg or "rate" in error_msg.lower():
                print(f"  ⏳ Rate limited. Waiting 5s...")
                time.sleep(5)
                try:
                    result = call_provider(provider_key, system_prompt, user_prompt)
                    print(f"  ✅ Retry succeeded")
                    return result, provider_key
                except:
                    pass
            continue

    print("  ❌ All providers failed")
    return (
        "All AI providers currently unavailable. Check your API keys.",
        "none"
    )


def get_available_providers():
    return {
        "Groq":     "✅" if GROQ_API_KEY    else "❌ No key",
        "Gemini":   "✅" if GOOGLE_API_KEY  else "❌ No key",
        "Mistral":  "✅" if MISTRAL_API_KEY else "❌ No key",
        "DeepSeek": "✅" if DEEPSEEK_API_KEY else "❌ No key (optional)",
    }


# ─────────────────────────────────────────
# TEST
# ─────────────────────────────────────────

if __name__ == "__main__":

    print("\n" + "="*55)
    print("  🔌 PROVIDER STATUS")
    print("="*55)
    for p, status in get_available_providers().items():
        print(f"  {status}  {p}")

    print("\n" + "="*55)
    print("  🧪 TESTING ALL 5 AGENTS")
    print("="*55)

    test_system = "You are a supply chain expert."
    test_user   = "Say exactly: Ready"

    agents  = ["orchestrator", "route_analyst", "risk_assessor", "playbook_writer", "fallback"]
    results = {}

    for agent in agents:
        print(f"\n  Testing {agent}...")
        response, provider = ask_ai(agent, test_system, test_user)
        results[agent]     = provider != "none"
        print(f"  Response : {response[:50]}")

    print("\n" + "="*55)
    print("  📊 RESULTS")
    print("="*55)
    for agent, success in results.items():
        print(f"  {'✅' if success else '❌'} {agent}")
    print(f"\n  {sum(results.values())}/5 agents ready")
    print("="*55)