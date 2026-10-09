// Deterministic numeric motion. Wire admission and authority live in contract/controller.
import data from "../motion-v1.json" with {type:"json"};
import {arbitrate,clear,neutral} from './arbitration.js';
import type {Scene,Constraints,Delivery,Operation} from './arbitration.js';
export * from './arbitration.js';
export type Pose = {
  x: number; y: number; tilt: number; body: number;
  eye: number; width: number; arc: number; slant: number; span: number;
  gx: number; gy: number; lid: number; opening: number;
};
export const canonical: Pose = Object.freeze({...data.canonical});
const marks: Record<Delivery, Partial<Pose>> = {...data.deliveries,resting:{}};
export function poseFor(scene: Scene, intensity = 1, gaze = {x:0,y:0}): Pose {
  const resolved = arbitrate(scene);
  const p = {...canonical, ...marks[resolved.delivery]};
  if (resolved.operation === 'verifying') {p.eye=.51;p.arc=0;p.gx=0;p.tilt=0;p.lid=0;p.opening=.4;}
  if (resolved.operation === 'executing') {p.x=-42;p.y=-18;p.gx=8;p.tilt=-8;p.opening=.8;}
  if (resolved.operation === 'processing') {p.x=-32;p.y=-24;p.gx=-6;p.gy=-5;p.tilt=-8;p.opening=.5;}
  if (resolved.operation === 'muted') {p.eye=.7;p.arc=0;p.gx=0;}
  if (resolved.operation === 'speaking') {p.x=-42;p.y=-6;p.tilt=6;p.opening=.95;}
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
export const defaults: Settings = {intensity:1,weight:1,gaze:{x:0,y:0}};

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
export type Study = {from:Pose; velocity:Pose; beats:Beat[]; duration:number; blink:boolean;choreography?:boolean};
export function study(from:Pose,scene:Scene,velocity=zeroVelocity(),blink=false):Study {
  const beats=[beat(0,scene.operation,scene.delivery,'Selection / retarget')];
  const recovery:Partial<Record<Delivery,number>>={surprised:850,amused:1400,pleased:1400,interrupted:650};
  const release=recovery[scene.delivery];
  if(release!==undefined)beats.push(beat(release,scene.operation,scene.delivery==='interrupted'?'attentive':'composed','Authored recovery; no result or perception claim'));
  return {from,velocity,beats,duration:(release??0)+(['speaking','executing'].includes(scene.operation)?5200:1800),blink};
}

// Authored phrase/engagement poses with continuous velocity, not a repeating idle orbit.
type Travel = readonly [number,number,number,number];
const speechTravel: Travel[] = data.speechTravel.map(([at,x,y,tilt])=>[at,x,y,tilt]);
const workTravel: Travel[] = data.workTravel.map(([at,x,y,tilt])=>[at,x,y,tilt]);
function travelAt(points:Travel[],ms:number):[number,number,number] {
  const segment=points.findIndex((point,i)=>i>0&&ms<point[0]);
  if(ms<=points[0][0]||segment<0)return [0,0,0];
  const a=points[segment-1],b=points[segment],before=points[Math.max(0,segment-2)],after=points[Math.min(points.length-1,segment+1)];
  const duration=b[0]-a[0],u=(ms-a[0])/duration;
  return [1,2,3].map(axis=>{
    const start=segment===1?0:(b[axis]-before[axis])/(b[0]-before[0]);
    const end=segment===points.length-1?0:(after[axis]-a[axis])/(after[0]-a[0]);
    return (2*u**3-3*u**2+1)*a[axis]+(u**3-2*u**2+u)*duration*start+(-2*u**3+3*u**2)*b[axis]+(u**3-u**2)*duration*end;
  }) as [number,number,number];
}
function perform(from:Pose,resolved:ReturnType<typeof arbitrate>,local:number,settings:Settings,velocity:Pose,reduced:boolean,blink:boolean,choreography=true) {
  const to=poseFor(resolved,settings.intensity,settings.gaze);
  const pose=reduced?to:blend(from,to,local,settings.weight,velocity);
  if(choreography&&!reduced&&!resolved.muted&&['speaking','executing'].includes(resolved.operation)) {
    const [x,y,tilt]=travelAt(resolved.operation==='speaking'?speechTravel:workTravel,local);
    pose.x+=x*settings.intensity;pose.y+=y*settings.intensity;pose.tilt+=tilt*settings.intensity;
    if(resolved.operation==='speaking') {
      const stress=Math.exp(-(((local-1200)/180)**2))+.7*Math.exp(-(((local-2300)/220)**2));
      pose.eye=clamp(pose.eye-.12*stress,0,1.3);pose.opening=clamp(pose.opening-.16*stress,0,1);
    }
  }
  if(blink&&!reduced&&local>80&&local<240&&!['unavailable','unknown','muted','error'].includes(resolved.operation)) {
    const close=1-Math.sin(Math.PI*(local-80)/160);pose.eye*=close;pose.opening*=close;
  }
  return pose;
}
export function sample(study:Study,ms:number,settings:Settings,reduced=false,boundary:Constraints=clear) {
  const t=clamp(ms,0,study.duration);
  let from=study.from, velocity=study.velocity;
  let current=study.beats[0], start=0;
  for (const next of study.beats.slice(1)) {
    if(t<next.at) break;
    const old=arbitrate(current.scene,boundary),elapsed=next.at-start;
    const at=perform(from,old,elapsed,settings,velocity,reduced,study.blink,study.choreography);
    const before=perform(from,old,Math.max(0,elapsed-.01),settings,velocity,reduced,study.blink,study.choreography);
    velocity=Object.fromEntries((Object.keys(at) as (keyof Pose)[]).map(k=>[k,(at[k]-before[k])*100000])) as Pose;
    from=at;current=next;start=next.at;
  }
  const resolved=arbitrate(current.scene,boundary);
  const local=t-start;
  const pose=perform(from,resolved,local,settings,velocity,reduced,study.blink,study.choreography);
  return {pose,resolved,beat:current,local};
}
export function velocityAt(s:Study,t:number,settings:Settings,boundary=clear):Pose {
  const a=sample(s,t,settings,false,boundary).pose, b=sample(s,t+.01,settings,false,boundary).pose;
  return Object.fromEntries((Object.keys(a) as (keyof Pose)[]).map(k=>[k,(b[k]-a[k])*100000])) as Pose;
}
