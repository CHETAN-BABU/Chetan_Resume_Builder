'use strict';
const $ = (s, parent=document) => parent.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl = s => { try { const u=new URL(s);return ['http:','https:'].includes(u.protocol)?u.href:'#'; } catch { return '#'; } };
const qaLabel = s => ({PASS:'Reviewed and ready',AUTOMATED_PASS_MANUAL_PENDING:'Checks passed · visual review pending',REVIEW_REQUIRED:'Review required',FAIL:'Checks need attention'}[s]||s);
const fileUrl = path => '/api/files/'+path.split('/').map(encodeURIComponent).join('/');
let loadSequence=0;
async function api(path, method='GET', data) {
  const r=await fetch('/api'+path,{method,headers:data?{'Content-Type':'application/json'}:{},body:data?JSON.stringify(data):undefined});
  const value=await r.json();
  if(!r.ok) throw new Error(typeof value.detail==='string'?value.detail:JSON.stringify(value.detail||value));
  return value;
}
function notice(message,error=false){const n=$('#notice');n.textContent=message;n.classList.toggle('error',error);n.hidden=false;}
function heading(eyebrow,title,body,action=''){return `<section class="hero"><div><p class="eyebrow">${eyebrow}</p><h1>${title}</h1><p class="muted">${body}</p></div>${action?`<div class="hero-actions">${action}</div>`:''}</section>`;}
const addButton='<button class="primary add-job">Save an opportunity <span>＋</span></button>';
function bindAdd(){document.querySelectorAll('.add-job').forEach(b=>b.onclick=()=>{$('#form-error').textContent='';$('#job-dialog').showModal();});}
function empty(title,body,button=''){return `<div class="empty"><p class="eyebrow">A FRESH START</p><h2>${title}</h2><p class="muted">${body}</p>${button}</div>`;}
function jobCard(j){return `<article class="job-card"><div><span class="eyebrow">${esc(j.company)}</span><h3>${esc(j.title)}</h3><p class="muted">${esc(j.location)} · ${esc(j.status)} · posting not verified</p></div><a class="secondary" href="#job/${j.id}">Open opportunity ↗</a></article>`;}
async function overview(){
 const d=await api('/overview'), jobs=await api('/jobs');
 return heading('YOUR CAREER, WITH INTENTION','Make your next move count.','A clear home for your experience, opportunities and applications. Built around your professional BI work and academic data science.',addButton)+
 `<section class="metrics" aria-label="Workspace statistics">${[[d.counts.projects,'Resume-ready projects','Approved project wording'],[d.counts.saved_jobs,'Saved opportunities','Your current pipeline'],[d.counts.applied,'Applications recorded','Actual submissions only'],[d.counts.historical_packs,'Historical resume packs','Preserved, awaiting recheck']].map(([n,l,s])=>`<div class="metric"><label>${l}</label><strong>${n}</strong><small>${s}</small></div>`).join('')}</section>
 <section class="grid-2"><article class="card"><div class="card-head"><h2>A focused path forward</h2><span class="tag">YOUR WORKFLOW</span></div><div class="step"><span class="step-num">1</span><div><h3>Find a role that fits your evidence</h3><p class="muted">Start with Data Analyst, BI Developer and reporting roles. Evaluate graduate data science through your academic projects.</p></div></div><div class="step"><span class="step-num">2</span><div><h3>Build a resume you can defend</h3><p class="muted">Choose one registered project. Prepare two A4 pages with your real employment, methods and results.</p></div></div><div class="step"><span class="step-num">3</span><div><h3>Review, then make your move</h3><p class="muted">Check the posting, evidence, PDF and open questions. Record the submission when you apply.</p></div></div></article><article class="card feature"><p class="eyebrow">YOUR PROFESSIONAL FOUNDATION</p><h2>Business intelligence.<br>Backed by real delivery.</h2><div class="rule"></div><p>Infocepts experience spanning Power BI, SQL, requirements, report migration and stakeholder-facing delivery.</p><p class="muted">Your MSc and candidate projects add data science, model evaluation and retrieval applications.</p><a class="secondary" href="#evidence">Explore your evidence ↗</a></article></section>
 <div class="section-heading"><h2>Your working resume</h2><a href="#resumes">Open resume studio →</a></div>
 ${d.artifacts.length?`<div class="strip"><div><h3>Chetan Babu M · Data Analyst & BI Developer</h3><p class="muted">Two A4 pages · one selected project · ${esc(qaLabel(d.artifacts.find(x=>x.path.startsWith('base/'))?.status||'Review required'))}</p></div><a class="secondary" href="${fileUrl('base/Chetan_Babu_M_Resume.pdf')}" target="_blank" rel="noopener">View base PDF ↗</a></div>`:empty('Your base resume is ready to build.','Follow the base-resume build command in README.md.')}
 <div class="section-heading"><h2>Recent opportunities</h2><a href="#opportunities">View pipeline →</a></div>${jobs.length?`<div class="job-list">${jobs.slice(0,3).map(jobCard).join('')}</div>`:empty('Your next opportunity starts here.','Save a full job description to compare it with your project evidence. Your historical packs are kept separately.',addButton)}`;
}
async function opportunities(){
 const jobs=await api('/jobs'), portals=await api('/portals');
 return heading('FIND YOUR FIT','A deliberate job search.','Keep the posting, project choice, resume draft and application status together. Start with a specific Irish opportunity.',addButton)+
 (jobs.length?`<div class="job-list">${jobs.map(jobCard).join('')}</div>`:empty('A clean pipeline. A clear direction.','Prioritise your strengths in Power BI, SQL, reporting and stakeholder delivery. Add a specific posting when you find a fit.',addButton))+
 `<div class="section-heading"><h2>Employer discovery starting points</h2><span class="tag warn">RECHECK BEFORE USE</span></div><p class="muted small">These are saved career-page references, not verified openings. Full discovery and live-posting verification are documented in workflows/.</p><div class="portals">${(portals.tracked_companies||[]).filter(c=>c.enabled!==false).map(c=>`<a href="${esc(safeUrl(c.careers_url))}" target="_blank" rel="noopener">${esc(c.name)} ↗</a>`).join('')}</div>`;
}
async function daily(){
 const data=await api('/search-runs'), jobs=await api('/jobs');
 const run=data.runs.find(r=>r.date===data.today);
 return heading('ONE DAY AT A TIME',"Today's job search.",'Save suitable postings, prepare your resume and record what you actually do. Search results and your application tracker share one record.',addButton)+
 `<section class="grid-2"><article class="card"><div class="card-head"><h2>${esc(data.today)}</h2><span class="tag">EUROPE / DUBLIN</span></div><p class="muted">${run?run.jobs.length+' opportunities in this run.':'Start a run to organize today’s opportunities.'}</p>${run?'':'<button class="primary" id="start-search">Start today’s search</button>'}
 <form id="search-link" class="spaced" data-date="${esc(data.today)}"><label>Add a saved opportunity<select id="search-job">${jobs.map(j=>`<option value="${j.id}">${esc(j.company)} · ${esc(j.title)}</option>`).join('')}</select></label><button class="secondary" ${jobs.length?'':'disabled'}>Add to today</button></form></article>
 <article class="card"><h2>Search notes & next actions</h2><p class="muted">Keep search coverage, rejected leads, gaps and follow-up plans here. Ask this chat to discover and verify live jobs.</p><form id="search-notes"><label>Today's notes<textarea id="daily-notes" rows="5">${esc(run?.notes||'')}</textarea></label><button class="secondary">Save search notes</button></form></article></section>
 <div class="section-heading"><h2>Today's opportunities</h2><a href="#opportunities">All opportunities →</a></div>${run?.jobs.length?'<div class="job-list">'+run.jobs.map(jobCard).join('')+'</div>':empty('Make space for a good match.','Save a full posting, then add it to today’s search.')}
 <div class="section-heading"><h2>Previous searches</h2></div>${data.runs.filter(r=>r.date!==data.today).map(r=>`<details class="card spaced"><summary>${esc(r.date)} · ${r.jobs.length} opportunities</summary><pre class="document spaced">${esc(r.notes)}</pre><div class="job-list">${r.jobs.map(jobCard).join('')}</div></details>`).join('')||'<p class="muted">Your completed days will appear here.</p>'}`;
}
async function activity(){
 const events=await api('/activity');
 const labels={job_saved:'Opportunity saved',progress_updated:'Application progress updated',draft_prepared:'Resume draft prepared',profile_notes_updated:'Profile update recorded',search_started:'Daily search started',search_job_added:'Opportunity added to search',search_notes_updated:'Search notes updated'};
 return heading('A RECORD YOU CAN TRUST','Your activity history.','Changes made in the dashboard and through this chat stay together. Profile notes retain their previous text; new resume facts still require evidence review.')+
 (events.length?events.map(e=>`<article class="card spaced"><div class="card-head"><h3>${esc(labels[e.action]||e.action)}</h3><span class="muted small">${esc(new Date(e.occurred_at).toLocaleString('en-IE'))}</span></div>${e.job_id?`<a href="#job/${e.job_id}">Open opportunity →</a>`:''}<details class="spaced"><summary>View recorded changes</summary><pre class="document">${esc(JSON.stringify(e.details,null,2))}</pre></details></article>`).join(''):empty('Your history starts here.','Save an opportunity or record an update to begin.'));
}
async function evidence(){
 const data=await api('/profile'), projects=await api('/projects');
 return heading('WHAT YOU CAN STAND BEHIND','Your evidence, organised.','Approved wording, project methods and limitations in one place. Professional work and academic projects keep their original context.')+
 `<input class="search" id="project-search" aria-label="Filter projects" placeholder="Filter projects: Power BI, fraud, RAG, PCA…"><div class="project-list">${projects.map(p=>`<article class="card project" data-search="${esc((p.title+' '+p.context+' '+p.bullets.join(' ')).toLowerCase())}"><div class="card-head"><span class="tag">${esc(p.status)}</span><code>${esc(p.id)}</code></div><h2>${esc(p.title)}</h2><p class="muted">${esc(p.context)}</p><details><summary>Read approved resume bullets</summary><ul>${p.bullets.map(b=>`<li>${esc(b)}</li>`).join('')}</ul></details></article>`).join('')}</div><p id="filter-empty" class="muted" hidden>No projects match that filter.</p>
 <div class="section-heading"><h2>Complete claim registry</h2><span class="tag">${data.evidence.claims.length} CLAIMS</span></div><details class="card"><summary>View every claim, including held and conditional information</summary><div class="spaced document-wrap"><pre class="document">${esc(JSON.stringify(data.evidence.claims,null,2))}</pre></div></details>`;
}
async function profile(){
 const data=await api('/profile'), overviewData=await api('/overview'),c=data.profile.candidate;
 return heading('THE SOURCE OF YOUR STORY','All your information, in view.','Your supplied details are preserved. Client names and your supplied Irish phone are included, following your disclosure preference.')+
 `<div class="grid-2"><article class="card"><h2>Chetan Babu M</h2><span class="tag">${esc(data.evidence.candidate_revision)}</span><dl class="metadata">${[['Professional identity',data.profile.professional_identity.primary],['Location',c.location],['Email',c.email],['Irish phone — supplied',c.phone],['Alternate phone — supplied',c.alternate_phone_as_supplied],['LinkedIn',c.linkedin],['Current permission',c.immigration_permission_as_confirmed+' · confirmed '+c.immigration_permission_confirmed_on],['Prior expiry — unconfirmed',c.visa_statement_as_supplied],['Current academic status',c.current_status],['Latest employment',c.most_recent_role]].map(([k,v])=>`<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join('')}</dl></article><article class="card"><h2>Details to resolve</h2><p class="muted small">Keeping information visible does not settle conflicting dates or verify reported outcomes.</p><div class="document-wrap"><pre class="document">${esc(overviewData.questions)}</pre></div></article></div>
 <article class="card spaced"><h2>Add a profile update</h2><p class="muted">Record corrections or new evidence here. These notes remain pending until the claim registry and template are updated; saving a note does not silently change approved resume facts.</p><form id="notes-form"><label>Updates and supporting evidence<textarea id="profile-notes" rows="7">${esc(data.notes)}</textarea></label><button class="primary" type="submit">Save update notes</button></form></article><details class="card spaced"><summary>View the complete structured profile</summary><pre class="document spaced">${esc(JSON.stringify(data.profile,null,2))}</pre></details>`;
}
async function resumes(){
 const data=await api('/overview');
 return heading('PREPARE. CHECK. REFINE.','Your resume studio.','One selected project. Two A4 pages. Clear evidence for each claim. Job drafts stay separate from reviewed releases.', '<a class="primary" href="#opportunities">Choose an opportunity ↗</a>')+
 `<div class="note">A generated PDF is a draft until the evidence mapping and visual review pass. Changing the source or candidate revision invalidates the displayed release status.</div>`+
 (data.artifacts.length?`<div class="job-list">${data.artifacts.map(a=>`<article class="job-card"><div><p class="eyebrow">${esc(a.path.startsWith('base/')?'BASE RESUME':'JOB DRAFT')}</p><h3>${esc(a.name)}</h3><p class="muted">${esc(a.path)}</p><p><span class="tag ${a.release_ready?'':'warn'}">${esc(qaLabel(a.status))}</span></p></div><a class="secondary" href="${fileUrl(a.path)}" target="_blank" rel="noopener">View ${a.release_ready?'PDF':'draft'} ↗</a></article>`).join('')}</div>`:empty('No compiled PDFs yet.','Build the base resume using README.md, or prepare a job draft from an opportunity.'))+
 `<details class="card history"><summary>${data.historical.length} historical prepared packs · preserved in backup/historical</summary><p class="muted spaced">Prior QA belongs to the earlier profile revision. These packs were not imported as applications or approved current resumes.</p><ul>${data.historical.map(h=>`<li><code>../${esc(h.folder)}</code><br><span class="muted">${esc(h.status)} · previous QA: ${esc(h.prior_qa_status)}</span></li>`).join('')}</ul></details>`;
}
async function jobPage(id){
 const data=await api('/jobs/'+id),j=data.job;
 return `<a class="back" href="#opportunities">← All opportunities</a>`+heading(esc(j.company),esc(j.title),`${esc(j.location)} · saved ${esc(j.created_at.slice(0,10))}`,`<a class="secondary" href="${esc(safeUrl(j.url))}" target="_blank" rel="noopener">Open original posting ↗</a>`)+
 `<div class="note">Posting not verified. ${esc(data.screen.note)}${data.screen.concerns.length?'<ul>'+data.screen.concerns.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>':''}</div>
 <div class="grid-2"><article class="card"><h2>Prepare an evidence-based draft</h2><p class="muted">Projects are ordered by overlapping terms in their approved wording. This is a starting point for manual tailoring, not a fit score.</p><label>Selected project<select id="selected-project">${data.projects.map(p=>`<option value="${esc(p.id)}" ${j.selected_project_id===p.id?'selected':''}>${esc(p.title)} · ${p.match_count} matching terms</option>`).join('')}</select></label><div class="button-row"><button class="primary" id="prepare">Prepare new draft</button>${j.folder?'<button class="secondary" id="preview">Compile preview</button><button class="secondary" id="validate">Run full checks</button>':''}</div>${j.folder?`<p class="muted small spaced">Current folder: <code>${esc(j.folder)}</code></p><p class="small">Review <a href="${fileUrl(j.folder.replace(/^output\//,'')+'/evidence-map.yml')}" target="_blank" rel="noopener">evidence-map.yml</a>, evaluation and research in this folder. Full checks require a reviewed role decision and requirement mapping.</p>`:''}<div id="build-result" class="spaced" aria-live="polite"></div></article>
 <article class="card"><h2>Track your actual progress</h2><form id="status-form"><label>Status<select id="job-status">${['saved','prepared','applied','interview','offer','rejected','withdrawn'].map(s=>`<option ${j.status===s?'selected':''}>${s}</option>`).join('')}</select></label><label>Actual application date<input id="application-date" type="date" value="${esc(j.application_date||'')}"></label><label>Notes<textarea id="job-notes" rows="4">${esc(j.notes)}</textarea></label><button class="secondary" type="submit">Save progress</button></form></article></div>
 <article class="card spaced"><h2>Saved job description</h2><div class="document-wrap"><pre class="document">${esc(j.description)}</pre></div></article>${j.folder?`<details class="card spaced"><summary>Open current PDF preview</summary><p class="muted spaced">Compile a preview first. This viewer displays the current draft and does not certify it for release.</p><iframe class="preview" title="Draft resume PDF" src="${fileUrl(j.folder.replace(/^output\//,'')+'/resume.pdf')}"></iframe></details>`:''}`;
}
function bindPage(route){
 bindAdd();
 if(route==='daily'){
   const act=async(fn,message)=>{try{await fn();notice(message);await render();}catch(err){notice(err.message,true);}};
   const date=$('#search-link').dataset.date;
   if($('#start-search')) $('#start-search').onclick=()=>act(()=>api('/search-runs/'+date,'POST'),'Today’s search started.');
   $('#search-link').onsubmit=e=>{e.preventDefault();act(()=>api('/search-runs/'+date+'/jobs/'+$('#search-job').value,'POST'),'Opportunity added to today’s search.');};
   $('#search-notes').onsubmit=e=>{e.preventDefault();act(()=>api('/search-runs/'+date,'PUT',{text:$('#daily-notes').value}),'Search notes saved.');};
 }
 if($('#project-search')) $('#project-search').oninput=e=>{let n=0;document.querySelectorAll('.project').forEach(card=>{card.hidden=!card.dataset.search.includes(e.target.value.toLowerCase());if(!card.hidden)n++;});$('#filter-empty').hidden=n>0;};
 if($('#notes-form')) $('#notes-form').onsubmit=async e=>{e.preventDefault();try{const r=await api('/profile/notes','PUT',{text:$('#profile-notes').value});notice(r.note);}catch(err){notice(err.message,true);}};
 if(route.startsWith('job/')){
   const id=route.slice(4);
   $('#status-form').onsubmit=async e=>{e.preventDefault();try{await api('/jobs/'+id,'PATCH',{status:$('#job-status').value,notes:$('#job-notes').value,application_date:$('#application-date').value||null});notice('Progress saved.');}catch(err){notice(err.message,true);}};
   for(const action of ['prepare','preview','validate']){
     const b=$('#'+action); if(!b)continue;
     b.onclick=async()=>{b.disabled=true;const old=b.textContent;b.textContent=action==='prepare'?'Preparing…':'Checking…';try{
       const r=await api('/jobs/'+id+'/'+action,'POST',action==='prepare'?{project_id:$('#selected-project').value}:undefined);
       if(action==='prepare'){notice('Draft created with one registered project. Compile its preview, then complete the review files.');await render();}
       else if(action==='preview'){notice('Two-page preview compiled. Evidence and visual review are still required.');await render();}
       else {$('#build-result').innerHTML=`<span class="tag ${r.release_ready?'':'warn'}">${esc(qaLabel(r.status))}</span><ul class="qa-list">${[...(r.failures||[]),...(r.warnings||[])].map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`;}
     }catch(err){notice(err.message,true);}finally{b.disabled=false;b.textContent=old;}};
   }
 }
}
async function render(){
 const seq=++loadSequence,route=location.hash.slice(1)||'overview';
 const name=route.startsWith('job/')?'opportunities':route;
 document.querySelectorAll('nav a').forEach(a=>a.classList.toggle('active',a.hash==='#'+name));
 $('#breadcrumb').textContent='Workspace / '+({'overview':'Overview','opportunities':'Opportunities','resumes':'Resume studio','evidence':'Evidence & projects','profile':'Your profile','daily':'Daily search','activity':'Activity'}[name]||'Overview');
 try{
   const html=route.startsWith('job/')?await jobPage(route.slice(4)):await ({overview,opportunities,resumes,evidence,profile,daily,activity}[route]||overview)();
   if(seq!==loadSequence)return;
   $('#view').innerHTML=html;bindPage(route);
 }catch(err){if(seq!==loadSequence)return;$('#view').innerHTML=empty('Something needs attention.',esc(err.message),'<button class="secondary" id="retry">Try again</button>');$('#retry').onclick=render;}
}
$('#job-dialog .close').onclick=()=>$('#job-dialog').close();
$('#job-form').onsubmit=async e=>{e.preventDefault();const button=$('button[type=submit]',e.target);button.disabled=true;try{const values=Object.fromEntries(new FormData(e.target));const j=await api('/jobs','POST',values);$('#job-dialog').close();e.target.reset();location.hash='job/'+j.id;notice('Opportunity saved. Its live status still needs verification.');}catch(err){$('#form-error').textContent=err.message;}finally{button.disabled=false;}};
window.addEventListener('hashchange',()=>{render();window.scrollTo(0,0);});
render();
