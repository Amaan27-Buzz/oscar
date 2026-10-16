export interface ExecutiveSummary {version:1;health:string;running:boolean;goals:{id:string;goal:string;state:string;verified_runs:number;max_runs:number;task_ids:string[]}[];workers:{id:string;name:string;enabled:boolean}[]}
export function executiveSummary(value:unknown):ExecutiveSummary|null {
  if(!value||typeof value!=='object')return null;
  const s=value as ExecutiveSummary;
  if(s.version!==1||typeof s.running!=='boolean'||!Array.isArray(s.goals)||s.goals.length>64||!Array.isArray(s.workers)||s.workers.length>32)return null;
  if(s.goals.some(g=>!g||typeof g.id!=='string'||g.id.length<1||g.id.length>80||typeof g.goal!=='string'||g.goal.length<1||g.goal.length>512||!['proposed','enabled','paused','cancelled','expired','completed'].includes(g.state)||!Number.isSafeInteger(g.max_runs)||g.max_runs<1||g.max_runs>100||!Number.isSafeInteger(g.verified_runs)||g.verified_runs<0||g.verified_runs>g.max_runs))return null;
  return s;
}
export function Automations({discuss,executive:raw}:{discuss:()=>void;executive?:unknown}) {
  const executive=executiveSummary(raw);
  return <section className="automations-page" aria-label="Automations"><div className="section-heading"><h1>Automations</h1><p className="leaf-secondary">The things you want OSCAR to keep an eye on.</p></div><div className="automation-introduction"><h2>Start with what you need.</h2><p>Tell OSCAR what to handle, when it matters, and how you’d like to be involved.</p><button onClick={discuss}>Talk it through</button></div><section className="automation-availability" aria-label="Automation availability">{executive?.version===1?<><p>{executive.running?'Core scheduling is connected.':'Core scheduler is not running.'} Review and activate responsibilities with your trusted Core. Changes aren’t available here yet.</p>{executive.goals.slice(0,64).map(goal=><article key={goal.id}><h3>{goal.goal}</h3><p>{goal.state} · {goal.verified_runs} of {goal.max_runs} runs verified</p></article>)}{executive.goals.length===0&&<p>No responsibilities configured.</p>}</>:<p>Automation readback isn’t available on this connection. You can follow authorized Core tasks in Activity.</p>}</section></section>;
}
