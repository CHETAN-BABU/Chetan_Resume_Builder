import { ArrowUpRight, MapPin, Search } from "lucide-react";
import { useState } from "react";
import { Badge, Empty } from "./UI";
import type { Job } from "../types";
export const statuses = [
  "saved",
  "prepared",
  "applied",
  "interview",
  "offer",
  "rejected",
  "withdrawn",
];
export function JobList({
  jobs,
  onSelect,
  compact = false,
}: {
  jobs: Job[];
  onSelect: (id: string) => void;
  compact?: boolean;
}) {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("all");
  const shown = jobs.filter(
    (j) =>
      (status === "all" || j.status === status) &&
      `${j.company} ${j.title} ${j.location}`
        .toLowerCase()
        .includes(q.toLowerCase()),
  );
  return (
    <>
      <div className="list-toolbar">
        <div className="search-input">
          <Search size={18} />
          <input
            aria-label="Search companies and roles"
            placeholder="Search companies or roles…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        <select
          aria-label="Filter application status"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="all">All statuses</option>
          {statuses.map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
        <span className="muted">{shown.length} jobs</span>
      </div>
      {!shown.length ? (
        <Empty title="No jobs in this view">
          Try another filter or save a new opportunity.
        </Empty>
      ) : (
        <div className="job-list">
          {shown.map((j) => (
            <button
              key={j.id}
              className="job-row"
              onClick={() => onSelect(j.id)}
            >
              <span className="company-avatar">
                {j.company.slice(0, 2).toUpperCase()}
              </span>
              <span className="job-main">
                <strong>{j.title}</strong>
                <span>
                  {j.company}{" "}
                  <span className="job-location">· {j.location}</span>
                </span>
              </span>
              <span className="job-meta">
                <Badge
                  tone={
                    ["applied", "offer", "interview"].includes(j.status)
                      ? "green"
                      : j.status === "rejected"
                        ? "red"
                        : "neutral"
                  }
                >
                  {j.status}
                </Badge>
                {!compact && (
                  <small>
                    {j.application_date
                      ? "Applied " + j.application_date
                      : "Date not recorded"}
                  </small>
                )}
              </span>
              <ArrowUpRight size={18} />
            </button>
          ))}
        </div>
      )}
    </>
  );
}
