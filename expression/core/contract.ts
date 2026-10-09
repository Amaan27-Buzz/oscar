/** Presentation-only wire contract. Provenance identifies a publisher; it never authenticates it. */
export const stateNames = ['idle','attentive','listening','processing','executing','verifying','waiting','speaking','muted','unavailable','error','unknown'] as const;
export const deliveryNames = ['composed','attentive','curious','focused','amused','pleased','surprised','concerned','hesitant','subdued','resting','asleep','interrupted'] as const;
export type OperationalState = typeof stateNames[number];
export type ExpressiveDelivery = typeof deliveryNames[number];
export type Source = Readonly<{kind:'core'|'lab'|'fixture';id:string}>;
export type ExpressionEvent = Readonly<{
  version:1;source:Source;generation:number;transitionId:string;eventTime:number;expiresAt:number;
  kind:'state'|'accent'|'interrupt'|'cancel';priority:'normal'|'urgent';
  operation:OperationalState;delivery:ExpressiveDelivery;
  availability:'available'|'unavailable'|'unknown';muted:boolean;
  attention:'none'|'owner';reducedMotion:boolean;
  accent?:'phrase'|'engagement'|'blink';
}>;
const keys = ['version','source','generation','transitionId','eventTime','expiresAt','kind','priority','operation','delivery','availability','muted','attention','reducedMotion'];
const id = (value:unknown):value is string => typeof value==='string'&&/^[A-Za-z0-9:_-]{1,64}$/.test(value);
const integer = (value:unknown):value is number => typeof value==='number'&&Number.isSafeInteger(value)&&value>=0;
const object = (value:unknown):value is Record<string,unknown> => typeof value==='object'&&value!==null&&!Array.isArray(value);
const member = (value:unknown,values:readonly string[]) => typeof value==='string'&&values.includes(value);

/** Structural decoding precedes generation arbitration; stale packets cannot invalidate newer state. */
export function parseEvent(input:unknown):ExpressionEvent|null {
  try {
    if(typeof input==='string') {if(input.length>4096)return null;input=JSON.parse(input);}
    if(!object(input))return null;
    if(Object.keys(input).some(key=>!keys.includes(key)&&key!=='accent')||keys.some(key=>!Object.prototype.hasOwnProperty.call(input,key)))return null;
    const source=input.source;
    if(!object(source)||Object.keys(source).length!==2||!Object.prototype.hasOwnProperty.call(source,'kind')||!Object.prototype.hasOwnProperty.call(source,'id')||!member(source.kind,['core','lab','fixture'])||!id(source.id))return null;
    if(input.version!==1||!integer(input.generation)||!id(input.transitionId)||!integer(input.eventTime)||!integer(input.expiresAt))return null;
    if(input.expiresAt<=input.eventTime||input.expiresAt-input.eventTime>30000)return null;
    if(!member(input.kind,['state','accent','interrupt','cancel'])||!member(input.priority,['normal','urgent']))return null;
    if(!member(input.operation,stateNames)||!member(input.delivery,deliveryNames)||!member(input.availability,['available','unavailable','unknown']))return null;
    if(typeof input.muted!=='boolean'||typeof input.reducedMotion!=='boolean'||!member(input.attention,['none','owner']))return null;
    if(input.kind==='accent'?!member(input.accent,['phrase','engagement','blink']):'accent' in input)return null;
    return Object.freeze({...input,source:Object.freeze({...source})}) as ExpressionEvent;
  } catch {return null;}
}

export function validateEvent(input:unknown,now:number):ExpressionEvent|null {
  const event=parseEvent(input);
  return event&&integer(now)&&event.eventTime<=now+250&&event.expiresAt>now?event:null;
}

export type AnimationOutcome = 'settled'|'accent_finished'|'superseded'|'cancelled'|'expired'|'invalid'|'lifecycle';
export type AnimationRecord = Readonly<{generation:number;transitionId:string;outcome:AnimationOutcome}>;
