import {invoke} from '@tauri-apps/api/core';
import {useEffect,useRef,useState} from 'react';
import {initialView,send,subscribe} from './bridge';
import type {Command,Send,View} from './bridge';
export type SurfaceRequest={kind:'ready'|'companion_menu'|'open_workspace'|'open_activity'|'hide_workspace'|'show_companion'|'hide_companion'|'cancel_listening'|'quit'}|{kind:'shortcut_enabled';enabled:boolean}|{kind:'theme';theme:'light'|'dark'};
export const surface=(request:SurfaceRequest)=>invoke<View>('surface_command',{request});
// Companion has no event-listening permission: Tauri's Any listeners can cross target labels.
export const companionEvents=async(callback:(view:View)=>void)=>{
  let active=true,pending=false;
  const timer=setInterval(async()=>{if(pending)return;pending=true;try{const view=await surface({kind:'ready'});if(active)callback(view);}catch{/* Existing snapshot expires instead of asserting live state. */}finally{pending=false;}},2000);
  return()=>{active=false;clearInterval(timer);};
};
export function useDesktop(port:Send=send,events=subscribe) {
  const [view,setView]=useState(initialView),[busy,setBusy]=useState(false),[error,setError]=useState(''),[now,setNow]=useState(Date.now());
  const latest=useRef(initialView),retired=useRef(new Set<string>()),pending=useRef(0),privateHidden=useRef(false);
  function accept(next:View) {
    const prior=latest.current.expression,read=next.expression;
    if(read&&prior&&(retired.current.has(read.epoch)||(read.epoch===prior.epoch&&read.generation<prior.generation)))return;
    if(read&&prior&&read.epoch!==prior.epoch)retired.current.add(prior.epoch);
    if(privateHidden.current)next={...next,context:null,preview:null,review:null,message:null,current:next.current?{...next.current,response:null,value:null}:null,tasks:next.tasks.map(t=>({...t,response:null,value:null}))};
    latest.current=next;setView(next);setNow(Date.now());
  }
  useEffect(()=>{let alive=true,stop:(()=>void)|undefined;
    events(next=>{if(alive)accept(next);}).then(fn=>{if(alive)stop=fn;else fn();}).catch(()=>{if(alive)setError('Native state events unavailable.');});
    port({kind:'ready'}).then(next=>{if(alive)accept(next);}).catch(()=>{if(alive)setError('Native bridge unavailable.');});
    const timer=setInterval(()=>setNow(Date.now()),1000);
    return()=>{alive=false;stop?.();clearInterval(timer);};
  },[port,events]);
  async function run(command:Command) {
    if(command.kind==='discard'){privateHidden.current=true;accept({...latest.current});}
    if(['interact','act','capture','voice_start'].includes(command.kind))privateHidden.current=false;
    pending.current++;setBusy(true);setError('');
    try {const next=await port(command);accept(next);return !next.feedback;}
    catch(e){setError(typeof e==='string'?e:'Request outcome unknown. Inspect Core before trying again.');return false;}
    finally {pending.current--;setBusy(pending.current>0);}
  }
  const available=view.link==='online'&&!!view.expression&&now-view.expression.observed_at_ms<8000&&view.expression.observed_at_ms<=now+250;
  return {view,busy,error,available,run,accept,setError,latest};
}
