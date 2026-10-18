import {getCurrentWindow} from '@tauri-apps/api/window';
import {useEffect,useRef,useState} from 'react';
import {DesktopExpression} from './DesktopExpression';
import {companionEvents,surface,useDesktop} from './surfaces';
import type {Send} from './bridge';
import {taskStatus} from './bridge';
import './companion.css';
const companionPort:Send=()=>surface({kind:'ready'});
const icons={open:'M4 5h16v11H9l-5 4V5Z',access:'M12 3 4 6v6c0 4 8 9 8 9s8-5 8-9V6l-8-3Zm-4 9 3 3 5-6',sentry:'M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7Zm10-3a3 3 0 1 0 0 6 3 3 0 0 0 0-6',voice:'M10 4a3 3 0 0 1 4 0v8a3 3 0 0 1-4 0V4ZM6 11a6 6 0 0 0 12 0m-6 6v4m-3 0h6',menu:'M5 12h.01M12 12h.01M19 12h.01'};
function Icon({name}:{name:keyof typeof icons}) {return <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={icons[name]}/></svg>;}
export function Companion() {
  const {view,available,error,accept,setError}=useDesktop(companionPort,companionEvents);
  const [hover,setHover]=useState(false),[gaze,setGaze]=useState({x:0,y:0});
  const dragStart=useRef<{x:number;y:number}|null>(null),dragged=useRef(false);
  const gazeFrame=useRef<number|undefined>(undefined),target=useRef(gaze);
  useEffect(()=>()=>{if(gazeFrame.current!==undefined)cancelAnimationFrame(gazeFrame.current);},[]);
  const at=Date.now();
  const fresh=(stamp:number|undefined)=>typeof stamp==='number'&&stamp<=at+250&&at-stamp<8000;
  const attention=available&&[...(fresh(view.expression?.tasks_observed_at_ms)?view.tasks:[]),...(fresh(view.expression?.current_observed_at_ms)&&view.current?[view.current]:[])].some(t=>t.actions.includes('approve'));
  const activeVoice=available&&['listening','processing','speaking'].includes(view.voice);
  const working=(fresh(view.expression?.tasks_observed_at_ms)?view.tasks:[]).find(t=>['executing','awaiting_result','result_received','verifying'].includes(t.state));
  const visibleTask=working??(fresh(view.expression?.current_observed_at_ms)?view.current:null);
  const state=error?'Control needs attention':!available?'Disconnected':attention?'Review needed':visibleTask?taskStatus(visibleTask):'Ready';
  async function control(request:Parameters<typeof surface>[0]) {try{accept(await surface(request));setError('');}catch(e){setError(typeof e==='string'?e:'Control unavailable. Open OSCAR to inspect.');}}
  function pointer(x:number,y:number){target.current={x:Math.max(-4,Math.min(4,x)),y:Math.max(-3,Math.min(3,y))};if(gazeFrame.current===undefined)gazeFrame.current=requestAnimationFrame(()=>{gazeFrame.current=undefined;setGaze(target.current);});}
  return <main className={`companion ${hover?'is-hovered':''}`} aria-label="OSCAR Companion" onPointerEnter={()=>setHover(true)} onPointerLeave={()=>{setHover(false);pointer(0,0);}} onContextMenu={e=>{e.preventDefault();void control({kind:'companion_menu'});}} onKeyDown={e=>{if(e.key==='ContextMenu'||(e.shiftKey&&e.key==='F10')){e.preventDefault();void control({kind:'companion_menu'});}}}>
    <div className="companion-orb-area"><div className="companion-drag-zone" data-tauri-drag-region aria-label="Move Companion"/><button className="companion-orb" aria-label={attention?'Open Workspace — owner attention required':'Open OSCAR Workspace'} title={state} onPointerDown={e=>{if(e.button===0){dragStart.current={x:e.clientX,y:e.clientY};dragged.current=false;}}} onPointerUp={()=>{dragStart.current=null;}} onPointerMove={e=>{if(dragStart.current&&(e.buttons&1)&&Math.hypot(e.clientX-dragStart.current.x,e.clientY-dragStart.current.y)>=5){dragged.current=true;dragStart.current=null;void getCurrentWindow().startDragging().catch(()=>setError('Move unavailable.'));return;}const box=e.currentTarget.getBoundingClientRect();pointer((e.clientX-box.left-box.width/2)/12,(e.clientY-box.top-box.height/2)/16);}} onClick={e=>{if(e.detail>0&&dragged.current){e.preventDefault();return;}void control({kind:attention?'open_activity':'open_workspace'});}}><DesktopExpression view={view} size={92} gaze={gaze}/></button><span className={`companion-state-dot ${attention?'attention':error?'error':!available?'offline':'online'}`} title={state}/></div>
    <span className="companion-status" role="status">{state}</span>
    <div className="companion-toolbar" aria-label="Immediate controls"><span className="companion-rest-handle" data-tauri-drag-region/><div className="companion-icon-row">
      <button aria-label="Open Workspace" title="Open OSCAR" onClick={()=>control({kind:'open_workspace'})}><Icon name="open"/></button>
      <button aria-label={`Access mode: ${available?view.access_mode??'Unknown':'Unknown'}`} title={`Access mode · ${available?view.access_mode==='Ask'?'Ask · inspect and propose; approve changes':view.access_mode??'Check connection':'Check connection'}`} onClick={()=>control({kind:'access_menu'})}><Icon name="access"/></button>
      <button aria-label="Sentry" title="Sentry · not available yet; no background listening" onClick={()=>control({kind:'sentry_menu'})}><Icon name="sentry"/></button>
      <span title={activeVoice?'Cancel voice turn':available&&view.voice_available?'Use voice':'Voice is not available on this device'}><button aria-label={activeVoice?'Cancel voice turn':'Use voice'} disabled={!activeVoice&&(!available||!view.voice_available)} onClick={()=>control({kind:activeVoice?'cancel_listening':'start_listening'})}><Icon name="voice"/></button></span>
      <button aria-label="Companion controls" title="More controls · right-click" onClick={()=>control({kind:'companion_menu'})}><Icon name="menu"/></button>
    </div></div>
  </main>;
}
