from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .settings import settings
from .schemas import (
    DecideRequest, DecideResponse,
    HistoryResponse, ErrorResponse,
    DecisionOutput, EvaluationOutput
)
from .llm import decide_ticket, evaluate_decision
from .db import insert_run, fetch_history

app = FastAPI(title="Sentinel (Enterprise Ops AI) - V1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True, "service": "sentinel", "version": "v1"}

@app.post(
    "/decide",
    response_model=DecideResponse,
    responses={500: {"model": ErrorResponse}},
)
def decide(req: DecideRequest):
    try:
        decision: DecisionOutput = decide_ticket(req.ticket_text)
        evaluation: EvaluationOutput = evaluate_decision(req.ticket_text, decision)

        run_id = insert_run(
            ticket_text=req.ticket_text,
            decision_json=decision.model_dump(),
            evaluation_json=evaluation.model_dump(),
            model_version=settings.OPENAI_MODEL,
        )

        return DecideResponse(run_id=run_id, decision=decision, evaluation=evaluation)

    except Exception as e:
        # raising HTTPException is cleaner, but returning structured error is ok for now
        return ErrorResponse(
            error_code="DECIDE_PIPELINE_FAILED",
            message="Decision pipeline failed",
            detail=str(e),
        )

@app.get(
    "/history",
    response_model=HistoryResponse,
    responses={500: {"model": ErrorResponse}},
)
def history(limit: int = Query(default=30, ge=1, le=200)):
    try:
        items = fetch_history(limit=limit)
        return {"items": items}
    except Exception as e:
        return ErrorResponse(
            error_code="HISTORY_FAILED",
            message="History fetch failed",
            detail=str(e),
        )
from .rag.ingest import ingest_kb

@app.post("/rag/ingest")
def rag_ingest():
    n = ingest_kb(kb_dir=settings.KB_DIR, chroma_dir=settings.CHROMA_DIR)
    return {"chunks_indexed": n}
