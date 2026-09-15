import { useEffect, useState } from "react";
import { api } from "../api";
import { Badge, Field, ReportView, Running } from "../components/UI";
import type { Summary } from "../types";

type Message = { id: string; message: string; response: string; state: string };
type Budget = {
  daily_call_limit: number;
  calls_today: number;
  cached_results: number;
  cache_hits: number;
  remaining_calls: number;
  note: string;
};
type Control = { budget: Budget; runs: Summary["runs"] };
export function AgentControl({
  jobId,
  revision,
  locked,
  onChanged,
  onBuilding,
}: {
  jobId: string;
  revision: number;
  locked: boolean;
  onChanged: () => Promise<void>;
  onBuilding: (active: boolean) => void;
}) {
  const [control, setControl] = useState<Control>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [message, setMessage] = useState("");
  const [limit, setLimit] = useState<number>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [watch, setWatch] = useState<string>();
  async function load() {
    const [c, m] = await Promise.all([
      api<Control>("/v2/agent-control"),
      api<Message[]>("/v2/instructions?job_id=" + jobId),
    ]);
    setControl(c);
    setMessages(m);
    return c;
  }
  useEffect(() => {
    let active = true;
    const refresh = async () => {
      try {
        const c = await load();
        const run = c.runs.find((r) => r.id === watch);
        if (active && run && !["queued", "running"].includes(run.state)) {
          setWatch(undefined);
          onBuilding(false);
          if (run.state === "completed") await onChanged();
          else
            setError(
              run.error ||
                "Build needs attention. Your saved draft is preserved.",
            );
        }
      } catch (e) {
        if (active) setError((e as Error).message);
      }
    };
    void refresh();
    const timer = window.setInterval(refresh, 4000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [jobId, watch]);
  async function perform(fn: () => Promise<unknown>) {
    setBusy(true);
    setError("");
    try {
      await fn();
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const runs = control?.runs.filter((r) => r.job_id === jobId) || [];
  const buildActive = runs.some(
    (r) => r.kind === "resume_build" && ["queued", "running"].includes(r.state),
  );
  const interpretation = runs.find((r) => r.kind === "instruction_interpret");
  const match = runs.find((r) => r.kind === "resume_match");
  return (
    <section className="card agent-control">
      <div className="section-head">
        <div>
          <div className="eyebrow">RESUME ASSISTANT</div>
          <h2>Ask for a change or check the draft</h2>
        </div>
        <Badge>Saved</Badge>
      </div>
      <div className="agent-quick-grid">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const text = message;
            void perform(async () => {
              await api("/v2/instructions", "POST", {
                message: text,
                job_id: jobId,
                revision,
                request_id: crypto.randomUUID(),
              });
              setMessage("");
              await onChanged();
            });
          }}
        >
          <Field label="What would you like to change?">
            <textarea
              rows={3}
              maxLength={10000}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="For example: make the summary more focused on Power BI"
            />
          </Field>
          <button
            className="primary"
            disabled={busy || locked || buildActive || !message.trim()}
          >
            Apply instruction
          </button>
          {locked && <p className="small">Save your editor changes first.</p>}
        </form>
        <div className="build-card">
          <h3>Ready to check it?</h3>
          <p>
            Build the PDF and compare its wording with this job description. No
            AI call is used.
          </p>
          <button
            className="primary"
            disabled={busy || locked || buildActive}
            onClick={() =>
              void perform(async () => {
                const result = await api<{ id: string }>(
                  "/v2/agents/run",
                  "POST",
                  { kind: "resume_build", job_id: jobId },
                );
                setWatch(result.id);
                onBuilding(true);
              })
            }
          >
            {buildActive ? "Building & checking…" : "Build & check resume"}
          </button>
        </div>
      </div>
      <details className="assistant-details" open={messages.length > 0}>
        <summary>
          Instruction history {messages.length ? `(${messages.length})` : ""}
        </summary>
        <div
          className="instruction-history"
          aria-label="Instruction history"
          aria-live="polite"
        >
          {messages.length ? (
            messages.map((m) => (
              <article key={m.id}>
                <p>
                  <b>You</b> · {m.message}
                </p>
                <p>
                  <b>Result</b> · {m.response}
                </p>
                <Badge tone={m.state === "applied" ? "green" : "amber"}>
                  {m.state.replaceAll("_", " ")}
                </Badge>
              </article>
            ))
          ) : (
            <p className="muted">No instructions yet.</p>
          )}
        </div>
        <details>
          <summary>Supported commands</summary>
          <p>
            summary: text · skills: semicolon-separated skills · project: ID ·
            second project: ID · font: 10–12 · experience: details · note: fact
          </p>
          <p>
            Summary, skills, projects and font apply to this job. Experience and
            notes go to Profile for evidence review.
          </p>
        </details>
      </details>
      <details className="assistant-details">
        <summary>Optional AI help</summary>
        <div className="assistant-option">
          <div>
            <h3>Understand free text</h3>
            <p>
              Turns a longer request into commands you can review before using.
            </p>
          </div>
          <button
            className="secondary"
            disabled={
              busy ||
              locked ||
              !messages.length ||
              runs.some(
                (r) =>
                  r.kind === "instruction_interpret" &&
                  ["queued", "running"].includes(r.state),
              )
            }
            onClick={() =>
              void perform(() =>
                api("/v2/agents/run", "POST", {
                  kind: "instruction_interpret",
                  job_id: jobId,
                }),
              )
            }
          >
            Interpret request
          </button>
        </div>
        {interpretation && (
          <div>
            <Running run={interpretation} />
            {interpretation.result?.commands?.map(
              (command: string, index: number) => (
                <p key={index}>
                  <button
                    className="secondary"
                    onClick={() => setMessage(command)}
                  >
                    Use command
                  </button>{" "}
                  {command}
                </p>
              ),
            )}
            {interpretation.result?.clarifications?.map((q: string) => (
              <p key={q}>{q}</p>
            ))}
          </div>
        )}
        <div className="assistant-option">
          <div>
            <h3>Independent document review</h3>
            <p>AI sees only the current PDF text and job description.</p>
          </div>
          <button
            className="secondary"
            disabled={
              busy ||
              locked ||
              runs.some(
                (r) =>
                  r.kind === "resume_match" &&
                  ["queued", "running"].includes(r.state),
              )
            }
            onClick={() =>
              void perform(() =>
                api("/v2/agents/run", "POST", {
                  kind: "resume_match",
                  job_id: jobId,
                }),
              )
            }
          >
            Review PDF
          </button>
        </div>
        {match && (
          <>
            <Running run={match} />
            <p className="small">
              This review is tied to the PDF version saved when it started.
            </p>
            {match.result?.review && (
              <ReportView report={match.result.review} />
            )}
          </>
        )}
      </details>
      {control && (
        <details className="assistant-details">
          <summary>AI limit & worker history</summary>
          <p>
            {control.budget.calls_today} of {control.budget.daily_call_limit} AI
            calls used today · {control.budget.cached_results} saved results ·{" "}
            {control.budget.cache_hits} cache hits
          </p>
          <form
            className="actions"
            onSubmit={(e) => {
              e.preventDefault();
              void perform(() =>
                api("/v2/agent-control/budget", "PUT", {
                  daily_call_limit: limit ?? control.budget.daily_call_limit,
                }),
              );
            }}
          >
            <Field label="Maximum AI calls per day">
              <input
                type="number"
                min={0}
                max={50}
                value={limit ?? control.budget.daily_call_limit}
                onChange={(e) => setLimit(Number(e.target.value))}
              />
            </Field>
            <button className="secondary" disabled={busy}>
              Save limit
            </button>
          </form>
          <p className="small">
            Set 0 for saved results and free checks only. {control.budget.note}
          </p>
          <details>
            <summary>All worker runs ({control.runs.length})</summary>
            <div className="agent-run-list">
              {control.runs.slice(0, 30).map((r) => (
                <article key={r.id}>
                  <b>{r.kind.replaceAll("_", " ")}</b> ·{" "}
                  {r.job_id || "workspace"}
                  <Running run={r} />
                </article>
              ))}
            </div>
          </details>
        </details>
      )}
      {error && (
        <p role="alert" className="callout warning">
          {error}
        </p>
      )}
    </section>
  );
}
