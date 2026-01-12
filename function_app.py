import azure.functions as func
import logging
from openai import OpenAI
import os
import json
import redis import pyodbc
from dotenv import load_dotenv

from ai_service.quote_generator import QuoteGenerator
from pinecone import Pinecone
from ai_service.models import (
    HistoricalQuote,
    QuoteRequest,
    UpsellSuggestionResponse,
    ExplainQuoteResponse,
    OptimizedPricingResponse,
    CatalogItem
)

# Load environment variables for local development
load_dotenv()

app = func.FunctionApp()
logger = logging.getLogger(__name__)

# Singleton AI engine
quote_generator = QuoteGenerator()

# ----------------------------------------------------------------------
# DATA ACCESS LAYER (production implementations)
# ----------------------------------------------------------------------

# Initialize Pinecone + OpenAI clients once
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
pinecone_index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))




def fetch_similar_quotes(request: QuoteRequest) -> list[HistoricalQuote]:
    """
    Production implementation:
    1. Convert request into an embedding
    2. Query Pinecone vector index
    3. Return top 50 similar quotes as HistoricalQuote models
    """

    # Build embedding text
    embedding_text = f"""
    Project Type: {request.project_type.value}
    Customer Notes: {request.customer_notes}
    Square Footage: {request.square_footage or 'N/A'}
    Ceiling Height: {request.ceiling_height or 'N/A'}
    Budget Range: {request.budget_range or 'N/A'}
    """

    # Generate embedding
    embedding = (
        openai_client.embeddings.create(
            model="text-embedding-3-large",
            input=embedding_text
        )
        .data[0]
        .embedding
    )

    # Query Pinecone
    results = pinecone_index.query(
        vector=embedding,
        top_k=50,
        include_metadata=True
    )

    similar_quotes: list[HistoricalQuote] = []

    # Convert metadata → HistoricalQuote models
    for match in results.matches:
        metadata = match.metadata
        try:
            similar_quotes.append(HistoricalQuote(**metadata))
        except Exception as e:
            logger.error(f"Invalid metadata in vector record: {e}")

    return similar_quotes



def fetch_catalog(tenant_id: str) -> list[CatalogItem]:
    """
    Production implementation:
    1. Check Redis cache
    2. If missing, load from Azure SQL
    3. Cache result for 1 hour
    4. Return List[CatalogItem]
    """

    cache_key = f"catalog:{tenant_id}"

    # ---------------------------------------------------------
    # 1. Try Redis cache
    # ---------------------------------------------------------
    cached = redis_client.get(cache_key)
    if cached:
        try:
            data = json.loads(cached)
            return [CatalogItem(**item) for item in data]
        except Exception:
            pass  # fall through to SQL

    # ---------------------------------------------------------
    # 2. Load from Azure SQL
    # ---------------------------------------------------------
    conn = pyodbc.connect(SQL_CONNECTION_STRING)
    cursor = conn.cursor()

    query = """
        SELECT catalog_item_id, tenant_id, sku, name, description,
               base_price, category, typical_quantity_range, pairs_well_with
        FROM Catalog
        WHERE tenant_id = ?
    """

    cursor.execute(query, tenant_id)
    rows = cursor.fetchall()

    catalog_items = []
    for row in rows:
        catalog_items.append(
            CatalogItem(
                catalog_item_id=row.catalog_item_id,
                tenant_id=row.tenant_id,
                sku=row.sku,
                name=row.name,
                description=row.description,
                base_price=row.base_price,
                category=row.category,
                typical_quantity_range=row.typical_quantity_range,
                pairs_well_with=json.loads(row.pairs_well_with) if row.pairs_well_with else None
            )
        )

    cursor.close()
    conn.close()

    # ---------------------------------------------------------
    # 3. Cache for 1 hour
    # ---------------------------------------------------------
    redis_client.setex(cache_key, 3600, json.dumps([item.model_dump() for item in catalog_items]))

    return catalog_items


def fetch_pricing_rules(tenant_id: str) -> dict:
    """
    Production implementation:
    Load pricing rules from Azure SQL.
    """

    conn = pyodbc.connect(SQL_CONNECTION_STRING)
    cursor = conn.cursor()

    query = """
        SELECT target_margin_percent,
               minimum_margin_percent,
               volume_discount_threshold,
               volume_discount_percent,
               seasonal_multiplier
        FROM PricingRules
        WHERE tenant_id = ?
    """

    cursor.execute(query, tenant_id)
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:
        # Fallback defaults
        return {
            "target_margin_percent": 40,
            "minimum_margin_percent": 25,
            "volume_discount_threshold": 10,
            "volume_discount_percent": 5,
            "seasonal_multiplier": 1.0
        }

    return {
        "target_margin_percent": row.target_margin_percent,
        "minimum_margin_percent": row.minimum_margin_percent,
        "volume_discount_threshold": row.volume_discount_threshold,
        "volume_discount_percent": row.volume_discount_percent,
        "seasonal_multiplier": row.seasonal_multiplier
    }


# ----------------------------------------------------------------------
# ENDPOINT: SUGGEST QUOTE
# ----------------------------------------------------------------------

@app.function_name(name="SuggestQuote")
@app.route(route="ai/suggest-quote", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def suggest_quote(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        quote_request = QuoteRequest(**req_body)

        similar_quotes = fetch_similar_quotes(quote_request)
        catalog = fetch_catalog(quote_request.tenant_id)

        suggestion = quote_generator.suggest_quote(
            request=quote_request,
            similar_quotes=similar_quotes,
            catalog=catalog
        )

        return func.HttpResponse(
            body=suggestion.model_dump_json(),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logger.error(f"Error in suggest-quote: {e}", exc_info=True)
        return func.HttpResponse(
            body=json.dumps({"error": "Internal server error"}),
            mimetype="application/json",
            status_code=500
        )

# ----------------------------------------------------------------------
# ENDPOINT: SUGGEST UPSELLS
# ----------------------------------------------------------------------

@app.function_name(name="SuggestUpsells")
@app.route(route="ai/suggest-upsells", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def suggest_upsells(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        quote_request = QuoteRequest(**req_body)

        catalog = fetch_catalog(quote_request.tenant_id)

        upsells = quote_generator.suggest_upsells(
            request=quote_request,
            catalog=catalog
        )

        # Convert dict → typed model → JSON
        response = UpsellSuggestionResponse(
            tenant_id=quote_request.tenant_id,
            project_type=quote_request.project_type,
            upsell_items=upsells.get("upsell_items", []),
            reasoning=upsells.get("reasoning"),
            confidence_score=upsells.get("confidence_score")
        )

        return func.HttpResponse(
            body=response.model_dump_json(),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logger.error(f"Error in suggest-upsells: {e}", exc_info=True)
        return func.HttpResponse(
            body=json.dumps({"error": "Internal server error"}),
            mimetype="application/json",
            status_code=500
        )

# ----------------------------------------------------------------------
# ENDPOINT: EXPLAIN QUOTE
# ----------------------------------------------------------------------

@app.function_name(name="ExplainQuote")
@app.route(route="ai/explain-quote", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def explain_quote(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        quote_request = QuoteRequest(**req_body)

        explanation = quote_generator.explain_quote(quote_request)

        response = ExplainQuoteResponse(
            explanation=explanation["explanation"]
        )

        return func.HttpResponse(
            body=response.model_dump_json(),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logger.error(f"Error in explain-quote: {e}", exc_info=True)
        return func.HttpResponse(
            body=json.dumps({"error": "Internal server error"}),
            mimetype="application/json",
            status_code=500
        )

# ----------------------------------------------------------------------
# ENDPOINT: OPTIMIZE PRICING
# ----------------------------------------------------------------------

@app.function_name(name="OptimizePricing")
@app.route(route="ai/optimize-pricing", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def optimize_pricing(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        quote_request = QuoteRequest(**req_body)

        pricing_rules = fetch_pricing_rules(quote_request.tenant_id)

        optimized = quote_generator.optimize_pricing(
            request=quote_request,
            pricing_rules=pricing_rules
        )

        response = OptimizedPricingResponse(**optimized)

        return func.HttpResponse(
            body=response.model_dump_json(),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logger.error(f"Error in optimize-pricing: {e}", exc_info=True)
        return func.HttpResponse(
            body=json.dumps({"error": "Internal server error"}),
            mimetype="application/json",
            status_code=500
        )

# ----------------------------------------------------------------------
# HEALTH CHECK
# ----------------------------------------------------------------------

@app.function_name(name="HealthCheck")
@app.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps({"status": "healthy", "service": "speedupsharepoint-ai-service"}),
        mimetype="application/json",
        status_code=200
    )
