import {useState} from 'react';
import {DesktopExpression} from './DesktopExpression';
import {companionEvents,surface,useDesktop} from './surfaces';
import {stateLabel} from './bridge';
import type {Send} from './bridge';
import './companion.css';
const companionPort:Send=()=>surface({kind:'ready'});
export function Companion() {
  const {view,available,error,accept,setError}=useDesktop(companionPort,companionEvents);
  const [controls,setControls]=useState(false);
  const at=Date.now();
  const fresh=(stamp:number|undefined)=>typeof stamp==='number'&&stamp<=at+250&&at-stamp<8000;
  const attention=available&&[...(fresh(view.expression?.tasks_observed_at_ms)?view.tasks:[]),...(fresh(view.expression?.current_observed_at_ms)&&view.current?[view.current]:[])].some(t=>t.actions.includes('approve'));
  async function control(request:Parameters<typeof surface>[0]) {try{accept(await surface(request));setError('');}catch(e){setError(typeof e==='string'?e:'Control unavailable. Open Workspace to inspect.');setControls(true);void surface({kind:'companion_controls',open:true}).catch(()=>{});}}
  return <main className="companion" aria-label="OSCAR Companion">
    <div className="companion-grip" data-tauri-drag-region aria-label="Move Companion">···</div>
    <button className="companion-orb" aria-label={attention?'Open Workspace — owner attention required':'Open OSCAR Workspace'} onClick={()=>control({kind:attention?'open_activity':'open_workspace'})}><DesktopExpression view={view} size={92}/></button>
    <p className="companion-status" role="status">{!available?'Core unavailable':attention?'Review needed':stateLabel(view)}</p>
    <div className="companion-actions"><button onClick={()=>control({kind:'open_workspace'})} aria-label="Open Workspace">Open ↗</button><button aria-expanded={controls} aria-label="Companion controls" onClick={()=>{setControls(!controls);void control({kind:'companion_controls',open:!controls});}}>···</button></div>
    {controls&&<div className="companion-controls" aria-label="Immediate controls">
      <button aria-pressed={!!view.shortcut_enabled} onClick={()=>control({kind:'shortcut_enabled',enabled:!view.shortcut_enabled})}>Shortcut {view.shortcut_enabled?'on':'off'}</button>
      {available&&['listening','processing','speaking'].includes(view.voice)&&<button onClick={()=>control({kind:'cancel_listening'})}>Cancel voice turn</button>}
      <span>Mute · {view.voice_support?.persistent_mute??'unavailable'}</span><span>Trigger-only · explicit activation</span><span>Sentry · {view.voice_support?.sentry??'unavailable'}</span>
      <button onClick={()=>control({kind:'hide_companion'})}>Hide Companion</button>
    </div>}
    {error&&<p className="companion-error" role="alert">{error}</p>}
  </main>;
}
