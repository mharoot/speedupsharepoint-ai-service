import os
import json
from typing import List, Optional
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

from .models import (
    QuoteRequest, 
    QuoteResponse, 
    QuoteLineItem,
    HistoricalQuote,
    CatalogItem
)
from .context_builder import ContextBuilder

logger = logging.getLogger(__name__)


class QuoteGenerator:
    """AI service for quote suggestions, upsells, explanations, and pricing optimization."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo")
        self.client = OpenAI(api_key=self.api_key)
        self.context_builder = ContextBuilder()

    # ----------------------------------------------------------------------
    # PRIMARY ENDPOINT: SUGGEST QUOTE
    # ----------------------------------------------------------------------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def suggest_quote(
        self,
        request: QuoteRequest,
        similar_quotes: List[HistoricalQuote],
        catalog: List[CatalogItem]
    ) -> QuoteResponse:
        """Generate an AI-powered quote suggestion using GPT-4."""

        logger.info(f"Suggesting quote for tenant={request.tenant_id}, type={request.project_type}")

        prompt = self.context_builder.build_suggest_quote_prompt(
            request=request,
            similar_quotes=similar_quotes,
            catalog=catalog
        )

        logger.debug(f"Prompt length: {len(prompt)} characters")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert estimator. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            logger.debug(f"Raw AI response: {content[:200]}...")

            quote_data = json.loads(content)

            # Build line items
            line_items = [QuoteLineItem(**item) for item in quote_data["line_items"]]
            subtotal = sum(item.total for item in line_items)
            tax = subtotal * 0.0825
            total = subtotal + tax

            # Estimate margin
            cost = sum(item.total * 0.6 for item in line_items)
            margin_percent = ((subtotal - cost) / subtotal * 100) if subtotal > 0 else 0

            quote_response = QuoteResponse(
                quote_id=f"quote_{request.tenant_id}_{int(response.created)}",
                tenant_id=request.tenant_id,
                line_items=line_items,
                subtotal=subtotal,
                tax=tax,
                total=total,
                estimated_margin_percent=round(margin_percent, 2),
                reasoning=quote_data.get("reasoning", ""),
                upsell_suggestions=[
                    QuoteLineItem(**item)
                    for item in quote_data.get("upsell_suggestions", [])
                ],
                similar_quotes_used=len(similar_quotes),
                confidence_score=quote_data.get("confidence_score", 0.7)
            )

            logger.info(f"Suggested quote: {quote_response.quote_id}, total=${total:.2f}")
            return quote_response

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise ValueError("AI returned invalid JSON")

        except Exception as e:
            logger.error(f"Error generating quote suggestion: {e}")
            raise

    # ----------------------------------------------------------------------
    # UPSSELL SUGGESTIONS
    # ----------------------------------------------------------------------
    def suggest_upsells(
        self,
        request: QuoteRequest,
        catalog: List[CatalogItem]
    ):
        """Suggest upsell items based on the project and catalog."""

        logger.info(f"Suggesting upsells for tenant={request.tenant_id}")

        prompt = self.context_builder.build_upsell_prompt(
            request=request,
            catalog=catalog
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert sales engineer. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=800,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        data = json.loads(content)

        return data

    # ----------------------------------------------------------------------
    # EXPLAIN QUOTE
    # ----------------------------------------------------------------------
    def explain_quote(self, request: QuoteRequest):
        """Explain the reasoning behind a quote in natural language."""

        logger.info(f"Explaining quote for tenant={request.tenant_id}")

        prompt = self.context_builder.build_explain_quote_prompt(request=request)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You explain quotes clearly and concisely."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1000
        )

        return {"explanation": response.choices[0].message.content}

    # ----------------------------------------------------------------------
    # OPTIMIZE PRICING
    # ----------------------------------------------------------------------
    def optimize_pricing(
        self,
        request: QuoteRequest,
        pricing_rules: dict
    ):
        """Optimize pricing based on tenant rules and AI reasoning."""

        logger.info(f"Optimizing pricing for tenant={request.tenant_id}")

        prompt = self.context_builder.build_optimize_pricing_prompt(
            request=request,
            pricing_rules=pricing_rules
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a pricing strategist. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1200,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)
