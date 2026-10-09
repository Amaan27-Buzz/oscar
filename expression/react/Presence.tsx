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
export function ExpressionPresence({event,source,size=64,onAnimationRecord}:{event:ExpressionEvent;source:Source;size?:number;onAnimationRecord?:(record:AnimationRecord)=>void}) {
  const controller=useRef<{key:string;engine:ExpressionController}|null>(null);
  const key=`${source.kind}:${source.id}`;
  if(!controller.current||controller.current.key!==key)controller.current={key,engine:new ExpressionController(source)};
  const engine=controller.current.engine;
  const [snapshot,setSnapshot]=useState(()=>engine.snapshot(Date.now()));
  const callback=useRef(onAnimationRecord);callback.current=onAnimationRecord;
  useLayoutEffect(()=>{
    let frame:number|undefined,timer:ReturnType<typeof setTimeout>|undefined,stopped=false;
    const system=matchMedia('(prefers-reduced-motion: reduce)');
    const refresh=()=>{
      if(stopped)return;
      const now=Date.now(),next=engine.snapshot(now);setSnapshot(next);
      for(const record of engine.takeAnimationRecords())callback.current?.(record);
      if(next.moving)frame=requestAnimationFrame(refresh);
      else if(next.expiresAt!==null)timer=setTimeout(refresh,Math.max(1,next.expiresAt-now));
    };
    engine.setReducedMotion(system.matches,Date.now());engine.receive(event,Date.now());
    if(document.hidden)engine.suspend();refresh();
    const visibility=()=>{
      if(document.hidden)engine.suspend();
      if(frame!==undefined)cancelAnimationFrame(frame);if(timer!==undefined)clearTimeout(timer);
      refresh();
    };
    const reduce=()=>{engine.setReducedMotion(system.matches,Date.now());visibility();};
    system.addEventListener('change',reduce);document.addEventListener('visibilitychange',visibility);
    return()=>{stopped=true;if(frame!==undefined)cancelAnimationFrame(frame);if(timer!==undefined)clearTimeout(timer);system.removeEventListener('change',reduce);document.removeEventListener('visibilitychange',visibility);};
  },[engine,event]);
  return <ExpressionOrb snapshot={snapshot} size={size}/>;
}
