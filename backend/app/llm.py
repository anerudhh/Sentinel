from openai import OpenAI
from .settings import settings
from .schemas import DecisionOutput, EvaluationOutput

client = OpenAI(api_key=settings.OPENAI_API_KEY)

DECIDE_SYSTEM = """You are Sentinel, an Enterprise Ops AI for support triage.
Your job: decide what action should happen next for this ticket.

Return a *structured* decision. Be conservative:
- If uncertain, choose "escalate" with lower confidence.
- Never promise actions you cannot guarantee (e.g., "I refunded you").
- Draft response must be professional and concise.

Output must match the required schema."""
EVAL_SYSTEM = """You are Sentinel QA, an enterprise evaluator.

Evaluate the decision & response for:
1) Intent match: decision/route/urgency align with ticket
2) Professional tone
3) No false promises or hallucinated actions
4) Reasons support the decision
5) Coherence of urgency/confidence

Be strict. Provide issues clearly and suggest a fix.
Output must match the required schema."""

def decide_ticket(ticket_text: str) -> DecisionOutput:
    resp = client.responses.parse(
        model=settings.OPENAI_MODEL,
        input=[
            {"role": "system", "content": DECIDE_SYSTEM},
            {"role": "user", "content": ticket_text},
        ],
        text_format=DecisionOutput,
    )
    return resp.output_parsed

def evaluate_decision(ticket_text: str, decision: DecisionOutput) -> EvaluationOutput:
    resp = client.responses.parse(
        model=settings.OPENAI_MODEL,
        input=[
            {"role": "system", "content": EVAL_SYSTEM},
            {
                "role": "user",
                "content": (
                    "Ticket:\n"
                    f"{ticket_text}\n\n"
                    "Decision JSON:\n"
                    f"{decision.model_dump_json()}\n"
                ),
            },
        ],
        text_format=EvaluationOutput,
    )
    return resp.output_parsed
