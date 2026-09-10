from __future__ import annotations
import hashlib
import json
import shutil
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'scripts'))
from career import Workspace, safe_child, tex_escape
from dashboard.app import create_app
from validate_resume import validate_selected_project, extract_zero_argument_macros, evidence_ids_from_source

@pytest.fixture
def workspace(tmp_path):
    for name in ('config','context','templates','scripts'):
        shutil.copytree(ROOT/name,tmp_path/name)
    (tmp_path/'data').mkdir(exist_ok=True)
    (tmp_path/'data/historical-packs.json').write_text('[]')
    return Workspace(tmp_path)

def add(workspace, suffix='1', title='Data Analyst'):
    return workspace.add_job('Example employer',title,'Cork, Ireland',f'https://careers.example.test/jobs/{suffix}','Develop Power BI dashboards and reconcile reporting from multiple sources. Use SQL and work with business stakeholders to gather requirements and validate reporting results.')

def test_clean_identity_and_disclosure(workspace):
    assert workspace.profile()['candidate']['full_name']=='Chetan Babu M'
    assert workspace.profile()['candidate']['phone']=='+353-0892401738'
    assert workspace.profile()['claim_policy']['client_name_disclosure'].startswith('approved')
    assert workspace.evidence()['candidate_revision']==workspace.profile()['candidate_revision']
    assert workspace.jobs()==[]
    for forbidden in ('su'+'deep','Soli'+'ton','Vi'+'ally'):
        assert forbidden.lower() not in json.dumps(workspace.evidence()).lower()

def test_job_duplicate_and_persistence(workspace):
    j=add(workspace)
    with pytest.raises(ValueError,match='already saved'): add(workspace)
    assert Workspace(workspace.root).get_job(j['id'])['status']=='saved'
    with pytest.raises(ValueError,match='actual application date'):
        workspace.update_job(j['id'],'applied')
    workspace.update_job(j['id'],'applied','Sent through company portal','2026-09-09')
    assert Workspace(workspace.root).get_job(j['id'])['application_date']=='2026-09-09'

def test_invalid_urls_and_statuses(workspace):
    with pytest.raises(ValueError): workspace.add_job('A','B','Ireland','file:///etc/passwd','description '*30)
    j=add(workspace)
    with pytest.raises(ValueError): workspace.update_job(j['id'],'imagined-status')
    with pytest.raises(ValueError): workspace.update_job(j['id'],'applied',application_date='not-a-date')
    with pytest.raises(ValueError): workspace.update_job(j['id'],'applied',application_date='2099-01-01')

def test_drafts_are_versioned_and_never_applications(workspace):
    j=add(workspace); first=workspace.prepare(j['id'],'PROJ-AZ-RECON'); second=workspace.prepare(j['id'],'PROJ-AZ-MIGRATION')
    assert first['folder']!=second['folder']
    assert (workspace.root/first['folder']/'resume.tex').exists()
    job=workspace.get_job(j['id']); assert job['status']=='prepared' and job['application_date'] is None
    assert job['folder']==second['folder']

def test_each_ready_project_uses_exact_registry_content(workspace):
    j=add(workspace)
    assert len(workspace.rank_projects('')) == 14
    for project in workspace.evidence()['projects']:
        if not project.get('resume_content'): continue
        result=workspace.prepare(j['id'],project['id'])
        folder=workspace.root/result['folder']
        source=(folder/'resume.tex').read_text()
        failures=[]
        ids=evidence_ids_from_source(source,workspace.evidence(),failures)
        assert not failures, (project['id'],failures)
        validation=validate_selected_project(source,workspace.evidence(),project['id'],failures)
        assert not failures, (project['id'],failures)
        assert validation['content_matches_registry']
        mapping=__import__('yaml').safe_load((folder/'evidence-map.yml').read_text())
        assert mapping['role_eligible'] is False
        assert mapping['requirements']==[]
        assert set(mapping['resume_claim_ids'])==ids
        assert mapping['job_snapshot_sha256']==hashlib.sha256((folder/'job-description.md').read_bytes()).hexdigest()

def test_disallowed_project_and_scope_screen(workspace):
    j=add(workspace,title='Senior Software Engineer')
    assert workspace.screen(j)['decision']=='review_required'
    assert len(workspace.screen(j)['concerns'])>=2
    with pytest.raises(ValueError): workspace.prepare(j['id'],'PROJ-INVENTED')

def test_path_escape_and_symlink(workspace,tmp_path):
    output=workspace.root/'output';output.mkdir(exist_ok=True)
    with pytest.raises(ValueError): safe_child(output,'../context/evidence.yml')
    (output/'outside').symlink_to(workspace.root/'context')
    with pytest.raises(ValueError): safe_child(output,'outside/evidence.yml')

def test_latex_escaping():
    assert tex_escape('A & B 50% $1 {x}_y')==r'A \& B 50\% \$1 \{x\}\_y'

def test_api_workflow_notes_and_origin(workspace):
    client=TestClient(create_app(workspace.root),base_url='http://127.0.0.1')
    assert client.get('/').status_code==200
    for path in ('overview','profile','projects','jobs','portals'):
        assert client.get('/api/'+path).status_code==200
    before=(workspace.root/'context/evidence.yml').read_bytes()
    assert client.put('/api/profile/notes',json={'text':'New award status needs review.'}).status_code==200
    assert (workspace.root/'context/evidence.yml').read_bytes()==before
    assert client.get('/api/profile').json()['notes']=='New award status needs review.'
    assert client.put('/api/profile/notes',json={'text':'evil'},headers={'Origin':'https://foreign.example'}).status_code==403
    assert client.get('/api/profile',headers={'Host':'foreign.example'}).status_code==403
    assert client.get('/api/files/%2e%2e/context/evidence.yml').status_code==404
    response=client.post('/api/jobs',json={'company':'Employer','title':'BI Analyst','location':'Ireland','url':'https://careers.example.test/2','description':'SQL and Power BI dashboard development with stakeholders and requirements gathering. Validate multi-source reports and prepare dashboards.'})
    assert response.status_code==201
    jid=response.json()['id']
    result=client.post('/api/jobs/'+jid+'/prepare',json={'project_id':'PROJ-AZ-RECON'})
    assert result.status_code==200
    assert client.get('/api/jobs/'+jid).json()['job']['status']=='prepared'
    assert client.post('/api/jobs/'+jid+'/prepare',json={'project_id':'PROJ-MADE-UP'}).status_code==400

def test_stale_pdf_never_shows_release_ready(workspace):
    base=workspace.root/'output/base';base.mkdir(parents=True)
    pdf=base/'resume.pdf';pdf.write_bytes(b'pdf fixture')
    source=workspace.root/'templates/resume-base.tex'
    qa={'release_ready':True,'status':'PASS','candidate_revision':workspace.evidence()['candidate_revision'],'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest()}
    qa['registry_sha256']=hashlib.sha256((workspace.root/'context/evidence.yml').read_bytes()).hexdigest()
    qa['profile_sha256']=hashlib.sha256((workspace.root/'config/profile.yml').read_bytes()).hexdigest()
    (base/'qa.json').write_text(json.dumps(qa))
    assert workspace.artifacts()[0]['release_ready']
    source.write_text(source.read_text()+'\n% changed\n')
    assert not workspace.artifacts()[0]['release_ready']
    assert workspace.artifacts()[0]['status']=='REVIEW_REQUIRED'
