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
                studio_folder = folder / 'studio'
                studio_folder.mkdir(exist_ok=True)
                stamp = self.s.now()
                with self.w.connect() as db:
                    db.execute('INSERT INTO studio_drafts VALUES(?,?,?,?,?,?)', (job_id, source, 1, str(studio_folder.relative_to(self.w.root)), stamp, self.w.evidence()['candidate_revision']))
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
        fields = {k: plain(v) for k, v in extract_zero_argument_macros(row['source']).items() if k in {'ResumeSummary', 'CoreSkills'} or k.startswith('SelectedProject')}
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
        active_projects = {i['id'] for i in self.s.knowledge() if i['kind'] == 'project' and i['review_state'] == 'registered'}
        return {**result, 'fields': fields, 'preview': preview, 'versions': versions,
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

    def save(self, job_id, revision, source=None, fields=None, project_id=None, restore_revision=None):
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
                if name not in {'ResumeSummary', 'CoreSkills'} and not name.startswith('SelectedProject'):
                    raise ValueError('Unknown resume field')
                source = replace_macro(source, name, value)
            if project_id:
                active = {i['id']: i for i in self.s.knowledge()}
                project = next((p for p in self.w.rank_projects('') if p['id'] == project_id), None)
                if not project or project_id not in active or active[project_id]['review_state'] != 'registered':
                    raise ValueError('Choose an active registered project. Edited projects need evidence review.')
                for name, value in {'SelectedProjectID': project_id, 'SelectedProjectTitle': project['title'], 'SelectedProjectContext': project['context'], **dict(zip(['SelectedProjectBulletOne', 'SelectedProjectBulletTwo', 'SelectedProjectBulletThree'], (project['bullets'] + [''])[:3]))}.items():
                    if name not in extract_zero_argument_macros(source):
                        source = source.replace(r'\begin{document}', '\\newcommand{\\' + name + '}{}\n' + r'\begin{document}')
                    source = replace_macro(source, name, value)
                start, end = source.index('% SELECTED_PROJECT_BLOCK_START'), source.index('% SELECTED_PROJECT_BLOCK_END')
                block = '% SELECTED_PROJECT_BLOCK_START\n\\textbf{\\SelectedProjectTitle}\\\\\n\\textit{\\SelectedProjectContext}\n\\begin{resumeitems}\n'
                for name in ['One', 'Two', 'Three'][:len(project['bullets'])]:
                    block += '% EVIDENCE: ' + project_id + '\n\\item \\SelectedProjectBullet' + name + '\n'
                source = source[:start] + block + '\\end{resumeitems}\n' + source[end:]
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
            return self.get(job_id)


    def fill(self, job_id, revision):
        """Commit a ranked full two-page version only after measuring the compiled result."""
        with self.lock:
            draft = self.get(job_id)
            if draft['revision'] != revision:
                raise ValueError('This resume changed elsewhere. Reload before filling two pages.')
            if self.s.profile_dirty() or draft['profile_revision'] != self.w.evidence()['candidate_revision']:
                raise ValueError('Reconcile your Profile edits with the evidence registry before adding ranked content. You can still edit and preview the saved draft.')
            source, ranking = ranked_source(draft['source'], self.w.get_job(job_id), self.w.evidence(), self.s.knowledge())
            executable = shutil.which('tectonic')
            if not executable:
                raise ValueError('PDF compiler is unavailable. Restart with Start Dashboard.command.')
            folder = safe_child(self.w.root / 'output', draft['file_root'])
            # Binary search typography within normal readable resume sizes. Never shrink below 10pt.
            low, high, point = 10.0, 12.0, 11.5
            best = None
            with tempfile.TemporaryDirectory(prefix='studio-fill-') as temp:
                for attempt in range(8):
                    build = Path(temp) / str(attempt)
                    build.mkdir()
                    candidate = set_density(source, round(point, 2), 5.0)
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
            return self.get(job_id)
