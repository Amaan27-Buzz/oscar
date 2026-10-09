// Development-only presentation study. No native calls, Core or media access.
import {useEffect,useRef,useState} from 'react';
import {flushSync} from 'react-dom';
import orb from '../../../assets/brand/oscar-orb.svg';
import {App} from '../App';
import {statuses} from '../bridge';
import type {Send,View} from '../bridge';
import {fixtures} from '../showcase';
import './presence.css';

export type Concept='a'|'b'|'c';
export type Scene='idle'|'active'|'waiting'|'offline';
export const names:Record<Concept,string>={a:'Ambient Presence',b:'Living Instrument',c:'Adaptive Presence'};
export const scenes:Scene[]=['idle','active','waiting','offline'];
const idle=fixtures.find(f=>f.id==='01-compact-idle')!.view;
const active=fixtures.find(f=>f.id==='02-compact-active')!.view;
export const views:Record<Scene,View>={idle,active,
  waiting:{...active,orb:'waiting',current:{...active.current!,state:'awaiting_result'},tasks:[{...active.current!,state:'awaiting_result'}]},
  // Preserve stale tasks to prove that losing availability suppresses live claims.
  offline:{...active,link:'unavailable',orb:'unavailable'}};
export function presentation(view:View) {
  const online=view.link==='online';
  const working=online&&view.tasks.some(t=>['executing','verifying'].includes(t.state));
  const attention=online?view.tasks.filter(t=>t.actions.includes('approve')).length:0;
  const waiting=online&&!working&&view.tasks.some(t=>t.state==='awaiting_result');
  const state=!online?'offline':working?'active':waiting?'waiting':'idle';
  const label=!online?'Core unavailable':view.current?statuses[view.current.state]??'Unknown outcome':'Available';
  return {state,label,working,attention,online};
}
export function dimensions(concept:Concept,state:string,attention=0):[number,number] {
  if(concept==='a')return [224,188];
  if(concept==='b')return [344,156];
  return state==='idle'&&!attention?[192,112]:state==='offline'?[304,156]:[364,164];
}
const noEvents=async()=>()=>{};
function transition(change:()=>void) {
  if(document.startViewTransition&&!matchMedia('(prefers-reduced-motion: reduce)').matches) {
    void document.startViewTransition(()=>flushSync(change)).finished.catch(()=>{});
  } else change();
}
export function Presence({concept,view,onOpen}:{concept:Concept;view:View;onOpen:()=>void}) {
  const {state,label,working,attention,online}=presentation(view);
  const signal=online?view.orb:'unavailable';
  return <section className={`presence-object concept-${concept}`} data-state={state} data-signal={signal}
    data-working={working} data-attention={attention>0} aria-label={`${names[concept]} compact OSCAR`}>
    <div className="presence-main">
      <button className="orb-control" onClick={onOpen} aria-label="Open OSCAR interaction" title="Open OSCAR">
        <span className="orb-seat"><img className="presence-orb" src={orb} alt="OSCAR Orb" draggable={false}/></span>
      </button>
      <div className="presence-copy"><h1>OSCAR</h1><p className="presence-status" role="status" aria-live="polite">{label}</p>
        {concept==='c'&&state!=='idle'&&<p className="presence-detail">{online?'Shared Core task':'Execution status unknown'}</p>}
      </div>
      {concept!=='a'&&<button className="open-control" onClick={onOpen} aria-label="Expand OSCAR" title="Expand OSCAR">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 12h14m-5-5 5 5-5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
      </button>}
    </div>
    <div className="presence-foot">
      <span className="state-mark" aria-hidden="true"/>
      <span className="foot-label">{!online?'Inspect before retry':state==='active'?'Core task underway':state==='waiting'?'Awaiting result':'Ready when you are'}</span>
      <button className="attention-control" onClick={onOpen} aria-label={`${attention} task${attention===1?'':'s'} require owner attention`}
        hidden={!attention}>{attention} to review</button>
    </div>
  </section>;
}

export function Exploration() {
  const query=new URLSearchParams(location.search);
  const first=query.get('presence');const initial=first==='b'||first==='c'?first:'a';
  const requested=query.get('state');
  const [concept,setConcept]=useState<Concept>(initial);
  const [scene,setScene]=useState<Scene>(scenes.includes(requested as Scene)?requested as Scene:'idle');
  const [expanded,setExpanded]=useState(false);
  const opener=useRef<HTMLDivElement>(null);
  const wasExpanded=useRef(false);
  useEffect(()=>{
    if(expanded||wasExpanded.current){const frame=requestAnimationFrame(()=>opener.current?.querySelector<HTMLButtonElement>(expanded?'.presence-expanded button':'.orb-control')?.focus());wasExpanded.current=expanded;return()=>cancelAnimationFrame(frame);}
  },[expanded]);
  const view=views[scene];const state=presentation(view);
  const [width,height]=expanded?[580,760]:dimensions(concept,state.state,state.attention);
  const close=()=>transition(()=>setExpanded(false));
  const port:Send=async command=>{
    if(command.kind==='ready'||command.kind==='refresh')return {...view,window:'interaction'};
    if(command.kind==='window') {
      if(command.mode==='compact')close();
      return {...view,window:command.mode};
    }
    throw new Error('10R.1 synthetic exploration cannot execute');
  };
  return <div className="presence-lab" data-tools={query.has('tools')}>
    {query.has('tools')&&<aside className="lab-tools" aria-label="Development fixtures">
      <p>10R.1 · Synthetic fixtures · No execution</p>
      <label>Concept<select value={concept} onChange={e=>{const next=e.target.value as Concept;transition(()=>{setConcept(next);setExpanded(false);});}}>{Object.entries(names).map(([key,name])=><option key={key} value={key}>{name}</option>)}</select></label>
      <div role="group" aria-label="Synthetic state">{scenes.map(s=><button key={s} aria-pressed={s===scene} onClick={()=>transition(()=>setScene(s))}>{s}</button>)}</div>
      <p>State controls simulate transitions only. Escape returns to compact.</p>
    </aside>}
    <div ref={opener} className="presence-window" data-concept={concept} data-expanded={expanded} style={{width,height}}
      onKeyDown={e=>{if(e.key==='Escape'&&expanded)close();}}>
      <div className="presence-origin" hidden={expanded}><Presence concept={concept} view={view} onOpen={()=>transition(()=>setExpanded(true))}/></div>
      {expanded&&<div className="presence-expanded"><p className="fixture-disclosure">Synthetic expansion · existing interaction UI · no execution</p><App key={scene} port={port} events={noEvents}/></div>}
    </div>
  </div>;
}
