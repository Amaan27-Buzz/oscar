import {act,cleanup,render,screen} from '@testing-library/react';
import {afterEach,describe,expect,it,vi} from 'vitest';
import {ExpressionController,validateEvent} from '@oscar/expression';
import {ExpressionPresence} from '@oscar/expression/react';
import {initialView} from './bridge';
import type {View} from './bridge';
import {CoreClock} from './core-clock';
import {DesktopExpressionAdapter} from './expression';

const server=100000;
const frame={version:1,source:{kind:'core',id:'presence:canonical'},generation:1,transitionId:'unchanged',eventTime:server,expiresAt:server+30000,kind:'state',priority:'normal',operation:'idle',delivery:'composed',availability:'available',muted:false,attention:'none',reducedMotion:true};
const remoteView=(local:number,patch:Partial<View>={}):View=>({...initialView,link:'online',voice:'idle',
  expression:{epoch:'a'.repeat(32),generation:1,observed_at_ms:local,voice_observed_at_ms:local,tasks_observed_at_ms:local,current_observed_at_ms:local},
  core_clock:{observed_at_ms:server,received_at_ms:local,transport_ms:200},presence:{version:1,visible:true,expression:frame},...patch});
afterEach(()=>{cleanup();vi.useRealTimers();});

describe('authenticated remote Core clock',()=>{
  it('does not move Core time backwards when an older snapshot follows a wall-clock rollback',()=>{
    let elapsed=1000;
    const observation={observed_at_ms:server,received_at_ms:server,transport_ms:0};
    const first=CoreClock.observe(observation,server,()=>elapsed)!;
    elapsed+=30000;
    const replay=CoreClock.observe({...observation,transport_ms:1},server,()=>elapsed,first)!;
    expect(replay.now()).toBe(server+30000);
    expect(validateEvent(frame,replay.now())).toBeNull();
    elapsed+=10000;
    const resumed=CoreClock.observe({...observation,observed_at_ms:server+40000,received_at_ms:server+40000},server+40000,()=>elapsed,first)!;
    expect(resumed.now()).toBe(server+40000);
  });
  it.each([-5000,5000])('preserves canonical state with device clock offset %d and charges transport and IPC age',offset=>{
    let elapsed=1000;
    const local=server+offset,adapter=new DesktopExpressionAdapter('core',()=>elapsed);
    const received=adapter.receive(remoteView(local),local+50)!;
    expect(received).toEqual(frame);
    expect(adapter.clock()).toBe(server+250);
    const engine=new ExpressionController(received.source);
    expect(engine.receive(received,adapter.clock())).toBe('accepted');
    elapsed+=500;expect(adapter.clock()).toBe(server+750);
    // A repeated native envelope does not anchor the old observation again.
    expect(adapter.receive(remoteView(local),local+550)).toEqual(frame);
    expect(adapter.clock()).toBe(server+750);
    elapsed+=29250;
    expect(engine.snapshot(adapter.clock()).resolved.operation).toBe('unknown');
  });
  it('uses monotonic elapsed after receipt and fails closed on rollback and invalid observations',()=>{
    let elapsed=1000;
    const observation={observed_at_ms:server,received_at_ms:server-1000,transport_ms:200};
    const clock=CoreClock.observe(observation,server-1000,()=>elapsed)!;
    elapsed+=500;expect(clock.now()).toBe(server+700);
    elapsed=999;expect(validateEvent(frame,clock.now())).toBeNull();
    expect(CoreClock.observe({...observation,observed_at_ms:server+30001},server-1000,()=>1000)).toBeNull();
    expect(CoreClock.observe({...observation,transport_ms:15001},server-1000,()=>1000)).toBeNull();
    expect(CoreClock.observe(observation,server-1001,()=>1000)).toBeNull();
    expect(CoreClock.observe(observation,server+15001,()=>1000)).toBeNull();
    expect(CoreClock.observe(observation,server-1000,()=>Number.NaN)).toBeNull();
  });
  it('cannot renew expired canonical state or widen the 250ms future contract',()=>{
    const adapter=new DesktopExpressionAdapter('core',()=>1000);
    const received=adapter.receive(remoteView(server,{core_clock:{observed_at_ms:server+30000,received_at_ms:server,transport_ms:0}}),server)!;
    expect(received.source.id).toMatch(/^desktop:/);expect(received.operation).toBe('unknown');
    const future={...frame,eventTime:server+251,expiresAt:server+30000};
    const rejected=new DesktopExpressionAdapter('core',()=>1000).receive(remoteView(server,{core_clock:{observed_at_ms:server,received_at_ms:server,transport_ms:0},presence:{version:1,visible:true,expression:future}}),server)!;
    expect(rejected.operation).toBe('unknown');
    const missing=new DesktopExpressionAdapter('core',()=>1000).receive(remoteView(server,{presence:null}),server)!;
    expect(missing.operation).toBe('unknown');
    const noClock=new DesktopExpressionAdapter('core',()=>1000).receive(remoteView(server,{core_clock:null,connection:{endpoint:'https://core.example',installation_id:'fixture',node_id:'desktop',public_key:'public',owner_public_key:'public',status:'online'}}),server)!;
    expect(noClock.operation).toBe('unknown');
  });
  it('renders and expires with the trusted clock even when local wall time jumps',async()=>{
    vi.useFakeTimers();vi.setSystemTime(server-1000);
    let elapsed=1000;
    const adapter=new DesktopExpressionAdapter('core',()=>elapsed),event=adapter.receive(remoteView(server-1000),server-1000)!;
    render(<ExpressionPresence event={event} source={event.source} now={adapter.clock}/>);
    expect(screen.getByRole('img').getAttribute('aria-label')).toContain('OSCAR: idle');
    vi.setSystemTime(server+600000);elapsed+=1000;
    await act(async()=>{vi.advanceTimersByTime(1000);});
    expect(screen.getByRole('img').getAttribute('aria-label')).toContain('OSCAR: idle');
    elapsed+=29000;
    await act(async()=>{vi.advanceTimersByTime(29000);});
    expect(screen.getByRole('img').getAttribute('aria-label')).toContain('OSCAR: unknown');
  });
});
