"""Job-specific editable drafts, version history and deterministic profile capture."""
from __future__ import annotations
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import threading
import yaml
from pathlib import Path
from pypdf import PdfReader
from career import atomic_write, safe_child, tex_escape
from validate_resume import extract_zero_argument_macros, inspect_pdf, evidence_ids_from_source
from services.resume_layout import ranked_source, set_density, measure_pages


def plain(text):
    for before, after in [(r'\textbar{}', '|'), (r'\textbackslash{}', '\\'),
                          (r'\textasciitilde{}', '~'), (r'\textasciicircum{}', '^')]:
        text = text.replace(before, after)
    return re.sub(r'\\([&%$#_{}])', r'\1', text).strip()


def replace_macro(source, name, value):
    old = extract_zero_argument_macros(source).get(name)
    if old is None:
        raise ValueError('Template field is missing: ' + name + '. Use the source editor to restore it.')
    prefix = re.search(r'\\newcommand\{\\' + re.escape(name) + r'\}\s*\{', source)
    start = prefix.end()
    return source[:start] + tex_escape(value.replace('\n', ' ')) + source[start + len(old):]


class ResumeStudio:
    def __init__(self, service):
        self.s, self.w = service, service.w
        self.lock = threading.RLock()
        with self.w.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS studio_drafts(job_id TEXT PRIMARY KEY REFERENCES jobs(id), source TEXT NOT NULL, revision INTEGER NOT NULL, folder TEXT NOT NULL, updated_at TEXT NOT NULL, profile_revision TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS studio_versions(job_id TEXT NOT NULL REFERENCES jobs(id), revision INTEGER NOT NULL, source TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(job_id,revision));
            CREATE TABLE IF NOT EXISTS resume_scores(job_id TEXT NOT NULL REFERENCES jobs(id), revision INTEGER NOT NULL, source_sha256 TEXT NOT NULL, pdf_sha256 TEXT NOT NULL, jd_sha256 TEXT NOT NULL, result TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(job_id,revision,jd_sha256,pdf_sha256));
            CREATE TABLE IF NOT EXISTS studio_captures(job_id TEXT NOT NULL REFERENCES jobs(id), fingerprint TEXT NOT NULL, knowledge_id TEXT NOT NULL REFERENCES knowledge(id), PRIMARY KEY(job_id,fingerprint));
            ''')

    def open(self, job_id):
        with self.lock:
            job = self.w.get_job(job_id)
            with self.w.connect() as db:
                row = db.execute('SELECT * FROM studio_drafts WHERE job_id=?', (job_id,)).fetchone()
            if not row:
                if self.s.profile_dirty():
                    raise ValueError('Profile edits need evidence reconciliation before creating a new resume. Existing Studio drafts remain editable.')
                if not job['folder']:
                    self.w.prepare(job_id)
                folder = self.w.current_folder(job_id)
                source = (folder / 'resume.tex').read_text()
                # Preserve existing prepared wording. Only a newly prepared draft gets skill ordering.
                if not job['folder']:
                    macros = extract_zero_argument_macros(source)
                    skills = plain(macros['CoreSkills']).split('; ')
                    jd = (job['title'] + ' ' + job['description']).casefold()
                    skills.sort(key=lambda skill: skill.casefold() not in jd)
                    source = replace_macro(source, 'CoreSkills', '; '.join(skills))
                mapping_file = folder / 'evidence-map.yml'
                draft_profile_revision = (yaml.safe_load(mapping_file.read_text()) or {}).get('candidate_revision', self.w.evidence()['candidate_revision']) if mapping_file.exists() else self.w.evidence()['candidate_revision']
                studio_folder = folder / 'studio'
                studio_folder.mkdir(exist_ok=True)
                stamp = self.s.now()
                with self.w.connect() as db:
                    db.execute('INSERT INTO studio_drafts VALUES(?,?,?,?,?,?)', (job_id, source, 1, str(studio_folder.relative_to(self.w.root)), stamp, draft_profile_revision))
                    db.execute('INSERT INTO studio_versions VALUES(?,?,?,?)', (job_id, 1, source, stamp))
                    self.w.record_event(db, 'studio_opened', job_id, revision=1)
                self.w.export_tracking()
            return self.get(job_id)

    def get(self, job_id):
        with self.w.connect() as db:
            row = db.execute('SELECT * FROM studio_drafts WHERE job_id=?', (job_id,)).fetchone()
            if not row:
                raise ValueError('Open Resume Studio for this job first')
            versions = [dict(r) for r in db.execute('SELECT revision,created_at FROM studio_versions WHERE job_id=? ORDER BY revision DESC', (job_id,))]
            captures = [dict(r) for r in db.execute('SELECT DISTINCT k.id,k.kind,k.title,k.review_state,k.deleted FROM studio_captures c JOIN knowledge k ON k.id=c.knowledge_id WHERE c.job_id=?', (job_id,))]
        result = dict(row)
        folder = safe_child(self.w.root / 'output', str(Path(row['folder']).relative_to('output')))
        atomic_write(folder / 'resume.tex', row['source'])
        preview_file = folder / 'preview.json'
        preview = json.loads(preview_file.read_text()) if preview_file.exists() else None
        if preview:
            preview['current'] = preview['source_sha256'] == hashlib.sha256(row['source'].encode()).hexdigest()
        fields = {k: plain(v) for k, v in extract_zero_argument_macros(row['source']).items() if k in {'ResumeSummary', 'CoreSkills'} or k.startswith(('SelectedProject', 'SecondProject'))}
        warnings = []
        if self.s.profile_dirty():
            warnings.append('Profile has unreviewed changes. Reconcile evidence before releasing this resume; this saved draft may contain older wording.')
        if row['profile_revision'] != self.w.evidence()['candidate_revision']:
            warnings.append('This draft was started with an older evidence revision. Review it against the current profile.')
        if not fields.get('SelectedProjectTitle') or not fields.get('SelectedProjectBulletOne'):
            warnings.append('Your selected project is missing. Add a project before exporting your application resume.')
        if preview and preview.get('layout') and not preview['layout']['full_two_pages']:
            warnings.append('The preview has unfilled space or more/fewer than two pages. Use Fill two pages to rank supported content and balance the layout.')
        warnings.append('Draft only: wording, evidence, two-page layout and visual review must pass before release.')
        if not fields.get('SecondProjectID') or not fields.get('SecondProjectTitle') or not fields.get('SecondProjectBulletOne'):
            warnings.append('A second project is required. Sync profile & rank 2 projects, or select a second registered project.')
        active_projects = {i['id'] for i in self.s.knowledge() if i['kind'] == 'project' and i['review_state'] == 'registered'}
        with self.w.connect() as db:
            score_row = db.execute('SELECT * FROM resume_scores WHERE job_id=? ORDER BY created_at DESC,rowid DESC LIMIT 1', (job_id,)).fetchone()
        match = None
        preview_pdf = safe_child(self.w.root / 'output', preview['path'] + '/resume.pdf') if preview else None
        current_pdf_hash = hashlib.sha256(preview_pdf.read_bytes()).hexdigest() if preview_pdf and preview_pdf.exists() else None
        if score_row:
            match = {**json.loads(score_row['result']), 'revision': score_row['revision'], 'created_at': score_row['created_at'],
                     'current': score_row['source_sha256'] == hashlib.sha256(row['source'].encode()).hexdigest()
                     and score_row['jd_sha256'] == hashlib.sha256(self.w.get_job(job_id)['description'].encode()).hexdigest()
                     and score_row['pdf_sha256'] == current_pdf_hash}
        library = self.s.knowledge()
        ranked = self.w.rank_projects(self.w.get_job(job_id)['description'])
        ranks = {p['id']: (index + 1, p) for index, p in enumerate(ranked)}
        projects = []
        for item in library:
            if item['kind'] != 'project':
                continue
            rank, known = ranks.get(item['id'], (None, {}))
            projects.append({'id': item['id'], 'title': item['title'], 'rank': rank if item['review_state'] == 'registered' else None,
                             'review_state': item['review_state'], 'eligible': item['id'] in active_projects and bool(known),
                             'score': known.get('match_count'), 'reason': known.get('matched_terms', [])})
        projects.sort(key=lambda p: (p['rank'] is None, p['rank'] or 999, p['title']))
        return {**result, 'fields': fields, 'match': match, 'project_library': projects, 'preview': preview, 'versions': versions,
                'captures': captures, 'warnings': warnings, 'file_root': str(folder.relative_to(self.w.root / 'output')),
                'projects': [p for p in self.w.rank_projects(self.w.get_job(job_id)['description']) if p['id'] in active_projects]}

    def capture(self, db, job_id, kind, title, summary):
        title, summary = title.strip()[:250], summary.strip()[:30000]
        if not title:
            return
        fingerprint = hashlib.sha256((kind + '\n' + title.casefold() + '\n' + summary).encode()).hexdigest()
        if db.execute('SELECT 1 FROM studio_captures WHERE job_id=? AND fingerprint=?', (job_id, fingerprint)).fetchone():
            return
        # Reuse an exact entry across jobs; never resurrect a deleted profile entry.
        old = db.execute('SELECT id,deleted FROM knowledge WHERE kind=? AND lower(title)=lower(?) AND summary=?', (kind, title, summary)).fetchone()
        if old and old['deleted']:
            return
        related = db.execute("SELECT * FROM knowledge WHERE kind=? AND lower(title)=lower(?) AND source=?", (kind, title, 'User edit in Resume Studio for job ' + job_id)).fetchone()
        if not old and related and not related['deleted']:
            db.execute("UPDATE knowledge SET summary=?,revision=revision+1,review_state='user_updated',updated_at=? WHERE id=?", (summary, self.s.now(), related['id']))
            self.w.record_event(db, 'profile_entry_saved', job_id, entry_id=related['id'], before=dict(related), summary=summary, origin='resume_studio')
            old = related
        key = old['id'] if old else 'studio:' + fingerprint[:24]
        if not old:
            db.execute('INSERT INTO knowledge VALUES(?,?,?,?,?,?,?,?,?,?)', (key, kind, title, summary,
                json.dumps({'origin': 'resume_studio', 'job_id': job_id, 'user_supplied': True}),
                'User edit in Resume Studio for job ' + job_id, 1, 0, 'user_updated', self.s.now()))
            self.w.record_event(db, 'profile_entry_saved', job_id, entry_id=key, origin='resume_studio', kind=kind)
        db.execute('INSERT OR IGNORE INTO studio_captures VALUES(?,?,?)', (job_id, fingerprint, key))

    def track(self, db, job_id, before, after):
        if 'SecondProjectTitle' in after:
            # Reuse the first-slot tracker on a document containing only second-slot definitions.
            def second_only(text):
                return '\n'.join(line for line in text.splitlines() if 'SecondProject' in line).replace('SecondProject', 'SelectedProject')
            self.track(db, job_id, second_only(before), second_only(after))
        old, new = extract_zero_argument_macros(before), extract_zero_argument_macros(after)
        keys = ['SelectedProjectTitle', 'SelectedProjectContext', 'SelectedProjectBulletOne', 'SelectedProjectBulletTwo', 'SelectedProjectBulletThree']
        if any(old.get(k) != new.get(k) for k in keys) and new.get('SelectedProjectTitle'):
            title = plain(new['SelectedProjectTitle'])
            summary = '\n'.join(plain(new[k]) for k in keys[1:] if new.get(k))
            registered = any(p.get('resume_content', {}).get('title') == title and
                             '\n'.join([p['resume_content'].get('context', ''), *p['resume_content'].get('bullets', [])]) == summary
                             for p in self.w.evidence()['projects'])
            if not registered:
                self.capture(db, job_id, 'project', title, summary)
        def skills(source, macros):
            text = plain(macros.get('CoreSkills', ''))
            section = source.split(r'\section{Technical Skills}')
            if len(section) > 1:
                body = section[1].split(r'\section{')[0].split(r'\end{document}')[0]
                for line in body.splitlines():
                    if line.strip().startswith(r'\textbf{') and not line.strip().startswith(r'\textbf{Languages'):
                        text += ';' + re.sub(r'\\\\\[.*?\]', '', line.split('}', 1)[-1])
            return {s.strip(): s.strip().casefold() for s in re.split('[;,\n]', plain(text)) if s.strip()}
        previous = set(skills(before, old).values())
        known = ' '.join(r['title'] + ' ' + r['summary'] for r in db.execute("SELECT title,summary FROM knowledge WHERE kind='skill' AND deleted=0")).casefold()
        for skill, normalized in skills(after, new).items():
            if normalized not in previous and not re.search(r'(?<!\w)' + re.escape(normalized) + r'(?!\w)', known):
                self.capture(db, job_id, 'skill', skill, skill)

    def save(self, job_id, revision, source=None, fields=None, project_id=None, restore_revision=None, second_project_id=None):
        with self.lock, self.w.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM studio_drafts WHERE job_id=?', (job_id,)).fetchone()
            if not row or row['revision'] != revision:
                raise ValueError('This resume changed elsewhere. Copy your edits, then reload before saving.')
            before = row['source']
            if restore_revision is not None:
                version = db.execute('SELECT source FROM studio_versions WHERE job_id=? AND revision=?', (job_id, restore_revision)).fetchone()
                if not version:
                    raise ValueError('Saved version not found')
                source = version['source']
            source = before if source is None else source
            for name, value in (fields or {}).items():
                if name not in {'ResumeSummary', 'CoreSkills'} and not name.startswith(('SelectedProject', 'SecondProject')):
                    raise ValueError('Unknown resume field')
                source = replace_macro(source, name, value)
            if project_id or second_project_id:
                from services.resume_projects import install_project
                active = {i['id']: i for i in self.s.knowledge()}
                for chosen, second in [(project_id, False), (second_project_id, True)]:
                    if not chosen:
                        continue
                    project = next((p for p in self.w.rank_projects('') if p['id'] == chosen), None)
                    if not project or chosen not in active or active[chosen]['review_state'] != 'registered':
                        raise ValueError('Choose an active registered project. Edited projects need evidence review.')
                    other = extract_zero_argument_macros(source).get('SelectedProjectID' if second else 'SecondProjectID')
                    if other == chosen:
                        raise ValueError('Choose two distinct projects')
                    source = install_project(source, project, second)
            if extract_zero_argument_macros(before).get('SelectedProjectID') != extract_zero_argument_macros(source).get('SelectedProjectID'):
                source = re.sub(r'% STUDIO_PROJECT_SKILLS\n% EVIDENCE:[^\n]+\n[^\n]+\n', '', source)
            if not source.strip() or len(source) > 150000:
                raise ValueError('Resume source must contain 1–150,000 characters')
            if source != before:
                if restore_revision is None:
                    self.track(db, job_id, before, source)
                stamp = self.s.now()
                db.execute('UPDATE studio_drafts SET source=?,revision=revision+1,updated_at=? WHERE job_id=?', (source, stamp, job_id))
                db.execute('INSERT INTO studio_versions VALUES(?,?,?,?)', (job_id, revision + 1, source, stamp))
                self.w.record_event(db, 'studio_saved', job_id, revision=revision + 1, restored_from=restore_revision)
        self.s.export_profile()
        self.w.export_tracking()
        return self.get(job_id)

    def write_review_sources(self, target, source, job_id):
        """Keep each preview's JD and claim references aligned without claiming a review."""
        original = self.w.current_folder(job_id)
        mapping_path = original / 'evidence-map.yml'
        mapping = yaml.safe_load(mapping_path.read_text()) if mapping_path.exists() else {}
        snapshot = original / 'job-description.md'
        if snapshot.exists():
            shutil.copy2(snapshot, target / 'job-description.md')
            mapping['job_snapshot_sha256'] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
        errors = []
        ids = evidence_ids_from_source(source, self.w.evidence(), errors)
        mapping.update(job_id=job_id, resume_claim_ids=sorted(ids),
                       selected_project_id=extract_zero_argument_macros(source).get('SelectedProjectID'),
                       selected_project_ids=[extract_zero_argument_macros(source).get(k) for k in ('SelectedProjectID', 'SecondProjectID') if extract_zero_argument_macros(source).get(k)],
                       candidate_revision=self.w.evidence()['candidate_revision'],
                       studio_review_required=True, source_evidence_errors=errors)
        atomic_write(target / 'resume.tex', source)
        atomic_write(target / 'evidence-map.yml', yaml.safe_dump(mapping, sort_keys=False))

    def preview(self, job_id, revision):
        with self.lock:
            draft = self.get(job_id)
            if draft['revision'] != revision:
                raise ValueError('Save or reload the current resume before compiling.')
            executable = shutil.which('tectonic')
            if not executable:
                raise ValueError('PDF compiler is unavailable. Your draft is saved; restart with Start Dashboard.command.')
            folder = safe_child(self.w.root / 'output', draft['file_root'])
            with tempfile.TemporaryDirectory(prefix='studio-preview-') as temp:
                build = Path(temp)
                (build / 'resume.tex').write_text(draft['source'])
                try:
                    run = subprocess.run([executable, '--untrusted', '--outdir', str(build), 'resume.tex'], cwd=build, capture_output=True, text=True, timeout=90)
                except subprocess.TimeoutExpired:
                    raise ValueError('Preview timed out. Your source is saved; check it for loops or very large content.') from None
                if run.returncode or not (build / 'resume.pdf').exists():
                    raise ValueError('Preview could not compile. Your edits are saved.\n' + (run.stderr + run.stdout)[-3500:])
                if len(PdfReader(str(build / 'resume.pdf')).pages) > 10:
                    raise ValueError('Preview exceeds ten pages. Reduce the content before compiling again.')
                report = inspect_pdf(build / 'resume.pdf', build / 'pages')
                target = folder / ('preview-' + str(revision))
                target.mkdir(exist_ok=True)
                self.write_review_sources(target, draft['source'], job_id)
                shutil.copy2(build / 'resume.pdf', target / 'resume.pdf')
                for page in (build / 'pages').glob('*.png'):
                    shutil.copy2(page, target / page.name)
                metadata = {'revision': revision, 'source_sha256': hashlib.sha256(draft['source'].encode()).hexdigest(), 'page_count': report['page_count'], 'created_at': self.s.now(), 'path': str(target.relative_to(self.w.root / 'output')), 'review_required': True, 'layout': measure_pages(build / 'resume.pdf', build / 'pages')}
                atomic_write(folder / 'preview.json', json.dumps(metadata))
            self.score(job_id)
            return self.get(job_id)


    def fill(self, job_id, revision):
        """Commit a ranked full two-page version only after measuring the compiled result."""
        with self.lock:
            draft = self.get(job_id)
            if draft['revision'] != revision:
                raise ValueError('This resume changed elsewhere. Reload before filling two pages.')
            if self.s.profile_dirty() or draft['profile_revision'] != self.w.evidence()['candidate_revision']:
                raise ValueError('Reconcile your Profile edits with the evidence registry before adding ranked content. You can still edit and preview the saved draft.')
            # Old saved drafts get the second ranked project on explicit fitting.
            from services.resume_projects import install_project
            base_source = draft['source']
            if not extract_zero_argument_macros(base_source).get('SecondProjectID'):
                choices = [p for p in draft['projects'] if p['id'] != draft['fields'].get('SelectedProjectID')]
                if not choices:
                    raise ValueError('Two active registered projects are required')
                base_source = install_project(base_source, choices[0], second=True)
            source, ranking = ranked_source(base_source, self.w.get_job(job_id), self.w.evidence(), self.s.knowledge())
            executable = shutil.which('tectonic')
            if not executable:
                raise ValueError('PDF compiler is unavailable. Restart with Start Dashboard.command.')
            folder = safe_child(self.w.root / 'output', draft['file_root'])
            # Binary search typography within normal readable resume sizes. Never shrink below 10pt.
            fixed_font = self.s.pref('resume_font:' + job_id)
            low, high, point = 10.0, 12.0, fixed_font or 11.5
            best = None
            with tempfile.TemporaryDirectory(prefix='studio-fill-') as temp:
                for attempt in range(2 if fixed_font else 13):
                    item_sep = 5.0
                    if fixed_font and attempt == 1:
                        point, item_sep = fixed_font, 6.0
                    elif not fixed_font and attempt >= 8:
                        point, item_sep = [12.0, 11.5, 11.0, 10.5, 10.0][attempt - 8], 6.0
                    build = Path(temp) / str(attempt)
                    build.mkdir()
                    candidate = set_density(source, round(point, 2), item_sep)
                    (build / 'resume.tex').write_text(candidate)
                    try:
                        result = subprocess.run([executable, '--untrusted', '--outdir', str(build), 'resume.tex'], cwd=build, capture_output=True, text=True, timeout=90)
                    except subprocess.TimeoutExpired:
                        raise ValueError('Page fitting timed out. Your previous draft remains unchanged.') from None
                    if result.returncode or not (build / 'resume.pdf').exists():
                        raise ValueError('Could not compile the ranked draft. Your previous version is preserved.\n' + (result.stderr + result.stdout)[-2000:])
                    if len(PdfReader(str(build / 'resume.pdf')).pages) > 2:
                        high = point
                        point = (low + high) / 2
                        continue
                    report = inspect_pdf(build / 'resume.pdf', build / 'pages')
                    layout = measure_pages(build / 'resume.pdf', build / 'pages')
                    if layout['full_two_pages']:
                        best = (build, candidate, layout, round(point, 2))
                        break
                    if report['page_count'] > 2:
                        high = point
                    else:
                        low = point
                    point = (low + high) / 2
                if best is None:
                    raise ValueError('The available supported content could not fill exactly two pages cleanly at 10–12pt. Your draft is unchanged. Add relevant confirmed detail or reduce unusually long custom text, then try again.')
                build, candidate, layout, body_pt = best
                stamp = self.s.now()
                new_revision = revision + 1 if candidate != draft['source'] else revision
                with self.w.connect() as db:
                    db.execute('BEGIN IMMEDIATE')
                    current = db.execute('SELECT revision FROM studio_drafts WHERE job_id=?', (job_id,)).fetchone()
                    if current[0] != revision:
                        raise ValueError('This resume changed elsewhere during fitting. Reload before retrying.')
                    if new_revision != revision:
                        # Registry-derived additions are not new user claims: do not feed the profile tracker.
                        db.execute('UPDATE studio_drafts SET source=?,revision=?,updated_at=? WHERE job_id=?', (candidate, new_revision, stamp, job_id))
                        db.execute('INSERT INTO studio_versions VALUES(?,?,?,?)', (job_id, new_revision, candidate, stamp))
                    self.w.record_event(db, 'studio_filled_two_pages', job_id, revision=new_revision, body_font_pt=body_pt, page_fill=[p['fill_percent'] for p in layout['pages']], section_order=ranking['section_order'])
                target = folder / ('preview-' + str(new_revision))
                target.mkdir(exist_ok=True)
                self.write_review_sources(target, candidate, job_id)
                shutil.copy2(build / 'resume.pdf', target / 'resume.pdf')
                for page in (build / 'pages').glob('*.png'):
                    shutil.copy2(page, target / page.name)
                metadata = {'revision': new_revision, 'source_sha256': hashlib.sha256(candidate.encode()).hexdigest(), 'page_count': 2, 'created_at': stamp, 'path': str(target.relative_to(self.w.root / 'output')), 'review_required': True, 'layout': layout, 'ranking': ranking, 'body_font_pt': body_pt}
                atomic_write(folder / 'preview.json', json.dumps(metadata, indent=2))
                atomic_write(target / 'layout-review.json', json.dumps(metadata, indent=2))
                atomic_write(target / 'resume.tex', candidate)
            self.w.export_tracking()
            self.score(job_id)
            return self.get(job_id)


    def match_input(self, job_id):
        """Allow-listed snapshot from the actual current PDF, never candidate context."""
        draft = self.get(job_id)
        preview = draft['preview']
        if not preview or not preview['current'] or preview['revision'] != draft['revision']:
            raise ValueError('Build the current saved resume before scoring')
        pdf = safe_child(self.w.root / 'output', preview['path'] + '/resume.pdf')
        text = '\n'.join(p.extract_text() or '' for p in PdfReader(str(pdf)).pages)
        jd = self.w.get_job(job_id)['description']
        return {'resume_text': text, 'job_description': jd, 'revision': draft['revision'],
                'source_sha256': hashlib.sha256(draft['source'].encode()).hexdigest(),
                'pdf_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
                'jd_sha256': hashlib.sha256(jd.encode()).hexdigest()}

    def score(self, job_id):
        from services.resume_match import evaluate
        with self.lock:
            payload = self.match_input(job_id)
            with self.w.connect() as db:
                old = db.execute('SELECT result FROM resume_scores WHERE job_id=? AND revision=? AND jd_sha256=? AND pdf_sha256=?',
                                 (job_id, payload['revision'], payload['jd_sha256'], payload['pdf_sha256'])).fetchone()
                if old:
                    return {**json.loads(old[0]), 'cached': True}
            result = evaluate(payload['resume_text'], payload['job_description'])
            with self.w.connect() as db:
                db.execute('INSERT INTO resume_scores VALUES(?,?,?,?,?,?,?)',
                           (job_id, payload['revision'], payload['source_sha256'], payload['pdf_sha256'], payload['jd_sha256'], json.dumps(result), self.s.now()))
                self.w.record_event(db, 'resume_scored', job_id, revision=payload['revision'], score=result['score'], profile_access=False)
            self.w.export_tracking()
            return {**result, 'cached': False}

    def sync_profile(self, job_id, revision):
        """Apply the reviewed September correction and rank both slots as a new version."""
        from services.resume_projects import install_project
        with self.lock:
            draft = self.get(job_id)
            if draft['revision'] != revision:
                raise ValueError('This resume changed elsewhere. Reload before syncing')
            if self.s.profile_dirty():
                raise ValueError('Reconcile pending Profile edits before syncing the resume')
            ranked = draft['projects']
            if len(ranked) < 2:
                raise ValueError('Two active registered projects are required')
            source = draft['source']
            # This migration is deliberately tied to reviewed evidence, not arbitrary date guessing.
            claim = next(c for c in self.w.evidence()['claims'] if c['id'] == 'EXP-INFOCEPTS-001')
            if claim['dates'] == 'Sep 2023-Jul 2025':
                source = source.replace('Sep 2023 -- Jan 2025', 'Sep 2023 -- Jul 2025')
            if any(c['id'] == 'EXP-TOTAL-001' for c in self.w.evidence()['claims']):
                source = source.replace('approximately two years of enterprise reporting experience', '3+ years of combined professional and internship experience')
                source = re.sub(r'(% EVIDENCE: )([^\n]+)(\n\\newcommand\{\\ResumeSummary\})',
                                lambda m: m[1] + ' '.join(dict.fromkeys((m[2] + ' EXP-TOTAL-001').split())) + m[3], source)
            source = install_project(source, ranked[0])
            source = install_project(source, ranked[1], second=True)
            # Registry-derived updates are not new user claims, so bypass capture.
            stamp = self.s.now()
            with self.w.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                current = db.execute('SELECT revision FROM studio_drafts WHERE job_id=?', (job_id,)).fetchone()
                if current[0] != revision:
                    raise ValueError('This resume changed elsewhere. Reload before syncing')
                db.execute('UPDATE studio_drafts SET source=?,revision=revision+1,profile_revision=?,updated_at=? WHERE job_id=?',
                           (source, self.w.evidence()['candidate_revision'], stamp, job_id))
                db.execute('INSERT INTO studio_versions VALUES(?,?,?,?)', (job_id, revision+1, source, stamp))
                self.w.record_event(db, 'studio_profile_synced', job_id, revision=revision+1,
                                    profile_revision=self.w.evidence()['candidate_revision'], projects=[p['id'] for p in ranked[:2]])
            self.w.export_tracking()
            return self.get(job_id)
