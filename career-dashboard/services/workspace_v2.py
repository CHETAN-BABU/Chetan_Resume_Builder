"""Application services. SQLite owns mutable state; original evidence is preserved."""

from __future__ import annotations
import hashlib, json, re, uuid
from datetime import datetime, timezone, date
from pathlib import Path
from zoneinfo import ZoneInfo
from services.planning import plan
from services.postings import canonical_url, posting_key

KINDS = {
    "personal",
    "skill",
    "project",
    "experience",
    "education",
    "certification",
    "fact",
}
AGENTS = [
    {
        "id": "research",
        "name": "Company researcher",
        "reads": "Saved job description and public company sources",
        "profile_access": False,
        "does": "Investigates the business, role outcomes, team, skills and company projects; cites sources and labels uncertainty.",
        "implementation": "Independent Codex run with web search",
        "guide": "workflows/agents/company-researcher.md",
    },
    {
        "id": "hiring",
        "name": "Independent hiring manager",
        "reads": "Job description and completed company research only",
        "profile_access": False,
        "does": "Defines expected skills, experience, convincing project evidence and interview preparation. It cannot promise a shortlist.",
        "implementation": "Fresh isolated Codex run; no profile, files, email or previous conversation",
        "guide": "workflows/agents/hiring-manager.md",
    },
    {
        "id": "match",
        "name": "Profile comparison",
        "reads": "Your active profile and the independent hiring review",
        "profile_access": True,
        "does": "Separates supported strengths, partial evidence, missing skills and practical next steps.",
        "implementation": "Separate Codex run after the independent review",
        "guide": "workflows/agents/profile-comparison.md",
    },
    {
        "id": "discovery",
        "name": "Job discovery",
        "reads": "Active skills, experience, role preferences and previously seen job IDs",
        "profile_access": True,
        "does": "Finds current suitable postings, verifies full requirements and removes previously seen postings.",
        "implementation": "Codex with web search; persistent unique posting store",
        "guide": "workflows/agents/job-discovery.md",
    },
    {
        "id": "email",
        "name": "Email evidence reviewer",
        "reads": "Job-related Gmail messages and the saved company/role/URL list",
        "profile_access": False,
        "does": "Finds confirmations and status updates; uncertain matches wait for review. No sending or mailbox changes.",
        "implementation": "Connected Gmail read tools through Codex; application service validates and applies evidence",
        "guide": "workflows/agents/email-reviewer.md",
    },
    {
        "id": "resume",
        "name": "Resume validator",
        "reads": "Approved registry, profile, selected JD and generated PDF",
        "profile_access": True,
        "does": "Checks evidence, two-page layout, project selection and current artifact hashes.",
        "implementation": "Existing Python validation; Resume Studio extension awaits your instructions",
        "guide": "workflows/TAILORING.md",
    },
]


class CareerServices:
    def __init__(self, workspace):
        self.w = workspace
        with self.w.connect() as db:
            db.executescript(
                """
            CREATE TABLE IF NOT EXISTS preferences(key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS knowledge(id TEXT PRIMARY KEY,kind TEXT NOT NULL,title TEXT NOT NULL,summary TEXT NOT NULL,data TEXT NOT NULL,source TEXT NOT NULL,revision INTEGER NOT NULL DEFAULT 1,deleted INTEGER NOT NULL DEFAULT 0,review_state TEXT NOT NULL DEFAULT 'registered',updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS mail_evidence(id TEXT PRIMARY KEY,job_id TEXT REFERENCES jobs(id),company TEXT NOT NULL,role TEXT NOT NULL,kind TEXT NOT NULL,subject TEXT NOT NULL,sender TEXT NOT NULL,received_at TEXT NOT NULL,submission_date TEXT,excerpt TEXT NOT NULL,reason TEXT NOT NULL,confidence TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'pending',created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS agent_runs(id TEXT PRIMARY KEY,kind TEXT NOT NULL,job_id TEXT REFERENCES jobs(id),state TEXT NOT NULL,input TEXT NOT NULL,result TEXT,error TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_agent_runs_state ON agent_runs(state,created_at);
            CREATE TABLE IF NOT EXISTS posting_identities(identity TEXT PRIMARY KEY,job_id TEXT NOT NULL REFERENCES jobs(id));
            CREATE TABLE IF NOT EXISTS application_evidence(job_id TEXT PRIMARY KEY REFERENCES jobs(id),source TEXT NOT NULL,confirmed_at TEXT NOT NULL,submission_date TEXT,message_id TEXT);
            """
            )
            for j in self.w.jobs():
                db.execute(
                    "INSERT OR IGNORE INTO posting_identities VALUES(?,?)",
                    (posting_key(j["url"]), j["id"]),
                )
            if not db.execute("SELECT 1 FROM preferences WHERE key='goals'").fetchone():
                self.set_pref(
                    "goals",
                    {
                        "weekly_target": 30,
                        "workdays": [0, 1, 2, 3, 4, 5],
                        "start_date": self.today(),
                    },
                    db,
                )
            if not db.execute(
                "SELECT 1 FROM preferences WHERE key='profile_initialized'"
            ).fetchone():
                self.seed_profile(db)
            for field in ("target_roles", "location_preferences"):
                config = self.w.profile().get(field, {})
                db.execute(
                    "INSERT OR IGNORE INTO knowledge(id,kind,title,summary,data,source,updated_at) VALUES(?,?,?,?,?,?,?)",
                    (
                        "personal:" + field,
                        "personal",
                        field.replace("_", " ").capitalize(),
                        json.dumps(config, ensure_ascii=False, indent=2),
                        json.dumps({"field": field, "value": config}),
                        "config/profile.yml > " + field,
                        self.now(),
                    ),
                )
            # Enrich only untouched imported entries; user edits always win.
            for claim in self.w.evidence()["claims"]:
                facts = claim.get("approved_facts", [])
                if facts:
                    db.execute(
                        "UPDATE knowledge SET title=?,summary=? WHERE id=? AND review_state='registered' AND summary=''",
                        (
                            claim.get("title") or facts[0][:150],
                            "\n".join(facts),
                            claim["id"],
                        ),
                    )

    @staticmethod
    def now():
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def today():
        return datetime.now(ZoneInfo("Europe/Dublin")).date().isoformat()

    def pref(self, key, default=None):
        with self.w.connect() as db:
            r = db.execute(
                "SELECT value FROM preferences WHERE key=?", (key,)
            ).fetchone()
        return json.loads(r[0]) if r else default

    def set_pref(self, key, value, db=None):
        if db is None:
            with self.w.connect() as db:
                self.set_pref(key, value, db)
        else:
            db.execute(
                "INSERT INTO preferences VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value)),
            )

    def seed_profile(self, db):
        profile = self.w.profile()
        evidence = self.w.evidence()

        def insert(id, kind, title, summary, data, source):
            db.execute(
                "INSERT OR IGNORE INTO knowledge(id,kind,title,summary,data,source,updated_at) VALUES(?,?,?,?,?,?,?)",
                (
                    id,
                    kind,
                    str(title),
                    str(summary),
                    json.dumps(data, ensure_ascii=False),
                    source,
                    self.now(),
                ),
            )

        for key, value in profile["candidate"].items():
            insert(
                "personal:" + key,
                "personal",
                key.replace("_", " ").capitalize(),
                value,
                {"field": key, "value": value},
                "config/profile.yml > candidate > " + key,
            )
        for claim in evidence["claims"]:
            cat = claim.get("category", "fact")
            kind = {
                "employment": "experience",
                "education": "education",
                "certification": "certification",
                "skill": "skill",
            }.get(cat, "fact")
            title = (
                claim.get("title")
                or claim.get("institution")
                or claim.get("value")
                or (claim.get("approved_facts") or [claim["id"]])[0][:150]
            )
            summary = (
                claim.get("value")
                or claim.get("value_as_supplied")
                or "\n".join(claim.get("approved_facts", []))
                or " · ".join(
                    str(claim[k])
                    for k in ("employer", "dates", "degree_as_supplied", "status_text")
                    if k in claim
                )
            )
            insert(
                claim["id"],
                kind,
                title,
                summary,
                claim,
                "context/evidence.yml > " + claim["id"],
            )
        for project in evidence["projects"]:
            content = project.get("resume_content", {})
            insert(
                project["id"],
                "project",
                content.get("title") or project.get("name") or project["id"],
                "\n".join(content.get("bullets", [])),
                project,
                "context/evidence.yml > " + project["id"],
            )
        # Seed known technologies only from the existing explicit skills claims.
        for claim in evidence["claims"]:
            if "skill" in claim.get("category", "") or claim["id"].startswith("SKILL"):
                for skill in claim.get("values", claim.get("skills", [])):
                    if isinstance(skill, str):
                        insert(
                            "skill:" + hashlib.sha256(skill.encode()).hexdigest()[:12],
                            "skill",
                            skill,
                            claim.get("approved_external_use", ""),
                            {"value": skill, "evidence_id": claim["id"]},
                            "context/evidence.yml > " + claim["id"],
                        )
        self.set_pref("profile_initialized", True, db)

    def knowledge(self, include_deleted=False):
        with self.w.connect() as db:
            rows = db.execute(
                "SELECT * FROM knowledge "
                + ("" if include_deleted else "WHERE deleted=0 ")
                + "ORDER BY kind,title"
            ).fetchall()
        return [{**dict(r), "data": json.loads(r["data"])} for r in rows]

    def save_knowledge(self, item, id=None):
        kind = item["kind"]
        title = item["title"].strip()
        summary = item.get("summary", "").strip()
        if kind not in KINDS or not title:
            raise ValueError("Choose a category and enter a title")
        if len(title) > 250 or len(summary) > 30000:
            raise ValueError("Profile entry is too long")
        with self.w.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = (
                db.execute("SELECT * FROM knowledge WHERE id=?", (id,)).fetchone()
                if id
                else None
            )
            if id and not old:
                raise ValueError("Profile entry not found")
            if old and item.get("revision") != old["revision"]:
                raise ValueError("This entry changed elsewhere. Reload before saving.")
            key = id or "user:" + uuid.uuid4().hex[:16]
            data = item.get("data", json.loads(old["data"]) if old else {})
            if not isinstance(data, dict):
                raise ValueError("Entry details must be an object")
            if old and old["kind"] == "personal":
                data = {**data, "value": summary}
            source = old["source"] if old else "User supplied in Profile"
            revision = old["revision"] + 1 if old else 1
            db.execute(
                "INSERT INTO knowledge VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET kind=excluded.kind,title=excluded.title,summary=excluded.summary,data=excluded.data,revision=excluded.revision,deleted=0,review_state=excluded.review_state,updated_at=excluded.updated_at",
                (
                    key,
                    kind,
                    title,
                    summary,
                    json.dumps(data, ensure_ascii=False),
                    source,
                    revision,
                    0,
                    "user_updated",
                    self.now(),
                ),
            )
            self.w.record_event(
                db,
                "profile_entry_saved",
                entry_id=key,
                before=dict(old) if old else None,
                after=item,
            )
        self.export_profile()
        self.w.export_tracking()
        return next(i for i in self.knowledge() if i["id"] == key)

    def delete_knowledge(self, id):
        with self.w.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute(
                "SELECT * FROM knowledge WHERE id=? AND deleted=0", (id,)
            ).fetchone()
            if not old:
                raise ValueError("Profile entry not found")
            db.execute(
                "UPDATE knowledge SET deleted=1,revision=revision+1,review_state='user_updated',updated_at=? WHERE id=?",
                (self.now(), id),
            )
            self.w.record_event(
                db, "profile_entry_removed", entry_id=id, before=dict(old)
            )
        self.export_profile()
        self.w.export_tracking()
        return {"deleted": True}

    def export_profile(self):
        from career import atomic_write

        atomic_write(
            self.w.root / "data/active-profile.json",
            json.dumps(self.knowledge(True), indent=2, ensure_ascii=False) + "\n",
        )

    def export_state(self):
        from career import atomic_write

        # A readable audit projection; SQLite remains authoritative.
        with self.w.connect() as db:
            preferences = {
                r["key"]: json.loads(r["value"])
                for r in db.execute("SELECT * FROM preferences")
            }
        atomic_write(
            self.w.root / "data/workspace-state.json",
            json.dumps(
                {"preferences": preferences, "mail": self.mail(), "runs": self.runs()},
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
        )

    def profile_context(self):
        return [
            {
                "id": i["id"],
                "kind": i["kind"],
                "title": i["title"],
                "summary": i["summary"],
                "details": (
                    i["data"]
                    if i["review_state"] == "registered"
                    else {"user_supplied": True}
                ),
                "review_state": i["review_state"],
            }
            for i in self.knowledge()
            if i["kind"] != "personal"
            or i["id"]
            in {
                "personal:location",
                "personal:current_status",
                "personal:most_recent_role",
                "personal:target_roles",
                "personal:location_preferences",
            }
        ]

    def profile_dirty(self):
        return any(i["review_state"] == "user_updated" for i in self.knowledge(True))

    def goals(self, on=None):
        with self.w.connect() as db:
            dates = [
                r[0]
                for r in db.execute(
                    "SELECT COALESCE(j.application_date,a.submission_date,substr(a.confirmed_at,1,10)) FROM jobs j LEFT JOIN application_evidence a ON a.job_id=j.id WHERE j.application_date IS NOT NULL OR a.job_id IS NOT NULL"
                )
            ]
        return plan(self.pref("goals"), dates, on or date.fromisoformat(self.today()))

    def save_goals(self, values):
        if (
            not isinstance(values["weekly_target"], int)
            or not 1 <= values["weekly_target"] <= 200
        ):
            raise ValueError("Choose a weekly target from 1 to 200")
        days = values["workdays"]
        if (
            not days
            or len(set(days)) != len(days)
            or any(not isinstance(d, int) or not 0 <= d <= 6 for d in days)
        ):
            raise ValueError("Choose at least one distinct workday")
        start = date.fromisoformat(values["start_date"])
        if start > date.fromisoformat(self.today()):
            raise ValueError("Goal tracking cannot start in the future")
        self.set_pref("goals", {**values, "workdays": sorted(days)})
        with self.w.connect() as db:
            self.w.record_event(db, "goal_updated", settings=values)
        self.w.export_tracking()
        self.export_state()
        return self.goals()

    def add_posting(self, values):
        clean = canonical_url(values["url"])
        keys = {
            posting_key(clean, values["company"], values.get("requisition_id", "")),
            posting_key(clean),
        }
        try:
            job = self.w.add_job(
                values["company"],
                values.get("title", values.get("role", "")),
                values["location"],
                clean,
                values["description"],
                values.get("requisition_id", ""),
            )
            return {"job": job, "duplicate": False}
        except ValueError as exc:
            if "already saved" not in str(exc):
                raise
            with self.w.connect() as db:
                for key in keys:
                    duplicate = db.execute(
                        "SELECT job_id FROM posting_identities WHERE identity=?", (key,)
                    ).fetchone()
                    if duplicate:
                        return {"job": self.w.get_job(duplicate[0]), "duplicate": True}
            raise

    def mail(self):
        with self.w.connect() as db:
            rows = [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM mail_evidence ORDER BY received_at DESC"
                )
            ]
        rows.sort(
            key=lambda m: datetime.fromisoformat(
                m["received_at"].replace("Z", "+00:00")
            ),
            reverse=True,
        )
        return {
            "connection": self.pref("gmail", {"connected": False}),
            "messages": rows,
        }

    def ingest_mail(self, batch):
        # Excerpts only: do not store entire inbox bodies, HTML, attachments or tracking URLs.
        count = 0
        with self.w.connect() as db:
            for m in batch["messages"]:
                if not re.fullmatch(r"[a-zA-Z0-9_-]{1,150}", m["id"]):
                    raise ValueError("Invalid message ID")
                if m["kind"] not in {
                    "applied",
                    "interview",
                    "offer",
                    "rejected",
                    "reminder",
                    "uncertain",
                }:
                    raise ValueError("Invalid email classification")
                timestamp = datetime.fromisoformat(
                    m["received_at"].replace("Z", "+00:00")
                )
                if timestamp.tzinfo is None or timestamp > datetime.now(timezone.utc):
                    raise ValueError(
                        "Email must have a valid timezone and cannot be from the future"
                    )
                if (
                    m.get("submission_date")
                    and date.fromisoformat(m["submission_date"])
                    > timestamp.astimezone(ZoneInfo("Europe/Dublin")).date()
                ):
                    raise ValueError("Submission date cannot be after the message")
                job_id = m.get("job_id") or None
                if job_id:
                    self.w.get_job(job_id)
                count += db.execute(
                    "INSERT OR IGNORE INTO mail_evidence VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        m["id"],
                        job_id,
                        m.get("company", ""),
                        m.get("role", ""),
                        m["kind"],
                        m["subject"],
                        m["sender"],
                        m["received_at"],
                        m.get("submission_date"),
                        m["excerpt"][:3000],
                        m.get("reason", ""),
                        m.get("confidence", "needs_review"),
                        "pending",
                        self.now(),
                    ),
                ).rowcount
            self.set_pref(
                "gmail",
                {
                    "connected": True,
                    "email": batch["email"],
                    "last_synced_at": self.now(),
                    "coverage": batch.get("coverage", "Job-related messages"),
                    "mode": "Connected Gmail via Codex",
                },
                db,
            )
            self.w.record_event(db, "email_synced", new_messages=count)
        # Automatic updates require an exact, unique saved company AND role match.
        # Anything ambiguous remains reviewable; no title-only or fuzzy matching.
        normalize = lambda text: re.sub(r"[^a-z0-9]+", "", text.casefold())
        for m in self.mail()["messages"]:
            if (
                m["state"] != "pending"
                or m["confidence"] != "high"
                or m["kind"] in {"reminder", "uncertain"}
            ):
                continue
            matches = [
                j
                for j in self.w.jobs()
                if normalize(j["company"]) == normalize(m["company"])
                and normalize(j["title"]) == normalize(m["role"])
            ]
            if len(matches) == 1 and m["job_id"] == matches[0]["id"]:
                self.resolve_mail(m["id"])
        self.w.export_tracking()
        self.export_state()
        return {"imported": count}

    def resolve_mail(self, id, job_id=None, action="confirm"):
        with self.w.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            m = db.execute("SELECT * FROM mail_evidence WHERE id=?", (id,)).fetchone()
            if not m:
                raise ValueError("Email evidence not found")
            if m["state"] != "pending":
                return {"state": m["state"]}
            if action not in {"confirm", "dismiss"}:
                raise ValueError("Choose confirm or dismiss")
            if action == "dismiss":
                db.execute(
                    "UPDATE mail_evidence SET state='dismissed' WHERE id=?", (id,)
                )
                self.w.record_event(db, "email_dismissed", message_id=id)
                db.commit()
                self.w.export_tracking()
                self.export_state()
                return {"state": "dismissed"}
            if m["kind"] in {"reminder", "uncertain"}:
                raise ValueError("This email does not establish an application status")
            job_id = job_id or m["job_id"]
            job = self.w.get_job(job_id)
            # A late old confirmation must never regress an interview, offer or rejection.
            status = m["kind"]
            if status == "applied" and job["status"] in {
                "interview",
                "offer",
                "rejected",
                "withdrawn",
            }:
                status = job["status"]
            timestamps = db.execute(
                "SELECT received_at FROM mail_evidence WHERE job_id=? AND state='confirmed'",
                (job_id,),
            ).fetchall()
            newest = max(
                (
                    datetime.fromisoformat(r[0].replace("Z", "+00:00"))
                    for r in timestamps
                ),
                default=None,
            )
            if newest and newest > datetime.fromisoformat(
                m["received_at"].replace("Z", "+00:00")
            ):
                status = job["status"]
            received = (
                datetime.fromisoformat(m["received_at"].replace("Z", "+00:00"))
                .astimezone(ZoneInfo("Europe/Dublin"))
                .isoformat()
            )
            # Rejections confirm prior submission but do not supply its date.
            if m["kind"] == "applied" or m["submission_date"]:
                db.execute(
                    "INSERT INTO application_evidence VALUES(?,?,?,?,?) ON CONFLICT(job_id) DO UPDATE SET confirmed_at=MIN(application_evidence.confirmed_at,excluded.confirmed_at),submission_date=COALESCE(application_evidence.submission_date,excluded.submission_date)",
                    (job_id, "gmail", received, m["submission_date"], id),
                )
            db.execute(
                "UPDATE jobs SET status=?,application_date=COALESCE(application_date,?),updated_at=? WHERE id=?",
                (status, m["submission_date"], self.now(), job_id),
            )
            db.execute(
                "UPDATE mail_evidence SET state='confirmed',job_id=? WHERE id=?",
                (job_id, id),
            )
            self.w.record_event(
                db,
                "email_status_confirmed",
                job_id,
                message_id=id,
                status=status,
                submission_date=m["submission_date"],
            )
        self.w.export_tracking()
        self.export_state()
        return {"state": "confirmed", "job": self.w.get_job(job_id)}

    def runs(self):
        with self.w.connect() as db:
            rows = db.execute(
                "SELECT id,kind,job_id,state,result,error,created_at,updated_at FROM agent_runs ORDER BY created_at DESC LIMIT 100"
            ).fetchall()
        return [
            {**dict(r), "result": json.loads(r["result"]) if r["result"] else None}
            for r in rows
        ]

    def summary(self):
        jobs = self.w.jobs()
        with self.w.connect() as db:
            confirmed = {
                r[0]
                for r in db.execute(
                    'SELECT job_id FROM application_evidence UNION SELECT job_id FROM mail_evidence WHERE state="confirmed"'
                )
            }
        return {
            "jobs": jobs,
            "goals": self.goals(),
            "mail": self.mail(),
            "runs": self.runs(),
            "agents": AGENTS,
            "profile_dirty": self.profile_dirty(),
            "counts": {
                "saved": len(jobs),
                "applied": sum(
                    bool(j["application_date"])
                    or j["id"] in confirmed
                    or j["status"] in {"applied", "interview", "offer"}
                    for j in jobs
                ),
                "interviews": sum(j["status"] == "interview" for j in jobs),
                "offers": sum(j["status"] == "offer" for j in jobs),
            },
            "activity": self.w.activity(15),
        }
