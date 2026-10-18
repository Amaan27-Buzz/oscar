import {Disclosure} from '../UIControls';
import {useEffect,useRef,useState} from 'react';
import {epistemicLabel,taskStatus} from '../bridge';
import type {Command,View} from '../bridge';

const terminal=['verified','partially_verified','failed','cancelled'];
function taskDescription(description:string) {
  const operations:Record<string,string>={write_file:'Create a file',read_file:'Read a file',list_files:'Browse files',find_files:'Find files',git_status:'Check project changes',git_diff:'Review project changes',git_branch:'Create a project branch',ps_environment:'Check this computer',ps_file_hash:'Check a file',ps_write_utf8:'Save text to a file',program_version:'Check an installed tool',inspect_page:'Read a web page',list_apps:'See available applications',launch_app:'Open an application',worker_tools:'See available tools'};
  return description.startsWith('Desktop owner ')?operations[description.slice(14)]??'Work on this computer':description;
}
export function Activity({view,available,busy,run,back,human=false}:{human?:boolean;view:View;available:boolean;busy:boolean;run:(command:Command)=>Promise<boolean>;back:()=>void}) {
  const title=useRef<HTMLHeadingElement>(null),reviewFocus=useRef<HTMLElement>(null);
  const [now,setNow]=useState(Date.now());
  const review=view.review;
  const task=review?(view.current?.task_id===review.task_id?view.current:view.tasks.find(t=>t.task_id===review.task_id)):view.current;
  const decisionCurrent=!!review&&!!task&&task.actions.includes(review.operation)&&now<review.expires_at_ms;
  useEffect(()=>{title.current?.focus({preventScroll:true});},[]);
  useEffect(()=>{
    if(!review)return;
    reviewFocus.current?.focus();
    setNow(Date.now());
    const timer=setTimeout(()=>setNow(Date.now()),Math.max(1,review.expires_at_ms-Date.now()));
    return()=>clearTimeout(timer);
  },[review?.review_id,review?.expires_at_ms]);
  const tasks=view.current?[view.current,...view.tasks.filter(t=>t.task_id!==view.current!.task_id)]:view.tasks;
  const attention=tasks.filter(t=>t.actions.includes('approve')||['blocked','unknown','failed'].includes(t.state));
  const active=tasks.filter(t=>!terminal.includes(t.state)&&!attention.includes(t));
  const completed=tasks.filter(t=>terminal.includes(t.state)&&!attention.includes(t));
  function list(items:View['tasks']) {return <ul className="activity-list">{items.map(t=><li key={t.task_id}><button disabled={!available||busy} aria-current={view.current?.task_id===t.task_id?'true':undefined} onClick={()=>run({kind:'inspect',task_id:t.task_id})}><span>{human?taskDescription(t.description):t.description}</span><small>{taskStatus(t)}</small></button></li>)}</ul>;}
  return <div className="activity-surface">
    <header data-tauri-drag-region><span data-tauri-drag-region>OSCAR / Activity</span><button onClick={back}>Back to Conversation</button></header>
    <div className="section-heading"><h1 ref={title} tabIndex={-1}>Activity</h1><p className="leaf-secondary">What OSCAR did, what is running, and what needs you.</p></div>
    {!available&&<p role="status" className="leaf-error">Connection unavailable. Saved work is visible; actions are disabled until you reconnect.</p>}
    {view.feedback&&!human&&<p className="leaf-error" role="alert">{view.feedback.message}</p>}
    <div className="activity-controls"><button disabled={busy} onClick={()=>run({kind:'refresh'})}>Refresh work</button><button disabled={busy} onClick={()=>run({kind:'discard'})}>Clear drafts and context</button></div>
    <div className="activity-history"><aside className="activity-timeline"><section aria-label="Needs attention"><h2>Needs attention <small>{attention.length}</small></h2>{attention.length?list(attention):<p className="leaf-secondary">Nothing needs your attention.</p>}</section><section aria-label="Active work"><h2>In progress <small>{active.length}</small></h2>{active.length?list(active):<p className="leaf-secondary">Nothing in progress.</p>}</section><section aria-label="Outcomes"><h2>Outcomes <small>{completed.length}</small></h2>{completed.length?list(completed):<p className="leaf-secondary">No outcomes yet.</p>}</section></aside>
    <div className="work-detail">
    {review?<section ref={reviewFocus} tabIndex={-1} className="decision-sheet" aria-label="Owner decision"><div className="decision-heading"><span className="decision-symbol" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M12 3 4 6v6c0 4 8 9 8 9s8-5 8-9V6l-8-3Zm-4 9 3 3 5-6"/></svg></span><div><h2>Review {review.operation==='approve'?'approval':review.operation==='deny'?'denial':'cancellation'}</h2><p>{human?taskDescription(review.description):review.description}</p></div></div>
      <dl className="review-context">{[['What will happen',review.consequence],['Why',review.reason]].map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
      <Disclosure className="exact-material" defaultOpen={true} title={<>Exact reviewed material</>}><pre>{review.review}</pre></Disclosure>
      <Disclosure className="request-details" title={<>Request details</>}><dl>{[['Permission',review.policy_reason],['Task',review.task_id??'Unknown'],['Executor',review.target],['Capability',review.capability],['Evidence state',review.evidence_state]].map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl></Disclosure>
      <p className="decision-guidance">You’ll confirm in a Windows dialog. Permission applies to this request; it does not create a permanent grant.</p>
      {!decisionCurrent&&<p role="status" className="leaf-error">This review is no longer current. Open this item again to review it.</p>}
      <div className="leaf-actions"><button className="leaf-primary" disabled={!available||busy||!decisionCurrent} onClick={()=>run({kind:'confirm',review_id:review.review_id,accept:true})}>Continue to confirmation</button><button disabled={busy} onClick={()=>run({kind:'confirm',review_id:review.review_id,accept:false})}>Dismiss review</button></div>
    </section>:view.current?<section aria-label="Selected task" className="selected-task"><div className="task-detail-heading"><span className={`task-status state-${view.current.state}`}>{taskStatus(view.current)}</span><h2>{human?taskDescription(view.current.description):view.current.description}</h2></div>
      {view.current.blocker&&<p role="status" className="leaf-error">{human?"This work needs attention before it can continue.":view.current.blocker}</p>}
      {view.current.progress&&Number.isFinite(view.current.progress.fraction)&&view.current.progress.fraction>=0&&view.current.progress.fraction<=1&&<div className="task-progress"><label>{human?'Progress':view.current.progress.step}<span>{Math.round(view.current.progress.fraction*100)}%</span></label><progress max="1" value={view.current.progress.fraction}/><small>{human?epistemicLabel(view.current.progress.status):view.current.progress.status}</small></div>}
      {(view.current.response||view.current.value)&&<div className="activity-result"><p className="leaf-secondary">{human?epistemicLabel(view.current.epistemic??view.current.response_status):view.current.epistemic??view.current.response_status??'REPORTED'}</p>{!!view.current.source_event_ids?.length&&<p className="leaf-secondary">{human?'From an earlier conversation. Things may have changed since then.':'Earlier retained evidence; current facts may differ. Inferred material remains inference.'}</p>}<pre tabIndex={0} aria-label="Task result">{view.current.value??view.current.response}</pre>{view.current.response_truncated&&<p className="leaf-secondary">Only an excerpt is available.</p>}</div>}
      <div className="leaf-actions">{(['approve','deny','cancel'] as const).filter(operation=>view.current!.actions.includes(operation)).map(operation=><button key={operation} disabled={!available||busy} onClick={()=>run({kind:'review',task_id:view.current!.task_id,operation})}>Review {operation==='approve'?'approval':operation==='deny'?'denial':'cancellation'}</button>)}</div>
      <Disclosure className="verification-details" title={<>{human?'Details and evidence':'Verification details'}</>}><dl>{view.current.blocker&&<div><dt>Why work stopped</dt><dd>{view.current.blocker}</dd></div>}<div><dt>Request</dt><dd>{view.current.description}</dd></div><div><dt>Executor</dt><dd>{view.current.target}</dd></div><div><dt>Attempt</dt><dd>{view.current.generation}</dd></div></dl><ul>{view.current.evidence_ids.map(id=><li key={id}>{id}</li>)}</ul>{!!view.current.source_event_ids?.length&&<><h3>Recall sources</h3><ul>{view.current.source_event_ids.map(id=><li key={id}>{id}</li>)}</ul></>}{view.current.evidence?.map(e=><p key={e.id}>{e.status} · {e.source} · {e.method} · {e.matches===true?'matches':e.matches===false?'does not match':'unknown match'} · {new Date(e.observed_at*1000).toLocaleString()}</p>)}{view.current.artifacts?.map(a=><p key={a.id}>{a.kind} · {a.status}<small>{a.id}{a.content_hash?` · SHA256 ${a.content_hash}`:''}</small></p>)}</Disclosure>
    </section>:<div className="activity-empty"><svg viewBox="0 0 40 40" aria-hidden="true"><path d="M10 12h20M10 20h14M10 28h18"/><circle cx="5" cy="12" r="1"/><circle cx="5" cy="20" r="1"/><circle cx="5" cy="28" r="1"/></svg><h2>Your recent work</h2><p>Open an item for its result, progress or anything that needs you.</p></div>}
    </div></div>
  </div>;
}
