import { test } from 'node:test';
import assert from 'node:assert/strict';
import { snapshot, acoustic, attention, mute, startTurn, scenarios } from './state.js';

test('acoustics, presence and background objectives remain independent', () => {
  const work = snapshot('background');
  const turn = startTurn(work, 100);
  assert.equal(acoustic(turn, 100), 'Conversational listening');
  assert.equal(turn.presence, 'Working');
  assert.equal(turn.tasks.length, 3);
  const muted = mute(turn, 100);
  assert.equal(acoustic(muted, 101), 'Conversation muted');
  assert.equal(muted.awareness, true);
  assert.equal(startTurn(muted, 101), muted);
  assert.equal(acoustic(muted, 900101), 'Sentry aware');
  assert.equal(acoustic({...work, awareness:false}), 'Acoustic awareness disabled');
  assert.equal(startTurn(snapshot('speaking')).presence, 'Ready');
});
test('unavailable sources cannot imply the room is quiet; alerts outrank working', () => {
  for (const name of ['sentry', 'microphone', 'desktop']) assert.notEqual(attention(snapshot(name)).title, 'Everything is quiet.');
  assert.equal(attention(snapshot('alert')).title, 'Something needs attention.');
  assert.equal(snapshot('alert').tasks.length, 1);
  assert.equal(acoustic(snapshot('network')), 'Sentry aware');
  const noMic = snapshot('microphone'); assert.equal(startTurn(noMic), noMic);
  for (const name of Object.keys(scenarios)) assert.ok(attention(snapshot(name)).title);
});
