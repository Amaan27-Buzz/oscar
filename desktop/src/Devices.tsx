import {Disclosure} from './UIControls';
import {useState} from 'react';
import type {Capability,View} from './bridge';
export function Devices({view,available,busy,prepare,refresh}:{view:View;available:boolean;busy:boolean;prepare:(capability:Capability)=>void;refresh:()=>void}) {
  const nodes=[...new Set(view.capabilities.map(c=>c.node))];
  const [chosenNode,setChosenNode]=useState(''),[chosenCapability,setChosenCapability]=useState('');
  const node=nodes.includes(chosenNode)?chosenNode:nodes[0];
  const capabilities=view.capabilities.filter(c=>c.node===node);
  const selected=capabilities.find(c=>c.id===chosenCapability)??capabilities[0];
  return <section className="devices-page" aria-label="Devices"><div className="section-heading"><h1>Devices</h1><p className="leaf-secondary">Explore where OSCAR can work.</p></div>
    <div className="catalog-heading"><span>{available?'Available now':'Last available capabilities'} · {nodes.length} {nodes.length===1?'executor':'executors'}</span><button disabled={busy} onClick={refresh}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 7v5h-5M20 12a8 8 0 1 0-2 5"/></svg>Refresh devices</button></div>
    {!nodes.length&&<div className="device-empty"><svg viewBox="0 0 48 48" aria-hidden="true"><rect x="8" y="10" width="32" height="23" rx="2"/><path d="M18 40h12m-6-7v7M18 21h12"/></svg><h2>No executors available</h2><p>{available?'Connected, but no executor is currently available.':'Reconnect to discover available executors.'}</p></div>}
    {node&&<><div className="executor-choices" aria-label="Advertised executors">{nodes.map(item=><button key={item} aria-pressed={node===item} onClick={()=>{setChosenNode(item);setChosenCapability('');}}><svg viewBox="0 0 32 32" aria-hidden="true"><rect x="11" y="11" width="10" height="10" rx="2"/><path d="M16 4v7m0 10v7M4 16h7m10 0h7"/><circle cx="16" cy="4" r="2"/><circle cx="16" cy="28" r="2"/><circle cx="4" cy="16" r="2"/><circle cx="28" cy="16" r="2"/></svg><span><strong>Executor{nodes.length>1?` ${nodes.indexOf(item)+1}`:''}</strong><small>{view.capabilities.filter(c=>c.node===item).length} capabilities</small></span><span className="executor-selected" aria-hidden="true"/></button>)}</div>
      <div className="device-workbench"><div className="capability-picker" role="group" aria-label="Executor capabilities">{capabilities.map(c=><button key={c.id} aria-pressed={selected?.id===c.id} onClick={()=>setChosenCapability(c.id)}><span>{c.label}</span><svg viewBox="0 0 20 20" aria-hidden="true"><path d="m8 5 5 5-5 5"/></svg></button>)}</div>
      {selected&&<section className="capability-inspector" key={selected.id} aria-label="Capability details"><div className="capability-title"><h2>{selected.label}</h2><span>{selected.risk} risk</span></div><p className="capability-description">{selected.summary}</p><dl><div><dt>Operations</dt><dd>{selected.operations.length?selected.operations.map(operation=><span key={operation} className="operation-token">{operation}</span>):'No direct operation exposed'}</dd></div><div><dt>Required scopes</dt><dd>{selected.permissions?.length?selected.permissions.join(', '):'Checked for each request'}</dd></div></dl><Disclosure className="executor-identity" title={<>Executor details</>}><dl><div><dt>Identifier</dt><dd>{node}</dd></div></dl></Disclosure><div className="capability-next">{selected.operations.length>0&&<button className="leaf-primary" disabled={!available||busy} onClick={()=>prepare(selected)}>Prepare an action</button>}<p>You’ll review the exact action before it runs.</p></div></section>}
      </div></>}
    <p className="catalog-note">Showing available executors. Other devices may not be listed.</p>
  </section>;
}
