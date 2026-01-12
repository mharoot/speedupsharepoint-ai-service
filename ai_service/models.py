from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ProjectType(str, Enum):
    GARAGE = "garage"
    CLOSET = "closet"
    PANTRY = "pantry"
    MUDROOM = "mudroom"
    HOME_OFFICE = "home_office"


class QuoteLineItem(BaseModel):
    sku: str
    description: str
    quantity: int
    unit_price: float
    total: float
    category: str  # "base", "upgrade", "upsell"
    reasoning: Optional[str] = None


class QuoteRequest(BaseModel):
    tenant_id: str
    customer_id: Optional[str] = None
    project_type: ProjectType
    customer_notes: str
    square_footage: Optional[float] = None
    ceiling_height: Optional[float] = None
    budget_range: Optional[str] = None  # "budget", "standard", "premium"
    site_photos: Optional[List[str]] = None  # Base64 encoded images
    customer_context: Optional[Dict[str, Any]] = None


class QuoteResponse(BaseModel):
    """
    Returned by /ai/suggest-quote
    """
    quote_id: str
    tenant_id: str
    line_items: List[QuoteLineItem]
    subtotal: float
    tax: float
    total: float
    estimated_margin_percent: float
    reasoning: str
    upsell_suggestions: List[QuoteLineItem]
    similar_quotes_used: int
    confidence_score: float  # 0.0 to 1.0
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class HistoricalQuote(BaseModel):
    quote_id: str
    tenant_id: str
    project_type: ProjectType
    customer_notes: str
    square_footage: Optional[float]
    line_items: List[QuoteLineItem]
    total_amount: float
    won: bool
    time_to_close_days: Optional[int]
    sales_rep_notes: Optional[str]
    created_at: datetime


class CatalogItem(BaseModel):
    catalog_item_id: str
    tenant_id: str
    sku: str
    name: str
    description: str
    base_price: float
    category: str
    typical_quantity_range: Optional[str] = None  # "1-5", "10-20"
    pairs_well_with: Optional[List[str]] = None  # List of SKUs

class UpsellSuggestionResponse(BaseModel):
    """
    Returned by /ai/suggest-upsells
    """
    tenant_id: str
    project_type: ProjectType
    upsell_items: List[QuoteLineItem]
    reasoning: Optional[str] = None
    confidence_score: Optional[float] = None


class ExplainQuoteResponse(BaseModel):
    """
    Returned by /ai/explain-quote
    """
    explanation: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class OptimizedPricingResponse(BaseModel):
    """
    Returned by /ai/optimize-pricing
    """
    recommended_price: float
    target_margin_percent: float
    reasoning: str
    adjustments: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
