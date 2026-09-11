import { useCallback, useEffect, useState } from "react";
import {
  LayoutDashboard,
  Search,
  FileText,
  UserRound,
  CheckCircle2,
  X,
} from "lucide-react";
import { api } from "./api";
import { Field, Modal, NoticeContext } from "./components/UI";
import JobDetail from "./components/JobDetail";
import Dashboard from "./features/Dashboard";
import DailySearch from "./features/DailySearch";
import ResumeStudio from "./features/ResumeStudio";
import Profile from "./features/Profile";
import type { Summary } from "./types";
const tabs = [
  ["dashboard", "Dashboard", LayoutDashboard],
  ["daily", "Daily Search", Search],
  ["resumes", "Resume Studio", FileText],
  ["profile", "Profile", UserRound],
] as const;
function routeFromHash() {
  const r = location.hash.slice(1);
  return tabs.some((t) => t[0] === r) ? r : "dashboard";
}
export default function App() {
  const [route, setRoute] = useState(routeFromHash);
  const [data, setData] = useState<Summary>();
  const [error, setError] = useState("");
  const [toast, setToast] = useState<{ text: string; error: boolean } | null>(
    null,
  );
  const [selected, setSelected] = useState<string | null>(null);
  const [add, setAdd] = useState(false);
  const notify = useCallback(
    (text: string, error = false) => setToast({ text, error }),
    [],
  );
  const refresh = useCallback(async () => {
    try {
      setData(await api("/v2/summary"));
      setError("");
    } catch (e) {
      setError((e as Error).message);
      throw e;
    }
  }, []);
  useEffect(() => {
    refresh().catch(() => {});
    const timer = setInterval(() => refresh().catch(() => {}), 8000);
    const hash = () => setRoute(routeFromHash());
    window.addEventListener("hashchange", hash);
    return () => {
      clearInterval(timer);
      window.removeEventListener("hashchange", hash);
    };
  }, [refresh]);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 10000);
    return () => clearTimeout(timer);
  }, [toast]);
  function navigate(r: string) {
    location.hash = r;
    setRoute(r);
  }
  const job = data?.jobs.find((j) => j.id === selected);
  return (
    <NoticeContext.Provider value={toast}>
      <div className="app">
        <aside>
          <div className="brand">
            <b>C</b>
            <div>
              CHETAN<small>CAREER WORKSPACE</small>
            </div>
          </div>
          <nav aria-label="Main navigation">
            {tabs.map(([id, label, Icon]) => (
              <button
                key={id}
                title={label}
                aria-current={route === id ? "page" : undefined}
                className={route === id ? "active" : ""}
                onClick={() => navigate(id)}
              >
                <Icon size={20} />
                <span>{label}</span>
              </button>
            ))}
          </nav>
          <div className="sidebar-note">
            <span className="status-dot" /> Personal workspace
            <p>
              A little progress.
              <br />
              Every single day.
            </p>
            <small>Saved locally · Dublin time</small>
          </div>
        </aside>
        <main>
          <header>
            <span>YOUR CAREER WORKSPACE</span>
            <span className="header-status">
              <span className="status-dot" />
              {error ? "Connection needs attention" : "Local workspace"}
              <span className="avatar">CB</span>
            </span>
          </header>
          <div className="page">
            {error && (
              <div className="callout warning" role="alert">
                {error}
                <button
                  className="secondary"
                  onClick={() => refresh().catch(() => {})}
                >
                  Retry connection
                </button>
              </div>
            )}
            {!data ? (
              <p>Loading your workspace…</p>
            ) : (
              <>
                {route === "dashboard" && (
                  <Dashboard
                    data={data}
                    refresh={refresh}
                    notify={notify}
                    onJob={setSelected}
                    onDaily={() => navigate("daily")}
                    onAdd={() => setAdd(true)}
                  />
                )}
                {route === "daily" && (
                  <DailySearch
                    data={data}
                    refresh={refresh}
                    notify={notify}
                    onJob={setSelected}
                    onAdd={() => setAdd(true)}
                  />
                )}
                {route === "resumes" && (
                  <ResumeStudio data={data} onJob={setSelected} />
                )}
                {route === "profile" && (
                  <Profile refresh={refresh} notify={notify} />
                )}
              </>
            )}
          </div>
        </main>
        {toast && (
          <div
            role={toast.error ? "alert" : "status"}
            className={"toast " + (toast.error ? "error" : "")}
          >
            <CheckCircle2 size={20} />
            <span>{toast.text}</span>
            <button
              aria-label="Dismiss notification"
              onClick={() => setToast(null)}
            >
              <X size={16} />
            </button>
          </div>
        )}
        {job && data && (
          <JobDetail
            key={job.id}
            job={job}
            data={data}
            onClose={() => setSelected(null)}
            refresh={refresh}
            notify={notify}
          />
        )}
        {add && data && (
          <AddJob
            date={data.goals.date}
            onClose={() => setAdd(false)}
            refresh={refresh}
            notify={notify}
            onSelect={setSelected}
          />
        )}
      </div>
    </NoticeContext.Provider>
  );
}
function AddJob({
  date,
  onClose,
  refresh,
  notify,
  onSelect,
}: {
  date: string;
  onClose: () => void;
  refresh: () => Promise<void>;
  notify: (s: string, e?: boolean) => void;
  onSelect: (s: string) => void;
}) {
  const [form, setForm] = useState({
    company: "",
    title: "",
    location: "Ireland",
    url: "",
    requisition_id: "",
    description: "",
  });
  const [today, setToday] = useState(true);
  const [busy, setBusy] = useState(false);
  return (
    <Modal title="Save a job posting" onClose={onClose}>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          try {
            const r = await api("/v2/jobs", "POST", form);
            if (today && !r.duplicate)
              await api("/search-runs/" + date + "/jobs/" + r.job.id, "POST");
            await refresh();
            onClose();
            onSelect(r.job.id);
            notify(
              r.duplicate
                ? "This posting is already saved. Opening its existing record."
                : "Job saved to your workspace.",
            );
          } catch (e) {
            notify((e as Error).message, true);
          } finally {
            setBusy(false);
          }
        }}
      >
        <div className="form-grid">
          {[
            ["company", "Company"],
            ["title", "Job title"],
            ["location", "Location"],
            ["requisition_id", "Requisition ID (optional)"],
          ].map(([key, label]) => (
            <Field key={key} label={label}>
              <input
                required={key !== "requisition_id"}
                maxLength={150}
                value={form[key as keyof typeof form]}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
              />
            </Field>
          ))}
        </div>
        <Field label="Direct posting URL">
          <input
            type="url"
            required
            maxLength={2500}
            value={form.url}
            onChange={(e) => setForm({ ...form, url: e.target.value })}
          />
        </Field>
        <Field label="Full job description">
          <textarea
            rows={9}
            required
            minLength={80}
            maxLength={100000}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
        </Field>
        <label className="check-line">
          <input
            type="checkbox"
            checked={today}
            onChange={(e) => setToday(e.target.checked)}
          />
          Add new posting to today’s search
        </label>
        <button className="primary" disabled={busy}>
          {busy ? "Saving…" : "Save job"}
        </button>
      </form>
    </Modal>
  );
}
