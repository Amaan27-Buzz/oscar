import {act,cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {afterEach,describe,expect,it,vi} from 'vitest';
import {ExpressionController} from '@oscar/expression';
import {LivingPresence} from './Living';
import {initialView} from '../bridge';
import type {Send,View} from '../bridge';
afterEach(()=>{cleanup();vi.useRealTimers();});
it('keeps native shortcut registration reachable in the default presence',async()=>{
  const h=harness();await screen.findByText('Here');
  fireEvent.click(screen.getByRole('button',{name:/OSCAR: Here/}));await screen.findByLabelText('Ask OSCAR');
  fireEvent.click(screen.getByText('Presence',{exact:true}));
  fireEvent.change(screen.getByLabelText('Global shortcut'),{target:{value:'Ctrl+Alt+Q'}});
  fireEvent.click(screen.getByRole('button',{name:'Register shortcut'}));
  await waitFor(()=>expect(h.port).toHaveBeenCalledWith({kind:'shortcut',accelerator:'Ctrl+Alt+Q'}));
});
function harness() {
  let generation=0;
  let view:View={...initialView,link:'online',expression:{epoch:'a'.repeat(32),generation:0,observed_at_ms:Date.now(),voice_observed_at_ms:Date.now(),tasks_observed_at_ms:Date.now(),current_observed_at_ms:Date.now()}};
  let push:(view:View)=>void=()=>{};
  const snapshot=()=>({...view,expression:{...view.expression!,generation:++generation,observed_at_ms:Date.now(),tasks_observed_at_ms:Date.now(),current_observed_at_ms:Date.now()}});
  const port=vi.fn<Send>(async command=>{if(command.kind==='window')view={...view,window:command.mode,window_revision:(view.window_revision??0)+1};return snapshot();});
  render(<LivingPresence port={port} events={async fn=>{push=fn;return()=>{};}} windowAction={async()=>{}}/>);
  return {port,update:(patch:Partial<View>)=>{view={...view,...patch};const next=snapshot();act(()=>push(next));return next;},stale:()=>act(()=>push({...view,link:'online',voice:'speaking',expression:{...view.expression!,generation:0}}))};
}
describe('living Desktop presence',()=>{
  it('retains the character in Activity and recovers an uncertain IPC warning only after task inspection',async()=>{
    const h=harness();await screen.findByText('Here');
    const current={task_id:'check',state:'verified',description:'Read back task',target:'fixture',blocker:null,actions:[],generation:1,evidence_ids:[],response:null,response_status:null,value:null,epistemic:null};
    h.update({window:'activity',current,tasks:[current]});
    expect(screen.getByRole('button',{name:/OSCAR: Here/})).toBeTruthy();
    h.port.mockRejectedValueOnce(new Error('Unknown IPC outcome'));
    fireEvent.click(screen.getByRole('button',{name:'Refresh Core'}));await screen.findByText(/The request outcome is unknown/);
    fireEvent.click(screen.getByRole('button',{name:/VerifiedRead back task/}));
    await waitFor(()=>expect(screen.queryByText(/The request outcome is unknown/)).toBeNull());
  });
  it('an uncertain Apply IPC outcome keeps the text tools from offering a blind retry',async()=>{
    const h=harness();await screen.findByText('Here');
    h.update({window:'tools',preview:{preview_id:'exact',before:null,after:'reference',epistemic:'REPORTED',expires:Date.now()/1000+15,destinations:['surface'],mode:'Dictate'}});
    await screen.findByRole('button',{name:'Apply reviewed text'});
    h.port.mockRejectedValueOnce(new Error('IPC outcome unknown'));
    fireEvent.click(screen.getByRole('button',{name:'Apply reviewed text'}));
    await screen.findByRole('alert');
    expect((screen.getByRole('button',{name:'Apply reviewed text'}) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole('button',{name:'Apply reviewed text'}));
    expect(h.port.mock.calls.filter(([command])=>command.kind==='apply')).toHaveLength(1);
  });
  it('an already-emitted interact acknowledgement clears only the accepted submitted draft',async()=>{
    const h=harness();await screen.findByText('Here');
    fireEvent.click(screen.getByRole('button',{name:/OSCAR: Here/}));await screen.findByLabelText('Ask OSCAR');
    fireEvent.change(screen.getByLabelText('Ask OSCAR'),{target:{value:'2 + 3'}});
    const current={task_id:'accepted',state:'partially_verified',description:'Result',target:'fixture',blocker:null,actions:[],generation:1,evidence_ids:[],response:'5',response_status:'REPORTED',value:null,epistemic:null};
    h.port.mockImplementationOnce(async()=>h.update({current}));
    fireEvent.click(screen.getByRole('button',{name:'Ask'}));await screen.findByRole('button',{name:'Ask again'});
    fireEvent.click(screen.getByRole('button',{name:'Ask again'}));
    await waitFor(()=>expect((screen.getByLabelText('Ask OSCAR') as HTMLTextAreaElement).value).toBe(''));
  });
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
  it('accepts an emitted window acknowledgement before its equal command reply without an expiry warning',async()=>{
    const h=harness();await screen.findByText('Here');
    h.port.mockImplementationOnce(async()=>h.update({window:'interaction',window_revision:1}));
    fireEvent.click(screen.getByRole('button',{name:/OSCAR: Here/}));
    await waitFor(()=>expect(document.activeElement).toBe(screen.getByLabelText('Ask OSCAR')));
    fireEvent.change(screen.getByLabelText('Ask OSCAR'),{target:{value:'Unfinished draft'}});
    fireEvent.keyDown(screen.getByLabelText('Ask OSCAR'),{key:'Escape'});
    await waitFor(()=>expect(screen.getByRole('button',{name:/OSCAR: Here/}).getAttribute('aria-expanded')).toBe('false'));
    h.port.mockImplementationOnce(async()=>h.update({window:'interaction',window_revision:3}));
    fireEvent.click(screen.getByRole('button',{name:/OSCAR: Here/}));
    await waitFor(()=>expect(document.activeElement).toBe(screen.getByLabelText('Ask OSCAR')));
    expect((screen.getByLabelText('Ask OSCAR') as HTMLTextAreaElement).value).toBe('Unfinished draft');
    expect(screen.queryByRole('alert')).toBeNull();
  });
  it('native reinvocation cancels pending retreat even when the native window mode is already interaction',async()=>{
    vi.useFakeTimers();const h=harness();await act(async()=>{});
    fireEvent.click(screen.getByRole('button',{name:/OSCAR: Here/}));await act(async()=>{});
    fireEvent.change(screen.getByLabelText('Ask OSCAR'),{target:{value:'Retained'}});
    fireEvent.keyDown(screen.getByLabelText('Ask OSCAR'),{key:'Escape'});
    h.update({window:'interaction',window_revision:2});await act(async()=>{});
    await act(async()=>{vi.advanceTimersByTime(200);});
    expect(h.port.mock.calls.filter(([c])=>c.kind==='window'&&c.mode==='compact')).toHaveLength(0);
    expect(document.querySelector('.writing-leaf')?.getAttribute('aria-hidden')).toBe('false');
    expect(document.activeElement).toBe(screen.getByLabelText('Ask OSCAR'));
  });
  it('an obsolete retreat rejection cannot obscure a newer native invocation or its draft',async()=>{
    vi.useFakeTimers();const h=harness();await act(async()=>{});
    fireEvent.click(screen.getByRole('button',{name:/OSCAR: Here/}));await act(async()=>{});
    fireEvent.change(screen.getByLabelText('Ask OSCAR'),{target:{value:'Do not lose this'}});
    let reject:(reason:Error)=>void=()=>{};
    h.port.mockImplementationOnce(()=>new Promise<View>((_,no)=>{reject=no;}));
    fireEvent.keyDown(screen.getByLabelText('Ask OSCAR'),{key:'Escape'});
    await act(async()=>{vi.advanceTimersByTime(181);});
    h.update({window:'interaction',window_revision:2});await act(async()=>{});
    await act(async()=>reject(new Error('late native resize failure')));
    expect(screen.queryByRole('alert')).toBeNull();
    expect((screen.getByLabelText('Ask OSCAR') as HTMLTextAreaElement).value).toBe('Do not lose this');
    expect(document.activeElement).toBe(screen.getByLabelText('Ask OSCAR'));
  });
  it.each(['blocked','denied','unknown'] as const)('keeps specific %s feedback through polling and retreat without offering blind execution retry',async kind=>{
    const h=harness();await screen.findByText('Here');
    fireEvent.click(screen.getByRole('button',{name:/OSCAR: Here/}));
    await screen.findByRole('button',{name:'Return to presence'});
    fireEvent.change(screen.getByLabelText('Ask OSCAR'),{target:{value:'2 + 3'}});
    h.update({feedback:{kind,message:`Core ${kind} fixture`,observed_at_ms:Date.now()}});
    await screen.findByText(`Core ${kind} fixture`);
    expect(screen.queryByRole('button',{name:/^Ask /})).toBeNull();
    const before=h.port.mock.calls.filter(([c])=>c.kind==='interact').length;
    if(kind==='unknown')expect(screen.queryByRole('button',{name:'Edit request'})).toBeNull();
    else {
      if(kind==='blocked'){
        fireEvent.click(screen.getByRole('button',{name:/Check availability/}));
        await waitFor(()=>expect(h.port.mock.calls.length).toBeGreaterThan(2));
      }
      fireEvent.click(screen.getByRole('button',{name:'Edit request'}));
      expect((screen.getByLabelText('Ask OSCAR') as HTMLTextAreaElement).value).toBe('2 + 3');
      expect(screen.getByText(`Last request: Core ${kind} fixture`)).toBeTruthy();
    }
    expect(h.port.mock.calls.filter(([c])=>c.kind==='interact')).toHaveLength(before);
  });
  it('IPC failure reports uncertain outcome and exposes inspection instead of resubmission',async()=>{
    const h=harness();await screen.findByText('Here');
    fireEvent.click(screen.getByRole('button',{name:/OSCAR: Here/}));await screen.findByRole('button',{name:'Return to presence'});
    fireEvent.change(screen.getByLabelText('Ask OSCAR'),{target:{value:'2 + 3'}});
    h.port.mockRejectedValueOnce(new Error('IPC timeout'));
    fireEvent.keyDown(screen.getByLabelText('Ask OSCAR'),{key:'Enter'});
    await screen.findByText('Let’s check the outcome.');
    expect(screen.getByRole('button',{name:/Inspect Activity/})).toBeTruthy();
    expect(screen.queryByRole('button',{name:/^Ask /})).toBeNull();
  });
  it('a genuine window failure stays visible until native recovery and cannot clear a Core denial',async()=>{
    const h=harness();await screen.findByText('Here');
    fireEvent.click(screen.getByRole('button',{name:/OSCAR: Here/}));await screen.findByRole('button',{name:'Return to presence'});
    h.update({feedback:{kind:'denied',message:'Policy denies this request',observed_at_ms:Date.now()}});
    h.port.mockRejectedValueOnce(new Error('resize failed'));
    fireEvent.click(screen.getByRole('button',{name:'Return to presence'}));
    await screen.findByText('The window could not change size. Open it again or use the tray.');
    h.update({window:'interaction',window_revision:2});
    expect(screen.queryByText(/could not change size/)).toBeNull();
    expect(screen.getByText('Policy denies this request')).toBeTruthy();
  });
  it('review opens only the exact approval route and leaving it pending performs no decision',async()=>{
    const h=harness();await screen.findByText('Here');
    const current={task_id:'exact-approval',state:'planned',description:'Add 2 and 3',target:'fixture',blocker:null,actions:['approve','deny'],generation:1,evidence_ids:[],response:null,response_status:null,value:null,epistemic:null};
    h.update({current});fireEvent.click(screen.getByRole('button',{name:/OSCAR: Review needed/}));
    await screen.findByText('Your decision is needed.');
    fireEvent.click(screen.getByRole('button',{name:/Review decision/}));
    await waitFor(()=>expect(h.port).toHaveBeenCalledWith({kind:'review',task_id:'exact-approval',operation:'approve'}));
    expect(h.port.mock.calls.some(([c])=>c.kind==='confirm')).toBe(false);
    fireEvent.click(screen.getByRole('button',{name:'Leave pending'}));
    await waitFor(()=>expect(screen.getByRole('button',{name:/OSCAR: Review needed/}).getAttribute('aria-expanded')).toBe('false'));
    expect(h.port.mock.calls.some(([c])=>c.kind==='confirm')).toBe(false);
  });
  it('quotes only this surface’s submitted request bound to the actual returned task',async()=>{
    const h=harness();await screen.findByText('Here');
    fireEvent.click(screen.getByRole('button',{name:/OSCAR: Here/}));await screen.findByRole('button',{name:'Return to presence'});
    const current={task_id:'own',state:'planned',description:'Private interaction',target:'fixture',blocker:null,actions:['approve'],generation:1,evidence_ids:[],response:null,response_status:null,value:null,epistemic:null};
    h.port.mockImplementationOnce(async()=>h.update({current}));
    fireEvent.change(screen.getByLabelText('Ask OSCAR'),{target:{value:'2 + 3'}});
    fireEvent.keyDown(screen.getByLabelText('Ask OSCAR'),{key:'Enter'});
    await screen.findByText('Your submitted request');expect(screen.getByText('2 + 3')).toBeTruthy();
    h.update({current:{...current,task_id:'other',description:'Another surface request'}});
    await screen.findByText('Another surface request');expect(screen.queryByText('Your submitted request')).toBeNull();
  });
});
