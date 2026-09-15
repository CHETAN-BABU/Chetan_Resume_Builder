import { describe, it, expect } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { RichText, ReportView } from "./UI";
import { JobList } from "./JobList";
import { safeUrl, fileUrl } from "../api";
describe("Agent report safety", () => {
  it("renders untrusted markup as plain text", () => {
    const html = renderToStaticMarkup(
      <RichText
        text={
          "<script>alert(1)</script>\n[Unsafe](javascript:alert(1))\n[Source](https://example.test/source)"
        }
      />,
    );
    expect(html).not.toContain("<script>");
    expect(html).not.toContain('href="javascript:');
    expect(html).toContain('href="https://example.test/source"');
  });
  it("rejects credential and script navigation", () => {
    expect(safeUrl("javascript:alert(1)")).toBe("#");
    expect(safeUrl("file:///private")).toBe("#");
  });
  it("encodes output filenames", () => {
    expect(fileUrl("base/my resume.pdf")).toBe(
      "/api/files/base/my%20resume.pdf",
    );
  });
  it("makes report limitations visible", () => {
    const html = renderToStaticMarkup(
      <ReportView
        report={{
          summary: "Role expectations",
          report: "## Skills\nSQL",
          sources: [],
          limitations: ["Hiring criteria are inferred"],
        }}
      />,
    );
    expect(html).toContain("Hiring criteria are inferred");
    expect(html).toContain("<h3>Skills</h3>");
  });
});

it("renders hiring comparisons as safe tables", () => {
  const html = renderToStaticMarkup(
    <RichText
      text={
        "| Skill | Evidence |\n|---|---|\n| SQL | <script>unsafe</script> |"
      }
    />,
  );
  expect(html).toContain("<table>");
  expect(html).toContain("<th>Skill</th>");
  expect(html).not.toContain("<script>");
});

it("shows cover-letter and removable-role actions without nesting buttons", () => {
  const html = renderToStaticMarkup(
    <JobList
      jobs={[
        {
          id: "job-1",
          company: "Example Co",
          title: "Data Analyst",
          location: "Ireland",
          url: "https://example.test/job-1",
          description:
            "A complete test job description for reporting and analytics.",
          status: "saved",
          notes: "",
          application_date: null,
          folder: null,
          created_at: "2026-09-15T10:00:00Z",
          selected_project_id: null,
          record_source: "posting",
          deleted_at: null,
          deletion_reason: "",
        },
      ]}
      onSelect={() => {}}
      onCoverLetter={() => {}}
      onRemove={() => {}}
    />,
  );
  expect(html).toContain("Cover letter");
  expect(html).toContain("Remove Example Co Data Analyst");
  expect(html).not.toContain("<button><button");
});
