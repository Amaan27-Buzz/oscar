import {useEffect,useState} from 'react';
import type {Command,View} from './bridge';
import {epistemicLabel} from './bridge';
import {assistanceSummary} from './Automations';
import {Disclosure} from './UIControls';

interface MemoryRow {id:string;content:string;digest:string;kind:string;status:string;source_event_ids:string[];excerpt:boolean;can_manage:boolean;can_correct:boolean}
interface MemoryView {available:boolean;records:MemoryRow[];truncated:boolean;generation?:number}
export function memoryView(raw:unknown):MemoryView|null {
  if(!raw||typeof raw!=='object')return null;
  const value=raw as MemoryView;
  if(typeof value.available!=='boolean'||typeof value.truncated!=='boolean'||!Array.isArray(value.records)||value.records.length>20)return null;
  if(value.available&&(!Number.isSafeInteger(value.generation)||value.generation!<0))return null;
  if(value.records.some(row=>!row||typeof row.id!=='string'||row.id.length<1||row.id.length>128||typeof row.content!=='string'||row.content.length<1||row.content.length>2000||typeof row.digest!=='string'||!/^[a-f0-9]{64}$/.test(row.digest)||typeof row.kind!=='string'||typeof row.status!=='string'||!Array.isArray(row.source_event_ids)||row.source_event_ids.length>32||row.source_event_ids.some(id=>typeof id!=='string'||id.length>128)||[row.excerpt,row.can_manage,row.can_correct].some(flag=>typeof flag!=='boolean')))return null;
  if(!value.available&&value.records.length)return null;
  return value;
}
export function MemorySettings({view,busy,run}:{view:View;busy:boolean;run:(command:Command)=>unknown}) {
  const memory=view.link==='online'?memoryView(assistanceSummary(view.executive?.management)?.memory):null;
  const [corrections,setCorrections]=useState<Record<string,string>>({}),[retain,setRetain]=useState<Record<string,boolean>>({}),[sources,setSources]=useState<Record<string,boolean>>({});
  useEffect(()=>{setCorrections({});setRetain({});setSources({});},[view.link,view.connection?.installation_id,memory?.generation]);
  return <section aria-label="Saved Core memory" className="settings-group"><h2>Saved memory</h2><p>These statements come from your Core. Corrections preserve the earlier statement as history. Forgetting removes the selected memory from recall.</p>{memory?.available?<>{memory.records.map(row=><Disclosure key={`${row.id}/${row.digest}`} title={<>{row.content.slice(0,80)}{row.content.length>80?'…':''}</>}><p>{row.content}{row.excerpt?'…':''}</p><p className="leaf-secondary">{epistemicLabel(row.status)} · {row.source_event_ids.length} retained source {row.source_event_ids.length===1?'statement':'statements'}</p>{row.can_manage?<><label><input type="checkbox" checked={sources[row.id]??false} onChange={e=>setSources({...sources,[row.id]:e.target.checked})}/>Also forget the retained source statements and dependent memories</label><p>Keeping sources leaves the original conversation available. Deletion does not securely erase backups or physical storage.</p><button disabled={busy} onClick={()=>run({kind:'manage_assistance',operation:'memory_forget',id:row.id,value:{digest:row.digest,forget_sources:sources[row.id]??false}})}>Review forgetting this memory</button>{row.can_correct&&<form className="responsibility-form" onSubmit={e=>{e.preventDefault();void run({kind:'manage_assistance',operation:'memory_correct',id:row.id,value:{digest:row.digest,content:corrections[row.id]??'',retain:true}});}}><label>Corrected statement<textarea required maxLength={2000} value={corrections[row.id]??''} onChange={e=>setCorrections({...corrections,[row.id]:e.target.value})}/></label><label><input type="checkbox" checked={retain[row.id]??false} onChange={e=>setRetain({...retain,[row.id]:e.target.checked})}/>Retain this exact correction</label><button disabled={busy||!retain[row.id]||!(corrections[row.id]??'').trim()}>Review memory correction</button></form>}{!row.can_correct&&<p>Corrections need a separate retention grant.</p>}</>:<p>Memory changes need a separate owner management grant.</p>}</Disclosure>)}{memory.records.length===0&&<p>No current saved memories were found in this bounded view.</p>}{memory.truncated&&<p>This view shows the most recent memories within its display limit.</p>}</>:<p>Saved memory needs a connected Core with a separate memory read grant.</p>}<button disabled={busy} onClick={()=>run({kind:'refresh'})}>Refresh saved memory</button></section>;
}
