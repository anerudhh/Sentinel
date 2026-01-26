from pydantic import BaseModel, Field
from typing import Literal, List, Optional, Any
from datetime import datetime

DecisionType = Literal["auto_resolve", "escalate", "route"]
RouteType = Literal["billing", "tech", "account", "sales", "other"]
UrgencyType = Literal["low", "medium", "high"]

class DecideRequest(BaseModel):
    ticket_text: str = Field(min_length=5, max_length=4000)

class DecisionOutput(BaseModel):
    decision: DecisionType
    route: RouteType
    urgency: UrgencyType
    confidence: float = Field(ge=0.0, le=1.0)
    reasons: List[str] = Field(min_length=1, max_length=6)
    draft_response: str = Field(min_length=10, max_length=2000)
    citations: list[str] = []
    retrieved_snippets: list[dict] = []

class EvaluationOutput(BaseModel):
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list, max_length=10)
    suggested_fix: str = Field(default="", max_length=1000)

class DecideResponse(BaseModel):
    run_id: str
    decision: DecisionOutput
    evaluation: EvaluationOutput

class HistoryItem(BaseModel):
    id: str
    ticket_text: str
    decision_json: Any
    evaluation_json: Any
    model_version: str
    created_at: datetime

class HistoryResponse(BaseModel):
    items: List[HistoryItem]

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    detail: Optional[str] = None

