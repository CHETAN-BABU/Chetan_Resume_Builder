import { describe, it, expect } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { RichText, ReportView } from "./UI";
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
