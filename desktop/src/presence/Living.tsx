import {useEffect,useRef,useState} from 'react';
import {ExpressionPresence} from '@oscar/expression/react';
import type {ExpressionEvent,Source} from '@oscar/expression';
import {App} from '../App';
import {initialView,send,subscribe} from '../bridge';
import type {Command,Send,View,WindowMode} from '../bridge';
import {DesktopExpressionAdapter} from '../expression';
import {AskComposer} from './AskComposer';
import {ResultView} from './ResultView';
import {TaskStage} from './TaskStage';
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
  const [requestError,setRequestError]=useState('');
  const [editingFeedback,setEditingFeedback]=useState('');
  const [submitted,setSubmitted]=useState<{taskId:string;text:string}|null>(null);
  const [answerDismissed,setAnswerDismissed]=useState<string|null>(null);
  const lastFocused=useRef<HTMLElement|null>(null);
  const orb=useRef<HTMLButtonElement>(null);
  const retreatTimer=useRef<ReturnType<typeof setTimeout>|undefined>(undefined);
  const windowIntent=useRef(0),requestedWindow=useRef<WindowMode|null>(null),requests=useRef(0);
  const latest=useRef(initialView),activeAccent=useRef('');
  const presentationGeneration=useRef(0);
  const [presentation,setPresentation]=useState<ExpressionEvent|null>(null);
  const [gaze,setGaze]=useState({x:0,y:0});const pointerAt=useRef(0);
  function accept(next:View) {
    const accepted=adapter.current.receive(next,Date.now());
    if(!accepted)return false;
    const windowChanged=next.window!==latest.current.window||next.window_revision!==latest.current.window_revision;
    latest.current=next;setView(next);setEvent(accepted);setExpired(false);
    if(windowChanged){
      clearTimeout(retreatTimer.current);
      if(next.window==='interaction'&&requestedWindow.current==='compact'){windowIntent.current++;requestedWindow.current=null;}
      setOpen(next.window==='interaction'||next.window==='reading');setLeaving(false);setError('');
    }
    return true;
  }
  useEffect(()=>{let alive=true;let stop:(()=>void)|undefined;
    events(next=>{if(alive)accept(next);}).then(fn=>{if(alive)stop=fn;else fn();})
      .catch(()=>{if(alive)setRequestError('Native connection unavailable. Inspect the current state before sending.');});
    port({kind:'ready'}).then(next=>{if(alive)accept(next);})
      .catch(()=>{if(alive)setRequestError('Open the native presence prototype.');});
    return()=>{alive=false;stop?.();clearTimeout(retreatTimer.current);};
  },[port,events]);
  useEffect(()=>{if(!event)return;const timer=setTimeout(()=>setExpired(true),Math.max(1,event.expiresAt-Date.now()));return()=>clearTimeout(timer);},[event]);
  useEffect(()=>{if(!event)return;
    const quiet=event.operation==='attentive'&&event.kind==='state'&&!expired;
    const frame={...event,generation:++presentationGeneration.current,
      transitionId:quiet?`${event.transitionId}:${open?'invoked':hover?'hover':'rest'}`:event.transitionId,
      delivery:quiet?(open?'attentive':hover?'curious':'resting'):event.delivery} as ExpressionEvent;
    setPresentation(frame);
    // One existing engagement phrase per real executing transition; heartbeats never replay it.
    const key=`${event.source.id}:${event.transitionId}`;
    if(!expired&&event.operation==='executing'&&!event.muted&&event.attention==='none'&&event.kind==='state'&&activeAccent.current!==key){
      const timer=setTimeout(()=>{
        if(Date.now()>=frame.expiresAt)return;
        activeAccent.current=key;
        setPresentation({...frame,generation:++presentationGeneration.current,kind:'accent',accent:'engagement'});
      },70);
      return()=>clearTimeout(timer);
    }
  },[event,open,hover,expired]);
  function focusInput(){document.getElementById('presence-ask')?.focus();}
  useEffect(()=>{if(open&&!leaving&&view.window==='interaction')focusInput();},[open,leaving,view.window,view.window_revision]);
  const available=!expired&&event?.availability==='available'&&event.operation!=='unknown';
  const operation=expired?'unknown':event?.operation??'unavailable';
  const owner=available&&event?.attention==='owner';
  const feedback=!expired?(view.feedback??(requestError?{kind:'unknown' as const,message:requestError,observed_at_ms:0}:null)):null;
  const feedbackKey=feedback?`${view.expression?.epoch}:${feedback.kind}:${feedback.observed_at_ms}`:'';
  const editing=feedbackKey!==''&&editingFeedback===feedbackKey;
  const pending=(view.current?.actions.includes('approve')?view.current:null)??view.tasks.find(t=>t.actions.includes('approve'));
  const task=(view.current&&!terminal.includes(view.current.state)?view.current:null)??view.tasks.find(t=>!terminal.includes(t.state))??view.current;
  const label=owner?'Review needed':view.link==='online'&&feedback?feedback.kind==='denied'?'Permission denied':feedback.kind==='unknown'?'Check outcome':'Request blocked':available&&operation==='attentive'&&view.voice==='interrupted'?'Interrupted':labels[operation]??'State unknown';
  const workspace=view.window==='activity'||view.window==='approval';
  const answer=!editing&&available&&task&&['verified','partially_verified'].includes(task.state)&&answerDismissed!==task.task_id&&(task.value??task.response);
  const headline=owner?'Your decision is needed.':editing?'Revise your request.':view.link==='online'&&feedback?feedback.kind==='denied'?'This request isn’t permitted.':feedback.kind==='unknown'?'Let’s check the outcome.':feedback.kind==='blocked'?'This request didn’t start.':'Core rejected this request.':operation==='unknown'?'Let’s check the state.':!available?'Connection paused.':operation==='error'?'Something stopped.':
    task?.state==='blocked'?'Work is blocked.':operation==='waiting'?'Waiting.':operation==='processing'?'Processing.':operation==='verifying'?'Checking the result.':operation==='executing'?'I’m on it.':
    operation==='listening'?'Listening.':operation==='speaking'?'Speaking.':answer?'Here’s the result.':'What’s on your mind?';
  useEffect(()=>{const focused=lastFocused.current;
    if(open&&!workspace&&focused&&!focused.isConnected&&document.activeElement===document.body)orb.current?.focus();
  },[operation,owner,answer,open,workspace]);
  async function run(command:Command) {
    const intent=command.kind==='window'?++windowIntent.current:0;
    if(command.kind==='window')requestedWindow.current=command.mode;
    requests.current++;setBusy(true);
    try {
      const next=await port(command),accepted=accept(next);
      if(command.kind==='window'){
        if(intent!==windowIntent.current)return true;
        const current=latest.current;
        // An emitted snapshot may have consumed this reply already. Rejection by the expression fence is not resize failure.
        const confirmed=next.window===command.mode&&current.window===command.mode&&
          next.expression?.epoch===current.expression?.epoch&&current.expression!==null&&next.expression!==null&&
          current.expression.generation>=next.expression.generation;
        if(confirmed){setError('');return true;}
        if(accepted)setError('The window did not reach the requested size. Open it again or use the tray.');
        return false;
      }
      if(accepted&&command.kind==='interact'&&!next.feedback)setRequestError('');
      if(command.kind==='interact'&&next.current&&next.current.task_id===latest.current.current?.task_id&&
        next.expression&&latest.current.expression&&next.expression.epoch===latest.current.expression.epoch&&
        next.expression.generation<=latest.current.expression.generation){
        setSubmitted({taskId:next.current.task_id,text:command.text});
        if(!next.feedback)setRequestError('');
        return true;
      }
      return accepted;
    }
    catch {
      if(command.kind==='window'){
        if(intent!==windowIntent.current)return true;
        setError('The window could not change size. Open it again or use the tray.');
      }else setRequestError('The request outcome is unknown. Inspect Activity before sending it again.');
      return false;
    }
    finally {requests.current--;setBusy(requests.current>0);}
  }
  function invoke() {clearTimeout(retreatTimer.current);setLeaving(false);void run({kind:'window',mode:'interaction'});}
  function retreat() {
    if(!open||leaving)return;requestedWindow.current='compact';setLeaving(true);orb.current?.focus();
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
    setEditingFeedback('');
    const previous=latest.current.current?.task_id;
    const ok=await run({kind:'interact',mode:'Ask',text:draft,context_id:view.context?.id??''});
    if(ok&&!latest.current.feedback&&latest.current.current?.task_id&&latest.current.current.task_id!==previous)setDraft('');
  }
  function track(e:React.PointerEvent<HTMLButtonElement>) {
    if(Date.now()-pointerAt.current<90)return;pointerAt.current=Date.now();
    const box=e.currentTarget.getBoundingClientRect();
    setGaze({x:Math.max(-10,Math.min(10,(e.clientX-box.left-box.width/2)/3)),y:Math.max(-7,Math.min(7,(e.clientY-box.top-box.height/2)/4))});
  }
  return <main className={`living-presence ${open?'is-open':''} ${leaving?'is-leaving':''} ${workspace?'has-workspace':''} ${view.window==='reading'?'reading-response':''}`}
    data-operation={operation} data-attention={owner?'owner':'none'} onFocusCapture={e=>{lastFocused.current=e.target as HTMLElement;}}
    onBlurCapture={e=>{if(e.relatedTarget&&!e.currentTarget.contains(e.relatedTarget as Node))lastFocused.current=null;}}
    onKeyDown={e=>{if(e.key==='Escape'&&workspace){e.preventDefault();void run({kind:'window',mode:'compact'});}}}>
    {workspace?<div className="living-workspace"><button className="workspace-return" onClick={()=>run({kind:'window',mode:'interaction'})}>Back to presence</button>{feedback&&<p className="workspace-feedback" role="alert">{feedback.message}</p>}<App port={port} events={events} expressionKind={sourceKind} focusReview/></div>:<>
      <div className="writing-leaf" inert={!open||leaving} aria-hidden={!open||leaving}>
        <div className="leaf-top" data-tauri-drag-region><span data-tauri-drag-region>OSCAR</span>
          <details className="presence-settings"><summary>Presence</summary><div><button aria-pressed={pinned} onClick={()=>native(pinned?'float':'pin')}>{pinned?'Unpin':'Pin on top'}</button><button onClick={()=>native('edge')}>To screen edge</button><button onClick={()=>native('hide')}>Hide to tray</button></div></details>
          <button onClick={retreat} aria-label="Return to presence">Back</button></div>
        <h1>{headline}</h1>
        {owner?<div className="attention-copy">{submitted?.taskId===pending?.task_id?<><p className="leaf-secondary">Your submitted request</p><p className="review-description submitted-request">{submitted!.text}</p></>:<p className="review-description">{pending?.description??'A task requires your review.'}</p>}<p className="leaf-secondary">Your approval is required before this task can run. Review the full details before deciding; opening review grants nothing.</p>
          <div className="leaf-actions"><button className="leaf-primary" disabled={busy||!pending} onClick={()=>pending&&run({kind:'review',task_id:pending.task_id,operation:'approve'})}>Review decision <Arrow/></button><button onClick={retreat}>Leave pending</button>
          </div></div>:
        view.link==='online'&&feedback&&!editing?<div className="attention-copy request-feedback" role="alert"><p>{feedback.message}</p>
          <p className="leaf-secondary">{feedback.kind==='unknown'?'An uncertain outcome is never retried automatically. Inspect Activity first.':feedback.kind==='denied'?'Review the permission or policy in Activity. Repeating the request will not grant access.':'Check capability availability before submitting again. Your draft is preserved.'}</p>
          <div className="leaf-actions"><button className="leaf-primary" disabled={busy} onClick={()=>run(feedback.kind==='blocked'?{kind:'refresh'}:{kind:'window',mode:'activity'})}>{feedback.kind==='blocked'?'Check availability':'Inspect Activity'} <Arrow/></button>
          {['blocked','denied'].includes(feedback.kind)&&<button disabled={busy} onClick={()=>{setEditingFeedback(feedbackKey);requestAnimationFrame(focusInput);}}>Edit request</button>}</div></div>:
        !available?<div className="attention-copy"><p>{operation==='unknown'?(expired?'The last observation expired. Check Core for current activity.':'Core reports an unresolved state. Inspect it before continuing.'):'Core is unavailable. Work status is unknown; new requests are disabled.'}</p>
          <button className="leaf-primary" disabled={busy} onClick={()=>run({kind:'refresh'})}>Check connection <Arrow/></button></div>:
        task&&(!terminal.includes(task.state)||task.state==='failed')?<TaskStage task={task} busy={busy} run={run}/>:
        answer?<ResultView task={task!} expanded={view.window==='reading'}
          read={()=>void run({kind:'window',mode:'reading'})} inspect={()=>void run({kind:'window',mode:'activity'})}
          askAgain={()=>{setAnswerDismissed(task!.task_id);void run({kind:'window',mode:'interaction'}).then(()=>requestAnimationFrame(focusInput));}}/>:
        <AskComposer draft={draft} setDraft={setDraft} disabled={busy||!available} submit={()=>void ask()}/>}
        {error&&<p className="leaf-error" role="alert">{error}</p>}
        {editing&&feedback&&<p className="leaf-error" role="status">Last request: {feedback.message}</p>}
        {requestError&&!feedback&&<p className="leaf-error" role="alert">{requestError}</p>}
        {owner&&feedback&&<p className="leaf-error" role="alert">{feedback.message}</p>}
        {!error&&view.context&&<p className="leaf-secondary">Attached: {view.context.source}. Review in workspace.</p>}
        <div className="leaf-bottom"><button onClick={()=>run({kind:'window',mode:'activity'})}>Activity <Arrow/></button><span>{view.reference?'Reference Core':'No background capture'}</span></div>
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
