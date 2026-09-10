#!/usr/bin/env python3
"""Local, evidence-first workspace operations. No applications or messages are sent."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import yaml
from tracking import Tracking

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {'saved', 'prepared', 'applied', 'interview', 'offer', 'rejected', 'withdrawn'}

def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def read_yaml(path):
    result = yaml.safe_load(path.read_text(encoding='utf-8'))
    if not isinstance(result, dict):
        raise ValueError(f'{path.name} must contain a mapping')
    return result

def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as f:
        f.write(text)
        tmp = Path(f.name)
    tmp.replace(path)

def safe_child(root, value):
    path = (root / value).resolve()
    if path == root.resolve() or root.resolve() not in path.parents:
        raise ValueError('Path must stay inside the workspace directory')
    return path

def job_url(value):
    parsed = urlsplit(value.strip())
    if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Use a complete public http(s) job URL without credentials')
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip('/') or '/', parsed.query, ''))

def tex_escape(text):
    return ''.join({'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}','|':r'\textbar{}'}.get(c,c) for c in text)

def tokens(text):
    stop = {'the','and','for','with','from','will','that','this','have','your','our','you','into','using','work','data','project','experience'}
    return {w for w in re.findall(r'[a-z][a-z0-9+#.-]{2,}', text.lower()) if w not in stop}

class Workspace(Tracking):
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()
        self.db_path = self.root / 'data/career.db'
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, company TEXT NOT NULL, title TEXT NOT NULL,
                location TEXT NOT NULL, url TEXT NOT NULL UNIQUE, description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'saved', created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '',
                application_date TEXT, selected_project_id TEXT, folder TEXT,
                verification TEXT NOT NULL DEFAULT 'not_verified')''')
            self.init_tracking(db)
    def connect(self):
        db = sqlite3.connect(self.db_path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        return db
    def profile(self):
        return read_yaml(self.root/'config/profile.yml')
    def evidence(self):
        return read_yaml(self.root/'context/evidence.yml')
    def jobs(self):
        with self.connect() as db:
            return [dict(r) for r in db.execute('SELECT * FROM jobs ORDER BY created_at DESC, id')]
    def get_job(self, job_id):
        with self.connect() as db:
            row = db.execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone()
        if row is None: raise ValueError('Opportunity not found')
        return dict(row)
    def add_job(self, company, title, location, url, description):
        values = [str(v).strip() for v in (company,title,location,url,description)]
        if not all(values): raise ValueError('Complete all job fields')
        company,title,location,url,description=values
        if len(description)<80: raise ValueError('Paste the actual job description (at least 80 characters)')
        url = job_url(url)
        job_id = hashlib.sha256(url.encode()).hexdigest()[:16]
        try:
            with self.connect() as db:
                db.execute('INSERT INTO jobs(id,company,title,location,url,description,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',(job_id,company,title,location,url,description,now(),now()))
                self.record_event(db, 'job_saved', job_id, company=company, title=title, url=url)
        except sqlite3.IntegrityError:
            raise ValueError('This posting is already saved') from None
        self.export_tracking()
        return self.get_job(job_id)
    def update_job(self, job_id, status, notes=None, application_date=None):
        old=self.get_job(job_id)
        if status not in STATUSES: raise ValueError('Unknown application status')
        if status=='applied' and not (application_date or old['application_date']):
            raise ValueError('Record the actual application date; preparing a resume is not an application')
        notes = old['notes'] if notes is None else notes
        if application_date:
            try:
                date=datetime.strptime(application_date,'%Y-%m-%d').date()
            except ValueError: raise ValueError('Application date must be YYYY-MM-DD') from None
            if date>datetime.now().date(): raise ValueError('Application date cannot be in the future')
        with self.connect() as db:
            db.execute('UPDATE jobs SET status=?,notes=?,application_date=?,updated_at=? WHERE id=?',(status,notes,application_date or old['application_date'],now(),job_id))
            self.record_event(db, 'progress_updated', job_id, before=old, after=dict(db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()))
        self.export_tracking()
        return self.get_job(job_id)
    def export_tracking(self):
        jobs=self.jobs()
        def cell(value): return str(value or '').replace('|','/').replace('\n',' ')
        header='# Active opportunity pipeline\n\nGenerated from data/career.db. Do not edit this projection directly.\n\n'
        rows=['| Company | Role | Location | Status | Posting |','|---|---|---|---|---|']
        rows += ['| '+' | '.join(cell(j[k]) for k in ('company','title','location','status','url'))+' |' for j in jobs]
        atomic_write(self.root/'data/pipeline.md',header+'\n'.join(rows)+'\n')
        applied=[j for j in jobs if j['application_date']]
        lines=['# Application tracker — Chetan Babu M','', 'Generated from data/career.db; only user-recorded application dates establish submission.','', '| Company | Role | Applied | Status |','|---|---|---|---|']
        lines += ['| '+' | '.join(cell(j[k]) for k in ('company','title','application_date','status'))+' |' for j in applied]
        atomic_write(self.root/'data/application-tracker.md','\n'.join(lines)+'\n')
        self.export_history()
        companies=sorted({j['company'] for j in applied},key=str.lower)
        atomic_write(self.root/'data/applied-companies.md','# Applied companies — Chetan Babu M\n\nGenerated from recorded application dates in data/career.db. No preparation implies an application.\n\n'+'\n'.join('- '+cell(c) for c in companies)+'\n')

    def rank_projects(self, description):
        target=tokens(description)
        out=[]
        for p in self.evidence()['projects']:
            if not p.get('resume_content') or p.get('status') in {'hold','missing'}: continue
            content=p.get('resume_content',{})
            evidence_text=' '.join([content.get('title',''),content.get('context',''),*content.get('bullets',[])])
            overlap=sorted(target & tokens(evidence_text))
            out.append({'id':p['id'],'title':content.get('title',p.get('name',p['id'])),'matched_terms':overlap,'match_count':len(overlap),'context':content.get('context',''),'bullets':content.get('bullets',[]),'caveats':p.get('prohibited',[]),'status':p.get('status')})
        return sorted(out,key=lambda p:(-p['match_count'],p['id']))
    def screen(self, job):
        title=job['title'].lower(); location=job['location'].lower()
        issues=[]
        if re.search(r'\b(senior|sr\.?|lead|principal|director|manager|head)\b',title): issues.append('Seniority needs evidence beyond the current early-career profile.')
        if re.search(r'\b(software|full.?stack|devops|mlops|hardware|embedded|firmware)\b',title): issues.append('This engineering track is outside the current professional profile.')
        if re.search(r'\b(?:ml|machine learning|ai|genai) engineer\b',title): issues.append('Professional AI/ML engineering is unsupported; confirm whether the role explicitly accepts candidate-project evidence.')
        if re.search(r'\bdata engineer\b',title): issues.append('Check for production pipeline/platform ownership requirements.')
        if not re.search(r'ireland|dublin|cork|limerick|galway|waterford|kilkenny|athlone|tralee|kerry|donegal|sligo|wexford|tipperary|kildare|meath|wicklow|clare|mayo|laois|louth|cavan|monaghan|roscommon|longford|leitrim|offaly|carlow|westmeath',location): issues.append('Ireland eligibility is not established by this location.')
        return {'decision':'review_required','concerns':issues,'note':'A title/keyword screen is not an eligibility decision. Review the full requirements and work-permission conditions.'}
    def prepare(self, job_id, project_id=None):
        job=self.get_job(job_id); ranked=self.rank_projects(job['title']+' '+job['description'])
        if not ranked: raise ValueError('No resume-ready projects in the registry')
        pid=project_id or ranked[0]['id']
        project=next((p for p in self.evidence()['projects'] if p['id']==pid and bool(p.get('resume_content')) and p.get('status') not in {'hold','missing'}),None)
        if not project: raise ValueError('Select a registered, resume-ready project')
        # A fresh version preserves previous edits and reviews.
        out=self.root/'output/applications'; out.mkdir(parents=True,exist_ok=True)
        folder=Path(tempfile.mkdtemp(prefix=f'{job_id}-',dir=out))
        source=(self.root/'templates/resume-base.tex').read_text()
        content=project['resume_content']
        values={'SelectedProjectID':pid,'SelectedProjectTitle':content['title'],'SelectedProjectContext':content['context']}
        bullets=content['bullets']
        values.update({f'SelectedProjectBullet{n}':b for n,b in zip(('One','Two','Three'),bullets)})
        for name,value in values.items():
            pattern=r'(% EVIDENCE: [^\n]+\n)(\\newcommand\{\\'+name+r'\}\{)[^\n]*(\})'
            source,count=re.subn(pattern,lambda m:'% EVIDENCE: '+pid+'\n'+m[2]+tex_escape(value)+m[3],source,count=1)
            if count!=1: raise ValueError('Base template content slot is missing: '+name)
        if len(bullets)==2:
            source=re.sub(r'% EVIDENCE: [^\n]+\n\\newcommand\{\\SelectedProjectBulletThree\}\{[^\n]*\}\n','',source)
            source=re.sub(r'\s*% EVIDENCE: [^\n]+\n\s*\\item \\SelectedProjectBulletThree\n','\n',source)
        a=source.index('% SELECTED_PROJECT_BLOCK_START'); b=source.index('% SELECTED_PROJECT_BLOCK_END')
        source=source[:a]+re.sub(r'% EVIDENCE: [^\n]+','% EVIDENCE: '+pid,source[a:b])+source[b:]
        snapshot=f"# {job['company']} — {job['title']}\n\nLocation: {job['location']}\nSource: {job['url']}\nSaved: {now()}\nVerification: not verified; user-supplied snapshot.\n\n{job['description']}\n"
        (folder/'job-description.md').write_text(snapshot)
        (folder/'resume.tex').write_text(source)
        ids=sorted({i for m in re.finditer(r'(?m)^\s*% EVIDENCE:\s*(.+)$',source) for i in m[1].split()})
        mapping={'candidate_revision':self.evidence()['candidate_revision'],'job_id':job_id,'role_eligible':False,'job_snapshot_sha256':hashlib.sha256(snapshot.encode()).hexdigest(),'supported_requirement_coverage':0,'requirements':[], 'company_problem':{'statement':'Pending review of the saved job description.','source_url':job['url'],'published_or_accessed':now()[:10],'evidence_class':'explicit','confidence':'low'},'selected_project_id':pid,'selected_project_reason':'Draft selection by overlap with approved project wording; review the business problem and full job requirements.','resume_claim_ids':ids,'held_claims_used':[]}
        (folder/'evidence-map.yml').write_text(yaml.safe_dump(mapping,sort_keys=False,allow_unicode=True))
        (folder/'evaluation.md').write_text('# Review required\n\n'+json.dumps(self.screen(job),indent=2)+'\n\nThis draft selects one existing project and retains the approved base summary. It has not received a recruiter review or complete JD tailoring. Review and complete evidence-map.yml before validation.\n')
        (folder/'company-research.md').write_text('# Research pending\n\nThe saved JD is user supplied. Verify the original posting, record employer sources and explain the selected project’s relevance. No employer research or live-job claim has been generated.\n')
        relative=str(folder.relative_to(self.root))
        with self.connect() as db:
            db.execute("UPDATE jobs SET folder=?, selected_project_id=?, status=CASE WHEN status='saved' THEN 'prepared' ELSE status END, updated_at=? WHERE id=?",(relative,pid,now(),job_id))
            self.record_event(db, 'draft_prepared', job_id, folder=relative, project_id=pid, review_required=True)
        self.export_tracking()
        return {'folder':relative,'project_id':pid,'review_required':True}
    def current_folder(self,job_id):
        job=self.get_job(job_id)
        if not job['folder']: raise ValueError('Prepare a draft first')
        return safe_child(self.root/'output',str(Path(job['folder']).relative_to('output')))
    def compile_preview(self,job_id):
        # Compile in a temporary directory; only publish a two-page, inspectable preview.
        folder=self.current_folder(job_id)
        sys.path.insert(0,str(self.root/'scripts'))
        from validate_resume import compile_latex, inspect_pdf
        with tempfile.TemporaryDirectory(prefix='chetan-compile-') as temp:
            pdf,log,error=compile_latex(folder/'resume.tex',Path(temp))
            if pdf is None: raise ValueError((error or log)[-5000:])
            report=inspect_pdf(pdf,folder/'resume-preview')
            if report['page_count']!=2: raise ValueError(f"Expected two pages; found {report['page_count']}. Edit the source before release.")
            (folder/'resume.pdf').write_bytes(pdf.read_bytes())
        atomic_write(folder/'preview.json',json.dumps({'review_required':True,'page_count':2,'source_sha256':hashlib.sha256((folder/'resume.tex').read_bytes()).hexdigest(),'created_at':now()},indent=2)+'\n')
        return {'folder':str(folder.relative_to(self.root)),'page_count':2,'review_required':True}
    def validate(self,job_id):
        folder=self.current_folder(job_id)
        result=subprocess.run([sys.executable,str(self.root/'scripts/validate_resume.py'),str(folder/'resume.tex'),'--compile','--output',str(folder/'resume.pdf'),'--render-dir',str(folder/'resume-preview'),'--qa-json',str(folder/'qa.json')],capture_output=True,text=True,timeout=180)
        qa=json.loads((folder/'qa.json').read_text()) if (folder/'qa.json').exists() else {'status':'FAIL','failures':[result.stderr or result.stdout]}
        return qa
    def artifacts(self):
        items=[]
        for p in sorted((self.root/'output').glob('**/*.pdf')):
            qa_path=p.parent/'qa.json'; qa={}
            if qa_path.exists():
                try: qa=json.loads(qa_path.read_text())
                except ValueError: pass
            source=self.root/'templates/resume-base.tex' if p.parent.name=='base' else p.parent/'resume.tex'
            stale=not source.exists() or qa.get('source_sha256')!=hashlib.sha256(source.read_bytes()).hexdigest() or qa.get('pdf_sha256')!=hashlib.sha256(p.read_bytes()).hexdigest() or qa.get('candidate_revision')!=self.evidence()['candidate_revision']
            stale = stale or qa.get('registry_sha256') != hashlib.sha256((self.root/'context/evidence.yml').read_bytes()).hexdigest() or qa.get('profile_sha256') != hashlib.sha256((self.root/'config/profile.yml').read_bytes()).hexdigest()
            for filename, expected in qa.get('preview_sha256', {}).items():
                preview = p.parent / 'resume-preview' / filename
                stale = stale or not preview.is_file() or hashlib.sha256(preview.read_bytes()).hexdigest() != expected
            if p.parent.name != 'base':
                mapping = p.parent / 'evidence-map.yml'
                jd = p.parent / 'job-description.md'
                stale = stale or not mapping.is_file() or qa.get('evidence_map', {}).get('sha256') != hashlib.sha256(mapping.read_bytes()).hexdigest()
                stale = stale or not jd.is_file() or qa.get('evidence_map', {}).get('job_snapshot_sha256') != hashlib.sha256(jd.read_bytes()).hexdigest()
            items.append({'path':str(p.relative_to(self.root/'output')),'name':p.name,'status':'REVIEW_REQUIRED' if stale else qa.get('status','REVIEW_REQUIRED'),'release_ready':bool(qa.get('release_ready')) and not stale})
        return items

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('status'); sub.add_parser('projects'); sub.add_parser('jobs'); sub.add_parser('activity'); sub.add_parser('export')
    notes=sub.add_parser('notes'); notes.add_argument('--file', type=Path, required=True)
    add=sub.add_parser('add'); add.add_argument('--file',type=Path,required=True)
    update=sub.add_parser('update'); update.add_argument('job_id'); update.add_argument('--status',choices=sorted(STATUSES),required=True); update.add_argument('--notes'); update.add_argument('--application-date')
    prep=sub.add_parser('prepare'); prep.add_argument('job_id'); prep.add_argument('--project')
    for name in ('preview','validate'):
        sub.add_parser(name).add_argument('job_id')
    args=parser.parse_args(); w=Workspace()
    if args.command=='status': result={'candidate':w.profile()['candidate']['full_name'],'jobs':len(w.jobs()),'artifacts':w.artifacts()}
    elif args.command=='jobs': result=w.jobs()
    elif args.command=='activity': result=w.activity()
    elif args.command=='export': w.export_tracking(); result={'exported':True}
    elif args.command=='notes': result=w.save_profile_notes(args.file.read_text())
    elif args.command=='add': result=w.add_job(**json.loads(args.file.read_text()))
    elif args.command=='update': result=w.update_job(args.job_id,args.status,args.notes,args.application_date)
    elif args.command=='projects': result=w.rank_projects('')
    elif args.command=='prepare': result=w.prepare(args.job_id,args.project)
    elif args.command=='preview': result=w.compile_preview(args.job_id)
    else: result=w.validate(args.job_id)
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
