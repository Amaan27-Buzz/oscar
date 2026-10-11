import type {Command,Task} from '../bridge';
import {statuses} from '../bridge';

export function TaskStage({task,busy,run}:{task:Task;busy:boolean;run:(command:Command)=>unknown}) {
  const progress=task.progress;
  const measured=progress&&Number.isFinite(progress.fraction)&&progress.fraction>=0&&progress.fraction<=1;
  return <div className="attention-copy task-stage">
    <p>{task.blocker??task.description}</p>
    <p className="leaf-secondary" role="status">{statuses[task.state]??'Unknown outcome'} · {task.evidence_ids.length} evidence references</p>
    {measured&&<p className="leaf-secondary">{progress.status} progress · {Math.round(progress.fraction*100)}% · {progress.step}</p>}
    <div className="leaf-actions"><button className="leaf-primary" onClick={()=>run({kind:'window',mode:'activity'})}>Inspect work</button>
      {task.actions.includes('cancel')&&<button disabled={busy} onClick={()=>run({kind:'review',task_id:task.task_id,operation:'cancel'})}>Review cancellation</button>}</div>
  </div>;
}
