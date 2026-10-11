import {useEffect,useRef,useState} from 'react';
import {statuses} from '../bridge';
import type {Command,View} from '../bridge';

const terminal=['verified','partially_verified','failed','cancelled'];
export function Activity({view,available,busy,run,back}:{view:View;available:boolean;busy:boolean;run:(command:Command)=>Promise<boolean>;back:()=>void}) {
  const title=useRef<HTMLHeadingElement>(null),reviewFocus=useRef<HTMLElement>(null);
  const [now,setNow]=useState(Date.now());
  const review=view.review;
  const task=review?(view.current?.task_id===review.task_id?view.current:view.tasks.find(t=>t.task_id===review.task_id)):view.current;
  const decisionCurrent=!!review&&!!task&&task.actions.includes(review.operation)&&now<review.expires_at_ms;
  useEffect(()=>{title.current?.focus();},[]);
  useEffect(()=>{
    if(!review)return;
    reviewFocus.current?.focus();
    setNow(Date.now());
    const timer=setTimeout(()=>setNow(Date.now()),Math.max(1,review.expires_at_ms-Date.now()));
    return()=>clearTimeout(timer);
  },[review?.review_id,review?.expires_at_ms]);
  const tasks=view.current?[view.current,...view.tasks.filter(t=>t.task_id!==view.current!.task_id)]:view.tasks;
  const active=tasks.filter(t=>!terminal.includes(t.state));
  const completed=tasks.filter(t=>terminal.includes(t.state));
  function list(tasks:View['tasks']) {return <ul className="activity-list">{tasks.map(t=><li key={t.task_id}><button disabled={!available||busy} aria-current={view.current?.task_id===t.task_id?'true':undefined} onClick={()=>run({kind:'inspect',task_id:t.task_id})}><strong>{statuses[t.state]??'Unknown outcome'}</strong><span>{t.description}</span><small>{t.mode||'Shared task'} · {t.target}</small></button></li>)}</ul>;}
  return <div className="activity-surface">
    <header data-tauri-drag-region><span data-tauri-drag-region>OSCAR / Activity</span><button onClick={back}>Back to presence</button></header>
    <h1 ref={title} tabIndex={-1}>Work and decisions.</h1>
    {!available&&<p role="status">Current Core state is unavailable. Displayed history grants no authority; controls are disabled.</p>}
    {view.feedback&&<p className="leaf-error" role="alert">{view.feedback.message}</p>}
    <div className="activity-controls"><button disabled={busy} onClick={()=>run({kind:'refresh'})}>Refresh Core</button><button disabled={busy} onClick={()=>run({kind:'discard'})}>Clear private drafts and context</button></div>
    <section aria-label="Active work"><h2>Active and waiting <small>{active.length}</small></h2>{active.length?list(active):<p className="leaf-secondary">No active tasks are visible.</p>}</section>
    {review?<section ref={reviewFocus} tabIndex={-1} className="decision-sheet" aria-label="Owner decision"><h2>Review {review.operation==='approve'?'approval':review.operation==='deny'?'denial':'cancellation'}</h2>
      <p>{review.description}</p>
      <dl>{[['Task',review.task_id??'Unknown'],['Target / capability',`${review.target} / ${review.capability}`],['Reason',review.reason],['Consequence',review.consequence],['Policy',review.policy_reason],['Evidence state',review.evidence_state]].map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
      <details open><summary>Exact reviewed material</summary><pre>{review.review}</pre></details>
      <p className="leaf-secondary">Opening this review grants nothing. Native confirmation and signing follow; Core rechecks task, scope and current plan. No permanent permission is granted.</p>
      {!decisionCurrent&&<p role="status" className="leaf-error">This review expired or its task changed. Inspect the task for a fresh decision.</p>}
      <div className="leaf-actions"><button className="leaf-primary" disabled={!available||busy||!decisionCurrent} onClick={()=>run({kind:'confirm',review_id:review.review_id,accept:true})}>Continue to native confirmation</button><button disabled={busy} onClick={()=>run({kind:'confirm',review_id:review.review_id,accept:false})}>Dismiss review</button></div>
    </section>:view.current&&<section aria-label="Selected task" className="selected-task"><h2>{statuses[view.current.state]??'Unknown outcome'}</h2><p>{view.current.description}</p><p className="leaf-secondary">{view.current.mode||'Shared task'} · Worker {view.current.target} · attempt {view.current.generation}</p>
      {view.current.blocker&&<p role="status">{view.current.blocker}</p>}
      {view.current.progress&&<p>{view.current.progress.status} progress · {Math.round(view.current.progress.fraction*100)}% · {view.current.progress.step}</p>}
      {(view.current.response||view.current.value)&&<div className="activity-result"><p className="leaf-secondary">{view.current.epistemic??view.current.response_status??'REPORTED'}</p>{!!view.current.source_event_ids?.length&&<p className="leaf-secondary">Earlier retained evidence; current facts may differ. Inferred material remains inference.</p>}<pre tabIndex={0} aria-label="Task result">{view.current.value??view.current.response}</pre>{view.current.response_truncated&&<p className="leaf-secondary">Core returned a bounded excerpt.</p>}</div>}
      <div className="leaf-actions">{(['approve','deny','cancel'] as const).filter(operation=>view.current!.actions.includes(operation)).map(operation=><button key={operation} disabled={!available||busy} onClick={()=>run({kind:'review',task_id:view.current!.task_id,operation})}>Review {operation==='approve'?'approval':operation==='deny'?'denial':'cancellation'}</button>)}</div>
      <details><summary>Evidence and artifacts</summary><ul>{view.current.evidence_ids.map(id=><li key={id}>{id}</li>)}</ul>{!!view.current.source_event_ids?.length&&<><h3>Canonical recall sources</h3><ul>{view.current.source_event_ids.map(id=><li key={id}>{id}</li>)}</ul></>}{view.current.evidence?.map(e=><p key={e.id}>{e.status} · {e.source} · {e.method} · {e.matches===true?'matches':e.matches===false?'does not match':'unknown match'} · {new Date(e.observed_at*1000).toLocaleString()}</p>)}{view.current.artifacts?.map(a=><p key={a.id}>{a.kind} artifact {a.id} · {a.status}{a.content_hash?` · SHA256 ${a.content_hash}`:''}</p>)}<p className="leaf-secondary">References and verification metadata do not grant file access. Private task inputs are not replayable; continuation requires a fresh scoped request.</p></details>
    </section>}
    <details className="completed-work"><summary>Completed, partial and failed <strong>{completed.length}</strong></summary>{list(completed)}</details>
    <p className="leaf-secondary">{view.reference?'Disposable reference Core. ':' '}Cancellation and denial also require exact native review. Attention is not consent.</p>
  </div>;
}
