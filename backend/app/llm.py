from openai import OpenAI

from .settings import settings
from .schemas import DecisionOutput, EvaluationOutput
from .rag.retriever import retrieve_context  # <-- Level 4: RAG retrieval

client = OpenAI(api_key=settings.OPENAI_API_KEY)

DECIDE_SYSTEM = """You are Sentinel, an Enterprise Ops AI for support triage.
Your job: decide what action should happen next for this ticket.

You are given Knowledge Base snippets (internal policies/SOPs).
Rules:
- Prefer KB policy/SOP over guesswork.
- If you use any snippet to justify your decision or draft response, you MUST cite it.
- citations must be a list of snippet IDs like ["S1","S3"].
- If no snippet is relevant, citations can be [].

Be conservative:
- If uncertain, choose "escalate" with lower confidence.
- Never promise actions you cannot guarantee (e.g., "I refunded you").
- Draft response must be professional and concise.

Output must match the required schema exactly.
"""

EVAL_SYSTEM = """You are Sentinel QA, an enterprise evaluator.

Evaluate the decision & response for:
1) Intent match: decision/route/urgency align with ticket
2) Professional tone
3) No false promises or hallucinated actions
4) Reasons support the decision
5) Coherence of urgency/confidence
6) Groundedness: if policy/SOP claims are made, they must be supported by cited KB snippets.
   - If citations exist, they should be plausible for the claims.
   - If citations are empty but policy details appear, flag it.

Be strict. Provide issues clearly and suggest a fix.
Output must match the required schema exactly.
"""

def _format_snippets(snips: list[dict]) -> str:
    """
    snips format: [{"id":"S1","source":"refund_policy.md","text":"..."}, ...]
    """
    if not snips:
        return "None"
    return "\n\n".join([f"[{s['id']}] ({s['source']}) {s['text']}" for s in snips])


def decide_ticket(ticket_text: str) -> DecisionOutput:
    # 1) Retrieve KB context (Level 4)
    snips = retrieve_context(
        query=ticket_text,
        chroma_dir=settings.CHROMA_DIR,
        k=settings.RAG_TOP_K,
    )
    snippets_block = _format_snippets(snips)

    # 2) Ask model for structured decision with citations
    resp = client.responses.parse(
        model=settings.OPENAI_MODEL,
        input=[
            {"role": "system", "content": DECIDE_SYSTEM},
            {
                "role": "user",
                "content": (
                    "Ticket:\n"
                    f"{ticket_text}\n\n"
                    "Knowledge Base Snippets:\n"
                    f"{snippets_block}\n\n"
                    "Return JSON that matches the schema. Remember: cite snippet IDs you used."
                ),
            },
        ],
        text_format=DecisionOutput,
    )
    return resp.output_parsed


def evaluate_decision(ticket_text: str, decision: DecisionOutput) -> EvaluationOutput:
    # Retrieve again so evaluator sees the same evidence
    snips = retrieve_context(
        query=ticket_text,
        chroma_dir=settings.CHROMA_DIR,
        k=settings.RAG_TOP_K,
    )
    snippets_block = _format_snippets(snips)

    resp = client.responses.parse(
        model=settings.OPENAI_MODEL,
        input=[
            {"role": "system", "content": EVAL_SYSTEM},
            {
                "role": "user",
                "content": (
                    "Ticket:\n"
                    f"{ticket_text}\n\n"
                    "Knowledge Base Snippets:\n"
                    f"{snippets_block}\n\n"
                    "Decision JSON:\n"
                    f"{decision.model_dump_json()}\n\n"
                    "Evaluate strictly. If citations are missing but policy claims appear, flag it."
                ),
            },
        ],
        text_format=EvaluationOutput,
    )
    return resp.output_parsed
