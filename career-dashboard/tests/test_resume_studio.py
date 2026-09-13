"""Studio persistence, profile capture and advisor isolation in disposable workspaces."""
import hashlib
import json
import shutil
import pytest
from concurrent.futures import ThreadPoolExecutor
from test_workspace_v2 import service
from test_career_workspace import workspace, add
from services.resume_studio import ResumeStudio, replace_macro
from services.agents import AgentRunner
from fastapi.testclient import TestClient
from dashboard.app import create_app


def test_open_preserves_existing_and_is_idempotent(service):
    j = add(service.w)
    studio = ResumeStudio(service)
    with ThreadPoolExecutor(max_workers=2) as pool:
        drafts = list(pool.map(studio.open, [j['id'], j['id']]))
    assert drafts[0]['source'] == drafts[1]['source']
    assert len(drafts[0]['versions']) == 1
    assert service.w.get_job(j['id'])['application_date'] is None
    folder = service.w.current_folder(j['id'])
    preserved = (folder / 'resume.tex').read_text()
    second = studio.save(j['id'], 1, fields={'ResumeSummary': 'User edit with 50% & SQL'})
    assert '50\\% \\& SQL' in second['source']
    assert (folder / 'resume.tex').read_text() == preserved
    assert studio.open(j['id'])['revision'] == 2


def test_capture_deduplicates_and_never_changes_registry(service):
    studio = ResumeStudio(service)
    j = add(service.w)
    draft = studio.open(j['id'])
    evidence = (service.w.root / 'context/evidence.yml').read_bytes()
    fields = {'SelectedProjectTitle': 'My new project', 'SelectedProjectContext': 'Personal work | Python', 'SelectedProjectBulletOne': 'Built a local prototype.', 'CoreSkills': 'SQL; New skill'}
    saved = studio.save(j['id'], 1, fields=fields)
    captured = [k for k in service.knowledge() if k['source'].startswith('User edit in Resume Studio')]
    assert {k['kind'] for k in captured} == {'project', 'skill'}
    assert all(k['review_state'] == 'user_updated' for k in captured)
    assert (service.w.root / 'context/evidence.yml').read_bytes() == evidence
    assert service.profile_dirty()
    assert studio.save(j['id'], 2, source=saved['source'])['revision'] == 2
    restored = studio.save(j['id'], 2, restore_revision=1)
    assert restored['source'] == draft['source']
    assert len(studio.get(j['id'])['captures']) == 2
    again = studio.save(j['id'], 3, fields=fields)
    assert len(again['captures']) == 2
    assert len(again['versions']) == 4
    assert service.w.get_job(j['id'])['status'] == 'prepared'


def test_concurrent_save_rejected_and_invalid_restore_atomic(service):
    studio = ResumeStudio(service)
    j = add(service.w)
    studio.open(j['id'])
    studio.save(j['id'], 1, fields={'ResumeSummary': 'First edit'})
    with pytest.raises(ValueError, match='changed elsewhere'):
        studio.save(j['id'], 1, fields={'ResumeSummary': 'Lost edit'})
    with pytest.raises(ValueError, match='not found'):
        studio.save(j['id'], 2, restore_revision=999)
    assert studio.get(j['id'])['revision'] == 2


def test_deleted_project_not_reintroduced_and_dirty_blocks_new_drafts(service):
    studio = ResumeStudio(service)
    j = add(service.w)
    studio.open(j['id'])
    project = next(i for i in service.knowledge() if i['kind'] == 'project')
    service.delete_knowledge(project['id'])
    with pytest.raises(ValueError, match='active registered'):
        studio.save(j['id'], 1, project_id=project['id'])
    with pytest.raises(ValueError, match='reconciliation'):
        studio.open(add(service.w, '2')['id'])
    assert studio.save(j['id'], 1, fields={'ResumeSummary': 'Existing draft edit'})['revision'] == 2


def test_project_switch_and_missing_project_warning(service):
    studio = ResumeStudio(service)
    j = add(service.w)
    studio.open(j['id'])
    d = studio.save(j['id'], 1, project_id='PROJ-SECOM-FAULT-DETECTION')
    assert d['fields']['SelectedProjectID'] == 'PROJ-SECOM-FAULT-DETECTION'
    assert not d['captures']
    d = studio.save(j['id'], 2, fields={'SelectedProjectTitle': ''})
    assert any('missing' in w for w in d['warnings'])


def test_advisor_receives_only_role_and_public_research(service):
    j = add(service.w)
    service.w.update_job(j['id'], 'saved', notes='PRIVATE-NOTES')
    service.save_knowledge({'kind': 'skill', 'title': 'PRIVATE-SKILL', 'summary': 'Secret'})
    calls = []
    def execute(prompt, schema, **kwargs):
        calls.append((prompt, kwargs))
        return {'summary': 'Public role expectations', 'report': 'Proposed project, not completed work', 'sources': [], 'limitations': []}
    runner = AgentRunner(service, execute)
    runner.enqueue('resume_advisor', j['id'])
    runner.pool.shutdown(wait=True)
    assert len(calls) == 2
    assert all('PRIVATE-' not in p for p, _ in calls)
    assert calls[1][1] == {'web': False}
    assert service.runs()[0]['result']['profile_access'] is False
    assert service.runs()[0]['state'] == 'completed'


def test_preview_revision_staleness_and_real_compile(service):
    if not shutil.which('tectonic'):
        pytest.skip('PDF runtime unavailable')
    studio = ResumeStudio(service)
    j = add(service.w)
    studio.open(j['id'])
    d = studio.preview(j['id'], 1)
    assert d['preview']['page_count'] == 2
    assert d['preview']['current']
    pdf = service.w.root / 'output' / d['preview']['path'] / 'resume.pdf'
    assert pdf.exists()
    assert (pdf.parent / 'page-01.png').exists()
    d = studio.save(j['id'], 1, fields={'ResumeSummary': 'A changed draft'})
    assert not d['preview']['current']
    with pytest.raises(ValueError, match='current resume'):
        studio.preview(j['id'], 1)
    assert pdf.exists()


def test_studio_api_keeps_origin_guard_and_rejects_stale_save(service):
    j = add(service.w)
    app = create_app(service.w.root)
    app.state.agents.execute = lambda *a, **kw: {'summary': 'Fixture', 'report': 'Fixture', 'sources': [], 'limitations': []}
    with TestClient(app, base_url='http://127.0.0.1') as client:
        url = '/api/v2/studio/' + j['id']
        assert client.post(url + '/open').status_code == 200
        assert client.post(url + '/open').status_code == 200
        assert len([r for r in service.runs() if r['kind'] == 'resume_advisor']) == 0
        assert client.put(url, json={'revision': 1, 'fields': {'CoreSkills': 'SQL; API test skill'}}, headers={'Origin': 'https://foreign.test'}).status_code == 403
        assert client.put(url, json={'revision': 1, 'fields': {'CoreSkills': 'SQL; API test skill'}}).status_code == 200
        assert client.put(url, json={'revision': 1, 'source': 'Stale'}).status_code == 400
        assert client.get(url).json()['revision'] == 2
