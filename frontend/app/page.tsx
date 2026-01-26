"use client";

import React, { useEffect, useMemo, useState } from "react";

type DecisionOutput = {
  decision: "auto_resolve" | "escalate" | "route";
  route: "billing" | "tech" | "account" | "sales" | "other";
  urgency: "low" | "medium" | "high";
  confidence: number;
  reasons: string[];
  draft_response: string;
  citations: string[]; // ✅ added
};

type EvaluationOutput = {
  passed: boolean;
  score: number;
  issues: string[];
  suggested_fix: string;
};

type DecideResponse = {
  run_id: string;
  decision: DecisionOutput;
  evaluation: EvaluationOutput;
};

type HistoryItem = {
  id: string;
  ticket_text: string;
  decision_json: any;
  evaluation_json: any;
  model_version: string;
  created_at: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

function fmt(ts: string) {
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return ts;
  }
}

function urgencyBadge(u?: string) {
  if (u === "high")
    return (
      <span className="badge warn">
        <span className="dot" />
        High
      </span>
    );
  if (u === "medium")
    return (
      <span className="badge">
        <span className="dot" />
        Medium
      </span>
    );
  if (u === "low")
    return (
      <span className="badge">
        <span className="dot" />
        Low
      </span>
    );
  return (
    <span className="badge">
      <span className="dot" />—
    </span>
  );
}

export default function Page() {
  const [ticket, setTicket] = useState(
    "Hi, I was charged twice for my subscription and need a refund. Please help ASAP."
  );
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DecideResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const canSubmit = useMemo(() => ticket.trim().length >= 5, [ticket]);

  async function loadHistory() {
    setHistoryLoading(true);
    try {
      const res = await fetch(`${API_BASE}/history?limit=20`, { cache: "no-store" });
      const data = await res.json();
      if (data?.error_code) throw new Error(data.message || "History error");
      setHistory(data.items || []);
    } catch {
      // keep UI usable even if history fails
    } finally {
      setHistoryLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  async function onDecide() {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/decide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticket_text: ticket }),
      });

      const data = await res.json();
      if (data?.error_code) {
        throw new Error(
          `${data.error_code}: ${data.message}${data.detail ? ` (${data.detail})` : ""}`
        );
      }

      setResult(data as DecideResponse);
      await loadHistory();
    } catch (e: any) {
      setError(e?.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  const evalBadge = result ? (
    <span className={`badge ${result.evaluation.passed ? "pass" : "fail"}`}>
      <span className="dot" />
      {result.evaluation.passed ? "Pass" : "Fail"} • {result.evaluation.score.toFixed(2)}
    </span>
  ) : (
    <span className="badge">
      <span className="dot" />
      No run
    </span>
  );

  return (
    <div className="shell">
      {/* Top bar */}
      <div className="topbar">
        <div className="brand">
          <div className="logo" style={{ display: "grid", placeItems: "center" }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 2l7 4v6c0 5-3.5 8-7 10-3.5-2-7-5-7-10V6l7-4z"
                stroke="white"
                strokeWidth="1.6"
              />
            </svg>
          </div>

          <div>
            <h1>Sentinel</h1>
            <p>Enterprise Ops Decision System • V1 (Decide + Evaluate + Log)</p>
          </div>
        </div>

        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          {evalBadge}
          <span className="badge">
            <span className="dot" />
            <span className="small">
              API: <code>{API_BASE}</code>
            </span>
          </span>
        </div>
      </div>

      <div className="grid2">
        {/* Ticket */}
        <div className="card">
          <div className="cardHeader">
            <h3 className="cardTitle">Incoming Ticket</h3>
            <div className="cardHint">Paste customer message / incident summary</div>
          </div>

          <textarea value={ticket} onChange={(e) => setTicket(e.target.value)} />

          <div className="actionsRow">
            <button disabled={!canSubmit || loading} onClick={onDecide}>
              {loading ? "Running…" : "Generate Decision"}
            </button>

            <button className="subtleBtn" onClick={loadHistory} disabled={historyLoading}>
              {historyLoading ? "Refreshing…" : "Refresh history"}
            </button>
          </div>

          {error && (
            <div className="errorBox" style={{ marginTop: 12 }}>
              <b style={{ color: "rgba(239,68,68,0.95)" }}>Error:</b>{" "}
              <span style={{ color: "rgba(255,255,255,0.88)" }}>{error}</span>
            </div>
          )}
        </div>

        {/* Decision Summary */}
        <div className="card">
          <div className="cardHeader">
            <h3 className="cardTitle">Decision Summary</h3>
            <div className="cardHint">Structured output + QA evaluation</div>
          </div>

          {!result && <div className="small">Run a ticket to generate the decision.</div>}

          {result && (
            <>
              <div className="kv">
                <div className="k">Run ID</div>
                <div className="v">
                  <code>{result.run_id}</code>
                </div>

                <div className="k">Action</div>
                <div className="v">
                  <b>{result.decision.decision}</b>
                </div>

                <div className="k">Route</div>
                <div className="v">
                  <b>{result.decision.route}</b>
                </div>

                <div className="k">Urgency</div>
                <div className="v">{urgencyBadge(result.decision.urgency)}</div>

                <div className="k">Confidence</div>
                <div className="v">{result.decision.confidence.toFixed(2)}</div>

                {/* ✅ Citations */}
                <div className="k">Citations</div>
                <div className="v">
                  {result.decision.citations?.length ? (
                    <span style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      {result.decision.citations.map((c) => (
                        <span key={c} className="badge">
                          <span className="dot" />
                          {c}
                        </span>
                      ))}
                    </span>
                  ) : (
                    <span className="small">—</span>
                  )}
                </div>

                <div className="k">Evaluation</div>
                <div className="v">
                  <span className={`badge ${result.evaluation.passed ? "pass" : "fail"}`}>
                    <span className="dot" />
                    {result.evaluation.passed ? "Pass" : "Fail"} •{" "}
                    {result.evaluation.score.toFixed(2)}
                  </span>
                </div>
              </div>

              <div className="hr" />

              <div>
                <div className="small" style={{ fontWeight: 650, marginBottom: 6 }}>
                  Reasons
                </div>
                <ul style={{ margin: 0, paddingLeft: 18 }}>
                  {result.decision.reasons.map((r, i) => (
                    <li
                      key={i}
                      style={{ marginBottom: 6, color: "rgba(255,255,255,0.86)" }}
                    >
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Draft response + Issues */}
      <div className="grid2">
        <div className="card">
          <div className="cardHeader">
            <h3 className="cardTitle">Draft Response</h3>
            <div className="cardHint">Operator-ready response text</div>
          </div>

          {!result ? (
            <div className="small">Generated response will appear here.</div>
          ) : (
            <>
              <pre>{result.decision.draft_response}</pre>

              {/* ✅ Optional: show sources under response */}
              {result.decision.citations?.length > 0 && (
                <div style={{ marginTop: 10 }} className="small">
                  Sources:{" "}
                  {result.decision.citations.map((c, i) => (
                    <span key={c}>
                      <b>{c}</b>
                      {i < result.decision.citations.length - 1 ? ", " : ""}
                    </span>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        <div className="card">
          <div className="cardHeader">
            <h3 className="cardTitle">QA Notes</h3>
            <div className="cardHint">Issues found by evaluation layer</div>
          </div>

          {!result ? (
            <div className="small">Evaluation issues will appear here.</div>
          ) : result.evaluation.issues?.length === 0 ? (
            <div className="badge pass">
              <span className="dot" />
              No issues detected
            </div>
          ) : (
            <>
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {result.evaluation.issues.map((iss, i) => (
                  <li
                    key={i}
                    style={{ marginBottom: 6, color: "rgba(255,255,255,0.86)" }}
                  >
                    {iss}
                  </li>
                ))}
              </ul>

              {result.evaluation.suggested_fix && (
                <>
                  <div className="hr" />
                  <div className="small" style={{ fontWeight: 650, marginBottom: 6 }}>
                    Suggested fix
                  </div>
                  <div style={{ color: "rgba(255,255,255,0.86)", fontSize: 13 }}>
                    {result.evaluation.suggested_fix}
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>

      {/* History */}
      <div className="card">
        <div className="cardHeader">
          <h3 className="cardTitle">Run History</h3>
          <div className="cardHint">Recent decisions logged in Postgres</div>
        </div>

        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Route</th>
              <th>Urgency</th>
              <th>Eval</th>
              <th>Ticket</th>
            </tr>
          </thead>

          <tbody>
            {history.map((h) => {
              const route = h?.decision_json?.route ?? "—";
              const urgency = h?.decision_json?.urgency ?? "—";
              const passed = h?.evaluation_json?.passed;
              const score = h?.evaluation_json?.score;

              return (
                <tr key={h.id}>
                  <td style={{ color: "rgba(255,255,255,0.80)" }}>{fmt(h.created_at)}</td>
                  <td>
                    <b>{route}</b>
                  </td>
                  <td>{urgencyBadge(urgency)}</td>
                  <td>
                    <span className={`badge ${passed ? "pass" : "fail"}`}>
                      <span className="dot" />
                      {passed ? "Pass" : "Fail"} •{" "}
                      {typeof score === "number" ? score.toFixed(2) : "--"}
                    </span>
                  </td>
                  <td style={{ color: "rgba(255,255,255,0.86)" }}>
                    {h.ticket_text.slice(0, 120)}
                    {h.ticket_text.length > 120 ? "…" : ""}
                  </td>
                </tr>
              );
            })}

            {history.length === 0 && (
              <tr>
                <td colSpan={5} style={{ color: "rgba(255,255,255,0.70)" }}>
                  No runs yet. Generate a decision to create the first entry.
                </td>
              </tr>
            )}
          </tbody>
        </table>

        <div style={{ marginTop: 10 }} className="small">
          Tip: Use varied ticket types (billing, account, tech) to demonstrate routing + QA
          behavior.
        </div>
      </div>
    </div>
  );
}
