import { useEffect, useRef, useState } from "react";
import {
  CheckCircle2,
  Copy,
  Download,
  FileText,
  RefreshCw,
  Save,
  Settings2,
  Sparkles,
} from "lucide-react";
import { api, fileUrl } from "../api";
import { Badge, Field, Modal, ReportView, Running } from "../components/UI";
import { JobList } from "../components/JobList";
import { macroSpan, readField, writeField } from "./studioFields";
import { AgentControl } from "./AgentControl";
import type { CoverLetter, Summary } from "../types";
type Draft = {
  match?: {
    score: number | null;
    current: boolean;
    revision: number;
    gaps: string[];
    limitations: string[];
    requirements: {
      term: string;
      matched: boolean;
      jd_excerpt: string;
      resume_excerpt: string;
    }[];
  };
  project_library: {
    id: string;
    title: string;
    rank: number | null;
    eligible: boolean;
    review_state: string;
  }[];
  source: string;
  revision: number;
  file_root: string;
  preview: {
    current: boolean;
    page_count: number;
    revision: number;
    path: string;
    layout?: {
      full_two_pages: boolean;
      pages: { page: number; fill_percent: number; bottom_blank_mm: number }[];
    };
    ranking?: { section_order: string[]; changes: string[] };
    body_font_pt?: number;
  } | null;
  versions: { revision: number; created_at: string }[];
  captures: { id: string; title: string; kind: string; deleted: boolean }[];
  warnings: string[];
  projects: { id: string; title: string }[];
};
const labels: Record<string, string> = {
  ResumeSummary: "Professional summary",
  CoreSkills: "Core skills · separate with semicolons",
  SecondProjectTitle: "Second project name",
  SecondProjectContext: "Second project context and tools",
  SecondProjectBulletOne: "Second project point 1",
  SecondProjectBulletTwo: "Second project point 2",
  SecondProjectBulletThree: "Second project point 3",
  SelectedProjectTitle: "First project name",
  SelectedProjectContext: "Project context and tools",
  SelectedProjectBulletOne: "Project point 1",
  SelectedProjectBulletTwo: "Project point 2",
  SelectedProjectBulletThree: "Project point 3",
};
const contentFields = ["ResumeSummary", "CoreSkills"];
const projectFields = [
  "SelectedProjectTitle",
  "SelectedProjectContext",
  "SelectedProjectBulletOne",
  "SelectedProjectBulletTwo",
  "SelectedProjectBulletThree",
  "SecondProjectTitle",
  "SecondProjectContext",
  "SecondProjectBulletOne",
  "SecondProjectBulletTwo",
  "SecondProjectBulletThree",
];
export default function ResumeStudio({
  data,
  jobId,
  onJob,
  onDetails,
  refresh,
}: {
  data: Summary;
  jobId: string | null;
  onJob: (id: string) => void;
  onDetails: (id: string) => void;
  refresh: () => Promise<void>;
}) {
  const job = data.jobs.find((j) => j.id === jobId);
  const [coverLetter, setCoverLetter] = useState<CoverLetter | null>(null);
  const [coverBusy, setCoverBusy] = useState(false);
  const [coverError, setCoverError] = useState("");
  return (
    <>
      <div className="page-title">
        <div>
          <h1>Resume Studio</h1>
          <p>
            Edit the important content, check the preview, then review the
            match.
          </p>
        </div>
        <Badge>Editable two-page draft</Badge>
      </div>
      <div className="studio-job-bar">
        <Field label="Company and role">
          <select value={jobId || ""} onChange={(e) => onJob(e.target.value)}>
            <option value="" disabled>
              Choose a saved job
            </option>
            {data.jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.company} · {j.title}
              </option>
            ))}
          </select>
        </Field>
        {job && (
          <div className="actions">
            <button
              className="primary"
              disabled={coverBusy || job.record_source === "gmail"}
              title={
                job.record_source === "gmail"
                  ? "Add the full job description first"
                  : `Generate a cover letter for ${job.company}`
              }
              onClick={async () => {
                setCoverBusy(true);
                setCoverError("");
                try {
                  const result = await api<CoverLetter>(
                    "/v2/jobs/" + job.id + "/cover-letter",
                    "POST",
                  );
                  setCoverLetter(result);
                  await refresh();
                } catch (e) {
                  setCoverError((e as Error).message);
                } finally {
                  setCoverBusy(false);
                }
              }}
            >
              <FileText size={16} />
              {coverBusy ? "Generating…" : "Cover letter"}
            </button>
            <button className="secondary" onClick={() => onDetails(job.id)}>
              Job details & progress
            </button>
          </div>
        )}
      </div>
      {coverError && (
        <div className="callout warning" role="alert">
          {coverError}
        </div>
      )}
      {job ? (
        <Editor
          key={job.id}
          jobId={job.id}
          company={job.company}
          data={data}
          refresh={refresh}
        />
      ) : (
        <section className="card spaced">
          <h2>Choose the role you’re preparing for</h2>
          <JobList jobs={data.jobs} onSelect={onJob} />
        </section>
      )}
      {coverLetter && (
        <Modal
          title={`${coverLetter.company} · Cover letter`}
          onClose={() => setCoverLetter(null)}
        >
          <div className="callout warning">
            Draft only. Review it against the job description before sending.
          </div>
          <div className="cover-letter-preview">{coverLetter.content}</div>
          <div className="actions">
            <button
              className="secondary"
              onClick={() => navigator.clipboard.writeText(coverLetter.content)}
            >
              Copy letter
            </button>
            <a
              className="primary"
              href={fileUrl(coverLetter.path)}
              target="_blank"
              rel="noreferrer"
            >
              Open saved file ↗
            </a>
          </div>
        </Modal>
      )}
    </>
  );
}
function Editor({
  jobId,
  company,
  data,
  refresh,
}: {
  jobId: string;
  company: string;
  data: Summary;
  refresh: () => Promise<void>;
}) {
  const [draft, setDraft] = useState<Draft>();
  const [source, setSource] = useState("");
  const [mode, setMode] = useState("content");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [auto, setAuto] = useState(true);
  const [restoring, setRestoring] = useState("");
  const [addingProject, setAddingProject] = useState(false);
  const [copyMessage, setCopyMessage] = useState("");
  const alive = useRef(true);
  const latestSource = useRef(source);
  latestSource.current = source;
  const key = "resume-studio:" + jobId;
  const base = "/v2/studio/" + jobId;
  const run = data.runs.find(
    (r) => r.kind === "resume_advisor" && r.job_id === jobId,
  );
  const dirty = !!draft && source !== draft.source;
  const activeRun = !!run && ["queued", "running"].includes(run.state);
  function edit(value: string) {
    setSource(value);
    sessionStorage.setItem(key, value);
    setError("");
  }
  async function open() {
    setBusy("Opening your company draft…");
    setError("");
    try {
      const d = await api<Draft>(base + "/open", "POST");
      if (!alive.current) return;
      setDraft(d);
      setSource(sessionStorage.getItem(key) ?? d.source);
      refresh().catch(() => {});
      if (!d.preview && !sessionStorage.getItem(key)) {
        setBusy("Filling two pages with ranked content…");
        const p = await api<Draft>(base + "/fill", "POST", {
          revision: d.revision,
        });
        if (alive.current) {
          setDraft(p);
          setSource(p.source);
        }
      }
    } catch (e) {
      if (alive.current) setError((e as Error).message);
    } finally {
      if (alive.current) setBusy("");
    }
  }
  useEffect(() => {
    alive.current = true;
    open();
    return () => {
      alive.current = false;
    };
  }, [jobId]);
  useEffect(() => {
    const warn = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault();
      }
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);
  async function save(compile = true, extra: Record<string, unknown> = {}) {
    if (!draft || busy) return;
    const snapshot = source;
    setBusy("Saving your edits…");
    setError("");
    try {
      let d = await api<Draft>(base, "PUT", {
        revision: draft.revision,
        source: snapshot,
        ...extra,
      });
      if (!alive.current) return;
      setDraft(d);
      if (Object.keys(extra).length) {
        setSource(d.source);
        sessionStorage.setItem(key, d.source);
        latestSource.current = d.source;
      } else if (latestSource.current === snapshot)
        sessionStorage.removeItem(key);
      refresh().catch(() => {});
      if (compile) {
        setBusy("Updating the preview…");
        d = await api<Draft>(base + "/preview", "POST", {
          revision: d.revision,
        });
        if (alive.current) setDraft(d);
      }
    } catch (e) {
      if (alive.current) setError((e as Error).message);
    } finally {
      if (alive.current) setBusy("");
    }
  }
  async function fillPages() {
    if (!draft || busy) return;
    setBusy("Filling two pages with ranked content…");
    setError("");
    try {
      let saved = draft;
      if (dirty) {
        saved = await api<Draft>(base, "PUT", {
          revision: draft.revision,
          source,
        });
        if (alive.current) setDraft(saved);
      }
      const fitted = await api<Draft>(base + "/fill", "POST", {
        revision: saved.revision,
      });
      if (!alive.current) return;
      setDraft(fitted);
      setSource(fitted.source);
      sessionStorage.removeItem(key);
      refresh().catch(() => {});
    } catch (e) {
      if (alive.current) setError((e as Error).message);
    } finally {
      if (alive.current) setBusy("");
    }
  }
  useEffect(() => {
    if (!auto || !dirty || busy || error) return;
    const timer = setTimeout(() => save(true), 1400);
    return () => clearTimeout(timer);
  }, [source, draft?.revision, busy, auto, error]);
  function downloadSource() {
    const url = URL.createObjectURL(
      new Blob([source], { type: "application/x-tex" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = company + "-resume.tex";
    a.click();
    URL.revokeObjectURL(url);
  }
  if (!draft)
    return (
      <section className="card spaced">
        <p role="status">{busy || "Unable to open this draft."}</p>
        {error && (
          <>
            <p role="alert">{error}</p>
            <button className="secondary" disabled={!!busy} onClick={open}>
              Retry
            </button>
          </>
        )}
      </section>
    );
  const current = !dirty && !!draft.preview?.current;
  return (
    <>
      <div className="studio-steps" aria-label="Resume workflow">
        <span className="active">
          <b>1</b> Edit content
        </span>
        <span className={current ? "complete" : ""}>
          <b>2</b> Check preview
        </span>
        <span>
          <b>3</b> Review & improve
        </span>
      </div>
      <div className="studio-toolbar">
        <div className="studio-save-state" role="status">
          {busy ? (
            <span className="working-dot" />
          ) : !dirty ? (
            <CheckCircle2 size={18} />
          ) : (
            <span className="unsaved-dot" />
          )}
          <span>
            <b>{busy || (dirty ? "Unsaved changes" : "All changes saved")}</b>
            <small>
              {dirty
                ? "Kept safely in this browser"
                : `Version ${draft.revision}`}
            </small>
          </span>
        </div>
        <div className="actions studio-primary-actions">
          <button className="primary" disabled={!!busy} onClick={() => save()}>
            <Save size={16} />
            Save & preview
          </button>
          {current && (
            <a
              className="secondary"
              href={fileUrl(draft.preview!.path + "/resume.pdf")}
              target="_blank"
              rel="noreferrer"
            >
              Open draft PDF ↗
            </a>
          )}
          <details className="studio-more-actions">
            <summary className="secondary">
              <Settings2 size={16} /> More tools
            </summary>
            <div className="studio-action-menu">
              <button
                className="text-button"
                disabled={!!busy}
                onClick={fillPages}
              >
                <Sparkles size={16} /> Fill two pages
              </button>
              <button
                className="text-button"
                disabled={!!busy || dirty}
                onClick={async () => {
                  setBusy("Syncing reviewed profile and ranking two projects…");
                  setError("");
                  try {
                    const d = await api<Draft>(base + "/sync-profile", "POST", {
                      revision: draft.revision,
                    });
                    setDraft(d);
                    setSource(d.source);
                    await refresh();
                  } catch (e) {
                    setError((e as Error).message);
                  } finally {
                    setBusy("");
                  }
                }}
              >
                <RefreshCw size={16} /> Sync profile & rank projects
              </button>
              <button
                className="text-button"
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(source);
                    setCopyMessage("Template copied");
                  } catch {
                    setCopyMessage(
                      "Copy unavailable. Download the source instead.",
                    );
                  }
                }}
              >
                <Copy size={16} /> Copy LaTeX template
              </button>
              <button className="text-button" onClick={downloadSource}>
                <Download size={16} /> Download LaTeX
              </button>
              <label className="check-line">
                <input
                  type="checkbox"
                  checked={auto}
                  onChange={(e) => setAuto(e.target.checked)}
                />
                Auto-save & refresh preview
              </label>
            </div>
          </details>
        </div>
      </div>
      {copyMessage && <p role="status">{copyMessage}</p>}
      {error && (
        <div className="callout warning" role="alert">
          <div>
            <b>Needs attention</b>
            <p className="jd-text">{error}</p>
            <button className="secondary" disabled={!!busy} onClick={open}>
              Reload saved draft
            </button>
          </div>
        </div>
      )}
      <div className="studio-split">
        <section className="studio-panel">
          <div className="studio-panel-heading">
            <h2>
              <FileText size={18} /> Edit resume
            </h2>
            <div className="segmented">
              <button
                className={mode === "content" ? "selected" : ""}
                onClick={() => setMode("content")}
              >
                Content
              </button>
              <button
                className={mode === "projects" ? "selected" : ""}
                onClick={() => setMode("projects")}
              >
                Projects
              </button>
              <button
                className={mode === "source" ? "selected" : ""}
                onClick={() => setMode("source")}
              >
                LaTeX source
              </button>
            </div>
          </div>
          <div className="studio-editor-body">
            <fieldset className="studio-edit-fields" disabled={!!busy}>
              {mode === "source" ? (
                <>
                  <div className="studio-help">
                    <b>Advanced editing</b>
                    <span>
                      Edit every section and the layout. Keep the named fields
                      so additions can still be tracked.
                    </span>
                  </div>
                  <textarea
                    className="source-editor"
                    aria-label="LaTeX resume source"
                    spellCheck={false}
                    value={source}
                    maxLength={150000}
                    onChange={(e) => edit(e.target.value)}
                  />
                </>
              ) : mode === "projects" ? (
                <>
                  <div className="studio-help">
                    <b>Two projects are required</b>
                    <span>
                      The best evidenced matches are selected automatically. You
                      can replace either one.
                    </span>
                  </div>
                  <div className="project-picker-grid">
                    <Field label="Replace first project">
                      <select
                        value=""
                        disabled={!!busy || dirty}
                        onChange={(e) =>
                          save(true, { project_id: e.target.value })
                        }
                      >
                        <option value="">Choose from Profile…</option>
                        {draft.projects.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.title}
                          </option>
                        ))}
                      </select>
                    </Field>
                    <Field label="Replace second project">
                      <select
                        value=""
                        disabled={!!busy || dirty}
                        onChange={(e) =>
                          save(true, { second_project_id: e.target.value })
                        }
                      >
                        <option value="">Choose from Profile…</option>
                        {draft.projects.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.title}
                          </option>
                        ))}
                      </select>
                    </Field>
                  </div>
                  <button
                    className="secondary"
                    disabled={!!busy}
                    onClick={() => setAddingProject(true)}
                  >
                    ＋ Add my own project
                  </button>
                  <details className="studio-inline-details">
                    <summary>See ranked project library</summary>
                    <ol>
                      {draft.project_library.map((p) => (
                        <li key={p.id}>
                          <b>
                            {p.rank ? `#${p.rank} ` : ""}
                            {p.title}
                          </b>
                          <br />
                          <small>
                            {p.id} ·{" "}
                            {p.eligible
                              ? "Ready to select"
                              : p.review_state + " · evidence review needed"}
                          </small>
                        </li>
                      ))}
                    </ol>
                    <p className="small">
                      Ranks reflect job-description overlap, not hiring
                      probability. The two projects must be distinct.
                    </p>
                  </details>
                  {projectFields.map(
                    (name) =>
                      macroSpan(source, name) && (
                        <Field label={labels[name]} key={name}>
                          <textarea
                            rows={
                              name === "ResumeSummary"
                                ? 7
                                : name.includes("Bullet")
                                  ? 4
                                  : 3
                            }
                            value={readField(source, name)}
                            onChange={(e) =>
                              edit(writeField(source, name, e.target.value))
                            }
                          />
                        </Field>
                      ),
                  )}
                  <p className="small">
                    New projects and skills are captured in Profile for evidence
                    review when you save.
                  </p>
                </>
              ) : (
                <>
                  <div className="studio-help">
                    <b>Start with the story</b>
                    <span>
                      Keep the summary specific to this role and put the
                      strongest matching skills first.
                    </span>
                  </div>
                  {contentFields.map(
                    (name) =>
                      macroSpan(source, name) && (
                        <Field label={labels[name]} key={name}>
                          <textarea
                            rows={name === "ResumeSummary" ? 8 : 6}
                            value={readField(source, name)}
                            onChange={(e) =>
                              edit(writeField(source, name, e.target.value))
                            }
                          />
                        </Field>
                      ),
                  )}
                  <button
                    className="secondary"
                    onClick={() => setMode("projects")}
                  >
                    Continue to projects →
                  </button>
                </>
              )}
            </fieldset>
          </div>
        </section>
        <section className="studio-panel preview-panel">
          <div className="studio-panel-heading">
            <h2>Resume preview</h2>
            <Badge tone={current ? "green" : "amber"}>
              {current ? "Current draft" : "Preview needs updating"}
            </Badge>
          </div>
          <div className="studio-preview-body">
            {draft.preview ? (
              <>
                <p className="preview-caption">
                  Version {draft.preview.revision} · {draft.preview.page_count}{" "}
                  {draft.preview.page_count === 1 ? "page" : "pages"} ·{" "}
                  {draft.preview.page_count === 2
                    ? "A4 target: 2 pages"
                    : "Adjust content to reach two pages"}
                </p>
                {draft.preview.layout && (
                  <div className="layout-meter">
                    <Badge
                      tone={
                        current && draft.preview.layout.full_two_pages
                          ? "green"
                          : "amber"
                      }
                    >
                      {draft.preview.layout.full_two_pages
                        ? "Two full pages"
                        : "Page fill needs attention"}
                    </Badge>
                    <p>
                      {draft.preview.layout.pages
                        .map((p) => `Page ${p.page}: ${p.fill_percent}% filled`)
                        .join(" · ")}
                      {draft.preview.body_font_pt
                        ? ` · ${draft.preview.body_font_pt}pt body`
                        : ""}
                    </p>
                    <small>
                      Measured within normal margins. Content and evidence still
                      need review.
                    </small>
                  </div>
                )}
                {draft.preview.ranking && (
                  <details className="layout-ranking">
                    <summary>Content order and additions</summary>
                    <p>{draft.preview.ranking.section_order.join(" → ")}</p>
                    <ul>
                      {draft.preview.ranking.changes.map((c) => (
                        <li key={c}>{c}</li>
                      ))}
                    </ul>
                  </details>
                )}
                {!current && (
                  <p className="callout warning">
                    Showing the last successful preview. Your newest edits are
                    not shown yet.
                  </p>
                )}
                {Array.from({ length: draft.preview.page_count }, (_, i) => (
                  <img
                    key={i}
                    className="resume-page"
                    alt={company + " resume preview, page " + (i + 1)}
                    src={fileUrl(
                      draft.preview!.path +
                        "/page-" +
                        String(i + 1).padStart(2, "0") +
                        ".png",
                    )}
                  />
                ))}
              </>
            ) : (
              <div className="studio-empty">
                <FileText size={42} />
                <h3>Your preview will appear here</h3>
                <p>Save and preview to compile your resume.</p>
              </div>
            )}
          </div>
        </section>
      </div>
      <AgentControl
        jobId={jobId}
        revision={draft.revision}
        locked={!!busy || dirty}
        onBuilding={(active) =>
          setBusy(active ? "Building and checking your resume…" : "")
        }
        onChanged={async () => {
          const next = await api<Draft>(base);
          setDraft(next);
          setSource(next.source);
          sessionStorage.removeItem(key);
          await refresh();
        }}
      />
      {addingProject && (
        <NewProject
          onClose={() => setAddingProject(false)}
          onAdd={(values) => {
            let next = source;
            const names = [
              "SelectedProjectID",
              "SelectedProjectTitle",
              "SelectedProjectContext",
              "SelectedProjectBulletOne",
              "SelectedProjectBulletTwo",
              "SelectedProjectBulletThree",
            ];
            for (const name of names) {
              if (!macroSpan(next, name))
                next = next.replace(
                  "\\begin{document}",
                  "\\newcommand{\\" + name + "}{}\n\\begin{document}",
                );
              next = writeField(next, name, values[name] || "");
            }
            const start = next.indexOf("% SELECTED_PROJECT_BLOCK_START"),
              end = next.indexOf("% SELECTED_PROJECT_BLOCK_END");
            if (start < 0 || end < start) {
              setError(
                "Restore the selected-project block markers in LaTeX source before adding a project.",
              );
              return;
            }
            const block =
              "% SELECTED_PROJECT_BLOCK_START\n\\textbf{\\SelectedProjectTitle}\\\\\n\\textit{\\SelectedProjectContext}\n\\begin{resumeitems}\n" +
              ["One", "Two", "Three"]
                .filter((n) => values["SelectedProjectBullet" + n])
                .map((n) => "\\item \\SelectedProjectBullet" + n)
                .join("\n") +
              "\n\\end{resumeitems}\n";
            next = next.slice(0, start) + block + next.slice(end);
            if (values.skills)
              next = writeField(
                next,
                "CoreSkills",
                readField(next, "CoreSkills") + "; " + values.skills,
              );
            edit(next);
            setAddingProject(false);
            setMode("projects");
          }}
        />
      )}
      <details className="studio-advanced">
        <summary>
          <span>
            <b>Review details & advanced tools</b>
            <small>
              Match breakdown, company research, Profile captures and version
              history
            </small>
          </span>
        </summary>
        <div className="studio-advanced-body">
          {draft.match && (
            <section className="card">
              <div className="section-head">
                <div>
                  <div className="eyebrow">
                    INDEPENDENT MATCHER · PDF + JD ONLY
                  </div>
                  <h2>
                    JD term coverage:{" "}
                    {draft.match.score === null
                      ? "Not scored"
                      : `${draft.match.score}/100`}
                  </h2>
                </div>
                <Badge tone={draft.match.current && !dirty ? "green" : "amber"}>
                  {draft.match.current && !dirty
                    ? "Current PDF"
                    : "Stale · rebuild"}
                </Badge>
              </div>
              <p>
                Version {draft.match.revision} · no profile access · zero AI
                calls.{" "}
                {draft.match.gaps.length
                  ? `Missing terms: ${draft.match.gaps.join(", ")}.`
                  : "No gaps in the detected vocabulary."}
              </p>
              <details>
                <summary>Evidence and scoring limits</summary>
                {draft.match.requirements.map((r) => (
                  <p key={r.term}>
                    <b>
                      {r.matched ? "✓" : "—"} {r.term}
                    </b>
                    <br />
                    JD: {r.jd_excerpt}
                    <br />
                    PDF: {r.resume_excerpt || "Not found"}
                  </p>
                ))}
                {draft.match.limitations.map((l) => (
                  <p className="small" key={l}>
                    {l}
                  </p>
                ))}
              </details>
            </section>
          )}
          <div className="studio-agents">
            <section className="card">
              <div className="section-head">
                <div>
                  <div className="eyebrow">AGENT 1 · INDEPENDENT RESEARCH</div>
                  <h2>What this company wants to see</h2>
                </div>
                <Badge>No profile access</Badge>
              </div>
              <p>
                Recent company research, resume priorities, suggested projects
                and skills. Project ideas stay here until you build them and add
                your evidence.
              </p>
              <button
                className="secondary"
                disabled={activeRun}
                onClick={async () => {
                  try {
                    await api("/v2/agents/run", "POST", {
                      kind: "resume_advisor",
                      job_id: jobId,
                    });
                    await refresh();
                  } catch (e) {
                    setError((e as Error).message);
                  }
                }}
              >
                <RefreshCw size={15} />
                {activeRun
                  ? "Research in progress…"
                  : run
                    ? "Research · reuse cache"
                    : "Research this company"}
              </button>
              {run && <Running run={run} />}
              {run?.result?.advice && <ReportView report={run.result.advice} />}
              {run?.result?.research && (
                <details className="report-section">
                  <summary>Company research and sources</summary>
                  <ReportView report={run.result.research} />
                </details>
              )}
            </section>
            <section className="card">
              <div className="eyebrow">AGENT 2 · RULE-BASED TRACKER</div>
              <h2>Keep your experience with you</h2>
              <p>
                Runs on each save. Tracks project fields and skills in this
                template, keeps version history and captures new entries in
                Profile.
              </p>
              {draft.warnings.map((w) => (
                <p className="tracker-note" key={w}>
                  {w}
                </p>
              ))}
              <h3>Captured in Profile</h3>
              {draft.captures.length ? (
                <ul>
                  {draft.captures.map((c) => (
                    <li key={c.id + c.title}>
                      {c.title}{" "}
                      <Badge>
                        {c.deleted
                          ? "Removed from Profile"
                          : "Saved for evidence review"}
                      </Badge>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="muted">
                  New projects and skills you add will appear here.
                </p>
              )}
              <h3>Version history</h3>
              <Field label="Restore an earlier version">
                <select
                  value={restoring}
                  onChange={(e) => setRestoring(e.target.value)}
                >
                  <option value="">Choose a saved version…</option>
                  {draft.versions.map((v) => (
                    <option key={v.revision} value={v.revision}>
                      Version {v.revision} ·{" "}
                      {new Date(v.created_at).toLocaleString()}
                    </option>
                  ))}
                </select>
              </Field>
              <button
                className="secondary"
                disabled={!!busy || dirty || !restoring}
                onClick={() =>
                  save(true, { restore_revision: Number(restoring) })
                }
              >
                Restore as a new version
              </button>
              <p className="small">
                Save your current edits first. Restoring a resume keeps its
                history and previously captured Profile entries.
              </p>
            </section>
          </div>
        </div>
      </details>
    </>
  );
}

function NewProject({
  onClose,
  onAdd,
}: {
  onClose: () => void;
  onAdd: (values: Record<string, string>) => void;
}) {
  const [form, setForm] = useState<Record<string, string>>({
    SelectedProjectID: "USER-PROJECT",
    SelectedProjectTitle: "",
    SelectedProjectContext: "",
    SelectedProjectBulletOne: "",
    SelectedProjectBulletTwo: "",
    SelectedProjectBulletThree: "",
    skills: "",
  });
  return (
    <Modal title="Add your project" onClose={onClose}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onAdd(form);
        }}
      >
        <p>
          This replaces the selected resume project. Your other projects stay in
          Profile. Describe work you have actually done; proposed company
          projects stay in the advisor.
        </p>
        {[
          "SelectedProjectTitle",
          "SelectedProjectContext",
          "SelectedProjectBulletOne",
          "SelectedProjectBulletTwo",
          "SelectedProjectBulletThree",
          "skills",
        ].map((name) => (
          <Field
            key={name}
            label={
              name === "skills"
                ? "New skills used · optional, separate with semicolons"
                : labels[name] +
                  (name === "SelectedProjectBulletThree" ? " · optional" : "")
            }
          >
            <textarea
              required={
                !["SelectedProjectBulletThree", "skills"].includes(name)
              }
              rows={3}
              maxLength={name === "SelectedProjectTitle" ? 250 : 2000}
              value={form[name]}
              onChange={(e) => setForm({ ...form, [name]: e.target.value })}
            />
          </Field>
        ))}
        <button className="primary">Add to resume</button>
        <p className="small">
          On save, Agent 2 also captures this project and any new skills in
          Profile for evidence review.
        </p>
      </form>
    </Modal>
  );
}
