"""Behavioral coverage for planner, evidence, independent workers and shared state."""

from datetime import date
from concurrent.futures import ThreadPoolExecutor
import json
import shutil
import pytest
from fastapi.testclient import TestClient
from test_career_workspace import workspace, add, ROOT
from services.planning import plan
from services.postings import canonical_url, posting_key
from services.workspace_v2 import CareerServices
from services.agents import AgentRunner, role_payload
from dashboard.app import create_app


@pytest.fixture
def service(workspace, monkeypatch):
    monkeypatch.setattr(CareerServices, "today", staticmethod(lambda: "2026-09-12"))
    shutil.copytree(ROOT / "workflows", workspace.root / "workflows")
    return CareerServices(workspace)


def settings(start="2026-09-07"):
    return {"weekly_target": 30, "workdays": [0, 1, 2, 3, 4, 5], "start_date": start}


def message(
    job, id="mail1", kind="applied", received="2026-09-08T23:39:27Z", submission=None
):
    return dict(
        id=id,
        job_id=job["id"],
        company=job["company"],
        role=job["title"],
        kind=kind,
        subject="Application update",
        sender="careers@example.test",
        received_at=received,
        submission_date=submission,
        excerpt="We received your application.",
        reason="Exact company and role.",
        confidence="high",
    )


def ingest(s, *messages):
    return s.ingest_mail(
        {
            "email": "test@example.test",
            "coverage": "Test fixture",
            "messages": list(messages),
        }
    )


def test_missed_target_stacks_across_days_and_weeks():
    assert plan(settings(), [], date(2026, 9, 8))["today_target"] == 10
    assert plan(settings(), [], date(2026, 9, 13))["today_target"] == 30
    assert plan(settings(), [], date(2026, 9, 14))["today_target"] == 35
    p = plan(settings(), ["2026-09-07"] * 7, date(2026, 9, 8))
    assert p["ahead"] == 2 and p["today_target"] == 3
    assert (
        plan(settings(), ["2026-09-08"] * 10, date(2026, 9, 8))["remaining_today"] == 0
    )


def test_partial_week_and_uneven_distribution():
    p = plan(settings("2026-09-11"), [], date(2026, 9, 11))
    assert p["current_week_target"] == 10 and p["week_remaining"] == 10
    s = {**settings(), "weekly_target": 31}
    assert sum(d["planned"] for d in plan(s, [], date(2026, 9, 7))["schedule"]) == 31
    assert plan(s, [], date(2026, 9, 7))["daily_base"] == 6


@pytest.mark.parametrize(
    "url",
    [
        "https://www.example.test/jobs/1?utm_source=email#x",
        "http://example.test/jobs/1/?source=li",
    ],
)
def test_tracking_parameters_are_not_new_jobs(url):
    assert canonical_url(url) == "https://example.test/jobs/1"


def test_requisition_and_linkedin_identities():
    assert posting_key("https://example.test/apply?job=abc&lang=en") == posting_key(
        "https://example.test/view?job=abc"
    )
    assert posting_key("https://example.test/apply?job=abc") != posting_key(
        "https://example.test/apply?job=def"
    )
    assert (
        canonical_url("https://www.linkedin.com/comm/jobs/view/4430071221?trk=foo")
        == "https://www.linkedin.com/jobs/view/4430071221"
    )


def test_every_save_path_deduplicates(service):
    j = add(service.w)
    with pytest.raises(ValueError, match="already saved"):
        service.w.add_job(
            j["company"],
            j["title"],
            j["location"],
            j["url"] + "?utm_source=test",
            j["description"],
        )
    value = {k: j[k] for k in ("company", "title", "location", "url", "description")}
    assert service.add_posting(value)["duplicate"]
    another = {
        **value,
        "url": "https://second.example.test/123",
        "requisition_id": "R123",
    }
    first = service.add_posting(another)
    assert not first["duplicate"]
    assert (
        service.add_posting({**another, "url": "https://third.example.test/alternate"})[
            "job"
        ]["id"]
        == first["job"]["id"]
    )


def test_simultaneous_save_has_one_record(service):
    value = {
        "company": "A",
        "title": "Analyst",
        "location": "Ireland",
        "url": "https://example.test/role/1",
        "description": "Use SQL for reporting and business analysis. " * 5,
        "requisition_id": "1",
    }
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(service.add_posting, [value] * 4))
    assert len(service.w.jobs()) == 1
    assert sum(not r["duplicate"] for r in results) == 1


def test_profile_revision_delete_and_sources_preserved(service):
    before = (service.w.root / "context/evidence.yml").read_bytes()
    assert (
        next(i for i in service.knowledge() if i["id"] == "SKILL-SQL-001")["summary"]
        == "SQL"
    )
    entry = service.save_knowledge(
        {"kind": "skill", "title": "Test skill", "summary": "User supplied evidence"}
    )
    edit = service.save_knowledge({**entry, "summary": "Updated evidence"}, entry["id"])
    assert edit["revision"] == 2
    with pytest.raises(ValueError, match="changed elsewhere"):
        service.save_knowledge(entry, entry["id"])
    assert "Updated evidence" in json.dumps(service.profile_context())
    service.delete_knowledge(entry["id"])
    assert entry["id"] not in json.dumps(service.profile_context())
    assert service.profile_dirty()
    assert before == (service.w.root / "context/evidence.yml").read_bytes()
    assert (
        json.loads((service.w.root / "data/active-profile.json").read_text())[-1:]
        is not None
    )


def test_pending_reminders_never_count(service):
    j = add(service.w)
    m = message(j, kind="reminder")
    ingest(service, m)
    assert service.summary()["counts"]["applied"] == 0
    with pytest.raises(ValueError, match="does not establish"):
        service.resolve_mail(m["id"])
    assert service.resolve_mail(m["id"], action="dismiss")["state"] == "dismissed"
    assert service.w.activity()[0]["action"] == "email_dismissed"


def test_receipt_date_is_separate_and_counted_once(service):
    service.save_goals(settings())
    j = add(service.w)
    m = message(j)
    ingest(service, m, m)
    assert len(service.mail()["messages"]) == 1
    service.resolve_mail(m["id"])
    assert service.w.get_job(j["id"])["application_date"] is None
    assert service.goals(date(2026, 9, 9))["today_completed"] == 1
    ingest(service, message(j, id="mail2", received="2026-09-10T10:00:00Z"))
    service.resolve_mail("mail2")
    assert service.goals(date(2026, 9, 10))["today_completed"] == 0
    assert service.summary()["counts"]["applied"] == 1
    # Editing notes after email confirmation never requires an invented date.
    service.w.update_job(j["id"], "applied", notes="Next action")


def test_old_mail_does_not_regress_status(service):
    j = add(service.w)
    ingest(
        service,
        message(j, id="offer", kind="offer", received="2026-09-10T09:00:00Z"),
        message(j, id="old", kind="rejected", received="2026-09-09T09:00:00Z"),
    )
    service.resolve_mail("offer")
    service.resolve_mail("old")
    assert service.w.get_job(j["id"])["status"] == "offer"
    assert service.w.get_job(j["id"])["application_date"] is None
    assert service.summary()["counts"]["applied"] == 1


def test_explicit_submission_date_wins_over_receipt(service):
    service.save_goals(settings())
    j = add(service.w)
    ingest(service, message(j, submission="2026-09-07"))
    service.resolve_mail("mail1")
    assert service.w.get_job(j["id"])["application_date"] == "2026-09-07"
    assert service.goals(date(2026, 9, 8))["today_completed"] == 0
    assert service.goals(date(2026, 9, 8))["carryover"] == 4


@pytest.mark.parametrize(
    "changes",
    [
        {"received_at": "not-a-date"},
        {"received_at": "2026-09-09T10:00:00"},
        {"submission_date": "2099-01-01"},
        {"kind": "imagined"},
        {"id": "bad/id"},
    ],
)
def test_invalid_mail_rejected_atomically(service, changes):
    j = add(service.w)
    with pytest.raises(ValueError):
        ingest(service, {**message(j), **changes})
    assert not service.mail()["messages"]


def test_independent_hiring_has_no_candidate_context(service):
    j = add(service.w)
    service.w.update_job(j["id"], "saved", notes="PRIVATE-NOTES-SECRET")
    service.save_knowledge(
        {
            "kind": "skill",
            "title": "PRIVATE-PROFILE-SECRET",
            "summary": "Private evidence",
        }
    )
    seen = []

    def execute(prompt, schema, **kwargs):
        seen.append((prompt, kwargs))
        return {
            "summary": "Test report",
            "report": "Verified fixture",
            "sources": [],
            "limitations": ["Test fixture"],
        }

    runner = AgentRunner(service, execute)
    run = runner.enqueue("research", j["id"])
    runner.pool.shutdown(wait=True)
    assert len(seen) == 3
    assert "PRIVATE-" not in seen[0][0] and "PRIVATE-" not in seen[1][0]
    assert "PRIVATE-PROFILE-SECRET" in seen[2][0]
    assert seen[1][1] == {"web": False}
    output = service.runs()[0]
    assert (
        output["state"] == "completed"
        and output["result"]["hiring_profile_access"] is False
    )
    assert set(role_payload(j)) == {
        "company",
        "title",
        "location",
        "url",
        "description",
    }


def test_worker_failure_is_durable(service):
    j = add(service.w)

    def fail(*a, **kw):
        raise RuntimeError("A recoverable test failure")

    runner = AgentRunner(service, fail)
    runner.enqueue("research", j["id"])
    runner.pool.shutdown(wait=True)
    assert service.runs()[0]["state"] == "failed"
    assert "recoverable test failure" in service.runs()[0]["error"]


def test_v2_api_and_profile_resume_guard(service):
    app = create_app(service.w.root)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        assert client.get("/api/v2/summary").status_code == 200
        assert client.get("/api/v2/profile").json()["items"]
        assert (
            client.put("/api/v2/goals", json={**settings(), "workdays": []}).status_code
            == 400
        )
        assert (
            client.put(
                "/api/v2/goals",
                json=settings(),
                headers={"Origin": "https://foreign.test"},
            ).status_code
            == 403
        )
        j = add(service.w)
        saved = client.post(
            "/api/v2/profile/items",
            json={"kind": "skill", "title": "New skill", "summary": "New detail"},
        )
        assert saved.status_code == 201
        assert (
            client.post("/api/jobs/" + j["id"] + "/prepare", json={}).status_code == 400
        )
        assert (
            client.post("/api/v2/agents/run", json={"kind": "unknown"}).status_code
            == 400
        )


def test_exact_email_updates_automatically_but_ambiguous_does_not(service):
    j = add(service.w)
    ingest(service, message(j))
    assert service.mail()["messages"][0]["state"] == "confirmed"
    assert service.w.get_job(j["id"])["status"] == "applied"
    second = add(service.w, "2")
    ingest(service, message(second, id="ambiguous"))
    assert (
        next(m for m in service.mail()["messages"] if m["id"] == "ambiguous")["state"]
        == "pending"
    )
    assert service.w.get_job(second["id"])["status"] == "saved"


def test_discovery_filters_historical_postings_even_if_agent_repeats(service):
    history = service.w.root.parent / "daily-job-search"
    history.mkdir(exist_ok=True)
    (history / "history.csv").write_text(
        "company,url,requisition_id\nOld Company,https://old.test/jobs/1,R1\n"
    )
    data = {
        "summary": "One new result",
        "rejected_leads": [],
        "jobs": [
            {
                "company": "Old Company",
                "title": "Analyst",
                "location": "Ireland",
                "url": "https://old.test/apply?new=1",
                "requisition_id": "R1",
                "description": "Actual test job description. " * 10,
            },
            {
                "company": "New Company",
                "title": "Analyst",
                "location": "Ireland",
                "url": "https://new.test/jobs/2",
                "requisition_id": "R2",
                "description": "Actual test job description. " * 10,
            },
        ],
    }
    r = AgentRunner(service, lambda *a, **kw: data)
    r.enqueue("discovery")
    r.pool.shutdown(wait=True)
    assert service.runs()[0]["state"] == "completed"
    assert [j["company"] for j in service.w.jobs()] == ["New Company"]
    assert len(service.w.search_runs()[0]["jobs"]) == 1


def test_direct_resume_command_respects_profile_edits(service):
    j = add(service.w)
    service.save_knowledge(
        {"kind": "fact", "title": "Changed fact", "summary": "New evidence"}
    )
    with pytest.raises(ValueError, match="Reconcile"):
        service.w.prepare(j["id"])


def test_partial_worker_output_survives_failure(service):
    calls = []

    def execute(*a, **kw):
        calls.append(1)
        if len(calls) > 1:
            raise RuntimeError("Hiring failed")
        return {
            "summary": "Research preserved",
            "report": "Public research",
            "sources": [],
            "limitations": [],
        }

    j = add(service.w)
    r = AgentRunner(service, execute)
    r.enqueue("research", j["id"])
    r.pool.shutdown(wait=True)
    output = service.runs()[0]
    assert (
        output["state"] == "failed"
        and output["result"]["research"]["summary"] == "Research preserved"
    )


def test_email_ordering_uses_instants_across_timezones(service):
    j = add(service.w)
    ingest(
        service,
        message(j, id="old", kind="offer", received="2026-09-09T01:00:00+02:00"),
    )
    ingest(
        service, message(j, id="new", kind="rejected", received="2026-09-08T23:30:00Z")
    )
    ingest(
        service,
        message(j, id="middle", kind="interview", received="2026-09-08T23:15:00Z"),
    )
    assert service.w.get_job(j["id"])["status"] == "rejected"
    assert [m["id"] for m in service.mail()["messages"]] == ["new", "middle", "old"]


def test_discovery_excludes_unlinked_email_confirmed_roles(service):
    j = add(service.w)
    m = {
        **message(j),
        "job_id": None,
        "company": "Already Applied Ltd",
        "role": "Data Analyst",
    }
    ingest(service, m)
    output = {
        "summary": "Fixture",
        "rejected_leads": [],
        "jobs": [
            {
                "company": "Already Applied Ltd",
                "title": "Data Analyst",
                "location": "Ireland",
                "url": "https://new.example.test/jobs/9",
                "description": "A real JD would be required for discovery. " * 5,
                "requisition_id": "9",
            }
        ],
    }
    runner = AgentRunner(service, lambda *a, **kw: output)
    runner.enqueue("discovery")
    runner.pool.shutdown(wait=True)
    assert service.runs()[0]["state"] == "completed"
    assert len(service.w.jobs()) == 1
    assert service.runs()[0]["result"]["duplicate_job_ids"] == [
        "https://new.example.test/jobs/9"
    ]
