import { useEffect, useState } from "react";
import { FileText, ExternalLink } from "lucide-react";
import { api, fileUrl } from "../api";
import { Badge } from "../components/UI";
import { JobList } from "../components/JobList";
import type { Summary } from "../types";
export default function ResumeStudio({
  data,
  onJob,
}: {
  data: Summary;
  onJob: (id: string) => void;
}) {
  const [overview, setOverview] = useState<any>();
  const [error, setError] = useState("");
  useEffect(() => {
    api("/overview")
      .then(setOverview)
      .catch((e) => setError(e.message));
  }, [data]);
  return (
    <>
      <div className="page-title">
        <div>
          <div className="eyebrow">EVIDENCE BEFORE WORDING</div>
          <h1>Resume Studio</h1>
          <p>Your existing resume tools, ready for the next stage.</p>
        </div>
        <Badge>Further customization awaits your brief</Badge>
      </div>
      <div className="callout">
        <FileText size={23} />
        <div>
          <b>One saved job. One registered project. Two A4 pages.</b>
          <p>
            Open an application below to select a project, prepare a draft,
            compile its preview and check the evidence. A draft still needs
            tailored wording and visual review before release.
          </p>
        </div>
      </div>
      {data.profile_dirty && (
        <div className="callout warning">
          <b>Your profile has changed.</b>
          <p>
            Existing PDFs may contain older facts. New drafts are paused until
            the edits are reconciled with the approved resume registry.
          </p>
        </div>
      )}
      {error && <p role="alert">{error}</p>}
      <section className="card spaced">
        <h2>Resume library</h2>
        <div className="artifact-grid">
          {overview?.artifacts.map((a: any) => (
            <a
              className="artifact"
              href={fileUrl(a.path)}
              target="_blank"
              rel="noreferrer"
              key={a.path}
            >
              <FileText size={30} />
              <span>
                <strong>
                  {a.path.startsWith("base/")
                    ? "Base resume"
                    : "Application resume"}
                </strong>
                <small>{a.path}</small>
                <Badge
                  tone={
                    !data.profile_dirty && a.release_ready ? "green" : "amber"
                  }
                >
                  {data.profile_dirty
                    ? "Profile changed"
                    : a.release_ready
                      ? "Reviewed"
                      : a.status.replaceAll("_", " ")}
                </Badge>
              </span>
              <ExternalLink size={17} />
            </a>
          ))}
        </div>
      </section>
      <section className="card spaced">
        <h2>Prepare for a saved role</h2>
        <JobList jobs={data.jobs} onSelect={onJob} />
      </section>
      <section className="card spaced">
        <h2>Preserved history</h2>
        <p>
          {overview?.counts.historical_packs ?? "…"} original resume packs are
          indexed in the backup folder. Historical drafts do not establish
          applications and need a fresh review before use.
        </p>
      </section>
    </>
  );
}
