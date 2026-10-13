import {Choice,Disclosure} from '../UIControls';
import {useEffect,useRef,useState} from 'react';
import {epistemicLabel} from '../bridge';
import type {Command,ContextChoice,View} from '../bridge';

export type TextMode='Dictate'|'Edit';
export function TextTools({view,available,busy,mode,setMode,draft,setDraft,run,discard,reviewOnly=false,useInMessage}:{reviewOnly?:boolean;useInMessage?:(text:string)=>Promise<void>;view:View;available:boolean;busy:boolean;mode:TextMode;setMode:(mode:TextMode)=>void;draft:string;setDraft:(text:string)=>void;run:(command:Command)=>Promise<boolean>;discard:()=>void}) {
  const source=view.capture_choice??'none';
  const [destination,setDestination]=useState('surface');
  const [clock,setClock]=useState(Date.now());
  const lastPreview=useRef('');const input=useRef<HTMLTextAreaElement>(null);
  const preview=view.preview&&(!view.preview.mode||view.preview.mode===mode)?view.preview:null;
  const context=view.context;
  const fresh=!!context&&context.permission==='granted'&&context.freshness==='fresh'&&
    typeof context.expires_at==='number'&&Number.isFinite(context.expires_at)&&context.expires_at*1000>clock;
  const editable=fresh&&['selection','focused'].includes(context!.source)&&context!.text!==null;
  const activeVoice=['listening','processing'].includes(view.voice);
  const expired=!preview||!Number.isFinite(preview.expires)||preview.expires*1000<=clock;
  useEffect(()=>{input.current?.focus();},[mode]);
  useEffect(()=>{const times=[context?.expires_at,preview?.expires].filter((n):n is number=>typeof n==='number'&&Number.isFinite(n)&&n*1000>Date.now());
    if(!times.length)return;const timer=setTimeout(()=>setClock(Date.now()),Math.max(1,Math.min(...times)*1000-Date.now()+1));return()=>clearTimeout(timer);
  },[context?.id,context?.expires_at,preview?.preview_id,preview?.expires,clock]);
  useEffect(()=>{if(preview&&preview.preview_id!==lastPreview.current){lastPreview.current=preview.preview_id;setDestination('surface');if(mode==='Dictate')setDraft(preview.after);}},[preview?.preview_id,mode]);
  const validDestination=preview?.destinations.includes(destination)?destination:'surface';
  const focused=validDestination==='focused';
  const before=focused?preview?.focused_before:preview?.before;
  const after=focused?preview?.focused_after:preview?.after;
  const canApply=available&&!busy&&!view.feedback&&!expired&&!activeVoice&&!!preview?.destinations.includes(validDestination)&&
    (!focused||(fresh&&typeof after==='string'&&typeof before==='string'));
  const editTask=view.current?.mode==='Edit'&&['verified','partially_verified'].includes(view.current.state)&&view.current.response;
  function submit(){if(available&&!busy&&!activeVoice&&draft.trim()&&(mode==='Dictate'||editable))void run({kind:'interact',mode,text:draft,context_id:context?.id??''});}
  function switchMode(next:TextMode){if(activeVoice)void run({kind:'voice_cancel'});setMode(next);}
  return <div className="text-tools">
    {!reviewOnly&&<><div role="tablist" aria-label="Text tools" className="text-mode-tabs">{(['Dictate','Edit'] as const).map(item=><button
      key={item} id={`tool-${item}`} role="tab" aria-selected={mode===item} aria-controls={`panel-${item}`} tabIndex={mode===item?0:-1}
      onClick={()=>switchMode(item)} onKeyDown={e=>{if(['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();switchMode(mode==='Dictate'?'Edit':'Dictate');requestAnimationFrame(()=>document.getElementById(`tool-${mode==='Dictate'?'Edit':'Dictate'}`)?.focus());}}}>{item}</button>)}</div>
    </>}<section role={reviewOnly?undefined:"tabpanel"} id={`panel-${mode}`} aria-labelledby={reviewOnly?undefined:`tool-${mode}`}>
      {!reviewOnly&&<><Disclosure className="context-details" title={<>{context?`${context.source} context · ${fresh?'fresh':'recapture required'}`:'Context · none attached'}</>}>
        {context&&<><p>{context.scope} · {context.provenance}</p><p>{context.permission} · {context.retained?'saved':'not saved'} · observed {new Date(context.timestamp*1000).toLocaleTimeString()}</p><pre>{context.text}</pre></>}
        <label>Capture on invocation<Choice label="Capture on invocation" value={source} onChange={value=>void run({kind:'capture_choice',source:value as ContextChoice})} options={[{value:'none',label:'No capture'},{value:'selection',label:'Selected text'},{value:'focused',label:'Focused field'},{value:'foreground',label:'Window identity'}]}/></label>
        <p className="leaf-secondary">Focus the intended application, then invoke OSCAR. Unregistered, password or inaccessible content remains unavailable.</p>
        <button disabled={busy||!available||source==='none'} onClick={()=>run({kind:'capture',source})}>Capture supported context</button>
        <button onClick={discard}>Discard private drafts and context</button>
        <p className="leaf-secondary">Clearing drafts leaves active tasks running. Review a task in Activity to cancel it.</p>
      </Disclosure>
      {mode==='Dictate'&&<div className="voice-controls"><p role="status" aria-live="polite">{view.voice==='listening'?'Listening — explicit capture active.':view.voice==='processing'?'Finalizing dictation.':view.voice==='cancelled'?'Dictation cancelled.':'Dictation capture starts only on your request.'}</p>
        {activeVoice?<><button disabled={busy||view.voice==='processing'} onClick={()=>run({kind:'voice_stop'})}>Finish dictation</button><button onClick={()=>run({kind:'voice_cancel'})}>Cancel dictation</button></>:<button disabled={busy||!available} onClick={()=>run({kind:'voice_start',context_id:context?.id??''})}>Start dictation</button>}</div>}
      <label htmlFor="text-tool-draft">{mode==='Dictate'?'Dictation draft':'Transformation instruction'}</label>
      <textarea ref={input} id="text-tool-draft" maxLength={4096} value={draft} onChange={e=>setDraft(e.target.value)}
        onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();submit();}}}/>
      {mode==='Edit'&&!editable&&<p className="leaf-secondary">Capture fresh selected text or a focused field before requesting an edit.</p>}
      <button className="leaf-primary" disabled={!available||busy||activeVoice||!draft.trim()||(mode==='Edit'&&!editable)} onClick={submit}>{mode==='Dictate'?'Preview text':'Request transformation'}</button>
      </>}{editTask&&!preview&&<button disabled={!available||busy} onClick={()=>run({kind:'preview',task_id:view.current!.task_id})}>Review suggested text</button>}
      {preview&&<section className="text-preview" aria-label="Review text preview"><h2>Review before applying</h2>
        <p className="leaf-secondary">{reviewOnly?epistemicLabel(preview.epistemic):preview.epistemic} text · {expired?'Preview expired — create a fresh preview.':'Preview is time limited.'}</p>
        <label>Destination<Choice label="Destination" value={validDestination} onChange={setDestination} options={preview.destinations.map(item=>({value:item,label:item==='surface'?'OSCAR only':item==='focused'?'Selected app field':'Clipboard'}))}/></label>
        <h3>{reviewOnly?'Original text':focused?'Captured field before':'Source text'}</h3><pre>{before??'No source text'}</pre>
        <h3>{reviewOnly?'Suggested text':focused?'Complete field after':'Reviewed text'}</h3><pre>{after??'Reliable replacement is unavailable'}</pre>
        <p className="leaf-secondary">{focused?'OSCAR will check that this field has not changed before replacing it.':validDestination==='clipboard'?'You’ll review this before it goes to the clipboard.':'No other application changes.'}</p>
        <button className="leaf-primary" disabled={!canApply} onClick={()=>useInMessage&&validDestination==='surface'?useInMessage(preview.after):run({kind:'apply',preview_id:preview.preview_id,destination:validDestination as 'surface'|'focused'|'clipboard'})}>{useInMessage&&validDestination==='surface'?'Use in message':'Apply reviewed text'}</button>
      </section>}
      {view.feedback&&!reviewOnly&&<p className="leaf-error" role="alert">{view.feedback.message} Inspect the outcome before resubmitting.</p>}
      {!reviewOnly&&view.message&&!view.feedback&&<p className="text-receipt" role="status">{view.message}</p>}
    </section>
  </div>;
}
