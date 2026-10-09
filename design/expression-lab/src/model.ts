// Lab-only samples. These types are not the Slice 11.3 production render contract.
export const operations = ['available','listening','processing','executing','verifying','waiting','speaking','muted','unavailable','error','unknown'] as const;
export type Operation = typeof operations[number];
export const deliveries = ['composed','attentive','curious','focused','amused','pleased','surprised','concerned','hesitant','subdued','asleep','interrupted'] as const;
export type Delivery = typeof deliveries[number];
export type Scene = {operation: Operation; delivery: Delivery};
export type Constraints = {availability: 'available'|'unavailable'|'unknown'; muted: boolean; ownerAttention: boolean};
export const clear: Constraints = {availability: 'available', muted: false, ownerAttention: false};
export const neutral: Scene = {operation: 'available', delivery: 'composed'};
export const disclosure = 'SIMULATED VISUAL STATE — NO CORE EXECUTION';

export function arbitrate(request: Scene, boundary: Constraints = clear) {
  let operation:Operation = operations.includes(request.operation)?request.operation:'unknown';
  let delivery:Delivery = deliveries.includes(request.delivery)?request.delivery:'composed';
  let reason = 'Delivery carries no perception, permission or outcome claim.';
  if (boundary.availability === 'unavailable' || operation === 'unavailable') {
    operation = 'unavailable'; delivery = 'subdued'; reason = 'Unavailable overrides activity and expressive delivery.';
  } else if (!['available','unavailable'].includes(boundary.availability) || operation === 'unknown') {
    operation = 'unknown'; delivery = 'hesitant'; reason = 'Unknown suppresses live activity claims.';
  } else if (operation === 'error') {
    delivery = 'concerned'; reason = 'Failure suppresses playful delivery; no success cue.';
  } else if (boundary.ownerAttention || operation === 'waiting') {
    operation = 'waiting'; delivery = 'subdued'; reason = 'Owner attention holds still; expressions never approve.';
  } else if (boundary.muted || operation === 'muted') {
    operation = 'muted'; delivery = 'composed'; reason = 'Conversational mute suppresses listening and speech choreography.';
  } else if (['processing','executing','verifying'].includes(operation)) {
    delivery = 'focused'; reason = 'Serious work constrains delivery, without claiming a result.';
  } else if (operation === 'listening') {
    delivery = 'attentive'; reason = 'Listening posture requires this explicit synthetic listening selection.';
  } else if (operation === 'speaking' && ['asleep','interrupted','subdued'].includes(delivery)) {
    delivery = 'composed'; reason = 'Speaking excludes sleep, interruption and withdrawn presentation.';
  }
  const muted = boundary.muted || request.operation === 'muted' || operation === 'muted';
  return {operation, delivery, reason, label: `${operation}${muted && operation !== 'muted' ? ' · conversational mute' : ''}`, muted};
}

export type Pose = {
  x: number; y: number; tilt: number; body: number;
  eye: number; width: number; arc: number; slant: number; span: number;
  gx: number; gy: number; lid: number; opening: number;
};
export const canonical: Pose = {x:0,y:0,tilt:0,body:0,eye:1,width:1,arc:-16,slant:-4,span:1,gx:0,gy:0,lid:0,opening:0};
const marks: Record<Delivery, Partial<Pose>> = {
  composed: {},
  attentive: {x:-6,y:-6,eye:1.04,arc:-9,gx:11,gy:-3,opening:.9},
  curious: {x:-8,y:-9,tilt:-5,body:-1,eye:1.08,arc:-27,slant:-17,gx:9,gy:-7,opening:.45},
  focused: {x:-11,y:-6,eye:.62,width:1,arc:-2,slant:-7,gx:3,gy:3,lid:3,opening:.55},
  amused: {y:2,tilt:3,eye:.82,arc:-29,slant:1,gx:-3,lid:-5},
  pleased: {y:-3,tilt:1,eye:.91,arc:-23,slant:-2},
  surprised: {x:-15,y:-14,tilt:-4,body:-1,eye:1.16,width:1.08,arc:-5,span:.9,gy:-7,opening:1},
  concerned: {x:-3,y:3,tilt:2,eye:.74,arc:23,slant:17,gx:-2,gy:4,lid:-9},
  hesitant: {x:-6,y:2,tilt:-4,eye:.86,width:.96,arc:3,slant:-18,gx:-11,gy:2,lid:7},
  subdued: {x:-3,y:8,tilt:0,eye:.52,arc:3,slant:0,gy:5},
  asleep: {x:-4,y:9,tilt:2,body:1,eye:.08,arc:5,slant:0,gy:8},
  interrupted: {x:-9,y:-5,tilt:-3,eye:1.07,arc:-3,slant:-11,gx:-9,gy:-2,opening:.8},
};
export function poseFor(scene: Scene, intensity = .75, gaze = {x:0,y:0}): Pose {
  const resolved = arbitrate(scene);
  const p = {...canonical, ...marks[resolved.delivery]};
  if (resolved.operation === 'verifying') {p.eye=.51;p.arc=0;p.gx=0;p.tilt=0;p.lid=0;p.opening=.4;}
  if (resolved.operation === 'executing') {p.x=-17;p.y=-11;p.gx=8;p.tilt=-5;p.opening=.8;}
  if (resolved.operation === 'processing') {p.gx=-6;p.gy=-5;p.tilt=-3;p.opening=.5;}
  if (resolved.operation === 'muted') {p.eye=.7;p.arc=0;p.gx=0;}
  if (resolved.operation === 'speaking') {p.x=-10;p.y=-3;p.tilt=3;p.opening=.95;}
  const amount = clamp(intensity, .35, 1);
  for (const key of Object.keys(p) as (keyof Pose)[]) p[key] = canonical[key] + (p[key] - canonical[key]) * amount;
  if(['attentive','surprised','interrupted'].includes(resolved.delivery)||resolved.operation==='speaking') {
    p.opening=resolved.operation==='speaking'?.95:(marks[resolved.delivery].opening??0);
  }
  // Closure is a posture invariant, not a faint emotion at low intensity.
  if(resolved.delivery==='asleep') {p.eye=0;p.opening=0;p.arc=5;p.slant=0;}
  // Explicit reviewer target only. Degraded/privacy poses never follow a target.
  if (!['unavailable','unknown','muted','error','waiting'].includes(resolved.operation)) {
    p.gx = clamp(p.gx + gaze.x, -14, 14); p.gy = clamp(p.gy + gaze.y, -10, 10);
  }
  return p;
}
export const clamp = (v:number, min:number, max:number) => Math.max(min, Math.min(max, Number.isFinite(v) ? v : min));
export const zeroVelocity = (): Pose => Object.fromEntries(Object.keys(canonical).map(k=>[k,0])) as Pose;
export type Settings = {intensity:number; weight:number; gaze:{x:number;y:number}};
export const defaults: Settings = {intensity:.75,weight:1,gaze:{x:0,y:0}};

// Closed-form damped spring: deterministic seek, bounded travel and velocity-aware retargeting.
function spring(from:number,to:number,velocity:number,seconds:number,weight:number) {
  const w = 19 / Math.sqrt(weight), z=.84, d=w*Math.sqrt(1-z*z), a=from-to;
  const b=(velocity+z*w*a)/d;
  return to+Math.exp(-z*w*seconds)*(a*Math.cos(d*seconds)+b*Math.sin(d*seconds));
}
export function blend(from:Pose,to:Pose,ms:number,weight:number,velocity=zeroVelocity()):Pose {
  const p={...from}, t=clamp(ms,0,700), mass=clamp(weight,.7,1.5);
  if(t===0)return p;
  for (const key of Object.keys(p) as (keyof Pose)[]) {
    if (['x','y','tilt','body'].includes(key)) {
      const travel=velocity[key]===0?Math.max(0,t-45):t;
      p[key]=t>=700?to[key]:spring(from[key],to[key],velocity[key],travel/1000,key==='body'?mass*1.35:mass);
    }
    else {
      const duration=['gx','gy'].includes(key)?95:['arc','slant','span'].includes(key)?170:210;
      const u=clamp(t/duration,0,1), ease=u*u*(3-2*u);
      p[key]=from[key]+(to[key]-from[key])*ease;
    }
  }
  return p;
}
export type Beat = {at:number; scene:Scene; note:string};
const beat=(at:number,operation:Operation,delivery:Delivery,note:string):Beat=>({at,scene:{operation,delivery},note});
export const sequences: {name:string; beats:Beat[]}[] = [
  {name:'Notice → listen',beats:[beat(0,'available','composed','Quiet rest'),beat(900,'available','attentive','Notice: gaze leads'),beat(2300,'listening','attentive','Listening selected explicitly')]},
  {name:'Listen → think → respond',beats:[beat(0,'listening','attentive','Receive'),beat(1600,'processing','focused','Concentrate'),beat(3400,'speaking','composed','Synthetic delivery beat'),beat(5200,'available','composed','Release attention')]},
  {name:'Work → owner approval',beats:[beat(0,'executing','focused','Engaged'),beat(1700,'waiting','subdued','Stop and wait; no approval granted')]},
  {name:'Think → interrupted → attentive',beats:[beat(0,'processing','focused','Concentrate'),beat(1600,'available','interrupted','Stop/reorient'),beat(2250,'available','attentive','Ready for a new turn')]},
  {name:'Curious → amused → composed',beats:[beat(0,'available','curious','Inquiry'),beat(1600,'available','amused','One dry inflection'),beat(2650,'available','composed','Return; no repetition')]},
  {name:'Available → unavailable',beats:[beat(0,'available','attentive','Present'),beat(1700,'unavailable','subdued','Withdraw; activity truth stops immediately')]},
  {name:'Unavailable → restored',beats:[beat(0,'unavailable','subdued','Unavailable'),beat(1900,'available','attentive','Explicit simulated restoration'),beat(3100,'available','composed','No celebration or success claim')]},
  {name:'Active → resting',beats:[beat(0,'executing','focused','Engaged'),beat(2000,'available','subdued','Release'),beat(3200,'available','composed','Stillness')]},
  {name:'Speaking → interrupted',beats:[beat(0,'speaking','composed','Synthetic cadence'),beat(1600,'available','interrupted','Cadence stops at event'),beat(2300,'available','attentive','Reorient; no automatic microphone')]},
  {name:'Muted → explicitly available',beats:[beat(0,'muted','composed','Conversational mute'),beat(1700,'available','attentive','Explicit selection, not microphone access'),beat(2900,'available','composed','Quiet availability')]},
];
export type Study = {from:Pose; velocity:Pose; beats:Beat[]; duration:number; blink:boolean};
export function study(from:Pose,scene:Scene,velocity=zeroVelocity(),blink=false):Study {
  const beats=[beat(0,scene.operation,scene.delivery,'Selection / retarget')];
  const recovery:Partial<Record<Delivery,number>>={surprised:850,amused:1400,pleased:1400,interrupted:650};
  const release=recovery[scene.delivery];
  if(release!==undefined)beats.push(beat(release,scene.operation,scene.delivery==='interrupted'?'attentive':'composed','Authored recovery; no result or perception claim'));
  return {from,velocity,beats,duration:(release??0)+1800,blink};
}
export function sample(study:Study,ms:number,settings:Settings,reduced=false,boundary:Constraints=clear) {
  const t=clamp(ms,0,study.duration);
  let from=study.from, velocity=study.velocity;
  let current=study.beats[0], start=0;
  for (const next of study.beats.slice(1)) {
    if(t<next.at) break;
    from=poseFor(arbitrate(current.scene,boundary),settings.intensity,settings.gaze);
    velocity=zeroVelocity();current=next;start=next.at;
  }
  const resolved=arbitrate(current.scene,boundary);
  const to=poseFor(resolved,settings.intensity,settings.gaze);
  const local=t-start;
  const pose=reduced?to:blend(from,to,local,settings.weight,velocity);
  const choreography=!reduced&&!resolved.muted&&resolved.operation==='speaking';
  if(!reduced&&!resolved.muted&&resolved.operation==='executing'&&local>240&&local<900) {
    const phase=(local-240)/660, arc=Math.sin(Math.PI*phase)*settings.intensity;
    pose.x-=7*arc;pose.y-=5*arc*Math.sin(Math.PI*phase);pose.tilt-=3*arc;
  }
  if(choreography&&local>400&&local<1400) {
    // Two authored phrase stresses; never random audio inference or ongoing idle motion.
    const pulse=Math.exp(-(((local-650)/110)**2))+.6*Math.exp(-(((local-1050)/140)**2));
    const envelope=Math.sin(Math.PI*clamp((local-400)/1000,0,1));
    const arc=(local-400)/1000*Math.PI*2;
    pose.eye-=.12*pulse;pose.opening-=.2*pulse;
    pose.x+=20*envelope*Math.sin(arc)*settings.intensity;
    pose.y-=13*envelope*Math.cos(arc)*settings.intensity;
    pose.tilt+=6*envelope*Math.sin(arc)*settings.intensity;
    pose.arc-=3*pulse;
  }
  if(study.blink&&!reduced&&local>80&&local<240&&!['unavailable','unknown','muted','error'].includes(resolved.operation)) {
    const close=1-Math.sin(Math.PI*(local-80)/160);
    pose.eye*=close;pose.opening*=close;
  }
  return {pose,resolved,beat:current,local};
}
export function velocityAt(s:Study,t:number,settings:Settings,boundary=clear):Pose {
  const a=sample(s,t,settings,false,boundary).pose, b=sample(s,t+.01,settings,false,boundary).pose;
  return Object.fromEntries((Object.keys(a) as (keyof Pose)[]).map(k=>[k,(b[k]-a[k])*100000])) as Pose;
}

export const vocabulary: {name:string;scene:Scene;detail:string}[] = [
  {name:'Resting',scene:neutral,detail:'Canonical asymmetry. No idle loop.'},
  {name:'Attentive',scene:{operation:'available',delivery:'attentive'},detail:'Gaze arrives before the puck.'},
  {name:'Curious',scene:{operation:'available',delivery:'curious'},detail:'Lifted arc, slight counter-tilt.'},
  {name:'Thinking',scene:{operation:'processing',delivery:'focused'},detail:'Inward, narrowed concentration.'},
  {name:'Listening',scene:{operation:'listening',delivery:'attentive'},detail:'Forward attention; synthetic selection only.'},
  {name:'Speaking',scene:{operation:'speaking',delivery:'composed'},detail:'Open wink and finite playful puck arc. No lip sync.'},
  {name:'Focused',scene:{operation:'executing',delivery:'focused'},detail:'Small directed commitment, no progress claim.'},
  {name:'Amused',scene:{operation:'available',delivery:'amused'},detail:'Unequal softening, one earned inflection.'},
  {name:'Pleased',scene:{operation:'available',delivery:'pleased'},detail:'Gentle acknowledgement, never task success.'},
  {name:'Surprised',scene:{operation:'available',delivery:'surprised'},detail:'Brief opening and controlled recoil.'},
  {name:'Concerned',scene:{operation:'available',delivery:'concerned'},detail:'Reserved arc tension, no cartoon distress.'},
  {name:'Unsure',scene:{operation:'unknown',delivery:'hesitant'},detail:'Offset hesitation; live state unknown.'},
  {name:'Waiting',scene:{operation:'waiting',delivery:'subdued'},detail:'Suspended posture. No busy animation.'},
  {name:'Interrupted',scene:{operation:'available',delivery:'interrupted'},detail:'Stop and orient; no automatic listening.'},
  {name:'Asleep',scene:{operation:'available',delivery:'asleep'},detail:'Presentation rest; says nothing about safety or sensing.'},
  {name:'Unavailable',scene:{operation:'unavailable',delivery:'subdued'},detail:'Low-energy withdrawal; not an idle wink.'},
];
