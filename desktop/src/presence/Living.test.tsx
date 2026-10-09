import {act,cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {afterEach,describe,expect,it,vi} from 'vitest';
import {ExpressionController} from '@oscar/expression';
import {LivingPresence} from './Living';
import {initialView} from '../bridge';
import type {Send,View} from '../bridge';
afterEach(()=>{cleanup();vi.useRealTimers();});
function harness() {
  let generation=0;
  let view:View={...initialView,link:'online',expression:{epoch:'a'.repeat(32),generation:0,observed_at_ms:Date.now(),voice_observed_at_ms:Date.now(),tasks_observed_at_ms:Date.now(),current_observed_at_ms:Date.now()}};
  let push:(view:View)=>void=()=>{};
  const snapshot=()=>({...view,expression:{...view.expression!,generation:++generation,observed_at_ms:Date.now(),tasks_observed_at_ms:Date.now(),current_observed_at_ms:Date.now()}});
  const port=vi.fn<Send>(async command=>{if(command.kind==='window')view={...view,window:command.mode};return snapshot();});
  render(<LivingPresence port={port} events={async fn=>{push=fn;return()=>{};}} windowAction={async()=>{}}/>);
  return {port,update:(patch:Partial<View>)=>{view={...view,...patch};act(()=>push(snapshot()));},stale:()=>act(()=>push({...view,link:'online',voice:'speaking',expression:{...view.expression!,generation:0}}))};
}
describe('living Desktop presence',()=>{
  it('invokes with focus, asks once, preserves draft on retreat and returns focus to character',async()=>{
    const h=harness();await screen.findByText('Here');
    fireEvent.click(screen.getByRole('button',{name:/OSCAR: Here/}));
    await waitFor(()=>expect(document.activeElement).toBe(screen.getByLabelText('Ask OSCAR')));
    fireEvent.change(screen.getByLabelText('Ask OSCAR'),{target:{value:'2 + 3'}});
    fireEvent.keyDown(screen.getByLabelText('Ask OSCAR'),{key:'Enter'});
    await waitFor(()=>expect(h.port).toHaveBeenCalledWith({kind:'interact',mode:'Ask',text:'2 + 3',context_id:''}));
    fireEvent.keyDown(screen.getByLabelText('Ask OSCAR'),{key:'Escape'});
    await waitFor(()=>expect(screen.getByRole('button',{name:/OSCAR: Here/}).getAttribute('aria-expanded')).toBe('false'));
    expect(document.activeElement).toBe(screen.getByRole('button',{name:/OSCAR: Here/}));
    expect((screen.getByLabelText('Ask OSCAR') as HTMLTextAreaElement).value).toBe('2 + 3');
    expect(h.port.mock.calls.filter(([c])=>c.kind==='interact')).toHaveLength(1);
  });
  it('does not steal focus on owner attention or revive work from a stale packet after loss',async()=>{
    const h=harness();await screen.findByText('Here');
    const current={task_id:'t',state:'planned',description:'Review temporary workspace',target:'fixture',blocker:null,actions:['approve'],generation:1,evidence_ids:[],response:null,response_status:null,value:null,epistemic:null};
    h.update({current});await screen.findByText('Review needed');
    expect(screen.getByRole('button',{name:/OSCAR: Review needed/}).getAttribute('aria-expanded')).toBe('false');
    h.update({link:'unavailable'});await screen.findByText('Offline');h.stale();
    expect(screen.getByText('Offline')).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:/OSCAR: Offline/}));
    await screen.findByRole('button',{name:/Check connection/});
    expect(screen.queryByRole('button',{name:/Review decision/})).toBeNull();
  });
  it('expires both expression and actionable text without fresh upstream evidence',async()=>{
    vi.useFakeTimers();harness();await act(async()=>{});
    await act(async()=>{vi.advanceTimersByTime(8100);});
    expect(screen.getByText('State unknown')).toBeTruthy();
    expect(document.querySelector('.living-presence')?.getAttribute('data-operation')).toBe('unknown');
  });
  it('uses the same weighted engine for bounded pointer targets, never changes operation or freshness',()=>{
    const now=100000,source={kind:'core' as const,id:'gaze-test'};
    const engine=new ExpressionController(source);
    engine.receive({version:1,source,generation:1,transitionId:'a',eventTime:now,expiresAt:now+8000,kind:'state',priority:'normal',operation:'attentive',delivery:'resting',availability:'available',muted:false,attention:'none',reducedMotion:false},now);
    const before=engine.snapshot(now+800);engine.setGaze({x:10,y:-7},now+800);
    expect(engine.snapshot(now+800).pose).toEqual(before.pose);
    const after=engine.snapshot(now+1600);expect(after.pose.gx).not.toBe(before.pose.gx);
    expect(after.expiresAt).toBe(now+8000);expect(after.generation).toBe(1);
    expect(()=>engine.setGaze({x:11,y:0},now+1600)).toThrow();
    expect(engine.snapshot(now+8100).resolved.operation).toBe('unknown');
  });
  it('recovers keyboard focus when a task removes the input and Escape still retreats',async()=>{
    const h=harness();await screen.findByText('Here');
    fireEvent.click(screen.getByRole('button',{name:/OSCAR: Here/}));
    await waitFor(()=>expect(document.activeElement).toBe(screen.getByLabelText('Ask OSCAR')));
    h.update({current:{task_id:'work',state:'executing',description:'Temporary work',target:'fixture',blocker:null,actions:[],generation:1,evidence_ids:[],response:null,response_status:null,value:null,epistemic:null}});
    await waitFor(()=>expect(document.activeElement).toBe(screen.getByRole('button',{name:/OSCAR: Working/})));
    fireEvent.keyDown(document.activeElement!,{key:'Escape'});
    await waitFor(()=>expect(screen.getByRole('button',{name:/OSCAR: Working/}).getAttribute('aria-expanded')).toBe('false'));
  });
  it('unwedges a rejected collapse and supports a subsequent retreat',async()=>{
    const h=harness();await screen.findByText('Here');fireEvent.click(screen.getByRole('button',{name:/OSCAR: Here/}));
    await screen.findByRole('button',{name:'Return to presence'});
    h.port.mockRejectedValueOnce(new Error('native resize failed'));
    fireEvent.click(screen.getByRole('button',{name:'Return to presence'}));
    await screen.findByRole('alert');
    expect(document.querySelector('.writing-leaf')?.getAttribute('aria-hidden')).toBe('false');
    fireEvent.keyDown(screen.getByRole('button',{name:/OSCAR: Here/}),{key:'Escape'});
    await waitFor(()=>expect(screen.getByRole('button',{name:/OSCAR: Here/}).getAttribute('aria-expanded')).toBe('false'));
  });
  it('keeps interruption below offline/error/unknown and distinguishes fresh unknown from expiry',async()=>{
    const h=harness();await screen.findByText('Here');
    h.update({link:'unavailable',voice:'interrupted'});await screen.findByText('Offline');
    h.update({link:'online',current:{task_id:'t',state:'unknown',description:'Unknown fixture',target:'fixture',blocker:null,actions:[],generation:1,evidence_ids:[],response:null,response_status:null,value:null,epistemic:null}});
    await screen.findByText('State unknown');
    fireEvent.click(screen.getByRole('button',{name:/OSCAR: State unknown/}));
    await screen.findByText('Core reports an unresolved state. Inspect it before continuing.');
    expect(screen.queryByText(/last observation expired/)).toBeNull();
    h.update({current:{task_id:'t',state:'failed',description:'Failure',target:'fixture',blocker:null,actions:[],generation:1,evidence_ids:[],response:null,response_status:null,value:null,epistemic:null}});
    await screen.findByText('Task failed');expect(screen.queryByText('Interrupted')).toBeNull();
  });
  it('shows supplied blockers and an evidence-labelled bounded answer without losing the draft',async()=>{
    const h=harness();await screen.findByText('Here');fireEvent.click(screen.getByRole('button',{name:/OSCAR: Here/}));
    await screen.findByRole('button',{name:'Return to presence'});
    fireEvent.change(screen.getByLabelText('Ask OSCAR'),{target:{value:'My draft'}});
    const current={task_id:'t',state:'blocked',description:'Work',target:'fixture',blocker:'Provider unavailable',actions:[],generation:1,evidence_ids:[],response:null,response_status:null,value:null,epistemic:null};
    h.update({current});await screen.findByText('Work is blocked.');await screen.findByText('Provider unavailable');
    h.update({current:{...current,state:'partially_verified',blocker:null,response:'A reported answer',response_status:'REPORTED'}});
    await screen.findByText('A reported answer');await screen.findByText('REPORTED');
    h.update({current:{...current,state:'verified',blocker:null,value:'5',epistemic:'VERIFIED'}});
    await screen.findByText('5');await screen.findByText('VERIFIED');
    fireEvent.click(screen.getByRole('button',{name:'Ask again'}));
    await waitFor(()=>expect((screen.getByLabelText('Ask OSCAR') as HTMLTextAreaElement).value).toBe('My draft'));
  });
});
