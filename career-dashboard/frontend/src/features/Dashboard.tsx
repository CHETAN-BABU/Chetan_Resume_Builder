import { useState } from "react";
import {
  Mail as MailIcon,
  RefreshCw,
  ArrowRight,
  Target,
  CalendarCheck,
  BriefcaseBusiness,
  MessageCircle,
  Settings2,
} from "lucide-react";
import { api, safeUrl } from "../api";
import { Badge, Empty, Modal, Field, Running } from "../components/UI";
import { JobList } from "../components/JobList";
import type { Summary, Mail, Job } from "../types";
type Props = {
  data: Summary;
  refresh: () => Promise<void>;
  notify: (text: string, error?: boolean) => void;
  onJob: (id: string) => void;
  onDaily: () => void;
  onAdd: () => void;
};
export default function Dashboard({
  data,
  refresh,
  notify,
  onJob,
  onDaily,
  onAdd,
}: Props) {
  const [mail, setMail] = useState<Mail | null>(null);
  const [section, setSection] = useState("applications");
  const [busy, setBusy] = useState(false);
  const [schedule, setSchedule] = useState<any>(null);
  const running = data.runs.find(
    (r) => r.kind === "email" && ["queued", "running"].includes(r.state),
  );
  const pending = data.mail.messages.filter((m) => m.state === "pending");
  async function sync() {
    setBusy(true);
    try {
      await api("/v2/agents/run", "POST", { kind: "email" });
      await refresh();
      notify("Gmail sync started. Only job-related messages are read.");
    } catch (e) {
      notify((e as Error).message, true);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="page-title">
        <div>
          <div className="eyebrow">YOUR APPLICATIONS, IN ONE PLACE</div>
          <h1>Dashboard</h1>
          <p>Small steps today. More opportunities tomorrow.</p>
        </div>
        <button className="primary" onClick={onAdd}>
          ＋ Save a job
        </button>
      </div>
      <div className="metrics">
        {[
          [BriefcaseBusiness, data.counts.applied, "Applications recorded"],
          [MessageCircle, data.counts.interviews, "Interview stage"],
          [CalendarCheck, data.counts.offers, "Offers"],
          [Target, data.goals.remaining_today, "Left for today"],
        ].map(([Icon, value, label]: any) => (
          <section className="card metric" key={label}>
            <span className="metric-icon">
              <Icon size={20} />
            </span>
            <strong>{value}</strong>
            <span>{label}</span>
          </section>
        ))}
      </div>
      <div className="dashboard-top">
        <section className="focus-card">
          <div>
            <Badge tone="lime">TODAY’S FOCUS</Badge>
            <h2>
              {data.goals.remaining_today
                ? `${data.goals.remaining_today} applications to move forward.`
                : "Your daily target is complete."}
            </h2>
            <p>
              {data.goals.carryover
                ? `${data.goals.daily_base} planned + ${data.goals.carryover} carried forward. Your unfinished work stays with you.`
                : "Your progress starts with one well-matched role."}
            </p>
            <button onClick={onDaily}>
              Open daily plan <ArrowRight size={17} />
            </button>
          </div>
          <div className="progress-dial">
            <strong>
              {data.goals.today_completed}
              <small>/{data.goals.today_target}</small>
            </strong>
            <span>today</span>
          </div>
        </section>
        <section className="card email-card">
          <div className="section-title">
            <h2>
              <MailIcon size={20} /> Gmail connection
            </h2>
            <Badge tone={data.mail.connection.connected ? "green" : "amber"}>
              {data.mail.connection.connected ? "Connected" : "Not synced"}
            </Badge>
          </div>
          <strong>
            {data.mail.connection.email || "Use your connected Gmail account"}
          </strong>
          <p>
            {data.mail.connection.last_synced_at
              ? "Last synced " +
                new Date(data.mail.connection.last_synced_at).toLocaleString(
                  "en-IE",
                )
              : "Sync to find application confirmations and status updates."}
          </p>
          <div className="actions">
            <button
              className="secondary"
              disabled={busy || !!running}
              onClick={sync}
            >
              <RefreshCw size={16} className={running ? "spin" : ""} />
              {running ? "Syncing…" : "Sync Gmail"}
            </button>
            <button
              className="icon-button"
              aria-label="Email sync schedule"
              onClick={async () => {
                try {
                  setSchedule(await api("/v2/email-schedule"));
                } catch (e) {
                  notify((e as Error).message, true);
                }
              }}
            >
              <Settings2 size={18} />
            </button>
          </div>
          {data.mail.connection.coverage && (
            <details>
              <summary>Sync coverage</summary>
              <p>{data.mail.connection.coverage}</p>
            </details>
          )}
          {running && (
            <small className="muted">
              This may take a few minutes. You can keep working.
            </small>
          )}
        </section>
      </div>
      <section className="card workspace-panel">
        <div className="section-title">
          <div className="segmented">
            <button
              className={section === "applications" ? "selected" : ""}
              onClick={() => setSection("applications")}
            >
              Applications <span>{data.jobs.length}</span>
            </button>
            <button
              className={section === "email" ? "selected" : ""}
              onClick={() => setSection("email")}
            >
              Email evidence <span>{pending.length} to review</span>
            </button>
            <button
              className={section === "activity" ? "selected" : ""}
              onClick={() => setSection("activity")}
            >
              Activity
            </button>
          </div>
        </div>
        {section === "applications" ? (
          <JobList jobs={data.jobs} onSelect={onJob} />
        ) : section === "email" ? (
          <>
            <p className="muted">
              Exact application confirmations are linked to their original
              email. Reminders and ambiguous matches need review.
            </p>
            {data.mail.messages.length ? (
              <div className="mail-list">
                {data.mail.messages.map((m) => (
                  <button
                    className="mail-row"
                    key={m.id}
                    onClick={() => setMail(m)}
                  >
                    <MailIcon size={18} />
                    <span>
                      <strong>{m.company || m.sender}</strong>
                      <span>{m.subject}</span>
                      <small>
                        {m.received_at.slice(0, 10)} ·{" "}
                        {m.role || "Role needs review"}
                      </small>
                    </span>
                    <Badge
                      tone={
                        m.state === "confirmed"
                          ? "green"
                          : m.kind === "reminder"
                            ? "neutral"
                            : "amber"
                      }
                    >
                      {m.state === "pending" ? m.kind : m.state}
                    </Badge>
                    <ArrowRight size={17} />
                  </button>
                ))}
              </div>
            ) : (
              <Empty title="Your inbox can fill in the gaps">
                Run a Gmail sync to see evidence here.
              </Empty>
            )}
          </>
        ) : (
          <div className="timeline">
            {data.activity.map((e) => (
              <div key={e.id}>
                <span className="timeline-dot" />
                <div>
                  <strong>{e.action.replaceAll("_", " ")}</strong>
                  <small>
                    {new Date(e.occurred_at).toLocaleString("en-IE")}
                  </small>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
      {data.runs
        .filter(
          (r, i, runs) =>
            r.state === "failed" &&
            runs.findIndex(
              (x) => x.kind === r.kind && x.job_id === r.job_id,
            ) === i,
        )
        .slice(0, 1)
        .map((r) => (
          <Running key={r.id} run={r} />
        ))}
      {mail && (
        <MailReview
          mail={mail}
          jobs={data.jobs}
          onClose={() => setMail(null)}
          refresh={refresh}
          notify={notify}
          onAdd={onAdd}
        />
      )}
      {schedule && (
        <Modal title="Email sync schedule" onClose={() => setSchedule(null)}>
          <p>
            Syncs use your signed-in Codex access and run while this app is
            open. Only job-related emails are read.
          </p>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              try {
                await api("/v2/email-schedule", "PUT", schedule);
                notify("Email schedule saved.");
                setSchedule(null);
              } catch (e) {
                notify((e as Error).message, true);
              }
            }}
          >
            <label className="check-line">
              <input
                type="checkbox"
                checked={schedule.enabled}
                onChange={(e) =>
                  setSchedule({ ...schedule, enabled: e.target.checked })
                }
              />
              Sync automatically while the app is running
            </label>
            <Field label="Hours between syncs">
              <input
                type="number"
                min="1"
                max="24"
                value={schedule.hours}
                onChange={(e) =>
                  setSchedule({ ...schedule, hours: Number(e.target.value) })
                }
              />
            </Field>
            <button className="primary">Save schedule</button>
          </form>
        </Modal>
      )}
    </>
  );
}
function MailReview({
  mail,
  jobs,
  onClose,
  refresh,
  notify,
  onAdd,
}: {
  mail: Mail;
  jobs: Job[];
  onClose: () => void;
  refresh: () => Promise<void>;
  notify: Props["notify"];
  onAdd: () => void;
}) {
  const [id, setId] = useState(mail.job_id || "");
  const [busy, setBusy] = useState(false);
  async function resolve(action: string) {
    setBusy(true);
    try {
      await api("/v2/mail/" + mail.id + "/resolve", "POST", {
        job_id: id || null,
        action,
      });
      await refresh();
      notify(
        action === "dismiss"
          ? "Email dismissed."
          : "Application updated with linked email evidence.",
      );
      onClose();
    } catch (e) {
      notify((e as Error).message, true);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal title="Review email evidence" onClose={onClose}>
      <div className="actions">
        <Badge tone="amber">{mail.kind}</Badge>
        <Badge>{mail.state}</Badge>
      </div>
      <h3>{mail.subject}</h3>
      <p>
        {mail.sender}
        <br />
        {new Date(mail.received_at).toLocaleString("en-IE")}
      </p>
      <blockquote>{mail.excerpt}</blockquote>
      <p>{mail.reason}</p>
      <a
        href={safeUrl("https://mail.google.com/mail/u/0/#all/" + mail.id)}
        target="_blank"
        rel="noreferrer"
      >
        Open original email ↗
      </a>
      {mail.state === "pending" && (
        <>
          <Field label="Matching application">
            <select value={id} onChange={(e) => setId(e.target.value)}>
              <option value="">Choose the exact company and role</option>
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.company} · {j.title}
                </option>
              ))}
            </select>
          </Field>
          <p className="small">
            {mail.submission_date
              ? "Email states application date: " + mail.submission_date
              : "No submission date is stated. The confirmation receipt date is kept separately."}
          </p>
          <div className="actions">
            <button
              className="primary"
              disabled={
                busy || !id || ["reminder", "uncertain"].includes(mail.kind)
              }
              onClick={() => resolve("confirm")}
            >
              Confirm status update
            </button>
            <button
              className="secondary"
              disabled={busy}
              onClick={() => resolve("dismiss")}
            >
              Dismiss
            </button>
          </div>
          <button
            className="text-button"
            onClick={() => {
              onClose();
              onAdd();
            }}
          >
            Job not listed? Save its posting first
          </button>
        </>
      )}
    </Modal>
  );
}
