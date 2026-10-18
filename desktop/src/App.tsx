import {useEffect,useRef,useState} from 'react';
import {DesktopExpression} from './DesktopExpression';
import type {Source} from '@oscar/expression';
import {Act} from './Act';
import {initialView,send,subscribe,stateLabel,taskStatus} from './bridge';
import type {Command,Mode,Send,View,ContextChoice} from './bridge';
export function App({port=send,events=subscribe,expressionKind='core',focusReview=false}:{port?:Send;events?:typeof subscribe;expressionKind?:Source['kind'];focusReview?:boolean}) {
  const [view,setView]=useState<View>(initialView);const [mode,setMode]=useState<Mode>('Ask');
  const [text,setText]=useState('');const [busy,setBusy]=useState(false);const [error,setError]=useState('');
  const [choice,setChoice]=useState<ContextChoice>('none');const [destination,setDestination]=useState<'surface'|'clipboard'|'focused'>('surface');
  const [shortcut,setShortcut]=useState('Ctrl+Alt+O');
  const approval=useRef<HTMLElement|null>(null);
  useEffect(()=>{if(focusReview&&view.review){approval.current?.focus({preventScroll:true});approval.current?.scrollIntoView({block:'start'});}},[focusReview,view.review?.review_id]);
  useEffect(()=>{let active=true;let stop:(()=>void)|undefined;
    events(v=>{if(active)setView(v);}).then(fn=>{if(active)stop=fn;else fn();}).catch(()=>{if(active)setError('Native event bridge unavailable.');});
    port({kind:'ready'}).then(v=>{if(active)setView(v);}).catch(()=>{if(active)setError('Open OSCAR through the native desktop executable.');});
    return()=>{active=false;stop?.();};},[]);
  async function run(command:Command){setBusy(true);setError('');try{setView(await port(command));}catch{setError('Native request unavailable. Inspect current Core state before retry.');}finally{setBusy(false);}}
  const online=view.link==='online';const task=view.current;
  const active=view.tasks.filter(t=>!['verified','failed','cancelled'].includes(t.state)).length;
  const attention=view.tasks.filter(t=>t.actions.includes('approve')).length;
  const expanded=view.window!=='compact';
  function ptt(start:boolean){void run(start?{kind:'voice_start',context_id:view.context?.id??''}:{kind:'voice_stop'});}
  return <main className={`oscar ${expanded?'expanded':'compact'}`} data-orb={view.orb}>
    <header data-tauri-drag-region><DesktopExpression view={view} size={expanded?64:58} sourceKind={expressionKind}/>
      <div data-tauri-drag-region><h1>OSCAR</h1><p role="status" aria-live="polite">{stateLabel(view)}</p>
        {active>0&&<small>{active} active · {attention} need owner attention</small>}</div>
      <button aria-label={expanded?'Compact presence':'Expand OSCAR'} onClick={()=>run({kind:'window',mode:expanded?'compact':'interaction'})}>{expanded?'Compact':'Open'}</button>
    </header>
    {expanded&&<>
      {view.reference&&<p className="reference">REFERENCE Core · temporary state · OWNER_ACCEPTANCE_NOT_RUN</p>}
      <nav aria-label="OSCAR surfaces"><button aria-current={view.window!=='activity'?'page':undefined} onClick={()=>run({kind:'window',mode:'interaction'})}>Interact</button>
        <button aria-current={view.window==='activity'?'page':undefined} onClick={()=>run({kind:'window',mode:'activity'})}>Activity</button>
        <button disabled={busy} onClick={()=>run({kind:'refresh'})}>Refresh Core</button></nav>
      {(error||view.message)&&<p className="notice" role="status">{error||view.message}</p>}
      {!online&&<p className="notice" role="status">Core unavailable. Actions are disabled; nothing is queued.</p>}
      {view.window==='activity'?<section aria-label="Shared Core activity"><h2>Activity</h2>
        {!view.tasks.length&&<p>No shared tasks are currently visible.</p>}
        <ul className="tasks">{view.tasks.map(t=><li key={t.task_id}><button disabled={!online} onClick={()=>run({kind:'inspect',task_id:t.task_id})}>
          <strong>{taskStatus(t)}</strong><span>{t.description}</span><small>{t.target}</small></button></li>)}</ul>
      </section>:<>
        <div className="modes" role="tablist" aria-label="Interaction mode">{(['Ask','Dictate','Edit','Act'] as Mode[]).map(m=><button
          key={m} role="tab" tabIndex={mode===m?0:-1} aria-selected={mode===m} onClick={()=>setMode(m)} onKeyDown={e=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();const modes:Mode[]=['Ask','Dictate','Edit','Act'];const i=e.key==='Home'?0:e.key==='End'?3:(modes.indexOf(m)+(e.key==='ArrowRight'?1:3))%4;setMode(modes[i]);(e.currentTarget.parentElement?.children[i] as HTMLElement)?.focus();}}}>{m}</button>)}</div>
        <section aria-label="Included context" className="context"><div className="context-title"><h2>Context</h2><button disabled={busy} onClick={()=>{setText('');setView(v=>({...v,context:null,preview:null,review:null,message:null,current:v.current?{...v.current,response:null,value:null}:null,tasks:v.tasks.map(t=>({...t,response:null,value:null}))}));run({kind:'discard'});}}>Discard now</button></div>
          <label>Capture on next invocation<select value={choice} disabled={!online} onChange={e=>{const source=e.target.value as ContextChoice;setChoice(source);run({kind:'capture_choice',source});}}>
            <option value="none">No context</option><option value="selection">Selection</option><option value="focused">Focused field</option><option value="foreground">Foreground window</option>
          </select></label><p className="secondary">Choose a source, focus the intended application, then invoke OSCAR with the shortcut or tray.</p>
          {view.context?<><p>{view.context.source} · {view.context.freshness} · {view.context.permission}</p><pre>{view.context.text??'Unavailable'}</pre>
            <details><summary>Provenance and permission</summary><p>{view.context.provenance}</p><p>{view.context.scope}</p><time>{new Date(view.context.timestamp*1000).toLocaleString()}</time><p>Not retained</p></details></>:<p>No context attached.</p>}
        </section>
        {mode==='Act'?<Act capabilities={view.capabilities} run={run} disabled={busy||!online}/>:<section aria-label={mode}>
          <label>{mode==='Ask'?'Ask OSCAR':mode==='Edit'?'Transformation instruction':'Dictated text'}<textarea maxLength={4096} value={text} onChange={e=>setText(e.target.value)}/></label>
          <div className="actions"><button disabled={!online||busy||!text.trim()||(mode==='Edit'&&!view.context)} onClick={()=>run({kind:'interact',mode,text,context_id:view.context?.id??''})}>
            {mode==='Dictate'?'Preview text':mode==='Edit'?'Request transformation':'Ask'}</button>
            {mode==='Dictate'&&<button disabled={!online} onPointerDown={e=>{e.currentTarget.setPointerCapture(e.pointerId);ptt(true);}}
              onPointerUp={()=>ptt(false)} onPointerCancel={()=>ptt(false)} onKeyDown={e=>{if(e.code==='Space'&&!e.repeat){e.preventDefault();ptt(true);}}}
              onKeyUp={e=>{if(e.code==='Space'){e.preventDefault();ptt(false);}}}>Hold to dictate</button>}
          </div><p className="secondary">{mode==='Edit'?'Core transforms; you review before any destination changes.':mode==='Dictate'?'Only a final transcript can become a preview. Microphone availability is reported by Core.':'One OSCAR relationship. Replies keep their evidence status.'}</p>
        </section>}
      </>}
      {task&&<section aria-label="Current Core task" className="result"><h2>{taskStatus(task)}</h2>
        {task.blocker&&<p>{task.blocker}</p>}{(task.response||task.value)&&<><p>{task.epistemic??task.response_status??'REPORTED'}</p><pre>{task.value??task.response}</pre></>}
        <small>{task.evidence_ids.length} evidence references · {task.target}</small>
        {task.progress&&<p className="secondary">{task.progress.status} Worker progress · {Math.round(task.progress.fraction*100)}% · {task.progress.step}</p>}
        <div className="actions">{(['approve','deny','cancel'] as const).filter(a=>task.actions.includes(a)).map(operation=><button key={operation}
          disabled={!online||busy} onClick={()=>run({kind:'review',task_id:task.task_id,operation})}>{operation==='approve'?'Review approval':operation==='deny'?'Deny task':'Cancel task'}</button>)}
          {mode==='Edit'&&task.response&&<button disabled={!online||busy} onClick={()=>run({kind:'preview',task_id:task.task_id})}>Review transformation</button>}</div>
      </section>}
      {view.preview&&<section aria-label="Text preview"><h2>Review before applying</h2><div className="comparison"><div><h3>Before</h3><pre>{view.preview.before??'No captured destination'}</pre></div><div><h3>After · {view.preview.epistemic}</h3><pre>{view.preview.after}</pre></div></div>
        <label>Destination<select value={destination} onChange={e=>setDestination(e.target.value as typeof destination)}>{view.preview.destinations.map(d=><option key={d} value={d}>{d==='surface'?'OSCAR surface':d==='focused'?'Captured field':'Explicit clipboard'}</option>)}</select></label>
        <button disabled={busy||!online} onClick={()=>run({kind:'apply',preview_id:view.preview!.preview_id,destination})}>Accept this preview</button>
      </section>}
      {view.review&&<section ref={approval} tabIndex={focusReview?-1:undefined} aria-label="Owner approval" className="approval"><h2>Owner decision</h2><dl>{[['What',view.review.description],['Operation',view.review.operation],['Target',view.review.target],['Capability',view.review.capability],['Reason',view.review.reason],['Consequence',view.review.consequence],['Policy',view.review.policy_reason],['Current evidence/state',view.review.evidence_state]].map(([label,value])=><div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
        <details open><summary>Exact reviewed material</summary><pre>{view.review.review}</pre></details><p>This approval grants no permanent authority. Native confirmation follows; signing stays outside the WebView.</p>
        <div className="actions"><button disabled={busy||!online} onClick={()=>run({kind:'confirm',review_id:view.review!.review_id,accept:true})}>Continue to native confirmation</button>
          <button disabled={busy} onClick={()=>run({kind:'confirm',review_id:view.review!.review_id,accept:false})}>Dismiss review</button></div>
      </section>}
      <footer><details><summary>Invocation</summary><label>Global shortcut<input value={shortcut} maxLength={10} onChange={e=>setShortcut(e.target.value)}/></label>
        <button disabled={busy} onClick={()=>run({kind:'shortcut',accelerator:shortcut})}>Register shortcut</button><p>{view.shortcut}</p><p>Ctrl+Alt+A through Z. Collision keeps the existing shortcut.</p></details>
        <p>No background screen recording or clipboard monitoring. Perception, retention and action are separate.</p></footer>
    </>}
  </main>;
}
