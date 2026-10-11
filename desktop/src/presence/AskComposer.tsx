import type {KeyboardEvent} from 'react';

export function AskComposer({draft,setDraft,disabled,submit}:{draft:string;setDraft:(text:string)=>void;disabled:boolean;submit:()=>void}) {
  function key(e:KeyboardEvent<HTMLTextAreaElement>) {
    if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();submit();}
  }
  return <form className="ask-composer" onSubmit={e=>{e.preventDefault();submit();}}>
    <label className="input-label" htmlFor="presence-ask">Ask OSCAR</label>
    <textarea id="presence-ask" value={draft} maxLength={4096} placeholder="A thought, a question, a next step…"
      onChange={e=>setDraft(e.target.value)} onKeyDown={key}/>
    <div className="leaf-submit"><span className="leaf-secondary">Enter to ask · Shift + Enter for a line</span>
      <button type="submit" className="leaf-primary" disabled={disabled||!draft.trim()}>Ask <Arrow/></button></div>
  </form>;
}
export function Arrow(){return <svg aria-hidden="true" viewBox="0 0 16 16" width="16" height="16"><path d="M3 8h9M8 3l5 5-5 5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>;}
