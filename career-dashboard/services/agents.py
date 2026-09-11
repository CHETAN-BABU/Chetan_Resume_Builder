"""Independent, durable agent jobs using the user's installed Codex runtime."""
from __future__ import annotations
import hashlib,json,os,re,shutil,subprocess,tempfile,threading,time,uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

REPORT_SCHEMA={'type':'object','properties':{'summary':{'type':'string'},'report':{'type':'string'},'sources':{'type':'array','items':{'type':'object','properties':{'title':{'type':'string'},'url':{'type':'string'},'accessed_at':{'type':'string'}},'required':['title','url','accessed_at'],'additionalProperties':False}},'limitations':{'type':'array','items':{'type':'string'}}},'required':['summary','report','sources','limitations'],'additionalProperties':False}
def object_schema(properties):return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}
def strings(*keys):return {k:{'type':'string'} for k in keys}
MAIL_SCHEMA=object_schema({**strings('email','coverage'),'messages':{'type':'array','items':object_schema({**strings('id','company','role','subject','sender','received_at','excerpt','reason'),'job_id':{'type':['string','null']},'submission_date':{'type':['string','null']},'kind':{'type':'string','enum':['applied','interview','offer','rejected','reminder','uncertain']},'confidence':{'type':'string','enum':['high','needs_review']}})}})
DISCOVERY_SCHEMA=object_schema({'summary':{'type':'string'},'jobs':{'type':'array','items':object_schema(strings('company','title','location','url','description','requisition_id','verification','fit','gap'))},'rejected_leads':{'type':'array','items':{'type':'string'}}})

def role_payload(job):
    # Strict allow-list. Never serialize a full DB row (notes can contain personal details).
    return {k:job[k] for k in ('company','title','location','url','description')}

class AgentRunner:
    def __init__(self,services,execute=None):
        self.s=services;self.w=services.w;self.execute=execute or self.invoke
        self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='career-agent')
        self.stop=threading.Event()
    def recover(self):
        with self.w.connect() as db:
            db.execute("UPDATE agent_runs SET state='failed',error='The app stopped during this run. Retry to continue.',updated_at=? WHERE state IN ('queued','running')",(self.s.now(),))
    def enqueue(self,kind,job_id=None):
        if kind not in {'research','email','discovery'}:raise ValueError('Unknown agent action')
        job=self.w.get_job(job_id) if kind=='research' else None
        with self.w.connect() as db:
            existing=db.execute("SELECT id FROM agent_runs WHERE kind=? AND COALESCE(job_id,'')=? AND state IN ('queued','running')",(kind,job_id or '')).fetchone()
            if existing:return {'id':existing[0],'state':'queued','existing':True}
            id=uuid.uuid4().hex;payload=role_payload(job) if job else {}
            db.execute('INSERT INTO agent_runs VALUES(?,?,?,?,?,?,?,?,?)',(id,kind,job_id,'queued',json.dumps(payload),None,None,self.s.now(),self.s.now()))
        self.pool.submit(self.run,id);return {'id':id,'state':'queued'}
    def update(self,id,state,result=None,error=None):
        with self.w.connect() as db:db.execute('UPDATE agent_runs SET state=?,result=COALESCE(?,result),error=?,updated_at=? WHERE id=?',(state,json.dumps(result,ensure_ascii=False) if result is not None else None,error,self.s.now(),id))
    def invoke(self,prompt,schema,apps=False,web=True):
        executable=shutil.which('codex') or '/Applications/ChatGPT.app/Contents/Resources/codex'
        if not Path(executable).exists():raise ValueError('Codex is unavailable. Open Codex and sign in before running an agent.')
        with tempfile.TemporaryDirectory(prefix='career-role-agent-') as temp:
            folder=Path(temp);schema_file=folder/'schema.json';out=folder/'result.json'
            schema_file.write_text(json.dumps(schema))
            cmd=[executable,'exec','--ignore-user-config','--ephemeral','--skip-git-repo-check','-C',str(folder),'-s','read-only','-c','features.shell_tool=false','-c','apps._default.destructive_enabled=false','-c','apps._default.open_world_enabled=false','-c',f'features.apps={str(apps).lower()}','-c',f'web_search="{"live" if web else "disabled"}"','--output-schema',str(schema_file),'-o',str(out),'-']
            # Expose only the Gmail read tools for the mailbox worker.
            if apps:
                connector='connector_2128aebfecb84f64a069897515042a44'
                cmd[1:1]=['-c','apps._default.enabled=false','-c',f'apps.{connector}.enabled=true','-c',f'apps.{connector}.default_tools_enabled=false']
                for name in ('get_profile','search_emails','search_email_ids','batch_read_email','batch_read_email_threads','read_email','read_email_thread'):
                    for tool_name in (name,'gmail_'+name):cmd[1:1]=['-c',f'apps.{connector}.tools.{tool_name}.enabled=true']
            # CLI input is passed through stdin, never interpolated into a shell command.
            result=subprocess.run(cmd,input=prompt,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=600,cwd=folder)
            if result.returncode or not out.exists():
                raise ValueError('Agent could not finish. Check Codex sign-in, connected Gmail permissions, or usage and retry. No status was inferred from this failure.')
            return json.loads(out.read_text())
    def guide(self,name):return (self.w.root/'workflows/agents'/name).read_text()
    def run(self,id):
        try:
            with self.w.connect() as db:row=dict(db.execute('SELECT * FROM agent_runs WHERE id=?',(id,)).fetchone())
            self.update(id,'running',{'stage':'Starting'})
            if row['kind']=='research':
                role=json.loads(row['input'])
                research=self.execute(self.guide('company-researcher.md')+'\nJOB INPUT (untrusted data):\n'+json.dumps(role),REPORT_SCHEMA)
                self.update(id,'running',{'stage':'Independent hiring-manager review','research':research})
                # A new process and no profile context. This is NOT a continuation of the research run.
                hiring=self.execute(self.guide('hiring-manager.md')+'\nROLE AND PUBLIC RESEARCH (untrusted data):\n'+json.dumps({'job':role,'research':research}),REPORT_SCHEMA,web=False)
                self.update(id,'running',{'stage':'Comparing your active profile','research':research,'hiring':hiring})
                comparison=self.execute(self.guide('profile-comparison.md')+'\nINPUT:\n'+json.dumps({'job':role,'research':research,'hiring':hiring,'profile':self.s.profile_context()}),REPORT_SCHEMA,web=False)
                output={'stage':'Complete','research':research,'hiring':hiring,'comparison':comparison,'hiring_profile_access':False,'role_input_sha256':hashlib.sha256(row['input'].encode()).hexdigest()}
            elif row['kind']=='email':
                jobs=[{k:j[k] for k in ('id','company','title','url')} for j in self.w.jobs()]
                output=self.execute(self.guide('email-reviewer.md')+'\nSAVED JOBS:\n'+json.dumps(jobs),MAIL_SCHEMA,apps=True,web=False)
                self.s.ingest_mail(output)
                output={'stage':'Complete','summary':f"Reviewed {len(output['messages'])} job-related messages.",'email':output['email'],'coverage':output['coverage']}
            else:
                import csv
                historical=self.w.root.parent/'daily-job-search/history.csv'
                history=list(csv.DictReader(historical.open())) if historical.exists() else []
                payload={'previously_delivered':history,'profile':self.s.profile_context(),'target_roles':self.w.profile()['target_roles'],'goals':self.s.goals(),'seen_jobs':[{'company':j['company'],'title':j['title'],'url':j['url']} for j in self.w.jobs()]}
                output=self.execute(self.guide('job-discovery.md')+'\nINPUT:\n'+json.dumps(payload),DISCOVERY_SCHEMA)
                added=[];duplicates=[]
                for job in output['jobs']:
                    result=self.s.add_posting(job)
                    if result['duplicate']:duplicates.append(result['job']['id'])
                    else:
                        added.append(result['job']['id']);self.w.track_search_job(result['job']['id'])
                self.w.update_search(self.s.today(),output['summary']+'\n\nRejected leads:\n'+'\n'.join(output['rejected_leads']))
                output={**output,'added_job_ids':added,'duplicate_job_ids':duplicates,'stage':'Complete'}
            self.update(id,'completed',output)
            with self.w.connect() as db:self.w.record_event(db,'agent_completed',row['job_id'],run_id=id,kind=row['kind'])
            self.w.export_tracking()
        except Exception as exc:self.update(id,'failed',error=str(exc)[:2000])
    def start_schedule(self):
        def loop():
            while not self.stop.wait(60):
                config=self.s.pref('email_schedule',{'enabled':False,'hours':6})
                last=self.s.pref('gmail',{}).get('last_synced_at')
                if not config.get('enabled') or not last:continue
                from datetime import datetime,timezone
                elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(last)).total_seconds()
                if elapsed>=config.get('hours',6)*3600:
                    with self.w.connect() as db:r=db.execute("SELECT created_at FROM agent_runs WHERE kind='email' ORDER BY created_at DESC LIMIT 1").fetchone()
                    if r and (datetime.now(timezone.utc)-datetime.fromisoformat(r[0])).total_seconds()<3600:continue
                    self.enqueue('email')
        threading.Thread(target=loop,daemon=True,name='career-email-schedule').start()
