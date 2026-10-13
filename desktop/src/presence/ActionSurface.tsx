import {useEffect,useRef} from 'react';
import type {Command,View} from '../bridge';
import {Act} from '../Act';
import type {ActionDraft} from '../Act';
import {TaskStage} from './TaskStage';

export function ActionSurface({view,draft,setDraft,available,busy,run,discard}:{view:View;draft:ActionDraft;setDraft:(draft:ActionDraft)=>void;available:boolean;busy:boolean;run:(command:Command)=>Promise<boolean>;discard:()=>void}) {
  const context=view.context;
  const surface=useRef<HTMLDivElement>(null);
  useEffect(()=>{surface.current?.focus();},[]);
  const active=(task:View['tasks'][number])=>['executing','awaiting_result','result_received','verifying'].includes(task.state);
  const workingTask=(view.current&&active(view.current)?view.current:null)??view.tasks.find(active);
  const task=workingTask??(view.current?.mode==='Act'?view.current:null);
  const working=!!workingTask;
  const fresh=!!context&&context.permission==='granted'&&typeof context.expires_at==='number'&&context.expires_at*1000>Date.now();
  return <div className="action-surface" ref={surface} tabIndex={-1} aria-label="Scoped actions">
    {task&&<TaskStage task={task} busy={busy} run={run}/>}
    <Act capabilities={view.capabilities} run={command=>void run(command)} disabled={!available||busy||working||!!view.feedback} draft={draft} onDraftChange={setDraft} context={<details className="context-details"><summary>{context?'Attached context':'Optional context'}</summary>
      {context?<><p>{context.source} · {context.scope} · {context.permission} · {fresh?'fresh observation':'recapture required'}</p><p>{context.provenance}</p><pre>{context.text}</pre></>:<p>Attach a window or selected text from Text tools when this action needs context.</p>}
      <p>Only permitted, supported text and window context can be attached.</p>
    </details>}/>
    {view.feedback&&<p className="leaf-error" role="alert">{view.feedback.message} Inspect the outcome before another proposal.</p>}

    <div className="action-footer"><button disabled={busy} onClick={()=>run({kind:'refresh'})}>Refresh actions</button><button onClick={discard}>Clear drafts and context</button></div>
  </div>;
}
