import {useEffect,useRef,useState} from 'react';
import sourceOrb from '../../../assets/brand/oscar-orb.svg';
import {Orb} from './Orb';
import {arbitrate,canonical,clear,defaults,deliveries,disclosure,neutral,operations,poseFor,sample,sequences,study,velocityAt,vocabulary,zeroVelocity} from './model';
import type {Constraints,Delivery,Operation,Pose,Scene,Settings,Study} from './model';

const sizes=[32,48,64,96,128,192];
function useReducedMotion() {
  const [system,setSystem]=useState(()=>matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(()=>{const media=matchMedia('(prefers-reduced-motion: reduce)');const update=()=>setSystem(media.matches);media.addEventListener('change',update);return()=>media.removeEventListener('change',update);},[]);
  return system;
}

export function Lab() {
  const [boundary,setBoundary]=useState<Constraints>(clear);
  const [settings,setSettings]=useState<Settings>(defaults);
  const [timeline,setTimeline]=useState<Study>(()=>study(canonical,neutral));
  const [time,setTime]=useState(1800);
  const [playing,setPlaying]=useState(false);
  const [speed,setSpeed]=useState(1);
  const [reduce,setReduce]=useState(false);
  const systemReduced=useReducedMotion(), reduced=reduce||systemReduced;
  const [sequence,setSequence]=useState(0);
  const [tab,setTab]=useState<'stage'|'vocabulary'|'mechanics'>('stage');
  const now=sample(timeline,time,settings,reduced,boundary);
  const previous=useRef(0);
  useEffect(()=>{
    if(!playing)return;
    let frame:number;
    previous.current=0;
    const tick=(stamp:number)=>{
      const delta=previous.current?Math.min(stamp-previous.current,80):0;previous.current=stamp;
      setTime(t=>{const next=Math.min(t+delta*speed,timeline.duration);return next;});
      frame=requestAnimationFrame(tick);
    };
    frame=requestAnimationFrame(tick);
    return()=>cancelAnimationFrame(frame);
  },[playing,speed,timeline]);
  useEffect(()=>{if(time>=timeline.duration)setPlaying(false);},[time,timeline.duration]);
  useEffect(()=>{
    const stop=()=>{if(document.hidden)setPlaying(false);};
    document.addEventListener('visibilitychange',stop);return()=>document.removeEventListener('visibilitychange',stop);
  },[]);
  function retarget(scene:Scene,blink=false) {
    const velocity=reduced?zeroVelocity():velocityAt(timeline,time,settings,boundary);
    setTimeline(study(now.pose,scene,velocity,blink));setTime(0);setPlaying(true);
  }
  function changeBoundary(next:Constraints) {
    // Privacy/degradation labels and choreography change in the same render, even while paused.
    setBoundary(next);
    setTimeline(study(now.pose,now.beat.scene));setTime(0);setPlaying(true);
  }
  function playSequence() {
    const beats=sequences[sequence].beats;
    setTimeline({from:now.pose,velocity:zeroVelocity(),beats,duration:beats.at(-1)!.at+1800,blink:false});
    setTime(0);setPlaying(true);
  }
  const shownRequest=now.beat.scene;
  const button=(name:string,action:()=>void,primary=false)=><button className={primary?'primary':''} onClick={action}>{name}</button>;
  return <main>
    <header className="page-head"><div><h1>OSCAR <span>Expression laboratory</span></h1><p>Character study v3 · Slice 11.1 + 11.2 · Owner review candidate</p></div><span className="proposal">Expressive derivative proposal</span></header>
    <div className="disclosure">{disclosure}</div>
    <nav aria-label="Study views" className="tabs">{(['stage','vocabulary','mechanics'] as const).map(t=><button key={t} aria-pressed={tab===t} onClick={()=>setTab(t)}>{t==='stage'?'Live study':t==='vocabulary'?'Expression atlas':'Geometry & restraint'}</button>)}</nav>
    <div className="workspace">
      <section className="work" aria-label="Character studies">
        {tab==='stage'&&<>
          <div className="stage" data-testid="stage">
            <div className="stage-label"><span>Two marks. One continuous presence.</span><span>{reduced?'Static equivalent':'Finite performance'}</span></div>
            <div className="character"><Orb pose={now.pose} size={340}/></div>
            <div className="stage-readout" role="status" aria-live="polite" aria-atomic="true"><strong>{now.resolved.label}</strong><span>{now.resolved.delivery} delivery · synthetic</span></div>
            <p className="stage-note">{now.beat.note}</p>
          </div>
          <div className="transport" aria-label="Motion inspection">
            <div className="transport-buttons">{button(playing?'Pause':'Play',()=>{if(time>=timeline.duration)setTime(0);setPlaying(!playing);},true)}{button('Replay',()=>{setTime(0);setPlaying(true);})}{button('Interrupt',()=>retarget({operation:'available',delivery:'interrupted'}))}{button('Return to neutral',()=>retarget(neutral))}{button('Blink study',()=>retarget(shownRequest,true))}</div>
            <label className="scrubber">Transition <input aria-label="Scrub transition" type="range" min="0" max={timeline.duration} step="1" value={time} onChange={e=>{setPlaying(false);setTime(Number(e.target.value));}}/><output>{(time/1000).toFixed(2)} / {(timeline.duration/1000).toFixed(2)} s</output></label>
            <label className="speed">Playback speed<select value={speed} onChange={e=>setSpeed(Number(e.target.value))}>{[.25,.5,1,1.5,2].map(s=><option key={s} value={s}>{s}×</option>)}</select></label>
          </div>
          <section className="sequence"><h2>Reaction & recovery</h2><div className="sequence-controls"><label>Transition sequence<select value={sequence} onChange={e=>setSequence(Number(e.target.value))}>{sequences.map((s,i)=><option key={s.name} value={i}>{s.name}</option>)}</select></label>{button('Run sequence',playSequence)}</div><ol className="beat-list">{sequences[sequence].beats.map(b=><li key={b.at}><span>{(b.at/1000).toFixed(1)}s</span>{b.scene.operation} / {b.scene.delivery}</li>)}</ol><p>Finite sequences stop. Restore and unmute happen only at explicit simulated events.</p></section>
        </>}
        {tab==='vocabulary'&&<section className="atlas" data-testid="atlas"><h2>The expressive vocabulary</h2><p>Sixteen studies built from one disc, one arc and a weighted puck. Select a study to perform it live.</p><div className="atlas-grid">{vocabulary.map(v=><button className="expression" key={v.name} onClick={()=>{setTab('stage');retarget(v.scene);}}><Orb pose={poseFor(v.scene,settings.intensity)} size={128} label={`OSCAR ${v.name}`}/><strong>{v.name}</strong><span>{v.detail}</span></button>)}</div></section>}
        {tab==='mechanics'&&<section className="mechanics" data-testid="mechanics"><h2>Identity before embellishment</h2><div className="identity-pair"><figure><img src={sourceOrb} width="220" height="220" alt="Unchanged canonical OSCAR Orb"/><figcaption>Canonical source · unchanged</figcaption></figure><figure><Orb pose={now.pose} size={220}/><figcaption>v2 derivative · {now.resolved.delivery}</figcaption></figure></div><dl><dt>Blue shell</dt><dd>(288, 292) · r264 · painted gradient retained</dd><dt>Yellow puck</dt><dd>r187 side / r177 front · 7-unit inset · original shadow</dd><dt>Red marks</dt><dd>Circular eye with a lid; wink unfolds into a smaller eye. No mouth or pupils.</dd><dt>Gaze</dt><dd>Explicit reviewer target. Marks shift first; puck follows.</dd><dt>Weight</dt><dd>Damped spring and finite playful puck arcs during selected activity. Rest is still.</dd></dl><p>Speaking is a finite, synthetic delivery beat. It is not audio-reactive, lip-synced or evidence of actual speech. Rest/asleep is presentation only; it makes no claim about sensing or safety.</p></section>}
        <section className="scale" data-testid="scale"><div className="section-title"><h2>Same character, smaller footprint</h2><span>Actual CSS pixels</span></div><div className="scale-row">{sizes.map(size=><figure key={size}><div className="scale-seat"><Orb pose={now.pose} size={size} label={`OSCAR at ${size} pixels: ${now.resolved.label}`}/></div><figcaption>{size}px · {now.resolved.operation}</figcaption></figure>)}</div><p>Expression supports identity; the operational label remains essential at compact size.</p></section>
      </section>
      <aside className="inspector" aria-label="Synthetic state controls">
        <fieldset><legend>Two independent channels</legend><label>Operational state<select value={shownRequest.operation} onChange={e=>retarget({...shownRequest,operation:e.target.value as Operation})}>{operations.map(o=><option key={o}>{o}</option>)}</select></label><label>Expressive delivery<select value={shownRequest.delivery} onChange={e=>retarget({...shownRequest,delivery:e.target.value as Delivery})}>{deliveries.map(d=><option key={d}>{d}</option>)}</select></label><div className="arbitration"><span>Requested</span><p>{shownRequest.operation} / {shownRequest.delivery}</p><span>Resolved</span><p data-testid="resolved">{now.resolved.label} / {now.resolved.delivery}</p><p className="reason">{now.resolved.reason}</p></div></fieldset>
        <fieldset><legend>Conflict studies</legend><label>Availability boundary<select value={boundary.availability} onChange={e=>changeBoundary({...boundary,availability:e.target.value as Constraints['availability']})}><option value="available">Available sample</option><option value="unavailable">Unavailable sample</option><option value="unknown">Unknown sample</option></select></label><label className="check"><input type="checkbox" checked={boundary.muted} onChange={e=>changeBoundary({...boundary,muted:e.target.checked})}/>Conversational mute</label><label className="check"><input type="checkbox" checked={boundary.ownerAttention} onChange={e=>changeBoundary({...boundary,ownerAttention:e.target.checked})}/>Owner attention required</label><p>No approval controls or executable actions exist here.</p></fieldset>
        <fieldset><legend>Physical studies</legend><label htmlFor="intensity">Expression intensity <output aria-hidden="true">{settings.intensity.toFixed(2)}</output><input id="intensity" type="range" min=".35" max="1" step=".05" value={settings.intensity} onChange={e=>setSettings({...settings,intensity:Number(e.target.value)})}/></label><label htmlFor="weight">Puck weight <output aria-hidden="true">{settings.weight.toFixed(2)}</output><input id="weight" type="range" min=".7" max="1.5" step=".05" value={settings.weight} onChange={e=>setSettings({...settings,weight:Number(e.target.value)})}/></label><label htmlFor="gaze-x">Gaze horizontal <output aria-hidden="true">{settings.gaze.x}</output><input id="gaze-x" type="range" min="-10" max="10" step="1" value={settings.gaze.x} onChange={e=>setSettings({...settings,gaze:{...settings.gaze,x:Number(e.target.value)}})}/></label><label htmlFor="gaze-y">Gaze vertical <output aria-hidden="true">{settings.gaze.y}</output><input id="gaze-y" type="range" min="-7" max="7" step="1" value={settings.gaze.y} onChange={e=>setSettings({...settings,gaze:{...settings.gaze,y:Number(e.target.value)}})}/></label><p>Targets are manually selected, never detected. Replay to inspect a changed setting.</p></fieldset>
        <fieldset><legend>Accessible presentation</legend><label className="check"><input type="checkbox" checked={reduced} disabled={systemReduced} onChange={e=>setReduce(e.target.checked)}/>Reduced motion</label><p>{systemReduced?'System reduced-motion preference is respected.':reduced?'Static poses replace travel, blink and cadence.':'System preference also applies. All sequences have static equivalents.'}</p><p>Keyboard: Tab reaches controls; arrow keys seek sliders. No state is communicated by color alone.</p></fieldset>
      </aside>
    </div>
    <footer><span>{disclosure}</span><span>Owner approval required before 11.3. No Core connection.</span></footer>
  </main>;
}
