// Development-only study vocabulary; production events use expression/core/contract.
export * from '../../../expression/core/motion';
import type {Scene,Beat} from '../../../expression/core/motion';
import {neutral} from '../../../expression/core/motion';
const beat=(at:number,operation:Scene['operation'],delivery:Scene['delivery'],note:string):Beat=>({at,scene:{operation,delivery},note});
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
