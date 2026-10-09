// Development-only evidence harness for the reusable renderer; no Core or capability connection.
import {useState} from 'react';
import fixtures from '../../../expression/fixtures/reference-v1.json';
import {arbitrate} from '../../../expression/core/motion';
import type {Pose,Scene} from '../../../expression/core/motion';
import type {ExpressionEvent,OperationalState} from '../../../expression/core/contract';
import {ExpressionOrb,ExpressionPresence} from '@oscar/expression/react';
const source={kind:'fixture',id:'browser-expression'} as const;
function event(generation:number,operation:OperationalState='speaking',kind:ExpressionEvent['kind']='state'):ExpressionEvent {
  const now=Date.now();return {version:1,source,generation,transitionId:`event-${generation}`,eventTime:now,expiresAt:now+30000,kind,priority:kind==='interrupt'?'urgent':'normal',operation,delivery:'composed',availability:'available',muted:operation==='muted',attention:'none',reducedMotion:false,...(kind==='accent'?{accent:'phrase' as const}:{})};
}
export function EngineProof() {
  const [current,setCurrent]=useState(()=>event(1));
  return <main><h1>OSCAR — Shared expression engine</h1><p>SIMULATED VISUAL STATE — NO CORE EXECUTION</p>
    <section className="stage" data-testid="engine-live"><ExpressionPresence source={source} event={current} size={192}/><p>Validated event stream · generation {current.generation}</p><div className="transport-buttons">
      <button onClick={()=>setCurrent(event(current.generation+1))}>Speech starts</button>
      <button onClick={()=>setCurrent(event(current.generation+1,'speaking','accent'))}>Permitted phrase accent</button>
      <button onClick={()=>setCurrent(event(current.generation+1,'attentive','interrupt'))}>Interrupt speech</button>
      <button onClick={()=>setCurrent(event(current.generation+1,'muted'))}>Mute</button>
      <button onClick={()=>setCurrent(event(current.generation+1,'idle'))}>Speech ends</button>
    </div></section>
    <section className="atlas" data-testid="engine-atlas"><h2>Shared v3 reference poses</h2><div className="atlas-grid">{fixtures.poseCases.map(fixture=>{
      const resolved=arbitrate(fixture.scene as Scene);
      return <figure className="expression" key={fixture.name}><ExpressionOrb snapshot={{pose:fixture.expected as Pose,resolved,source,generation:0,animation:'held',moving:false,expiresAt:null,priority:'delivery'}} size={96}/><figcaption>{fixture.name}</figcaption></figure>;
    })}</div></section>
  </main>;
}
