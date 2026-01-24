import psycopg
from psycopg.rows import dict_row
from .settings import settings

def get_conn():
    return psycopg.connect(settings.DATABASE_URL, row_factory=dict_row)

def insert_run(ticket_text: str, decision_json: dict, evaluation_json: dict, model_version: str) -> str:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into runs (ticket_text, decision_json, evaluation_json, model_version)
                values (%s, %s, %s, %s)
                returning id
                """,
                (ticket_text, decision_json, evaluation_json, model_version),
            )
            row = cur.fetchone()
            return str(row["id"])

def fetch_history(limit: int = 50) -> list[dict]:
    limit = max(1, min(limit, 200))
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select id, ticket_text, decision_json, evaluation_json, model_version, created_at
                from runs
                order by created_at desc
                limit %s
                """,
                (limit,),
            )
            return list(cur.fetchall())
