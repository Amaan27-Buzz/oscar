import type {Command,View} from '../bridge';
import {Act} from '../Act';
import type {ActionDraft} from '../Act';
import {TaskStage} from './TaskStage';

export function ActionSurface({view,draft,setDraft,available,busy,run,discard}:{view:View;draft:ActionDraft;setDraft:(draft:ActionDraft)=>void;available:boolean;busy:boolean;run:(command:Command)=>Promise<boolean>;discard:()=>void}) {
  const context=view.context;
  const active=(task:View['tasks'][number])=>['executing','awaiting_result','result_received','verifying'].includes(task.state);
  const workingTask=(view.current&&active(view.current)?view.current:null)??view.tasks.find(active);
  const task=workingTask??(view.current?.mode==='Act'?view.current:null);
  const working=!!workingTask;
  const fresh=!!context&&context.permission==='granted'&&typeof context.expires_at==='number'&&context.expires_at*1000>Date.now();
  return <div className="action-surface">
    <details className="context-details"><summary>{context?'Attached application context':'Application context is not attached'}</summary>
      {context?<><p>{context.source} · {context.scope} · {context.permission} · {fresh?'fresh observation':'recapture required'}</p><p>{context.provenance}</p><pre>{context.text}</pre></>:<p>Choose supported window, selection or focused-field capture in Text tools. No background observation runs.</p>}
      <p>Screenshot context is not advertised by this adapter. Accessibility text requires a registered, permitted target.</p>
    </details>
    {task&&<TaskStage task={task} busy={busy} run={run}/>}
    <Act capabilities={view.capabilities} run={command=>void run(command)} disabled={!available||busy||working||!!view.feedback} draft={draft} onDraftChange={setDraft}/>
    {view.feedback&&<p className="leaf-error" role="alert">{view.feedback.message} Inspect the outcome before another proposal.</p>}
    <p className="leaf-secondary">Preparing a task changes no application. Core policy, the exact plan and native owner review govern execution. Critical-risk actions are unavailable here.</p>
    <button disabled={busy} onClick={()=>run({kind:'refresh'})}>Refresh capabilities</button><button onClick={discard}>Clear private drafts and context</button>
  </div>;
}
