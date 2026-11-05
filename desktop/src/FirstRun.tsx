import {useEffect,useRef,useState} from 'react';
import type {Command,View} from './bridge';
import {DesktopExpression} from './DesktopExpression';
import {ModelSettings} from './ModelSettings';
import './first-run.css';

export function FirstRun({view,busy,error,available,run,onClose}:{view:View;busy:boolean;error:string;available:boolean;run:(command:Command)=>Promise<boolean>;onClose:(prompt?:string)=>void}) {
  const saved=view.setup?.onboarding;
  const [step,setStep]=useState(saved?.step??0),[name,setName]=useState(saved?.preferred_name??'');
  const [tone,setTone]=useState(saved?.tone??'steady'),[muted,setMuted]=useState(saved?.muted??true);
  const [reduced,setReduced]=useState(saved?.reduced_motion??false);
  const [prompt,setPrompt]=useState('Explain one useful thing you can help me do on this computer.');
  const heading=useRef<HTMLHeadingElement>(null),audio=useRef<AudioContext|null>(null);
  useEffect(()=>{heading.current?.focus({preventScroll:true});},[step]);
  useEffect(()=>()=>{void audio.current?.close().catch(()=>{});},[]);
  function cue(){if(muted||typeof window.AudioContext==='undefined')return;try{const context=new AudioContext();audio.current=context;const note=context.createOscillator(),volume=context.createGain();note.type='sine';note.frequency.setValueAtTime(440,context.currentTime);note.frequency.exponentialRampToValueAtTime(660,context.currentTime+.12);volume.gain.setValueAtTime(.025,context.currentTime);volume.gain.exponentialRampToValueAtTime(.001,context.currentTime+.18);note.connect(volume);volume.connect(context.destination);note.start();note.stop(context.currentTime+.2);note.onended=()=>{void context.close().catch(()=>{});};}catch{/* Optional introduction audio never blocks first use. */}}
  async function save(next:number,completed=false,text?:string){
    if(!available){if(completed)onClose();return;}
    const ok=await run({kind:'configure_setup',section:'onboarding',value:{completed,step:next,preferred_name:name.trim(),tone,muted,reduced_motion:reduced}});
    if(ok){if(completed)onClose(text);else{setStep(next);cue();}}
  }
  const titles=['Oh. Hello.','What should I call you?','A mind of your choosing.','Let us try something real.'];
  return <main className="workspace first-run" data-reduced={reduced} aria-label="Meet OSCAR">
    <header className="first-run-top"><strong>OSCAR</strong><button disabled={busy} onClick={()=>void save(step,true)}>Skip introduction</button></header>
    <section className="first-run-scene" key={step}>
      <div className="first-run-figure"><DesktopExpression view={view} size={step===0?184:112} reducedMotion={reduced}/></div>
      <p className="first-run-eyebrow">{step+1} of 4 <span aria-hidden="true">/</span> {['A first encounter','Getting acquainted','Your intelligence','First magic'][step]}</p>
      <h1 ref={heading} tabIndex={-1}>{titles[step]}</h1>
      {step===0&&<><p className="first-run-lead">A little help. A little personality. One OSCAR, wherever you need me.</p><p className="first-run-state" role="status">{available?'Your Core is connected. We can take this at your pace.':'Your Core is not connected yet. You can explore, then retry in Workspace.'}</p></>}
      {step===1&&<div className="first-run-form"><label htmlFor="preferred-name">Your name, if you like</label><input id="preferred-name" autoComplete="given-name" value={name} maxLength={80} onChange={event=>setName(event.target.value)}/><fieldset><legend>A starting personality</legend><div className="first-run-tones">{[['steady','Steady','Clear, warm, unhurried.'],['spark','Spark','Curious, bright, playful.'],['wry','Wry','A little dry. Still on your side.']].map(([value,label,description])=><button type="button" key={value} aria-pressed={tone===value} onClick={()=>setTone(value)}><strong>{label}</strong><span>{description}</span></button>)}</div></fieldset><p>These preferences are saved to your Core. They change how OSCAR speaks, never what it may do.</p></div>}
      {step===2&&<div className="first-run-form"><ModelSettings view={view} busy={busy} run={run}/><p className="first-run-state" role="status">{view.models?.available.length?`${view.models.available.length} models currently eligible. A real response will verify the connection.`:'No eligible model yet. You can finish setup later; no answer will be invented.'}</p></div>}
      {step===3&&<div className="first-run-form"><p className="first-run-lead">Bring a question. Give me a small task. We will use the real Workspace and review any action together.</p><label htmlFor="first-request">Your first request</label><textarea id="first-request" value={prompt} maxLength={4096} rows={3} onChange={event=>setPrompt(event.target.value)}/><p>One conversation continues here. Connections, devices and permissions can wait until you need them.</p><button className="first-run-primary" disabled={busy||!available||!view.models?.available.length||!prompt.trim()} onClick={()=>void save(3,true,prompt)}>Ask OSCAR in Workspace</button></div>}
      {error&&<p className="first-run-error" role="alert">{error}</p>}
      <div className="first-run-actions">{step>0&&<button disabled={busy} onClick={()=>void save(step-1)}>Back</button>}{step<3?<button className="first-run-primary" disabled={busy||!available} onClick={()=>void save(step+1)}>{step===0?'Meet OSCAR':'Continue'}</button>:<button disabled={busy} onClick={()=>void save(3,true)}>Continue to Workspace</button>}</div>
    </section>
    <footer className="first-run-footer"><label><input type="checkbox" checked={reduced} onChange={event=>setReduced(event.target.checked)}/>Reduce motion</label><button aria-pressed={!muted} disabled={typeof window.AudioContext==='undefined'} onClick={()=>setMuted(value=>!value)}>Introduction sound: {muted?'off':'on'}</button><span>No microphone access requested here.</span></footer>
  </main>;
}
