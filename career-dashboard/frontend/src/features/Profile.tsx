import { useEffect, useState } from "react";
import { Pencil, Plus, Trash2, ShieldCheck } from "lucide-react";
import { api } from "../api";
import { Badge, Field, Modal, RichText } from "../components/UI";
import type { Knowledge, ProfileData } from "../types";
const kinds = [
  "personal",
  "skill",
  "project",
  "experience",
  "education",
  "certification",
  "fact",
];
export default function Profile({
  notify,
  refresh,
}: {
  notify: (s: string, e?: boolean) => void;
  refresh: () => Promise<void>;
}) {
  const [data, setData] = useState<ProfileData>();
  const [error, setError] = useState("");
  const [category, setCategory] = useState("skill");
  const [edit, setEdit] = useState<Partial<Knowledge> | null>(null);
  const [remove, setRemove] = useState<Knowledge | null>(null);
  const [busy, setBusy] = useState(false);
  async function load() {
    try {
      setData(await api("/v2/profile"));
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    load();
  }, []);
  if (error)
    return (
      <div role="alert">
        {error}
        <button onClick={load}>Retry</button>
      </div>
    );
  if (!data) return <p>Loading your knowledge library…</p>;
  return (
    <>
      <div className="page-title">
        <div>
          <div className="eyebrow">YOUR INFORMATION, YOUR CONTROL</div>
          <h1>Profile</h1>
          <p>
            See what the agents know. Add, correct or remove any active entry.
          </p>
        </div>
        <button
          className="primary"
          onClick={() =>
            setEdit({ kind: category, title: "", summary: "", data: {} })
          }
        >
          <Plus size={17} />
          Add entry
        </button>
      </div>
      <div className="callout">
        <ShieldCheck size={21} />
        <div>
          <b>
            {data.items.length} active entries · {data.removed} removed
          </b>
          <p>
            Search and profile comparison use these active entries. Original
            source documents remain available for provenance. Edited facts need
            evidence reconciliation before a new resume can be generated.
          </p>
        </div>
      </div>
      <section className="card spaced">
        <div className="category-list">
          {kinds.map((k) => (
            <button
              key={k}
              className={category === k ? "selected" : ""}
              onClick={() => setCategory(k)}
            >
              {k}
              <span>{data.items.filter((i) => i.kind === k).length}</span>
            </button>
          ))}
        </div>
        <div className="knowledge-grid">
          {data.items
            .filter((i) => i.kind === category)
            .map((item) => (
              <article key={item.id} className="knowledge-item">
                <div className="section-title">
                  <Badge
                    tone={
                      item.review_state === "registered" ? "green" : "amber"
                    }
                  >
                    {item.review_state === "registered"
                      ? item.data.status || "Registered"
                      : "User updated"}
                  </Badge>
                  <div className="actions">
                    <button
                      className="icon-button"
                      aria-label={"Edit " + item.title}
                      onClick={() => setEdit({ ...item })}
                    >
                      <Pencil size={16} />
                    </button>
                    <button
                      className="icon-button"
                      aria-label={"Remove " + item.title}
                      onClick={() => setRemove(item)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                <h3>{item.title}</h3>
                <p className="preserve">
                  {item.summary || "See source details below."}
                </p>
                <details>
                  <summary>Evidence & original details</summary>
                  <small>
                    {item.id} · Revision {item.revision}
                    <br />
                    {item.source}
                  </small>
                  <pre>{JSON.stringify(item.data, null, 2)}</pre>
                </details>
              </article>
            ))}
        </div>
      </section>
      <section className="card spaced">
        <h2>Agents working for you</h2>
        <div className="agent-grid">
          {data.agents.map((a) => (
            <article key={a.id}>
              <Badge tone={a.profile_access ? "neutral" : "green"}>
                {a.profile_access
                  ? "Uses active profile"
                  : "No candidate profile"}
              </Badge>
              <h3>{a.name}</h3>
              <p>{a.does}</p>
              <small>
                <b>Inputs:</b> {a.reads}
                <br />
                <b>Runs as:</b> {a.implementation}
              </small>
            </article>
          ))}
        </div>
        <details>
          <summary>Skills & workflow instructions</summary>
          {data.skills.map((s) => (
            <p key={s.name}>
              <b>{s.name}</b> — {s.purpose}
              <br />
              <code>{s.path}</code>
            </p>
          ))}
        </details>
      </section>
      <section className="card spaced">
        <h2>Original evidence & source documents</h2>
        <p>
          These preserved sources explain where your profile came from. Agents
          use the active entries above; removed entries remain only in the audit
          history and original documents.
        </p>
        {Object.entries(data.sources).map(([name, text]) => (
          <details key={name}>
            <summary>{name}</summary>
            <RichText text={text} />
          </details>
        ))}
        <details>
          <summary>Canonical profile configuration</summary>
          <pre>{JSON.stringify(data.configuration, null, 2)}</pre>
        </details>
        <details>
          <summary>Complete evidence registry</summary>
          <pre>{JSON.stringify(data.registry, null, 2)}</pre>
        </details>
      </section>
      {edit && (
        <Modal
          title={edit.id ? "Edit profile entry" : "Add profile entry"}
          onClose={() => setEdit(null)}
        >
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              setBusy(true);
              try {
                await api(
                  "/v2/profile/items" +
                    (edit.id ? "/" + encodeURIComponent(edit.id) : ""),
                  edit.id ? "PUT" : "POST",
                  edit,
                );
                await load();
                await refresh();
                setEdit(null);
                notify(
                  "Profile saved. Search and comparison will use this update.",
                );
              } catch (e) {
                notify((e as Error).message, true);
              } finally {
                setBusy(false);
              }
            }}
          >
            <Field label="Category">
              <select
                value={edit.kind}
                onChange={(e) => setEdit({ ...edit, kind: e.target.value })}
              >
                {kinds.map((k) => (
                  <option key={k}>{k}</option>
                ))}
              </select>
            </Field>
            <Field label="Title">
              <input
                required
                maxLength={250}
                value={edit.title}
                onChange={(e) => setEdit({ ...edit, title: e.target.value })}
              />
            </Field>
            <Field label="What should AI know? Include dates, skills, evidence and any limitations.">
              <textarea
                rows={9}
                maxLength={30000}
                value={edit.summary}
                onChange={(e) => setEdit({ ...edit, summary: e.target.value })}
              />
            </Field>
            <button className="primary" disabled={busy}>
              {busy ? "Saving…" : "Save entry"}
            </button>
          </form>
        </Modal>
      )}
      {remove && (
        <Modal
          title="Remove active profile entry"
          onClose={() => setRemove(null)}
        >
          <p>
            Remove <b>{remove.title}</b> from the profile used for search and
            comparison? Its original source and change history are preserved.
          </p>
          <button
            className="danger"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                await api(
                  "/v2/profile/items/" + encodeURIComponent(remove.id),
                  "DELETE",
                );
                await load();
                await refresh();
                setRemove(null);
                notify("Entry removed from the active profile.");
              } catch (e) {
                notify((e as Error).message, true);
              } finally {
                setBusy(false);
              }
            }}
          >
            Remove entry
          </button>
        </Modal>
      )}
    </>
  );
}
