/** @typedef {'Ready'|'Listening'|'Speaking'|'Working'|'Verifying'|'Waiting'|'Blocked'} Presence */
/** @typedef {'quiet'|'background'|'review'|'urgent'} Attention */
/** @typedef {'Passive'|'Aware'|'Guard'|'Away'|'Sleep'} SentryMode */
/** @typedef {{id:string,title:string,presence:Presence,detail:string}} Activity */
/** @typedef {{presence:Presence,attention:Attention,mode:SentryMode,awareness:boolean,mutedUntil:number,turn:boolean,sentry:boolean,microphone:boolean,desktop:boolean,network:boolean,tasks:Activity[],alert:string|null}} Snapshot */

const task = (presence = 'Working', title = 'Preparing your meeting notes') => ({
  id: 'notes', title, presence, detail: 'Organizing the decisions and open questions. Nothing has been sent.'
});
export const scenarios = {
  quiet: 'Everything quiet', background: 'Several background activities', verifying: 'Verifying',
  waiting: 'Waiting', blocked: 'Blocked', review: 'Useful result to review', alert: 'Alert during work',
  long: 'Very long activity title', sentry: 'Sentry unavailable', microphone: 'Microphone unavailable',
  desktop: 'Desktop offline', network: 'No network', speaking: 'Speaking / interrupt'
};
/** Explicit scripted fixtures. Never consumed as real telemetry. @returns {Snapshot} */
export function snapshot(name = 'quiet') {
  const state = { presence: 'Ready', attention: 'quiet', mode: 'Aware', awareness: true,
    mutedUntil: 0, turn: false, sentry: true, microphone: true, desktop: true, network: true, tasks: [], alert: null };
  switch (name) {
    case 'background': state.presence = 'Working'; state.attention = 'background'; state.tasks = [task(), task('Working', 'Checking your saved reading'), task('Waiting', 'Waiting for a document')]; break;
    case 'verifying': state.presence = 'Verifying'; state.attention = 'background'; state.tasks = [task('Verifying')]; break;
    case 'waiting': state.presence = 'Waiting'; state.attention = 'review'; state.tasks = [task('Waiting', 'A detail needs your review')]; break;
    case 'blocked': state.presence = 'Blocked'; state.attention = 'review'; state.tasks = [task('Blocked', 'Document access has expired')]; break;
    case 'review': state.attention = 'review'; state.tasks = [task('Ready', 'Your notes are ready to review')]; break;
    case 'alert': state.presence = 'Working'; state.attention = 'urgent'; state.tasks = [task()]; state.alert = 'A room sensor needs attention'; break;
    case 'long': state.presence = 'Working'; state.attention = 'background'; state.tasks = [task('Working', 'Comparing every decision, unresolved question and reference from this week’s planning conversations before preparing a concise summary for your next meeting')]; break;
    case 'sentry': state.sentry = false; break;
    case 'microphone': state.microphone = false; break;
    case 'desktop': state.desktop = false; break;
    case 'network': state.network = false; break;
    case 'speaking': state.presence = 'Speaking'; break;
  }
  return state;
}
export function acoustic(state, now = Date.now()) {
  if (!state.microphone) return 'Microphone unavailable';
  if (state.mutedUntil > now) return 'Conversation muted';
  if (state.turn) return 'Conversational listening';
  if (!state.awareness) return 'Acoustic awareness disabled';
  if (!state.sentry) return 'Sentry unavailable';
  return 'Sentry aware';
}
export function attention(state) {
  if (state.alert) return { title: 'Something needs attention.', detail: state.alert };
  if (!state.sentry || !state.microphone) return { title: 'Awareness is limited.', detail: 'Some local acoustic signals are unavailable.' };
  if (!state.awareness) return { title: 'A quieter kind of presence.', detail: 'Acoustic awareness is off. Text is still here.' };
  if (!state.network) return { title: 'Quiet on this device.', detail: 'Remote context cannot be refreshed.' };
  if (!state.desktop) return { title: 'Quiet on this device.', detail: 'Desktop context is unavailable.' };
  if (state.presence === 'Blocked') return { title: 'A little help is needed.', detail: 'Access has expired. Work cannot continue yet.' };
  if (state.presence === 'Waiting') return { title: 'Waiting on a detail.', detail: 'Your response will let this continue.' };
  if (state.attention === 'review') return { title: 'Something for you.', detail: 'A useful moment to review, when you’re ready.' };
  if (state.tasks.length) return { title: 'A little work in the background.', detail: 'You can leave it with OSCAR.' };
  return { title: 'Everything is quiet.', detail: 'Nothing needs your attention.' };
}
/** Foreground turns never erase the background objective. */
export function startTurn(state, now = Date.now()) {
  if (!state.microphone || state.mutedUntil > now) return state;
  return { ...state, presence: state.presence === 'Speaking' ? 'Ready' : state.presence, turn: true };
}
export function mute(state, now = Date.now()) { return { ...state, turn: false, mutedUntil: now + 15 * 60_000 }; }
