import {Disclosure} from '../UIControls';
import {useEffect,useRef} from 'react';
import {epistemicLabel} from '../bridge';
import type {Task} from '../bridge';

export function ResultView({task,expanded,read,inspect,askAgain,human=false}:{human?:boolean;task:Task;expanded:boolean;read:()=>void;inspect:()=>void;askAgain:()=>void}) {
  const region=useRef<HTMLDivElement>(null);
  const text=task.value??task.response??'';
  const bounded=text.length>600||text.split('\n').length>6;
  useEffect(()=>{if(expanded)region.current?.focus();},[expanded,task.task_id]);
  return <div className={`presence-answer ${expanded?'is-reading':''}`}>
    <p className="leaf-secondary" role="status">{human?epistemicLabel(task.epistemic??task.response_status):task.epistemic??task.response_status??(task.state==='verified'?'VERIFIED':'PARTIALLY VERIFIED')}</p>
    {task.response_status==='RECALLED'&&<p className="leaf-secondary">{human?'From an earlier conversation. Things may have changed since then.':'Earlier retained evidence; current facts may differ.'}</p>}
    <div ref={region} tabIndex={expanded?0:undefined} role="region" aria-label="OSCAR response" className="response-text">
      <pre>{!expanded&&text.length>600?text.slice(0,600)+'…':text}</pre>
    </div>
    {task.response_truncated&&<p className="leaf-secondary">Only an excerpt is available.</p>}
    {expanded&&task.source_event_ids?.length?<Disclosure title={<>Recall sources</>}><ul>{task.source_event_ids.map(id=><li key={id}>{id}</li>)}</ul></Disclosure>:null}
    <div className="result-actions">{!expanded&&bounded&&<button className="leaf-primary" onClick={read}>Read response</button>}
      <button onClick={inspect}>{human?'Details':'Inspect result'}</button><button onClick={askAgain}>Ask again</button></div>
  </div>;
}
