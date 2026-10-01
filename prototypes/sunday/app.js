import { snapshot, scenarios, acoustic, attention, startTurn, mute } from './state.js';
import { createPresence } from './presence.js';

const $ = id => document.getElementById(id);
let state = snapshot(new URLSearchParams(location.search).get('scenario') || 'quiet');
let composing = false;
let dockAnimation;
let presenceAnimation;
const preference = matchMedia('(prefers-reduced-motion: reduce)');
const movePuck = createPresence(document.querySelector('.avatar'), () => preference.matches || $('motion').checked);
const escape = value => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
Object.entries(scenarios).forEach(([value, label]) => $('scenario').add(new Option(label, value)));
$('scenario').value = new URLSearchParams(location.search).get('scenario') || 'quiet';

function render() {
  const previousDock = $('input-surface').getBoundingClientRect();
  const previousObject = document.querySelector('.avatar').getBoundingClientRect();
  dockAnimation?.cancel();
  presenceAnimation?.cancel();
  const sentryPage = location.hash === '#awareness';
  const acousticState = acoustic(state);
  const message = attention(state);
  const presence = state.turn ? 'Listening' : state.presence;
  $('phone').dataset.surface = sentryPage ? 'awareness' : 'home';
  $('phone').dataset.input = composing || state.turn ? 'expanded' : 'compact';
  $('phone').dataset.attention = state.alert ? 'urgent' : state.attention;
  $('back').hidden = !sentryPage; $('home-brand').hidden = sentryPage;
  $('presence-label').textContent = presence;
  document.querySelector('.presence-caption').hidden = sentryPage ? presence === 'Ready' : true;
  const homeTitle = state.alert ? 'Needs attention.' : !state.sentry || !state.microphone ? 'Partly aware.' : !state.awareness ? 'Awareness off.' : !state.desktop || !state.network ? 'Here, locally.' : state.turn ? 'Listening.' : ({Ready:state.tasks.length ? 'For you.' : 'Quiet.', Working:'Working.', Verifying:'Verifying.', Waiting:'Waiting.', Blocked:'Blocked.', Speaking:'Speaking.'})[presence];
  $('headline').textContent = sentryPage ? acousticState : state.turn ? 'Listening.' : homeTitle;
  $('description').textContent = sentryPage
    ? acousticState === 'Sentry aware' ? 'Local · no transcription'
      : acousticState === 'Conversation muted' ? state.awareness && state.sentry && state.microphone ? 'Local awareness is still on.' : 'Local awareness is off or unavailable.'
      : acousticState === 'Conversational listening' ? 'Conversational turn · preview only'
      : acousticState === 'Acoustic awareness disabled' ? 'Voice available on demand.'
      : 'Text is still available.'
    : !state.sentry || !state.microphone || !state.awareness || !state.desktop || !state.network ? message.detail : '';
  $('description').hidden = !$('description').textContent;
  $('privacy').setAttribute('aria-label', state.turn ? 'Inspect active-turn privacy state' : 'Inspect local-first privacy state');
  $('context').hidden = sentryPage ? !state.alert : !state.tasks.length && !state.alert && state.network;
  $('awareness-link').hidden = sentryPage;
  $('sentry-controls').hidden = !sentryPage;
  $('acoustic-label').textContent = acousticState;
  $('awareness-link').setAttribute('aria-label', `Open Awareness: ${acousticState}`);
  $('mode-label').textContent = state.mode;
  $('mode-button').setAttribute('aria-label', `Change Sentry mode, currently ${state.mode}`);
  $('attention-note').hidden = !sentryPage;
  $('attention-note').textContent = state.alert ? 'Needs attention.' : !state.sentry || !state.microphone || !state.awareness ? 'Room state unknown.' : !state.desktop || !state.network ? 'Remote state unknown.' : 'Quiet.';
  $('mute').textContent = state.mutedUntil > Date.now() ? 'Resume' : 'Mute 15m';
  $('mute').disabled = !state.microphone;
  $('mute').setAttribute('aria-label', state.mutedUntil > Date.now() ? 'Resume conversational listening' : 'Mute conversation for 15 minutes');
  $('mute').title = state.mutedUntil > Date.now() ? 'Resumes at ' + new Intl.DateTimeFormat(undefined, {hour:'numeric', minute:'2-digit'}).format(state.mutedUntil) : 'Pause ordinary conversational turns; local awareness follows its own policy.';
  const activity = state.tasks[0];
  $('activity').hidden = !activity && !state.alert && state.network;
  $('activity-meta').textContent = state.alert ? 'Attention required' : !state.network ? 'Connection unavailable' : activity?.presence === 'Ready' ? 'For review' : activity?.presence || '';
  $('activity-title').textContent = state.alert || (!state.network ? 'You’re offline.' : activity?.title || '');
  $('activity-detail').textContent = state.alert ? 'Background work continues' : !state.network ? 'Remote updates unavailable' : state.tasks.length > 1 ? `+${state.tasks.length - 1} in the background` : '';
  $('activity-detail').hidden = !$('activity-detail').textContent;
  $('input-hint').textContent = !state.microphone ? 'Microphone unavailable' : state.mutedUntil > Date.now() ? 'Conversation muted' : state.turn || composing ? '' : !state.awareness || !state.sentry ? 'Wake detection off' : '';
  $('input-hint').hidden = !$('input-hint').textContent;
  $('input-surface').dataset.expanded = String(composing || state.turn);
  $('voice').disabled = !state.microphone || state.mutedUntil > Date.now();
  $('voice').setAttribute('aria-label', presence === 'Speaking' ? 'Preview barge-in and conversational listening' : 'Preview conversational listening');
  $('type').hidden = composing || state.turn; $('voice').hidden = composing || state.turn;
  $('composer').hidden = !composing; $('voice-preview').hidden = !state.turn || composing;
  movePuck(state.alert ? 'Alert' : presence, state.mutedUntil > Date.now() || !state.microphone);
  // The compact input becomes the expanded input; state is already applied before motion.
  const nextDock = $('input-surface').getBoundingClientRect();
  const nextObject = document.querySelector('.avatar').getBoundingClientRect();
  if (!preference.matches && !$('motion').checked && Math.abs(previousObject.top - nextObject.top) > 2) {
    presenceAnimation = document.querySelector('.presence-composition').animate([
      {transform:`translateY(${previousObject.top - nextObject.top}px)`}, {transform:'translateY(0)'}
    ], {duration:220, easing:'cubic-bezier(.23,1,.32,1)'});
  }
  if (!preference.matches && !$('motion').checked && previousDock.height && Math.abs(previousDock.height - nextDock.height) > 2) {
    dockAnimation = $('input-surface').animate([
      {height:previousDock.height + 'px', width:previousDock.width + 'px', transform:`translateY(${previousDock.top - nextDock.top}px)`},
      {height:nextDock.height + 'px', width:nextDock.width + 'px', transform:'translateY(0)'}
    ], {duration:220, easing:'cubic-bezier(.23,1,.32,1)'});
  }
}
function disclose(title, body) {
  $('detail-title').textContent = title;
  $('detail-body').innerHTML = body;
  const phoneBounds = $('phone').getBoundingClientRect();
  $('detail').style.left = phoneBounds.left + 'px';
  $('detail').style.width = phoneBounds.width + 'px';
  $('detail').showModal();
}
function showSources() {
  disclose('A little context.', `<p class="sheet-intro">${escape(attention(state).detail)} These are scripted observations, not live evidence.</p>
    <dl class="source-list"><div><dt>This device</dt><dd>${escape(acoustic(state))}</dd>${state.sentry && state.microphone && state.awareness ? '<dd>Wake detection, speech presence and configured sounds · processed locally</dd>' : ''}</div><div><dt>Desktop context</dt><dd>${state.desktop && state.network ? 'Available in this scenario' : 'Unavailable · current state unknown'}</dd></div><div><dt>Room events</dt><dd>${state.sentry && state.microphone && state.awareness ? state.alert ? 'Sensor event reported · not yet verified' : 'No urgent event in this scenario' : 'Unavailable · no quiet-room claim'}</dd></div></dl>
    <details><summary>Source & evidence</summary><p>Source: local review fixture. Freshness: scenario selection. No microphone, sensor or desktop is connected. Voice Map recognition does not grant permission.</p></details>`);
}
$('awareness-link').onclick = () => { location.hash = 'awareness'; };
$('back').onclick = () => { location.hash = 'home'; };
$('privacy').onclick = () => disclose('Local by default.', `<p class="sheet-intro">${escape(acoustic(state))}</p><dl class="source-list"><div><dt>Local acoustic signals</dt><dd>${state.awareness && state.sentry && state.microphone ? 'Enabled in this scenario' : 'Unavailable or disabled'}</dd></div><div><dt>Conversational STT</dt><dd>${state.turn ? 'Active-turn preview only' : 'Inactive'}</dd></div><div><dt>Continuous cloud audio</dt><dd>Off</dd></div><div><dt>Raw audio retention</dt><dd>Off</dd></div></dl><p>This study captures no audio. In production, transcription and retention require their own permission and policy.</p><details><summary>Mute is not a hardware switch</summary><p>Conversation mute pauses ordinary turns. Configured local wake, perception or safety/reflex paths may remain available. Disabling acoustic awareness requests a software policy change; it is not proof that every microphone is physically off.</p></details>`);
$('sources').onclick = showSources;
$('mode-button').onclick = () => {
  disclose('Sentry mode', `<p class="sheet-intro">Choose how much context OSCAR attends to. This changes the study only.</p><fieldset class="mode-options"><legend class="sr-only">Sentry mode</legend>${Object.entries({Passive:'Wake and basic device health',Aware:'Quiet local context',Guard:'Configured security events',Away:'Configured events while you’re away',Sleep:'Keep nonurgent speech quiet'}).map(([mode, desc]) => `<label><input type="radio" name="mode" value="${mode}" ${state.mode === mode ? 'checked' : ''}><span><strong>${mode}</strong><small>${desc}</small></span></label>`).join('')}</fieldset><label class="awareness-toggle"><span>Local acoustic awareness</span><input type="checkbox" id="awareness-enabled" ${state.awareness ? 'checked' : ''}></label><p>Mode changes never grant new permissions. Guard and Away use only previously authorized sources.</p>`);
  $('detail-body').querySelectorAll('[name=mode]').forEach(input => input.onchange = () => { state.mode = input.value; render(); });
  $('awareness-enabled').onchange = event => { state.awareness = event.target.checked; render(); };
};
$('mute').onclick = () => { state = state.mutedUntil > Date.now() ? {...state, mutedUntil:0} : mute(state); render(); };
$('activity').onclick = () => {
  if (state.alert) { showSources(); return; }
  const activity = state.tasks[0];
  disclose(activity?.title || 'Connection unavailable', `<p class="sheet-intro">${escape(!state.network ? 'Remote state cannot be refreshed. No requests have been queued or sent.' : activity?.presence === 'Blocked' ? 'Document access has expired. Reconnecting belongs to the future runtime; this study cannot restore access.' : activity?.presence === 'Verifying' ? 'The result has been reported. Independent verification is still in progress.' : activity?.detail || '')}</p><dl class="source-list"><div><dt>Status</dt><dd>${escape(activity?.presence || 'Unavailable')}</dd></div><div><dt>Evidence</dt><dd>Scripted review fixture · not verified</dd></div></dl><details><summary>Activity context</summary><p>${escape(activity?.title || 'No current activity')}</p><p>Background objectives persist when you switch input modalities. Only one activity is surfaced on Home.</p></details>${state.tasks.length > 1 ? `<details><summary>Other background activities</summary><dl class="source-list">${state.tasks.slice(1).map(item => `<div><dt>${escape(item.title)}</dt><dd>${escape(item.presence)}</dd></div>`).join('')}</dl></details>` : ''}`);
};
function compose() { state = {...state, turn:false}; composing = true; render(); $('draft').focus({preventScroll:true}); }
$('type').onclick = compose; $('voice-to-text').onclick = compose;
$('voice').onclick = () => { state = startTurn(state); composing = false; render(); };
$('stop-voice').onclick = () => { state = {...state, turn:false}; render(); $('voice').focus({preventScroll:true}); };
$('close-compose').onclick = () => { composing = false; render(); $('type').focus({preventScroll:true}); };
$('composer').onsubmit = event => { event.preventDefault(); $('notice').textContent = $('draft').value.trim() ? 'Draft kept for this visit. Execution is not connected.' : 'Write a thought first.'; };
$('close-detail').onclick = () => $('detail').close();
$('detail').onclick = event => { if (event.target === $('detail')) { const bounds = $('detail').getBoundingClientRect(); if (event.clientY < bounds.top || event.clientX < bounds.left || event.clientX > bounds.right) $('detail').close(); } };
$('scenario').onchange = event => { state = snapshot(event.target.value); composing = false; $('notice').textContent = ''; $('detail').close(); render(); };
$('theme').onchange = event => { document.documentElement.dataset.theme = event.target.value; };
$('motion').onchange = () => { document.documentElement.dataset.reduced = String($('motion').checked); render(); }; preference.addEventListener('change', render);
addEventListener('hashchange', () => { render(); window.scrollTo({top:0, behavior:'instant'}); });
addEventListener('keydown', event => { if (event.key === 'Escape' && !$('detail').open) { state = {...state, turn:false}; composing = false; render(); } });
// Expiry remains correct after tab suspension; it does not depend on animation callbacks.
setInterval(() => { if (state.mutedUntil && state.mutedUntil <= Date.now()) { state.mutedUntil = 0; render(); } }, 1000);
render();
window.scrollTo({top:0, behavior:'instant'});
