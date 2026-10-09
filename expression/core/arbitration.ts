// Presentation arbitration only; it never grants Core authority.
export const operations = ['available','listening','processing','executing','verifying','waiting','speaking','muted','unavailable','error','unknown'] as const;
export type Operation = typeof operations[number] | 'idle' | 'attentive';
export const deliveries = ['composed','attentive','curious','focused','amused','pleased','surprised','concerned','hesitant','subdued','asleep','interrupted','resting'] as const;
export type Delivery = typeof deliveries[number];
export type Scene = {operation: Operation; delivery: Delivery};
export type Constraints = {availability: 'available'|'unavailable'|'unknown'; muted: boolean; ownerAttention: boolean};
export const clear: Constraints = {availability: 'available', muted: false, ownerAttention: false};
export const neutral: Scene = {operation: 'available', delivery: 'composed'};
export const disclosure = 'SIMULATED VISUAL STATE — NO CORE EXECUTION';

export function arbitrate(request: Scene, boundary: Constraints = clear) {
  let operation:Operation = [...operations,'idle','attentive'].includes(request.operation)?request.operation:'unknown';
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
  } else if (operation === 'listening' || (operation === 'attentive' && delivery!=='interrupted')) {
    delivery = 'attentive'; reason = 'Listening posture requires this explicit synthetic listening selection.';
  } else if (operation === 'speaking' && ['asleep','interrupted','subdued'].includes(delivery)) {
    delivery = 'composed'; reason = 'Speaking excludes sleep, interruption and withdrawn presentation.';
  }
  const muted = boundary.muted || request.operation === 'muted' || operation === 'muted';
  return {operation, delivery, reason, label: `${operation}${muted && operation !== 'muted' ? ' · conversational mute' : ''}`, muted};
}
