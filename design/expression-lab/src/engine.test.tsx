import React from 'react';
import {afterEach,describe,expect,it,vi} from 'vitest';
import {act,cleanup,render,screen} from '@testing-library/react';
import {ExpressionController} from '../../../expression/core/controller';
import {validateEvent} from '../../../expression/core/contract';
import type {ExpressionEvent} from '../../../expression/core/contract';
import {ExpressionPresence} from '../../../expression/react/Presence';
const source={kind:'fixture',id:'cross-v1'} as const;
const base=1000000;
function event(generation=1,changes:Partial<ExpressionEvent>={}):ExpressionEvent {
  return {version:1,source,generation,transitionId:`event-${generation}`,eventTime:base,expiresAt:base+30000,kind:'state',priority:'normal',operation:'idle',delivery:'composed',availability:'available',muted:false,attention:'none',reducedMotion:false,...changes};
}
afterEach(()=>{cleanup();vi.useRealTimers();vi.unstubAllGlobals();});
describe('versioned event contract and controller',()=>{
  it('strictly rejects private/unknown fields and malformed numbers, enums and source',()=>{
    expect(validateEvent(event(),base)).not.toBeNull();
    for(const bad of [{...event(),text:'private content'},{...event(),version:2},{...event(),muted:'false'},{...event(),operation:'available'},{...event(),source:{...source,token:'private'}},{...event(),generation:Infinity},{...event(),expiresAt:base+30001},{...event(),eventTime:base+251},{...event(),kind:'accent'},{...event(),accent:'phrase'}])expect(validateEvent(bad,base)).toBeNull();
    const encoded=JSON.stringify(event());
    for(const raw of [encoded+' trailing garbage',encoded.replace('"version":','version:'),encoded.replaceAll('"',"'"),encoded.replace('"version":1','"version":01')])expect(validateEvent(raw,base)).toBeNull();
    expect(validateEvent(encoded.replace('"version":1','"version":1,"version":1'),base)).not.toBeNull();
  });
  it('generation fences keep old speech/accents from resurrecting after unavailability',()=>{
    const engine=new ExpressionController(source);
    engine.receive(event(1,{operation:'speaking'}),base);
    engine.receive(event(2,{operation:'unavailable',priority:'normal'}),base+200);
    expect(engine.receive(event(1,{operation:'speaking',kind:'accent',accent:'phrase'}),base+210)).toBe('stale');
    expect(engine.snapshot(base+210).resolved.operation).toBe('unavailable');
    expect(engine.snapshot(base+210).priority).toBe('critical');
  });
  it('long speech holds, explicit accents move once, and fresh heartbeats do not replay',()=>{
    const engine=new ExpressionController(source);
    engine.receive(event(1,{operation:'speaking'}),base);
    const held=engine.snapshot(base+700).pose;
    expect(engine.snapshot(base+10000).pose).toEqual(held);
    engine.receive(event(2,{operation:'speaking',transitionId:'event-1',eventTime:base+10000,expiresAt:base+40000}),base+10000);
    expect(engine.snapshot(base+10000).moving).toBe(false);
    engine.receive(event(3,{operation:'speaking',kind:'accent',accent:'phrase',eventTime:base+10000,expiresAt:base+40000}),base+10000);
    expect(Math.abs(engine.snapshot(base+12300).pose.x-held.x)).toBeGreaterThan(60);
    expect(engine.snapshot(base+15200).pose).toEqual(held);
    expect(engine.snapshot(base+25000).pose).toEqual(held);
  });
  it('presentation cancellation never invents that actual speech ended',()=>{
    const engine=new ExpressionController(source);
    engine.receive(event(1,{operation:'speaking'}),base);
    const at=engine.snapshot(base+100).pose;
    engine.receive(event(2,{kind:'cancel',operation:'speaking'}),base+100);
    expect(engine.snapshot(base+1000).pose).toEqual(at);
    expect(engine.snapshot(base+1000).resolved.operation).toBe('speaking');
    expect(engine.takeAnimationRecords().some(r=>r.outcome==='cancelled')).toBe(true);
  });
  it('authored reactions recover without changing operation or replaying on a heartbeat',()=>{
    const engine=new ExpressionController(source);engine.receive(event(1,{delivery:'amused'}),base);
    expect(engine.snapshot(base+3200).resolved.operation).toBe('idle');
    expect(engine.snapshot(base+3200).resolved.delivery).toBe('composed');
    engine.receive(event(2,{delivery:'amused',transitionId:'event-1'}),base+4000);
    expect(engine.snapshot(base+4000).moving).toBe(false);
    expect(engine.snapshot(base+4000).resolved.delivery).toBe('composed');
  });
  it('expiry, malformed current input and lifecycle loss fail closed, retaining mute',()=>{
    for(const reason of ['expired','invalid','lifecycle']) {
      const engine=new ExpressionController(source);engine.receive(event(1,{muted:true}),base);
      if(reason==='invalid')engine.receive({broken:true},base+10);
      if(reason==='lifecycle')engine.suspend();
      const snapshot=engine.snapshot(reason==='expired'?base+30000:base+10);
      expect(snapshot.resolved.operation).toBe('unknown');expect(snapshot.resolved.muted).toBe(true);expect(snapshot.moving).toBe(false);
      expect(engine.receive(event(1),base+20)).toBe('stale');
    }
  });
  it('mute/owner attention defeat accents and priority hints; blink does not start a phrase',()=>{
    const engine=new ExpressionController(source);engine.receive(event(1,{operation:'speaking'}),base);
    engine.snapshot(base+700);
    engine.receive(event(2,{operation:'speaking',kind:'accent',accent:'blink'}),base+700);
    expect(engine.snapshot(base+1200).pose.x).toBe(-42);
    engine.receive(event(3,{operation:'speaking',muted:true,attention:'owner',priority:'urgent'}),base+1200);
    expect(engine.snapshot(base+1200).resolved.operation).toBe('waiting');
    expect(engine.snapshot(base+1200).resolved.muted).toBe(true);
    engine.receive(event(4,{operation:'speaking',kind:'accent',accent:'phrase',muted:true}),base+1300);
    expect(engine.snapshot(base+1300).resolved.operation).toBe('unknown');
  });
  it('interruption preserves the performed pose; reduced motion removes travel and expiry remains enforced',()=>{
    const engine=new ExpressionController(source);engine.receive(event(1,{operation:'speaking'}),base);
    engine.receive(event(2,{operation:'speaking',kind:'accent',accent:'phrase'}),base+700);
    const at=engine.snapshot(base+1900).pose;
    engine.receive(event(3,{operation:'attentive',kind:'interrupt'}),base+1900);
    expect(engine.snapshot(base+1900).pose).toEqual(at);
    engine.setReducedMotion(true,base+1910);
    const reduced=engine.snapshot(base+1910).pose;
    expect(engine.snapshot(base+2000).pose).toEqual(reduced);
    expect(engine.snapshot(base+20000).resolved.delivery).toBe('attentive');
    expect(engine.snapshot(base+30000).resolved.operation).toBe('unknown');
  });
  it('reduced motion keeps surprise recovery as discrete static poses, including a mid-reaction preference change',()=>{
    for(const initiallyReduced of [true,false]) {
      const engine=new ExpressionController(source);
      engine.receive(event(1,{delivery:'surprised',reducedMotion:initiallyReduced}),base);
      if(!initiallyReduced)engine.setReducedMotion(true,base+100);
      const initial=engine.snapshot(base+100).pose;
      expect(engine.snapshot(base+500).pose).toEqual(initial);
      expect(engine.snapshot(base+1000).resolved.delivery).toBe('composed');
      expect(engine.snapshot(base+4000).resolved.delivery).toBe('composed');
      expect(engine.snapshot(base+4000).moving).toBe(false);
    }
  });
});
describe('reusable React renderer',()=>{
  it('updates state before paint without remounting SVG identity and expires held claims',()=>{
    vi.useFakeTimers();vi.setSystemTime(base);
    vi.stubGlobal('matchMedia',()=>({matches:false,addEventListener:vi.fn(),removeEventListener:vi.fn()}));
    vi.stubGlobal('requestAnimationFrame',vi.fn(()=>1));vi.stubGlobal('cancelAnimationFrame',vi.fn());
    const {rerender}=render(<ExpressionPresence source={source} event={event(1,{operation:'speaking'})}/>);
    const node=screen.getByRole('img');
    rerender(<ExpressionPresence source={source} event={event(2,{operation:'unavailable',reducedMotion:true})}/>);
    expect(screen.getByRole('img')).toBe(node);
    expect(node.getAttribute('aria-label')).toContain('SIMULATED — OSCAR: unavailable');
    act(()=>vi.advanceTimersByTime(30000));
    expect(node.getAttribute('aria-label')).toContain('unknown');
  });
});
