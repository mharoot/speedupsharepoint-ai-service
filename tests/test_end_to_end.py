#!/usr/bin/env python3
import json
import requests
import sys
from pprint import pprint

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------

# Local:
BASE_URL = "http://localhost:7071/api"

# Azure example:
# BASE_URL = "https://speedupsharepoint-ai-service-michael.azurewebsites.net/api"
# FUNCTION_KEY = "your-key-here"

HEADERS = {
    "Content-Type": "application/json"
}

# ----------------------------------------------------------------------
# SHARED PAYLOAD
# ----------------------------------------------------------------------

QUOTE_REQUEST = {
    "tenant_id": "closet-world",
    "project_type": "closet",
    "customer_notes": "8x8 master closet, need more shoe storage",
    "square_footage": 64,
    "ceiling_height": 8,
    "budget_range": "standard"
}

# ----------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------

def call(endpoint: str, payload: dict):
    """Call an endpoint and return JSON or raise."""
    url = f"{BASE_URL}/{endpoint}"

    print(f"\n=== Calling {url} ===")

    response = requests.post(url, headers=HEADERS, data=json.dumps(payload))

    if response.status_code != 200:
        print(f"❌ ERROR {response.status_code}: {response.text}")
        sys.exit(1)

    try:
        return response.json()
    except json.JSONDecodeError:
        print("❌ Invalid JSON returned:")
        print(response.text)
        sys.exit(1)


def print_section(title: str, data):
    print(f"\n\n==================== {title} ====================")
    pprint(data)


# ----------------------------------------------------------------------
# MAIN TEST FLOW
# ----------------------------------------------------------------------

def main():
    print("\n🚀 Running Full End‑to‑End Test for All AI Endpoints\n")

    # 1. Health Check
    print("Checking health endpoint...")
    health = requests.get(f"{BASE_URL}/health")
    if health.status_code != 200:
        print(f"❌ Health check failed: {health.text}")
        sys.exit(1)
    print("✅ Health OK")

    # 2. Suggest Quote (Primary)
    suggest_quote = call("ai/suggest-quote", QUOTE_REQUEST)
    print_section("Suggest Quote Response", suggest_quote)

    # 3. Suggest Upsells
    upsells = call("ai/suggest-upsells", QUOTE_REQUEST)
    print_section("Upsell Suggestions", upsells)

    # 4. Explain Quote
    explain = call("ai/explain-quote", QUOTE_REQUEST)
    print_section("Quote Explanation", explain)

    # 5. Optimize Pricing
    optimize = call("ai/optimize-pricing", QUOTE_REQUEST)
    print_section("Optimized Pricing", optimize)

    print("\n🎉 All endpoints tested successfully!\n")


if __name__ == "__main__":
    main()
