import {useEffect,useState} from 'react';

export interface AdaptiveDescriptor {version:1;view_id:string;task_id:string;revision:number;observed_at_ms:number;expires_at_ms:number;fallback:string;components:{type:'prose'|'task_progress'|'result_evidence';text:string;source_ids:string[]}[];actions:{type:'inspect_task';task_id:string}[]}
export function adaptiveDescriptor(input:unknown):AdaptiveDescriptor|null {
  if(!input||typeof input!=='object'||Array.isArray(input))return null;
  const d=input as AdaptiveDescriptor;
  try {if(JSON.stringify(d).length>8192)return null;} catch {return null;}
  if(Object.keys(d).sort().join(',')!=='actions,components,expires_at_ms,fallback,observed_at_ms,revision,task_id,version,view_id'||d.version!==1)return null;
  if(![d.view_id,d.task_id,d.fallback].every(s=>typeof s==='string'&&s.length>0&&s.length<=512)||d.task_id.length>80||d.view_id.length>80)return null;
  if(![d.revision,d.observed_at_ms,d.expires_at_ms].every(n=>Number.isSafeInteger(n)&&n>=0)||d.expires_at_ms<=d.observed_at_ms||d.expires_at_ms-d.observed_at_ms>30000)return null;
  if(!Array.isArray(d.components)||d.components.length<1||d.components.length>8||d.components.some(c=>!c||Object.keys(c).sort().join(',')!=='source_ids,text,type'||!['prose','task_progress','result_evidence'].includes(c.type)||typeof c.text!=='string'||c.text.length<1||c.text.length>1024||!Array.isArray(c.source_ids)||c.source_ids.length>20||c.source_ids.some(s=>typeof s!=='string'||s.length<1||s.length>80)))return null;
  if(!Array.isArray(d.actions)||d.actions.length!==1||!d.actions[0]||typeof d.actions[0]!=='object'||Array.isArray(d.actions[0])||Object.keys(d.actions[0]).sort().join(',')!=='task_id,type'||d.actions[0].type!=='inspect_task'||d.actions[0].task_id!==d.task_id)return null;
  return d;
}
export function AdaptiveView({descriptor,inspect}:{descriptor:unknown;inspect:(id:string)=>void}) {
  const [now,setNow]=useState(Date.now());
  useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),1000);return()=>clearInterval(timer);},[]);
  const d=adaptiveDescriptor(descriptor);
  if(!d)return <p role="status">Interactive details unavailable. Open Activity for current state.</p>;
  const fresh=d.observed_at_ms<=now+250&&d.expires_at_ms>now;
  return <details className="adaptive-view"><summary>Task details</summary>{fresh?d.components.map((c,i)=><p key={i}>{c.text}{c.source_ids.length>0&&<small> · {c.source_ids.length} evidence references</small>}</p>):<p>Details expired. Refresh to see current state.</p>}<button disabled={!fresh} onClick={()=>inspect(d.task_id)}>Inspect task</button></details>;
}
