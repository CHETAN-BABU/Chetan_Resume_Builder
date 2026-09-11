"""Versioned API for the four-tab React application."""
from typing import Any,Optional
from contextlib import asynccontextmanager
from fastapi import APIRouter
from pydantic import BaseModel,Field
from services.workspace_v2 import CareerServices,AGENTS
from services.agents import AgentRunner

class GoalInput(BaseModel):
    weekly_target:int=Field(ge=1,le=200)
    workdays:list[int]
    start_date:str
class KnowledgeInput(BaseModel):
    kind:str
    title:str=Field(min_length=1,max_length=250)
    summary:str=Field(default='',max_length=30000)
    data:dict[str,Any]=Field(default_factory=dict)
    revision:Optional[int]=None
class PostingInput(BaseModel):
    company:str=Field(min_length=1,max_length=150)
    title:str=Field(min_length=1,max_length=200)
    location:str=Field(min_length=1,max_length=150)
    url:str=Field(min_length=8,max_length=2500)
    description:str=Field(min_length=80,max_length=100000)
    requisition_id:str=''
class MailResolution(BaseModel):
    job_id:Optional[str]=None
    action:str='confirm'
class AgentInput(BaseModel):
    kind:str
    job_id:Optional[str]=None
class ScheduleInput(BaseModel):
    enabled:bool
    hours:int=Field(ge=1,le=24)

def attach(app,workspace):
    service=CareerServices(workspace);runner=AgentRunner(service)
    app.state.career=service;app.state.agents=runner
    router=APIRouter(prefix='/api/v2')
    @router.get('/summary')
    def summary():return service.summary()
    @router.get('/goals')
    def goals():return service.goals()
    @router.put('/goals')
    def save_goals(data:GoalInput):return service.save_goals(data.model_dump())
    @router.get('/profile')
    def profile():
        sources={}
        for relative in ['context/PROFILE.md','context/PROFILE-NOTES.md','context/QUESTIONS-FOR-YOU.md','context/UPDATES.md','context/sources/career.md','context/sources/masters-projects.md','context/sources/portfolio-audit.md']:
            path=workspace.root/relative
            if path.exists():sources[relative]=path.read_text()
        return {'items':service.knowledge(),'removed':sum(i['deleted'] for i in service.knowledge(True)),'registry':workspace.evidence(),'configuration':workspace.profile(),'sources':sources,'agents':AGENTS,'profile_dirty':service.profile_dirty(),'skills':[{'name':'Evidence registry','purpose':'Approved candidate wording and evidence IDs','path':'context/evidence.yml'},{'name':'Company-research playbook','purpose':'Public company and role investigation','path':'workflows/agents/company-researcher.md'},{'name':'Independent hiring review','purpose':'Role expectations without candidate context','path':'workflows/agents/hiring-manager.md'},{'name':'Verify job URL','purpose':'Checks specific posting URLs; browser review may still be required','path':'.agents/skills/verify-job-url/SKILL.md'},{'name':'Resume validation','purpose':'Evidence, two-page PDF and visual-review gates','path':'scripts/validate_resume.py'}]}
    @router.post('/profile/items',status_code=201)
    def add_item(data:KnowledgeInput):return service.save_knowledge(data.model_dump())
    @router.put('/profile/items/{id}')
    def edit_item(id:str,data:KnowledgeInput):return service.save_knowledge(data.model_dump(),id)
    @router.delete('/profile/items/{id}')
    def remove_item(id:str):return service.delete_knowledge(id)
    @router.post('/jobs')
    def add_posting(data:PostingInput):return service.add_posting(data.model_dump())
    @router.get('/mail')
    def mail():return service.mail()
    @router.post('/mail/{id}/resolve')
    def resolve_mail(id:str,data:MailResolution):return service.resolve_mail(id,**data.model_dump())
    @router.get('/email-schedule')
    def schedule():return service.pref('email_schedule',{'enabled':False,'hours':6})
    @router.put('/email-schedule')
    def save_schedule(data:ScheduleInput):service.set_pref('email_schedule',data.model_dump());return data.model_dump()
    @router.get('/agents')
    def agents():return {'agents':AGENTS,'runs':service.runs()}
    @router.post('/agents/run',status_code=202)
    def run(data:AgentInput):return runner.enqueue(data.kind,data.job_id)
    app.include_router(router)
    @asynccontextmanager
    async def lifespan(app):
        runner.recover();runner.start_schedule()
        yield
        runner.stop.set();runner.pool.shutdown(wait=False,cancel_futures=True)
    app.router.lifespan_context=lifespan
    return service
