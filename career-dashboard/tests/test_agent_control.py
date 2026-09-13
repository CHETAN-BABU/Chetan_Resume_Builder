"""Free orchestration, spending limits, durable instructions and document isolation."""
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
import pytest
from test_career_workspace import workspace, add
from test_workspace_v2 import service
from services.agents import AgentRunner, REPORT_SCHEMA
from services.agent_cache import AgentCache
from services.resume_studio import ResumeStudio
from services.instruction_tracker import InstructionTracker
from services.resume_match import evaluate


def test_cache_reuses_stages_and_limits_even_failed_calls(service):
    cache = AgentCache(service)
    calls = []
    def invoke(*args, **kwargs):
        calls.append(args)
        return {'summary': 'ok', 'report': 'Saved result', 'sources': [], 'limitations': []}
    cache.configure(1)
    one = cache.execute(invoke, 'public role', REPORT_SCHEMA, web=False)
    assert cache.execute(invoke, 'public role', REPORT_SCHEMA, web=False) == one
    assert len(calls) == 1 and cache.stats()['cache_hits'] == 1
    with pytest.raises(ValueError, match='budget'):
        cache.execute(invoke, 'changed role', REPORT_SCHEMA, web=False)
    cache.configure(0)
    assert cache.execute(invoke, 'public role', REPORT_SCHEMA, web=False) == one
    assert AgentCache(service).stats()['cached_results'] == 1


def test_concurrent_cache_misses_make_one_call(service):
    cache = AgentCache(service)
    calls = []
    def invoke(*a, **k):
        calls.append(1)
        return {'summary': 'ok', 'report': 'ok', 'sources': [], 'limitations': []}
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: cache.execute(invoke, 'same', REPORT_SCHEMA, web=False), range(2)))
    assert len(calls) == 1


def test_cache_expiry_failure_and_schema_change(service):
    cache = AgentCache(service)
    calls=[]
    def invoke(*a, **k):
        calls.append(1)
        return {'summary': 'ok', 'report': 'ok', 'sources': [], 'limitations': []}
    cache.execute(invoke, 'web', REPORT_SCHEMA)
    with service.w.connect() as db:
        db.execute("UPDATE ai_cache SET created_at='2020-01-01T00:00:00+00:00'")
    cache.execute(invoke, 'web', REPORT_SCHEMA)
    assert len(calls)==2
    with pytest.raises(ValueError, match='incomplete'):
        cache.execute(lambda *a,**k: {}, 'bad', REPORT_SCHEMA)
    assert cache.stats()['cached_results']==1 and cache.stats()['calls_today']==3


def test_chat_applies_and_retains_unknown_conflicts_and_duplicate_requests(service):
    j=add(service.w); studio=ResumeStudio(service); d=studio.open(j['id']); chat=InstructionTracker(service, studio)
    r=chat.send('summary: My own 50% & SQL wording',j['id'],d['revision'],'message-1')
    assert r['state']=='applied'
    assert chat.send('summary: My own 50% & SQL wording',j['id'],d['revision'],'message-1')==r
    assert len(studio.get(j['id'])['versions'])==2
    assert chat.send('summary: Stale edit',j['id'],1)['state']=='needs_attention'
    assert chat.send('listen to this unusual contextual request',j['id'],2)['state']=='needs_clarification'
    assert chat.send('font: 8',j['id'],2)['state']=='needs_attention'
    assert len(InstructionTracker(service,studio).history(j['id']))==4
    assert service.w.get_job(j['id'])['application_date'] is None


def test_two_project_slots_and_second_capture(service):
    studio=ResumeStudio(service); j=add(service.w); d=studio.open(j['id'])
    assert d['fields']['SecondProjectID'] != d['fields']['SelectedProjectID']
    assert len(d['project_library'])>=14
    with pytest.raises(ValueError, match='distinct'):
        studio.save(j['id'],1,second_project_id=d['fields']['SelectedProjectID'])
    d=studio.save(j['id'],1,fields={'SecondProjectTitle':'New second project','SecondProjectBulletOne':'My independent prototype'})
    assert any(k['title']=='New second project' for k in service.knowledge())
    assert service.profile_dirty()


def test_document_scorer_has_no_profile_dependency():
    result=evaluate('Power BI dashboards using SQL.', 'Required SQL and Power BI dashboards. Python preferred.')
    assert result['score']==86
    assert result['gaps']==['python']
    assert result['profile_access'] is False and result['ai_used'] is False
    assert evaluate('SQL','Unrecognized-specialism')['score'] is None
    assert evaluate('Py', 'Python')['score']==0


def test_build_scores_actual_pdf_and_ai_review_has_only_document(service):
    if not shutil.which('tectonic'): pytest.skip('PDF runtime unavailable')
    studio=ResumeStudio(service); j=add(service.w); d=studio.open(j['id'])
    runner=AgentRunner(service);runner.studio=studio
    runner.enqueue('resume_build',j['id']);runner.pool.shutdown(wait=True)
    assert service.runs()[0]['state']=='completed', service.runs()[0]
    d=studio.get(j['id']);assert d['match']['current'] and d['match']['score'] is not None
    assert runner.cache.stats()['calls_today']==0
    service.w.update_job(j['id'],'prepared',notes='PRIVATE-NOTES')
    service.save_knowledge({'kind':'fact','title':'PRIVATE-PROFILE','summary':'Do not disclose'})
    prompts=[]
    def invoke(prompt,schema,**kwargs):
        prompts.append(prompt)
        return {'summary':'Review','report':'Review','sources':[],'limitations':[]}
    runner=AgentRunner(service,invoke);runner.studio=studio
    runner.enqueue('resume_match',j['id']);runner.pool.shutdown(wait=True)
    assert len(prompts)==1 and 'PRIVATE-' not in prompts[0]
    assert 'resume_text' in prompts[0] and 'job_description' in prompts[0]
    assert service.runs()[0]['result']['profile_access'] is False
    changed=studio.save(j['id'],d['revision'],fields={'ResumeSummary':'Different summary'})
    assert not changed['match']['current']
    with pytest.raises(ValueError,match='Build'):
        studio.match_input(j['id'])
