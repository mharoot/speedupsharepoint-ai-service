#!/usr/bin/env python3
"""Quick local test script - tests the AI service directly (no Azure Functions)."""

import os
import json
from dotenv import load_dotenv

from ai_service.quote_generator import QuoteGenerator
from ai_service.models import (
    QuoteRequest,
    CatalogItem,
    ProjectType
)

# Load environment variables
load_dotenv()


def main():
    print("🚀 Testing Speed Up SharePoint AI Service Locally (Direct AI Calls)\n")

    # Load catalog
    with open("data/closet-world_catalog.json") as f:
        catalog_data = json.load(f)
        catalog = [CatalogItem(**item) for item in catalog_data]

    print(f"✅ Loaded {len(catalog)} catalog items")

    # Create quote request
    request = QuoteRequest(
        tenant_id="closet-world",
        project_type=ProjectType.CLOSET,
        customer_notes=(
            "I need to organize my master bedroom closet. "
            "It's about 8 feet wide and I have lots of shoes and hanging clothes."
        ),
        square_footage=64.0,
        ceiling_height=8.0,
        budget_range="standard"
    )

    print("\n📝 Quote Request:")
    print(f"  Tenant: {request.tenant_id}")
    print(f"  Type: {request.project_type.value}")
    print(f"  Notes: {request.customer_notes}")

    generator = QuoteGenerator()

    # ----------------------------------------------------------------------
    # 1. Suggest Quote
    # ----------------------------------------------------------------------
    print("\n🤖 Calling suggest_quote...")
    try:
        quote = generator.suggest_quote(
            request=request,
            similar_quotes=[],
            catalog=catalog
        )

        print("\n✅ Quote Suggested Successfully!\n")
        print(f"Quote ID: {quote.quote_id}")
        print(f"Total: ${quote.total:,.2f}")
        print(f"Margin: {quote.estimated_margin_percent}%")
        print(f"Confidence: {quote.confidence_score}")

        print("\n📋 Line Items:")
        for item in quote.line_items:
            print(f"  - {item.quantity}x {item.sku}: {item.description}")
            print(f"    ${item.unit_price:.2f} each = ${item.total:.2f}")
            if item.reasoning:
                print(f"    💡 {item.reasoning}")

        print(f"\n💡 Reasoning:\n{quote.reasoning}")

        if quote.upsell_suggestions:
            print("\n🎁 Upsell Suggestions:")
            for item in quote.upsell_suggestions:
                print(f"  - {item.sku}: {item.description} (${item.unit_price:.2f})")

        # Save output
        output_file = "data/test_suggest_quote_output.json"
        with open(output_file, "w") as f:
            f.write(quote.model_dump_json(indent=2))

        print(f"\n💾 Full quote saved to: {output_file}")

    except Exception as e:
        print(f"\n❌ Error in suggest_quote: {e}")
        import traceback
        traceback.print_exc()

    # ----------------------------------------------------------------------
    # 2. Suggest Upsells
    # ----------------------------------------------------------------------
    print("\n🤖 Calling suggest_upsells...")
    try:
        upsells = generator.suggest_upsells(
            request=request,
            catalog=catalog
        )

        print("\n🎁 Upsell Suggestions Returned:")
        print(json.dumps(upsells, indent=2))

    except Exception as e:
        print(f"\n❌ Error in suggest_upsells: {e}")
        import traceback
        traceback.print_exc()

    # ----------------------------------------------------------------------
    # 3. Explain Quote
    # ----------------------------------------------------------------------
    print("\n🤖 Calling explain_quote...")
    try:
        explanation = generator.explain_quote(request=request)

        print("\n📝 Quote Explanation:")
        print(explanation["explanation"])

    except Exception as e:
        print(f"\n❌ Error in explain_quote: {e}")
        import traceback
        traceback.print_exc()

    # ----------------------------------------------------------------------
    # 4. Optimize Pricing
    # ----------------------------------------------------------------------
    print("\n🤖 Calling optimize_pricing...")
    try:
        optimized = generator.optimize_pricing(
            request=request,
            pricing_rules={
                "target_margin_percent": 40,
                "minimum_margin_percent": 25,
                "volume_discount_threshold": 10,
                "volume_discount_percent": 5,
                "seasonal_multiplier": 1.0
            }
        )

        print("\n💰 Optimized Pricing:")
        print(json.dumps(optimized, indent=2))

    except Exception as e:
        print(f"\n❌ Error in optimize_pricing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
