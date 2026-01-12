from typing import List, Dict, Any
from .models import HistoricalQuote, CatalogItem, QuoteRequest


class ContextBuilder:
    """Builds rich context for the AI model from historical data and catalogs."""

    # ----------------------------------------------------------------------
    # PRIMARY: SUGGEST QUOTE
    # ----------------------------------------------------------------------
    def build_suggest_quote_prompt(
        self,
        request: QuoteRequest,
        similar_quotes: List[HistoricalQuote],
        catalog: List[CatalogItem]
    ) -> str:
        """Prompt for /ai/suggest-quote (primary quote generation)."""

        relevant_catalog = [
            item for item in catalog
            if request.project_type.value in item.category.lower()
        ]

        prompt = f"""You are an expert estimator for {request.tenant_id}.

# CUSTOMER REQUEST
Project Type: {request.project_type.value}
Customer Notes: {request.customer_notes}
Square Footage: {request.square_footage or 'Not specified'}
Ceiling Height: {request.ceiling_height or 'Not specified'}
Budget Range: {request.budget_range or 'Not specified'}

# SIMILAR PAST QUOTES
{self._format_similar_quotes(similar_quotes)}

# AVAILABLE CATALOG ITEMS
{self._format_catalog(relevant_catalog)}

# TASK
Generate a detailed quote suggestion using ONLY valid JSON:

{{
  "line_items": [
    {{
      "sku": "EXACT_SKU_FROM_CATALOG",
      "description": "User-friendly description",
      "quantity": 5,
      "unit_price": 299.99,
      "total": 1499.95,
      "category": "base",
      "reasoning": "Why this item and quantity"
    }}
  ],
  "reasoning": "Overall quote strategy",
  "upsell_suggestions": [],
  "confidence_score": 0.85
}}

RULES:
1. Use only SKUs from the catalog.
2. Base quantities on square footage and project type.
3. Reference patterns from similar quotes.
4. Include reasoning for each line item.
5. Suggest 2–3 upsells.
6. Return ONLY valid JSON.
"""
        return prompt

    # ----------------------------------------------------------------------
    # UPSSELL SUGGESTIONS
    # ----------------------------------------------------------------------
    def build_upsell_prompt(
        self,
        request: QuoteRequest,
        catalog: List[CatalogItem]
    ) -> str:
        """Prompt for /ai/suggest-upsells."""

        relevant_catalog = [
            item for item in catalog
            if request.project_type.value in item.category.lower()
        ]

        prompt = f"""You are an expert sales engineer for {request.tenant_id}.

# CUSTOMER REQUEST
Project Type: {request.project_type.value}
Customer Notes: {request.customer_notes}

# AVAILABLE CATALOG ITEMS
{self._format_catalog(relevant_catalog)}

# TASK
Suggest 2–5 upsell items that would meaningfully improve the project outcome.

Return ONLY valid JSON:

{{
  "upsell_items": [
    {{
      "sku": "EXACT_SKU_FROM_CATALOG",
      "description": "Short description",
      "quantity": 1,
      "unit_price": 199.99,
      "total": 199.99,
      "category": "upsell",
      "reasoning": "Why this is a valuable upgrade"
    }}
  ],
  "reasoning": "Overall upsell strategy",
  "confidence_score": 0.85
}}
"""
        return prompt

    # ----------------------------------------------------------------------
    # EXPLAIN QUOTE
    # ----------------------------------------------------------------------
    def build_explain_quote_prompt(self, request: QuoteRequest) -> str:
        """Prompt for /ai/explain-quote."""

        prompt = f"""You are an expert estimator who explains quotes clearly.

# CUSTOMER REQUEST
Project Type: {request.project_type.value}
Customer Notes: {request.customer_notes}

# TASK
Explain the reasoning behind the quote in clear, friendly language.
Do NOT return JSON. Return plain text only.
"""
        return prompt

    # ----------------------------------------------------------------------
    # OPTIMIZE PRICING
    # ----------------------------------------------------------------------
    def build_optimize_pricing_prompt(
        self,
        request: QuoteRequest,
        pricing_rules: Dict[str, Any]
    ) -> str:
        """Prompt for /ai/optimize-pricing."""

        prompt = f"""You are a pricing strategist for {request.tenant_id}.

# CUSTOMER REQUEST
Project Type: {request.project_type.value}
Customer Notes: {request.customer_notes}
Budget Range: {request.budget_range or 'Not specified'}

# PRICING RULES
{self._format_pricing_rules(pricing_rules)}

# TASK
Recommend an optimized price and margin strategy.

Return ONLY valid JSON:

{{
  "recommended_price": 1234.56,
  "target_margin_percent": 40,
  "reasoning": "Why this pricing strategy is optimal",
  "adjustments": {{
    "seasonal_multiplier": 1.0,
    "volume_discount_applied": false
  }},
  "confidence_score": 0.85
}}
"""
        return prompt

    # ----------------------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------------------
    def _format_similar_quotes(self, quotes: List[HistoricalQuote]) -> str:
        if not quotes:
            return "No similar quotes found."

        formatted = []
        for i, quote in enumerate(quotes[:10], 1):
            items_summary = ", ".join([
                f"{item.quantity}x {item.sku}"
                for item in quote.line_items[:5]
            ])

            formatted.append(f"""
Quote {i}:
  - Project: {quote.project_type.value} ({quote.square_footage or 'N/A'} sqft)
  - Customer: "{quote.customer_notes[:100]}..."
  - Items: {items_summary}
  - Total: ${quote.total_amount:,.2f}
  - Result: {'WON' if quote.won else 'LOST'}
""")

        return "\n".join(formatted)

    def _format_catalog(self, catalog: List[CatalogItem]) -> str:
        if not catalog:
            return "No catalog items available."

        formatted = []
        for item in catalog:
            formatted.append(f"""
- SKU: {item.sku}
  Name: {item.name}
  Description: {item.description}
  Price: ${item.base_price:.2f}
  Typical Qty: {item.typical_quantity_range or 'Varies'}
""")

        return "\n".join(formatted)

    def _format_pricing_rules(self, rules: Dict[str, Any]) -> str:
        if not rules:
            return "Standard pricing applies."

        return f"""
- Target Margin: {rules.get('target_margin_percent', 40)}%
- Minimum Margin: {rules.get('minimum_margin_percent', 25)}%
- Volume Discount: {rules.get('volume_discount_threshold', 10)} items @ {rules.get('volume_discount_percent', 5)}%
"""
