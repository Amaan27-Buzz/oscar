import {arbitrate,blend,canonical,clear,defaults,poseFor,sample,study,zeroVelocity} from './motion.js';
import type {Pose,Settings,Study} from './motion.js';
import {parseEvent,validateEvent} from './contract.js';
import type {AnimationOutcome,AnimationRecord,ExpressionEvent,Source,ExpressiveDelivery} from './contract.js';

type Motion = {from:Pose;velocity:Pose;started:number;duration:number;generation:number;transitionId:string;accent:Study|null};
export type ExpressionSnapshot = Readonly<{
  pose:Pose;resolved:ReturnType<typeof arbitrate>;source:Source;generation:number;
  animation:'settling'|'accent'|'held'|'cancelled';moving:boolean;expiresAt:number|null;
  priority:'critical'|'attention'|'privacy'|'urgent'|'activity'|'delivery';
}>;

/** No Core, audio, timers or React dependency. The authenticated adapter supplies state and time. */
export class ExpressionController {
  private frame:ExpressionEvent|null=null;
  private motion:Motion|null=null;
  private held:Pose={...canonical};
  private lastGeneration=-1;
  private records:AnimationRecord[]=[];
  private invalid=false;
  private cancelled=false;
  private settledDelivery:ExpressiveDelivery|null=null;
  private forceReduced=false;
  private gaze:{x:number;y:number};
  readonly settings:Settings;
  readonly source:Source;
  constructor(source:Source,settings:Settings=defaults) {
    if(!/^[A-Za-z0-9:_-]{1,64}$/.test(source.id)||!['core','lab','fixture'].includes(source.kind))throw new Error('Invalid expression source');
    if(!Number.isFinite(settings.intensity)||settings.intensity<.35||settings.intensity>1||!Number.isFinite(settings.weight)||settings.weight<.7||settings.weight>1.5||!Number.isFinite(settings.gaze.x)||!Number.isFinite(settings.gaze.y)||Math.abs(settings.gaze.x)>10||Math.abs(settings.gaze.y)>7)throw new Error('Invalid expression settings');
    this.source=Object.freeze({...source});this.settings=Object.freeze({...settings,gaze:Object.freeze({...settings.gaze})});
    this.gaze={...settings.gaze};
    this.held=poseFor({operation:'unknown',delivery:'hesitant'},settings.intensity,settings.gaze);
  }
  private resolve() {
    if(this.invalid||!this.frame)return arbitrate({operation:'unknown',delivery:'hesitant'},{...clear,muted:this.frame?.muted===true||this.frame?.operation==='muted'});
    const delivery=this.settledDelivery??(this.frame.kind==='interrupt'?'interrupted':this.frame.delivery);
    return arbitrate({operation:this.frame.operation,delivery},{availability:this.frame.availability,muted:this.frame.muted,ownerAttention:this.frame.attention==='owner'});
  }
  private reduced() {return this.forceReduced||this.frame?.reducedMotion===true;}
  private poseAt(now:number):Pose {
    if(!this.motion)return this.held;
    const m=this.motion,t=Math.max(0,now-m.started),resolved=this.resolve();
    if(this.reduced())return m.accent?sample(m.accent,t,this.settings,true).pose:poseFor(resolved,this.settings.intensity,this.gaze);
    return m.accent?sample(m.accent,t,this.settings,false).pose:blend(m.from,poseFor(resolved,this.settings.intensity,this.gaze),t,this.settings.weight,m.velocity);
  }
  private velocity(now:number) {
    if(!this.motion||this.reduced())return zeroVelocity();
    const a=this.poseAt(now),b=this.poseAt(now+.01);
    return Object.fromEntries((Object.keys(a) as (keyof Pose)[]).map(key=>[key,(b[key]-a[key])*100000])) as Pose;
  }
  private finish(outcome:AnimationOutcome) {
    if(this.motion) {
      this.records.push({generation:this.motion.generation,transitionId:this.motion.transitionId,outcome});
      if(this.records.length>32)this.records.shift();
      this.motion=null;
    }
  }
  private invalidate(outcome:AnimationOutcome) {
    this.finish(outcome);this.invalid=true;this.cancelled=true;
    this.held=poseFor(this.resolve(),this.settings.intensity,this.gaze);
  }
  receive(raw:unknown,now:number):'accepted'|'stale'|'invalid'|'source_mismatch' {
    const event=parseEvent(raw);
    if(!event) {this.invalidate('invalid');return 'invalid';}
    if(event.source.kind!==this.source.kind||event.source.id!==this.source.id) {this.invalidate('invalid');return 'source_mismatch';}
    if(event.generation<=this.lastGeneration)return 'stale';
    if(!validateEvent(event,now)) {this.invalidate('invalid');return 'invalid';}
    this.snapshot(now);
    const previous=this.resolve(),from={...this.poseAt(now)},velocity=this.velocity(now);
    const oldFrame=this.frame,wasInvalid=this.invalid,wasCancelled=this.cancelled;
    this.frame=event;this.lastGeneration=event.generation;this.invalid=false;this.cancelled=false;
    const resolved=this.resolve();
    if(event.kind==='accent') {
      const permitted=event.accent==='phrase'?previous.operation==='speaking'&&resolved.operation==='speaking':event.accent==='engagement'?previous.operation==='executing'&&resolved.operation==='executing':!['unavailable','unknown','muted','waiting','error'].includes(resolved.operation);
      if(!oldFrame||!permitted||resolved.muted) {this.invalidate('invalid');return 'invalid';}
    }
    // Fresh state heartbeats update authority/freshness without replaying a gesture.
    if(event.kind==='state'&&oldFrame&&!wasInvalid&&!wasCancelled&&oldFrame.transitionId===event.transitionId&&['operation','delivery','availability','muted','attention','reducedMotion'].every(key=>oldFrame[key as keyof ExpressionEvent]===event[key as keyof ExpressionEvent]))return 'accepted';
    this.settledDelivery=null;
    this.finish(event.kind==='cancel'?'cancelled':'superseded');
    if(event.kind==='cancel') {this.held=from;this.cancelled=true;return 'accepted';}
    const target=this.resolve();
    const reaction=['amused','pleased','surprised','interrupted'].includes(target.delivery)&&['idle','attentive'].includes(target.operation);
    const accent:Study|null=event.kind==='accent'?{from,velocity,beats:[{at:0,scene:target,note:'Permitted presentation accent'}],duration:event.accent==='blink'?700:5200,blink:event.accent==='blink',choreography:event.accent!=='blink'}:reaction?{...study(from,target,velocity),choreography:false}:null;
    this.motion={from,velocity,started:now,duration:this.reduced()&&!reaction?0:accent?accent.duration:700,generation:event.generation,transitionId:event.transitionId,accent};
    this.held=from;this.snapshot(now);return 'accepted';
  }
  snapshot(now:number):ExpressionSnapshot {
    if(this.frame&&!this.invalid&&(now>=this.frame.expiresAt||now<this.frame.eventTime-250))this.invalidate('expired');
    const pose={...this.poseAt(now)};
    const delivery=this.motion?.accent?sample(this.motion.accent,Math.max(0,now-this.motion.started),this.settings,this.reduced()).resolved.delivery:null;
    if(this.motion&&now-this.motion.started>=this.motion.duration) {
      this.settledDelivery=delivery as ExpressiveDelivery|null;
      const outcome=this.motion.accent?'accent_finished':'settled';this.held=pose;this.finish(outcome);
    }
    const resolved={...this.resolve(),...(delivery?{delivery}:{} )};
    const priority=['unavailable','unknown','error'].includes(resolved.operation)?'critical':resolved.operation==='waiting'?'attention':resolved.muted?'privacy':this.frame?.priority==='urgent'||this.frame?.kind==='interrupt'?'urgent':['listening','speaking','processing','executing','verifying'].includes(resolved.operation)?'activity':'delivery';
    return {pose,resolved,source:this.source,generation:this.lastGeneration,priority,animation:this.motion?(this.motion.accent?'accent':'settling'):this.cancelled?'cancelled':'held',moving:this.motion!==null,expiresAt:this.invalid?null:this.frame?.expiresAt??null};
  }
  suspend() {this.invalidate('lifecycle');}
  /** Local explicit pointer target; critical/privacy/activity poses never track it. */
  setGaze(gaze:{x:number;y:number},now:number) {
    if(!Number.isFinite(gaze.x)||!Number.isFinite(gaze.y)||Math.abs(gaze.x)>10||Math.abs(gaze.y)>7)throw new Error('Invalid gaze target');
    this.snapshot(now);
    if(!this.frame||this.invalid||!['idle','attentive'].includes(this.resolve().operation)||this.motion?.accent)return;
    if(gaze.x===this.gaze.x&&gaze.y===this.gaze.y)return;
    const from={...this.poseAt(now)},velocity=this.velocity(now);this.gaze={...gaze};
    this.finish('superseded');
    this.motion={from,velocity,started:now,duration:this.reduced()?0:700,generation:this.frame.generation,transitionId:this.frame.transitionId,accent:null};
    this.held=from;this.snapshot(now);
  }
  setReducedMotion(reduced:boolean,now:number) {
    this.forceReduced=reduced;
    if(!this.frame)return;
    if(this.reduced()) {
      this.held=poseFor(this.resolve(),this.settings.intensity,this.gaze);
      if(!this.motion?.accent||this.motion.accent.beats.length===1)this.finish('cancelled');
    }
    this.snapshot(now);
  }
  takeAnimationRecords():AnimationRecord[] {const records=this.records;this.records=[];return records;}
}
