import {useLayoutEffect,useRef,useState} from 'react';
import {ExpressionController} from '../core/controller.js';
import type {ExpressionSnapshot} from '../core/controller.js';
import type {AnimationRecord,ExpressionEvent,Source} from '../core/contract.js';
import {Orb} from './Orb.js';
export {Orb};

export function ExpressionOrb({snapshot,size=64}:{snapshot:ExpressionSnapshot;size?:number}) {
  const prefix=snapshot.source.kind==='core'?'':'SIMULATED — ';
  return <Orb pose={snapshot.pose} size={size} label={`${prefix}OSCAR: ${snapshot.resolved.label}. ${snapshot.resolved.delivery} delivery.`}/>;
}

/** Source must be supplied by a trusted adapter. This component has no bridge, audio or execution APIs. */
export function ExpressionPresence({event,source,size=64,onAnimationRecord,gaze,now=Date.now}:{event:ExpressionEvent;source:Source;size?:number;onAnimationRecord?:(record:AnimationRecord)=>void;gaze?:{x:number;y:number};now?:()=>number}) {
  const controller=useRef<{key:string;engine:ExpressionController}|null>(null);
  const key=`${source.kind}:${source.id}`;
  if(!controller.current||controller.current.key!==key)controller.current={key,engine:new ExpressionController(source)};
  const engine=controller.current.engine;
  const [snapshot,setSnapshot]=useState(()=>engine.snapshot(now()));
  const callback=useRef(onAnimationRecord);callback.current=onAnimationRecord;
  useLayoutEffect(()=>{
    let frame:number|undefined,timer:ReturnType<typeof setTimeout>|undefined,stopped=false;
    const system=matchMedia('(prefers-reduced-motion: reduce)');
    const refresh=()=>{
      if(stopped)return;
      const at=now(),next=engine.snapshot(at);setSnapshot(next);
      for(const record of engine.takeAnimationRecords())callback.current?.(record);
      if(next.moving)frame=requestAnimationFrame(refresh);
      else if(next.expiresAt!==null)timer=setTimeout(refresh,Math.max(1,next.expiresAt-at));
    };
    engine.setReducedMotion(system.matches,now());engine.receive(event,now());
    if(gaze)engine.setGaze(gaze,now());
    if(document.hidden)engine.suspend();refresh();
    const visibility=()=>{
      if(document.hidden)engine.suspend();
      if(frame!==undefined)cancelAnimationFrame(frame);if(timer!==undefined)clearTimeout(timer);
      refresh();
    };
    const reduce=()=>{engine.setReducedMotion(system.matches,now());visibility();};
    system.addEventListener('change',reduce);document.addEventListener('visibilitychange',visibility);
    return()=>{stopped=true;if(frame!==undefined)cancelAnimationFrame(frame);if(timer!==undefined)clearTimeout(timer);system.removeEventListener('change',reduce);document.removeEventListener('visibilitychange',visibility);};
  },[engine,event,gaze?.x,gaze?.y,now]);
  return <ExpressionOrb snapshot={snapshot} size={size}/>;
}
