import {describe,it,expect} from 'vitest';
import {ExpressionController} from '@oscar/expression';
import {DesktopExpressionAdapter,freshnessMs} from './expression';
import {initialView} from './bridge';
import type {View,Task} from './bridge';
const now=100000;
const task=(state:string,actions:string[]=[]):Task=>({task_id:'private-task-id',state,actions,description:'PRIVATE description',target:'private-target',generation:1,evidence_ids:[],blocker:null,response:'PRIVATE response',response_status:null,value:null,epistemic:null});
const view=(patch:Partial<View>={}):View=>({...initialView,link:'online',voice:'idle',expression:{epoch:'a'.repeat(32),generation:1,observed_at_ms:now,voice_observed_at_ms:now,tasks_observed_at_ms:now,current_observed_at_ms:now},...patch});
describe('native Desktop expression adapter',()=>{
  it('admits reserved Core publications without replaying a stable transition',()=>{
    const adapter=new DesktopExpressionAdapter();
    const frame={version:1,source:{kind:'core',id:'presence:canonical'},generation:1,transitionId:'unchanged',eventTime:now,expiresAt:now+30000,kind:'state',priority:'normal',operation:'idle',delivery:'composed',availability:'available',muted:false,attention:'none',reducedMotion:true};
    const first=adapter.receive(view({presence:{version:1,visible:true,expression:frame}}),now)!;
    const engine=new ExpressionController(first.source);expect(engine.receive(first,now)).toBe('accepted');
    engine.snapshot(now+1000);engine.takeAnimationRecords();
    const fresh=adapter.receive(view({presence:{version:1,visible:true,expression:{...frame,generation:1025,eventTime:now+5000,expiresAt:now+35000}}}),now+5000)!;
    expect(engine.receive(fresh,now+5000)).toBe('accepted');
    expect(engine.snapshot(now+31000).resolved.operation).toBe('idle');
    expect(engine.takeAnimationRecords()).toEqual([]);
    expect(engine.receive(first,now+6000)).toBe('stale');
    expect(engine.snapshot(now+35000).resolved.operation).toBe('unknown');
  });
  it('maps actual task truth, attention and unknown without forwarding private content',()=>{
    for(const [state,operation] of [['executing','executing'],['verifying','verifying'],['awaiting_result','waiting'],['result_received','processing'],['verified','attentive'],['partially_verified','attentive'],['failed','error'],['unknown','unknown'],['unexpected','unknown']]) {
      const e=new DesktopExpressionAdapter().receive(view({current:task(state)}),now)!;
      expect(e.operation).toBe(operation);expect(JSON.stringify(e)).not.toMatch(/PRIVATE|private-task|private-target/);
    }
    const e=new DesktopExpressionAdapter().receive(view({voice:'speaking',tasks:[task('planned',['approve'])]}),now)!;
    expect(e.operation).toBe('waiting');expect(e.attention).toBe('owner');
  });
  it('fences cached readbacks, retired epochs and stable heartbeat intents',()=>{
    const adapter=new DesktopExpressionAdapter();const first=adapter.receive(view(),now)!;
    expect(adapter.receive(view(),now+1)).toBeNull();
    const heartbeat=adapter.receive(view({expression:{...view().expression!,generation:2,observed_at_ms:now+2}}),now+2)!;
    expect(heartbeat.transitionId).toBe(first.transitionId);
    expect(heartbeat.generation).toBeGreaterThan(first.generation);
    adapter.receive(view({link:'unavailable',expression:{...view().expression!,epoch:'b'.repeat(32)}}),now);
    expect(adapter.receive(view({expression:{...view().expression!,generation:99}}),now)).toBeNull();
  });
  it('never renews cached speech with a task heartbeat; expiry cancels choreography',()=>{
    const adapter=new DesktopExpressionAdapter();const e=adapter.receive(view({voice:'speaking'}),now)!;
    const engine=new ExpressionController(e.source);engine.receive(e,now);
    expect(engine.snapshot(now+6000).resolved.operation).toBe('speaking');
    const heartbeat=adapter.receive(view({voice:'speaking',expression:{...view().expression!,generation:2,observed_at_ms:now+6000}}),now+6000)!;
    expect(heartbeat.expiresAt).toBe(now+freshnessMs);engine.receive(heartbeat,now+6000);
    expect(engine.snapshot(now+freshnessMs+1).resolved.operation).toBe('unknown');
  });
  it('availability, mute, cancellation and interruption suppress speech',()=>{
    expect(new DesktopExpressionAdapter().receive(view({link:'unavailable',voice:'speaking'}),now)!.operation).toBe('unavailable');
    expect(new DesktopExpressionAdapter().receive(view({voice:'muted'}),now)!.muted).toBe(true);
    expect(new DesktopExpressionAdapter().receive(view({current:task('cancelled')}),now)!.kind).toBe('cancel');
    const adapter=new DesktopExpressionAdapter();const e=adapter.receive(view({voice:'speaking'}),now)!;
    const engine=new ExpressionController(e.source);engine.receive(e,now);
    const stop=adapter.receive(view({voice:'interrupted',expression:{...view().expression!,generation:2}}),now+10)!;
    engine.receive(stop,now+10);expect(stop.kind).toBe('interrupt');expect(engine.snapshot(now+10).resolved.operation).toBe('attentive');
    expect(engine.takeAnimationRecords().some(r=>r.outcome==='cancelled'||r.outcome==='superseded')).toBe(true);
  });
  it('rejects malformed readback and portrays expired online state as unknown',()=>{
    expect(new DesktopExpressionAdapter().receive(view({expression:null}),now)).toBeNull();
    const adapter=new DesktopExpressionAdapter();adapter.receive(view(),now);
    expect(adapter.receive(view({expression:{...view().expression!,generation:2}}),now+freshnessMs)!.operation).toBe('unknown');
    expect(new DesktopExpressionAdapter().receive(view({voice:'listening',expression:{...view().expression!,voice_observed_at_ms:0}}),now)!.operation).toBe('unknown');
  });
  it('does not borrow voice freshness for tasks or let historical failures dominate current work',()=>{
    const e=new DesktopExpressionAdapter().receive(view({current:task('executing'),tasks:[task('failed')],expression:{...view().expression!,observed_at_ms:now+6000,voice_observed_at_ms:now+6000}}),now+6000)!;
    expect(e.operation).toBe('executing');expect(e.expiresAt).toBe(now+freshnessMs);
    const adapter=new DesktopExpressionAdapter();adapter.receive(view(),now);
    expect(adapter.receive(view({expression:{...view().expression!,epoch:'b'.repeat(32),observed_at_ms:0}}),now)).toBeNull();
    expect(adapter.receive(view({expression:{...view().expression!,generation:2}}),now)).not.toBeNull();
  });
});
