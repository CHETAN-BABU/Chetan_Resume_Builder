from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts/validate_resume.py"
BASE = ROOT / "templates/resume-base.tex"
PDF_INTEGRATION_AVAILABLE = bool(
    shutil.which("tectonic") and (shutil.which("swiftc") or shutil.which("swift"))
)


class ResumeQualityTests(unittest.TestCase):
    def run_validator(self, source: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(source), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def make_tailored_fixture(
        self,
        directory: Path,
        source_text: str | None = None,
        selected_project_id: str = "PROJ-AZ-RECON",
    ) -> tuple[Path, Path, Path]:
        source_text = source_text or BASE.read_text(encoding="utf-8")
        source = directory / "resume.tex"
        source.write_text(source_text, encoding="utf-8")

        job_description = directory / "job-description.md"
        job_description.write_text(
            "# Job Description\n\n"
            "The Data Analyst will develop Power BI dashboards, validate multi-source "
            "reporting, and communicate findings to stakeholders.\n",
            encoding="utf-8",
        )
        job_hash = hashlib.sha256(job_description.read_bytes()).hexdigest()
        source_ids = sorted(
            {
                evidence_id
                for match in re.finditer(
                    r"(?m)^\s*%\s*EVIDENCE:\s*(.*?)\s*$",
                    source_text,
                )
                for evidence_id in match.group(1).split()
            }
        )
        claim_list = "\n".join(f'  - "{evidence_id}"' for evidence_id in source_ids)

        from validate_resume import extract_zero_argument_macros
        second_id = extract_zero_argument_macros(source_text).get('SecondProjectID')
        evidence_map = directory / "evidence-map.yml"
        evidence_map.write_text(
            'candidate_revision: "2026-09-14.1"\n'
            'job_id: "001-data-analyst-test"\n'
            "role_eligible: true\n"
            f'job_snapshot_sha256: "{job_hash}"\n'
            "supported_requirement_coverage: 75.0\n"
            "requirements:\n"
            '  - id: "R01"\n'
            '    priority: "required"\n'
            '    text: "Power BI dashboard development"\n'
            "    evidence_ids:\n"
            '      - "PROJ-AZ-RECON"\n'
            '    strength: "strong"\n'
            '  - id: "R02"\n'
            '    priority: "preferred"\n'
            '    text: "Tableau reporting"\n'
            "    evidence_ids:\n"
            '      - "SKILL-BI-001"\n'
            '    strength: "partial"\n'
            "company_problem:\n"
            '  statement: "The role requires reliable multi-source reporting and '
            'traceable dashboard delivery."\n'
            '  source_url: "https://www.infocepts.ai/"\n'
            '  published_or_accessed: "2026-07-27"\n'
            '  evidence_class: "explicit"\n'
            '  confidence: "high"\n'
            f'selected_project_ids: ["{selected_project_id}", "{second_id}"]\n'
            f'selected_project_id: "{selected_project_id}"\n'
            'selected_project_reason: "The reconciliation dashboard directly '
            'demonstrates multi-source reporting and traceability."\n'
            "resume_claim_ids:\n"
            f"{claim_list}\n"
            "held_claims_used: []\n",
            encoding="utf-8",
        )
        return source, evidence_map, job_description

    def registered_projects(self) -> list[dict[str, object]]:
        program = (
            'require "yaml"; require "json"; '
            "data = YAML.safe_load(File.read(ARGV.fetch(0)), aliases: false); "
            'STDOUT.write(JSON.generate(data.fetch("projects")))'
        )
        result = subprocess.run(
            ["ruby", "-e", program, str(ROOT / "context/evidence.yml")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(result.stdout)

    def source_with_project(self, project: dict[str, object]) -> str:
        from services.resume_projects import install_project
        source = install_project(BASE.read_text(), project)
        second = next(p for p in self.registered_projects() if p['id'] != project['id'] and p['id'] == 'PROJ-AZ-RECON') if project['id'] != 'PROJ-AZ-RECON' else next(p for p in self.registered_projects() if p['id'] == 'PROJ-POWERBI-PORTFOLIO')
        return install_project(source, second, second=True)

    def test_base_resume_passes_static_contract(self) -> None:
        result = self.run_validator(BASE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("AUTOMATED_PASS_MANUAL_PENDING", result.stdout)

    def test_valid_tailored_fixture_passes_static_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source, evidence_map, _ = self.make_tailored_fixture(Path(temporary))
            result = self.run_validator(
                source,
                "--evidence-map",
                str(evidence_map),
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("AUTOMATED_PASS_MANUAL_PENDING", result.stdout)

    def test_authorised_supplied_phone_passes(self) -> None:
        result = self.run_validator(BASE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("+353-0892401738", BASE.read_text())

    def test_unknown_project_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "resume.tex"
            source.write_text(
                BASE.read_text(encoding="utf-8").replace(
                    r"\newcommand{\SelectedProjectID}{PROJ-AZ-RECON}",
                    r"\newcommand{\SelectedProjectID}{PROJ-INVENTED}",
                    1,
                ),
                encoding="utf-8",
            )
            result = self.run_validator(source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not resume-ready", result.stdout)

    def test_second_project_section_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "resume.tex"
            text = BASE.read_text(encoding="utf-8").replace(
                "\\section{Education}",
                "\\section{Selected Project}\nInvented duplicate\n\n\\section{Education}",
                1,
            )
            source.write_text(text, encoding="utf-8")
            result = self.run_validator(source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exactly one Selected Project", result.stdout)

    def test_fabricated_registered_project_content_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source, evidence_map, _ = self.make_tailored_fixture(Path(temporary))
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    r"\newcommand{\SelectedProjectTitle}{Finance Access Reconciliation Dashboard}",
                    r"\newcommand{\SelectedProjectTitle}{Invented Autonomous Forecasting Platform}",
                    1,
                ),
                encoding="utf-8",
            )
            result = self.run_validator(
                source,
                "--evidence-map",
                str(evidence_map),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Selected project title does not match its registered project ID",
            result.stdout,
        )

    def test_second_project_inside_selected_block_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source, evidence_map, _ = self.make_tailored_fixture(Path(temporary))
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    "% SELECTED_PROJECT_BLOCK_END",
                    "\\textbf{Second Project: Invented Forecasting Work}\\\\\n"
                    "\\begin{resumeitems}\n"
                    "  % EVIDENCE: PROJ-AZ-RECON\n"
                    "  \\item Added another visible project inside the selected-project block.\n"
                    "\\end{resumeitems}\n"
                    "% SELECTED_PROJECT_BLOCK_END",
                    1,
                ),
                encoding="utf-8",
            )
            result = self.run_validator(
                source,
                "--evidence-map",
                str(evidence_map),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Selected project block must render only the registered 2-3 project bullets",
            result.stdout,
        )

    def test_layout_overrides_are_rejected(self) -> None:
        mutations = {
            "geometry": (
                r"\usepackage[top=0.52in,bottom=0.52in,left=0.62in,right=0.62in]{geometry}",
                r"\usepackage[top=0.52in,bottom=0.52in,left=0.62in,right=0.62in]{geometry}"
                "\n"
                r"\geometry{top=0.20in,bottom=0.20in,left=0.20in,right=0.20in}",
                "Prohibited layout detected: geometry override",
            ),
            "line-spread": (
                r"\renewcommand{\baselinestretch}{1.04}",
                r"\renewcommand{\baselinestretch}{1.04}"
                "\n"
                r"\renewcommand{\baselinestretch}{0.60}",
                "Resume must preserve the single fixed baselinestretch value",
            ),
        }
        for label, (old, new, expected) in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                source, evidence_map, _ = self.make_tailored_fixture(Path(temporary))
                source.write_text(
                    source.read_text(encoding="utf-8").replace(old, new, 1),
                    encoding="utf-8",
                )
                result = self.run_validator(
                    source,
                    "--evidence-map",
                    str(evidence_map),
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stdout)

    def test_visual_pass_requires_reviewer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source, evidence_map, _ = self.make_tailored_fixture(Path(temporary))
            result = self.run_validator(
                source,
                "--evidence-map",
                str(evidence_map),
                "--visual-review",
                "pass",
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "A visual reviewer identity is required for a pass/fail visual review",
            result.stdout,
        )

    def test_stale_job_snapshot_hash_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source, evidence_map, job_description = self.make_tailored_fixture(
                Path(temporary)
            )
            job_description.write_text(
                job_description.read_text(encoding="utf-8")
                + "\nThis requirement was added after the evidence map was created.\n",
                encoding="utf-8",
            )
            result = self.run_validator(
                source,
                "--evidence-map",
                str(evidence_map),
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "Evidence-map job_snapshot_sha256 does not match the saved JD snapshot",
            result.stdout,
        )

    def test_invalid_evidence_map_fields_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source, evidence_map, _ = self.make_tailored_fixture(Path(temporary))
            mapping = evidence_map.read_text(encoding="utf-8")
            mapping = mapping.replace("role_eligible: true", "role_eligible: false", 1)
            mapping = mapping.replace(
                "supported_requirement_coverage: 75.0",
                "supported_requirement_coverage: 101",
                1,
            )
            mapping = mapping.replace(
                'source_url: "https://www.infocepts.ai/"',
                'source_url: "https://example.invalid/problem"',
                1,
            )
            mapping = mapping.replace(
                'published_or_accessed: "2026-07-27"',
                'published_or_accessed: "2026/07/27"',
                1,
            )
            evidence_map.write_text(mapping, encoding="utf-8")
            result = self.run_validator(
                source,
                "--evidence-map",
                str(evidence_map),
            )
        self.assertNotEqual(result.returncode, 0)
        for expected in (
            "Evidence map role_eligible must be true",
            "supported_requirement_coverage must be a number from 0 to 100",
            "company_problem.source_url must be a real HTTP(S) source",
            "company_problem.published_or_accessed must be YYYY-MM-DD",
        ):
            self.assertIn(expected, result.stdout)

    def test_tailored_copy_requires_evidence_map(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "resume.tex"
            source.write_text(BASE.read_text(encoding="utf-8"), encoding="utf-8")
            result = self.run_validator(source)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing evidence map", result.stdout)

    @unittest.skipUnless(PDF_INTEGRATION_AVAILABLE, "PDF integration tools are required")
    def test_compiled_base_is_release_ready_after_visual_signoff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            output = directory / "resume.pdf"
            qa_path = directory / "qa.json"
            result = self.run_validator(
                BASE,
                "--compile",
                "--output",
                str(output),
                "--qa-json",
                str(qa_path),
                "--visual-review",
                "pass",
                "--visual-reviewer",
                "Automated test reviewer",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            qa = json.loads(qa_path.read_text(encoding="utf-8"))
            self.assertEqual(qa["status"], "PASS")
            self.assertTrue(qa["release_ready"])
            self.assertEqual(qa["page_count"], 2)
            self.assertEqual(qa["project_count"], 2)
            self.assertTrue(qa["pdf_text_extractable"])
            self.assertEqual(qa["overflow_count"], 0)
            self.assertTrue(output.is_file())

    @unittest.skipUnless(PDF_INTEGRATION_AVAILABLE, "PDF integration tools are required")
    def test_valid_tailored_fixture_is_release_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source, evidence_map, _ = self.make_tailored_fixture(directory)
            output = directory / "resume.pdf"
            qa_path = directory / "qa.json"
            result = self.run_validator(
                source,
                "--compile",
                "--output",
                str(output),
                "--qa-json",
                str(qa_path),
                "--evidence-map",
                str(evidence_map),
                "--visual-review",
                "pass",
                "--visual-reviewer",
                "Automated test reviewer",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            qa = json.loads(qa_path.read_text(encoding="utf-8"))
            self.assertEqual(qa["status"], "PASS")
            self.assertTrue(qa["release_ready"])
            self.assertTrue(qa["published_pdf"])
            self.assertTrue(qa["selected_project"]["content_matches_registry"])
            self.assertTrue(qa["evidence_map"]["all_candidate_claims_grounded"])
            self.assertEqual(
                set(qa["preview_sha256"]),
                {"page-01.png", "page-02.png"},
            )
            self.assertTrue(output.is_file())

    @unittest.skipUnless(PDF_INTEGRATION_AVAILABLE, "PDF integration tools are required")
    def test_every_registered_project_variant_compiles_to_two_pages(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            projects = self.registered_projects()
            self.assertGreaterEqual(len(projects), 10)
            for project in projects:
                project_id = str(project["id"])
                with self.subTest(project=project_id):
                    directory = root / project_id
                    directory.mkdir()
                    source, evidence_map, _ = self.make_tailored_fixture(
                        directory,
                        self.source_with_project(project),
                        project_id,
                    )
                    output = directory / "resume.pdf"
                    qa_path = directory / "qa.json"
                    result = self.run_validator(
                        source,
                        "--compile",
                        "--output",
                        str(output),
                        "--qa-json",
                        str(qa_path),
                        "--evidence-map",
                        str(evidence_map),
                        "--visual-review",
                        "pass",
                        "--visual-reviewer",
                        "Automated project-variant test",
                    )
                    self.assertEqual(
                        result.returncode,
                        0,
                        f"{project_id}\n{result.stdout}{result.stderr}",
                    )
                    qa = json.loads(qa_path.read_text(encoding="utf-8"))
                    self.assertEqual(qa["status"], "PASS")
                    self.assertEqual(qa["selected_project_id"], project_id)
                    self.assertEqual(qa["page_count"], 2)
                    self.assertTrue(
                        qa["selected_project"]["content_matches_registry"]
                    )

    @unittest.skipUnless(PDF_INTEGRATION_AVAILABLE, "PDF integration tools are required")
    def test_failed_validation_does_not_overwrite_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source, evidence_map, _ = self.make_tailored_fixture(directory)
            source.write_text(
                source.read_text(encoding="utf-8").replace(
                    r"\newcommand{\SelectedProjectTitle}{Finance Access Reconciliation Dashboard}",
                    r"\newcommand{\SelectedProjectTitle}{Invented Forecasting Platform}",
                    1,
                ),
                encoding="utf-8",
            )
            output = directory / "resume.pdf"
            sentinel = b"known-good-pdf"
            output.write_bytes(sentinel)
            qa_path = directory / "qa.json"
            result = self.run_validator(
                source,
                "--compile",
                "--output",
                str(output),
                "--qa-json",
                str(qa_path),
                "--evidence-map",
                str(evidence_map),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_bytes(), sentinel)
            qa = json.loads(qa_path.read_text(encoding="utf-8"))
            self.assertEqual(qa["status"], "FAIL")
            self.assertFalse(qa["published_pdf"])


if __name__ == "__main__":
    unittest.main()
