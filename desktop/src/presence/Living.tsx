import {useEffect,useRef,useState} from 'react';
import {ExpressionPresence} from '@oscar/expression/react';
import type {ExpressionEvent,Source} from '@oscar/expression';
import {App} from '../App';
import {initialView,send,subscribe,statuses} from '../bridge';
import type {Command,Send,View} from '../bridge';
import {DesktopExpressionAdapter} from '../expression';
import './living.css';

export type PresenceAction='hide'|'pin'|'float'|'edge';
export async function nativePresence(action:PresenceAction) {
  const {invoke}=await import('@tauri-apps/api/core');
  await invoke('presence_window',{action});
}
const labels:Record<string,string>={attentive:'Here',idle:'Here',processing:'Processing',executing:'Working',
  verifying:'Verifying',waiting:'Waiting',speaking:'Speaking',listening:'Listening',muted:'Muted',
  unavailable:'Offline',error:'Task failed',unknown:'State unknown'};
const terminal=['verified','partially_verified','failed','cancelled'];

// Presentation accepts the same fenced readback as the shared character, including text/action freshness.
export function LivingPresence({port=send,events=subscribe,sourceKind='core',windowAction=nativePresence}:
  {port?:Send;events?:typeof subscribe;sourceKind?:Source['kind'];windowAction?:(action:PresenceAction)=>Promise<void>}) {
  const adapter=useRef(new DesktopExpressionAdapter(sourceKind));
  const [view,setView]=useState(initialView),[event,setEvent]=useState<ExpressionEvent|null>(null);
  const [expired,setExpired]=useState(true),[open,setOpen]=useState(false),[leaving,setLeaving]=useState(false);
  const [hover,setHover]=useState(false),[draft,setDraft]=useState(''),[busy,setBusy]=useState(false);
  const [error,setError]=useState(''),[pinned,setPinned]=useState(false);
  const [answerDismissed,setAnswerDismissed]=useState<string|null>(null);
  const lastFocused=useRef<HTMLElement|null>(null);
  const orb=useRef<HTMLButtonElement>(null),input=useRef<HTMLTextAreaElement>(null);
  const retreatTimer=useRef<ReturnType<typeof setTimeout>|undefined>(undefined);
  const presentationGeneration=useRef(0);
  const lastWindow=useRef(initialView.window);
  const [presentation,setPresentation]=useState<ExpressionEvent|null>(null);
  const [gaze,setGaze]=useState({x:0,y:0});const pointerAt=useRef(0);
  function accept(next:View) {
    const accepted=adapter.current.receive(next,Date.now());
    if(!accepted)return false;
    setView(next);setEvent(accepted);setExpired(false);
    if(next.window!==lastWindow.current){setOpen(next.window==='interaction');setLeaving(false);lastWindow.current=next.window;}
    return true;
  }
  useEffect(()=>{let alive=true;let stop:(()=>void)|undefined;
    events(next=>{if(alive)accept(next);}).then(fn=>{if(alive)stop=fn;else fn();})
      .catch(()=>{if(alive)setError('Native connection unavailable.');});
    port({kind:'ready'}).then(next=>{if(alive)accept(next);})
      .catch(()=>{if(alive)setError('Open the native presence prototype.');});
    return()=>{alive=false;stop?.();clearTimeout(retreatTimer.current);};
  },[port,events]);
  useEffect(()=>{if(!event)return;const timer=setTimeout(()=>setExpired(true),Math.max(1,event.expiresAt-Date.now()));return()=>clearTimeout(timer);},[event]);
  useEffect(()=>{if(!event)return;
    const quiet=event.operation==='attentive'&&event.kind==='state'&&!expired;
    setPresentation({...event,generation:++presentationGeneration.current,
      transitionId:quiet?`${event.transitionId}:${open?'invoked':hover?'hover':'rest'}`:event.transitionId,
      delivery:quiet?(open?'attentive':hover?'curious':'resting'):event.delivery});
  },[event,open,hover,expired]);
  useEffect(()=>{if(open&&!leaving&&view.window==='interaction')input.current?.focus();},[open,leaving,view.window]);
  const available=!expired&&event?.availability==='available'&&event.operation!=='unknown';
  const operation=expired?'unknown':event?.operation??'unavailable';
  const owner=available&&event?.attention==='owner';
  const pending=view.tasks.find(t=>t.actions.includes('approve'))??view.current;
  const task=(view.current&&!terminal.includes(view.current.state)?view.current:null)??view.tasks.find(t=>!terminal.includes(t.state))??view.current;
  const label=owner?'Review needed':available&&operation==='attentive'&&view.voice==='interrupted'?'Interrupted':labels[operation]??'State unknown';
  const workspace=view.window==='activity'||view.window==='approval';
  const answer=available&&task&&['verified','partially_verified'].includes(task.state)&&answerDismissed!==task.task_id&&(task.value??task.response);
  const headline=owner?'A decision for you.':operation==='unknown'?'Let’s check the state.':!available?'Connection paused.':operation==='error'?'Something stopped.':
    task?.state==='blocked'?'Work is blocked.':operation==='waiting'?'Waiting.':operation==='processing'?'Processing.':operation==='verifying'?'Checking the result.':operation==='executing'?'I’m on it.':
    operation==='listening'?'Listening.':operation==='speaking'?'Speaking.':answer?'Here’s the result.':'What’s on your mind?';
  useEffect(()=>{const focused=lastFocused.current;
    if(open&&!workspace&&focused&&!focused.isConnected&&document.activeElement===document.body)orb.current?.focus();
  },[operation,owner,answer,open,workspace]);
  async function run(command:Command) {
    setBusy(true);setError('');
    try {const accepted=accept(await port(command));if(!accepted&&command.kind==='window')setError('Window confirmation expired. Try opening the presence again.');return accepted;}
    catch {setError('Request unavailable. Inspect Core before retrying.');return false;}
    finally {setBusy(false);}
  }
  function invoke() {clearTimeout(retreatTimer.current);setLeaving(false);void run({kind:'window',mode:'interaction'});}
  function retreat() {
    if(!open||leaving)return;setLeaving(true);orb.current?.focus();
    const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
    retreatTimer.current=setTimeout(()=>{void run({kind:'window',mode:'compact'}).then(ok=>{if(!ok)setLeaving(false);});},reduced?0:180);
  }
  useEffect(()=>{const escape=(e:KeyboardEvent)=>{if(e.key==='Escape'&&open){e.preventDefault();retreat();}};
    const blur=()=>{lastFocused.current=null;};window.addEventListener('keydown',escape);window.addEventListener('blur',blur);
    return()=>{window.removeEventListener('keydown',escape);window.removeEventListener('blur',blur);};
  },[open,leaving]);
  async function native(action:PresenceAction) {
    try {await windowAction(action);if(action==='pin'||action==='float')setPinned(action==='pin');}
    catch {setError('Window action unavailable. Use the native tray to recover.');}
  }
  async function ask() {
    if(!available||busy||!draft.trim())return;
    await run({kind:'interact',mode:'Ask',text:draft,context_id:view.context?.id??''});
  }
  function track(e:React.PointerEvent<HTMLButtonElement>) {
    if(Date.now()-pointerAt.current<90)return;pointerAt.current=Date.now();
    const box=e.currentTarget.getBoundingClientRect();
    setGaze({x:Math.max(-10,Math.min(10,(e.clientX-box.left-box.width/2)/3)),y:Math.max(-7,Math.min(7,(e.clientY-box.top-box.height/2)/4))});
  }
  return <main className={`living-presence ${open?'is-open':''} ${leaving?'is-leaving':''} ${workspace?'has-workspace':''}`}
    data-operation={operation} data-attention={owner?'owner':'none'} onFocusCapture={e=>{lastFocused.current=e.target as HTMLElement;}}
    onBlurCapture={e=>{if(e.relatedTarget&&!e.currentTarget.contains(e.relatedTarget as Node))lastFocused.current=null;}}
    onKeyDown={e=>{if(e.key==='Escape'&&workspace){e.preventDefault();void run({kind:'window',mode:'compact'});}}}>
    {workspace?<div className="living-workspace"><App port={port} events={events} expressionKind={sourceKind}/></div>:<>
      <div className="writing-leaf" inert={!open||leaving} aria-hidden={!open||leaving}>
        <div className="leaf-top" data-tauri-drag-region><span data-tauri-drag-region>OSCAR</span>
          <details className="presence-settings"><summary>Presence</summary><div><button aria-pressed={pinned} onClick={()=>native(pinned?'float':'pin')}>{pinned?'Unpin':'Pin on top'}</button><button onClick={()=>native('edge')}>To screen edge</button><button onClick={()=>native('hide')}>Hide to tray</button></div></details>
          <button onClick={retreat} aria-label="Return to presence">Close</button></div>
        <h1>{headline}</h1>
        {owner?<div className="attention-copy"><p>{pending?.description??'A task requires your review.'}</p><p className="leaf-secondary">Nothing is approved by opening this surface.</p>
          <button className="leaf-primary" disabled={busy||!pending} onClick={()=>pending&&run({kind:'review',task_id:pending.task_id,operation:'approve'})}>Review decision <Arrow/></button></div>:
        !available?<div className="attention-copy"><p>{operation==='unknown'?(expired?'The last observation expired. Check Core for current activity.':'Core reports an unresolved state. Inspect it before continuing.'):'Core is unavailable. Work status is unknown; new requests are disabled.'}</p>
          <button className="leaf-primary" disabled={busy} onClick={()=>run({kind:'refresh'})}>Check connection <Arrow/></button></div>:
        task&&(!terminal.includes(task.state)||task.state==='failed')?<div className="attention-copy"><p>{task.blocker??task.description}</p><p className="leaf-secondary">{task.state==='planned'?'Waiting':statuses[task.state]??'Unknown outcome'} · {task.evidence_ids.length} evidence references</p>
          <button className="leaf-primary" onClick={()=>run({kind:'window',mode:'activity'})}>Inspect work <Arrow/></button></div>:
        answer?<div className="presence-answer"><p className="leaf-secondary">{task!.epistemic??task!.response_status??(task!.state==='verified'?'VERIFIED':'PARTIALLY VERIFIED')}</p><pre>{answer}</pre>
          <div><button onClick={()=>run({kind:'window',mode:'activity'})}>Inspect result</button><button onClick={()=>{setAnswerDismissed(task!.task_id);requestAnimationFrame(()=>input.current?.focus());}}>Ask again</button></div></div>:
        <form onSubmit={e=>{e.preventDefault();void ask();}}><label className="input-label" htmlFor="presence-ask">Ask OSCAR</label>
          <textarea id="presence-ask" ref={input} value={draft} maxLength={4096} placeholder="A thought, a question, a next step…"
            onChange={e=>setDraft(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();void ask();}}}/>
          <div className="leaf-submit"><span className="leaf-secondary">Enter to ask · Shift + Enter for a line</span><button type="submit" className="leaf-primary" disabled={busy||!draft.trim()}>Ask <Arrow/></button></div>
        </form>}
        {error&&<p className="leaf-error" role="alert">{error}</p>}
        {!error&&view.context&&<p className="leaf-secondary">Attached: {view.context.source}. Review in workspace.</p>}
        <div className="leaf-bottom"><button onClick={()=>run({kind:'window',mode:'activity'})}>Open workspace</button><span>{view.reference?'Reference Core':'No background capture'}</span></div>
      </div>
      <div className="presence-object">
        <button className="character-button" ref={orb} aria-label={`OSCAR: ${label}. ${open?'Return to presence':'Open interaction'}`} aria-expanded={open}
          onClick={open&&!leaving?retreat:invoke} onPointerEnter={()=>setHover(true)} onPointerMove={track}
          onPointerLeave={()=>{setHover(false);setGaze({x:0,y:0});}}>
          {presentation?<ExpressionPresence event={presentation} source={presentation.source} size={76} gaze={gaze}/>:<span className="unconfigured-mark">OSCAR</span>}
        </button>
        <p className="presence-caption" role="status" aria-live="polite">{label}</p>
      </div>
      {!open&&error&&<p className="compact-error" role="alert">Connection unavailable</p>}
    </>}
  </main>;
}
function Arrow(){return <svg aria-hidden="true" viewBox="0 0 16 16" width="16" height="16"><path d="M3 8h9M8 3l5 5-5 5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>;}
export function Living() {
  const preview=new URLSearchParams(location.search).get('living')==='preview';
  if(preview)return <Preview/>;
  return <LivingPresence/>;
}
function Preview() {
  const [fixture,setFixture]=useState('rest');const callback=useRef<(view:View)=>void>(()=>{});
  const revision=useRef(0),current=useRef(initialView);
  function fixtureView(state:string):View {
    const now=Date.now(),work=['working','approval','processing','error','unknown'].includes(state);
    const task=work?{task_id:'synthetic-task',state:state==='working'?'executing':state==='approval'?'planned':state==='error'?'failed':state==='unknown'?'unknown':'result_received',description:'Inspect the disposable workspace',target:'fixture-worker',blocker:null,actions:state==='approval'?['approve']:[],generation:1,evidence_ids:[],response:null,response_status:null,value:null,epistemic:null}:null;
    return {...initialView,window:current.current.window,link:state==='offline'?'unavailable':'online',reference:true,current:task,
      voice:['speaking','listening','interrupted'].includes(state)?state:'idle',
      expression:{epoch:'f'.repeat(32),generation:++revision.current,observed_at_ms:now,voice_observed_at_ms:now,tasks_observed_at_ms:now,current_observed_at_ms:now}};
  }
  const events=useRef<typeof subscribe>(async fn=>{callback.current=fn;return()=>{callback.current=()=>{};};}).current;
  const port=useRef<Send>(async command=>{
    if(command.kind==='window')current.current={...current.current,window:command.mode};
    else if(!['ready','refresh'].includes(command.kind))throw new Error('Synthetic preview cannot execute or approve.');
    current.current={...current.current,expression:{...current.current.expression!,generation:++revision.current,observed_at_ms:Date.now(),tasks_observed_at_ms:Date.now(),current_observed_at_ms:Date.now()}};
    return current.current;
  }).current;
  useEffect(()=>{current.current=fixtureView(fixture);callback.current(current.current);
    const timer=setInterval(()=>{current.current=fixtureView(fixture);callback.current(current.current);},2000);
    return()=>clearInterval(timer);
  },[fixture]);
  return <><aside className="preview-controls"><strong>Synthetic preview · no execution or audio</strong>
    <label>State<select aria-label="Preview state" value={fixture} onChange={e=>setFixture(e.target.value)}>{['rest','processing','working','approval','speaking','listening','interrupted','offline','error','unknown'].map(value=><option key={value}>{value}</option>)}</select></label></aside>
    <LivingPresence port={port} events={events} sourceKind="fixture" windowAction={async()=>{throw new Error('Preview has no native window');}}/></>;
}
