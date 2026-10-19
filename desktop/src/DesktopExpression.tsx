import {useEffect,useRef,useState} from 'react';
import {ExpressionPresence} from '@oscar/expression/react';
import type {ExpressionEvent,Source} from '@oscar/expression';
import type {View} from './bridge';
import {DesktopExpressionAdapter} from './expression';

export function DesktopExpression({view,size,sourceKind='core',gaze}:{view:View;size:number;sourceKind?:Source['kind'];gaze?:{x:number;y:number}}) {
  const adapter=useRef(new DesktopExpressionAdapter(sourceKind));
  const [event,setEvent]=useState<ExpressionEvent>(()=>({version:1,source:{kind:sourceKind,id:'desktop:unconfigured'},
    generation:0,transitionId:'initial',eventTime:Date.now(),expiresAt:Date.now()+8000,
    kind:'state',priority:'normal',operation:'unavailable',delivery:'subdued',availability:'unavailable',muted:false,attention:'none',reducedMotion:false}));
  useEffect(()=>{const next=adapter.current.receive(view,Date.now());if(next)setEvent(next);},[view]);
  return <ExpressionPresence event={event} source={event.source} size={size} gaze={gaze} now={adapter.current.clock}/>;
}
