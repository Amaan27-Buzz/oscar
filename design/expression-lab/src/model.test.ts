import {describe,it,expect} from 'vitest';
import {arbitrate,canonical,clear,defaults,deliveries,neutral,operations,poseFor,sample,sequences,study,velocityAt} from './model';

describe('lab arbitration',()=>{
  it('fails closed for degraded samples across every operation and delivery',()=>{
    for(const operation of operations) for(const delivery of deliveries) {
      const scene={operation,delivery};
      expect(arbitrate(scene,{...clear,availability:'unavailable'}).operation).toBe('unavailable');
      expect(arbitrate(scene,{...clear,availability:'unavailable'}).delivery).toBe('subdued');
      expect(arbitrate(scene,{...clear,availability:'unknown'}).operation).toBe(operation==='unavailable'?'unavailable':'unknown');
    }
  });
  it('mute cannot be hidden by listening, speech, playful delivery or owner attention',()=>{
    for(const operation of ['listening','speaking','available'] as const) {
      expect(arbitrate({operation,delivery:'amused'},{...clear,muted:true}).operation).toBe('muted');
    }
    const waiting=arbitrate({operation:'listening',delivery:'amused'},{...clear,muted:true,ownerAttention:true});
    expect(waiting.label).toBe('waiting · conversational mute');
    expect(waiting.delivery).toBe('subdued');
    expect(arbitrate({operation:'muted',delivery:'composed'},{...clear,availability:'unavailable'}).label).toBe('unavailable · conversational mute');
  });
  it('never turns pleasure into verification, consent or perception',()=>{
    expect(arbitrate({operation:'available',delivery:'pleased'}).operation).toBe('available');
    expect(arbitrate({operation:'verifying',delivery:'pleased'}).delivery).toBe('focused');
    expect(arbitrate({operation:'error',delivery:'amused'}).delivery).toBe('concerned');
    expect(arbitrate({operation:'waiting',delivery:'pleased'}).operation).toBe('waiting');
    expect(arbitrate({operation:'available',delivery:'attentive'}).operation).toBe('available');
  });
});
describe('geometry and finite motion',()=>{
  it('neutral is the exact canonical two-mark pose',()=>expect(poseFor(neutral)).toEqual(canonical));
  it('all combinations, weights and intensity bounds remain finite and inside the study envelope',()=>{
    for(const operation of operations)for(const delivery of deliveries)for(const weight of [.7,1.5])for(const intensity of [.35,1]) {
      const settings={...defaults,weight,intensity,gaze:{x:10,y:-7}};
      const s=study(canonical,{operation,delivery});
      for(let t=0;t<=1800;t+=20) {
        const p=sample(s,t,settings).pose;
        expect(Object.values(p).every(Number.isFinite)).toBe(true);
        expect(Math.abs(p.x)).toBeLessThan(32);expect(Math.abs(p.y)).toBeLessThan(26);
        expect(Math.abs(p.tilt)).toBeLessThan(9);
        expect(p.eye).toBeGreaterThanOrEqual(0);expect(p.eye).toBeLessThan(1.3);
        expect(p.opening).toBeGreaterThanOrEqual(0);expect(p.opening).toBeLessThanOrEqual(1);
        expect(Math.abs(p.gx)).toBeLessThanOrEqual(14);expect(Math.abs(p.gy)).toBeLessThanOrEqual(10);
      }
    }
  });
  it('retargets mid-travel without a pose jump and retains body velocity',()=>{
    const first=study(canonical,{operation:'available',delivery:'curious'});
    const at=sample(first,100,defaults).pose;
    const velocity=velocityAt(first,100,defaults);
    const next=study(at,{operation:'available',delivery:'interrupted'},velocity);
    expect(sample(next,0,defaults).pose).toEqual(at);
    const after=velocityAt(next,0,defaults);
    expect(after.x).toBeCloseTo(velocity.x,0);
    expect(sample(next,next.duration,defaults).pose).toEqual(poseFor({operation:'available',delivery:'attentive'}));
  });
  it('reduced motion never blinks, travels or cadences',()=>{
    const s=study(canonical,{operation:'speaking',delivery:'composed'},undefined,true);
    const target=poseFor(s.beats[0].scene);
    for(const t of [0,100,200,650,1050,1800])expect(sample(s,t,defaults,true).pose).toEqual(target);
  });
  it('unavailable and mute stop speaking cadence at the same sample',()=>{
    const s=study(canonical,{operation:'speaking',delivery:'composed'});
    for(const boundary of [{...clear,availability:'unavailable' as const},{...clear,muted:true}]) {
      const at=sample(s,650,defaults,false,boundary);
      expect(at.resolved.operation).not.toBe('speaking');
      const settled=sample(s,1800,defaults,false,boundary).pose;
      expect(at.pose.y).toBeCloseTo(settled.y,3);
      expect(at.pose.eye).toBe(settled.eye);expect(at.pose.arc).toBe(settled.arc);
    }
  });
  it('all ten sequences have ordered explicit events and end in a held pose',()=>{
    expect(sequences).toHaveLength(10);
    for(const sequence of sequences) {
      const duration=sequence.beats.at(-1)!.at+1800;
      const s={from:canonical,velocity:study(canonical,neutral).velocity,beats:sequence.beats,duration,blink:false};
      expect(sequence.beats[0].at).toBe(0);
      expect(sequence.beats.map(b=>b.at)).toEqual(sequence.beats.map(b=>b.at).sort((a,b)=>a-b));
      expect(sample(s,duration,defaults).pose).toEqual(sample(s,duration+10000,defaults).pose);
      for(const beat of sequence.beats)expect(sample(s,beat.at,defaults).resolved.operation).toBe(arbitrate(beat.scene).operation);
    }
  });
  it('brief reactions recover; interruption cancels their queued recovery',()=>{
    for(const delivery of ['amused','pleased','surprised'] as const) {
      const s=study(canonical,{operation:'available',delivery});
      expect(sample(s,s.duration,defaults).resolved.delivery).toBe('composed');
      const at=sample(s,500,defaults).pose;
      const interrupted=study(at,{operation:'unavailable',delivery:'subdued'});
      expect(sample(interrupted,10000,defaults).resolved.operation).toBe('unavailable');
      expect(sample(s,s.duration,defaults,true).resolved.operation).toBe('available');
    }
  });
  it('closed-eye rest is invariant at every intensity, and eye opening respects degraded priority',()=>{
    for(const intensity of [.35,.75,1]) {
      expect(poseFor({operation:'available',delivery:'asleep'},intensity).eye).toBe(0);
      expect(poseFor({operation:'available',delivery:'asleep'},intensity).opening).toBe(0);
      expect(poseFor({operation:'speaking',delivery:'composed'},intensity).opening).toBeGreaterThan(0);
      expect(poseFor({operation:'unavailable',delivery:'attentive'},intensity).opening).toBe(0);
    }
  });
  it('attention acquires before zero-velocity physical travel; rapid retargeting remains bounded',()=>{
    let s=study(canonical,{operation:'available',delivery:'attentive'});
    const at40=sample(s,40,defaults).pose;
    expect(at40.x).toBe(0);expect(at40.gx).toBeGreaterThan(0);
    for(let i=0;i<40;i++) {
      const current=sample(s,80,defaults).pose;
      expect(Math.abs(current.x)).toBeLessThan(32);expect(Math.abs(current.y)).toBeLessThan(26);
      s=study(current,{operation:'available',delivery:i%2?'surprised':'concerned'},velocityAt(s,80,defaults));
      expect(sample(s,0,defaults).pose).toEqual(current);
    }
  });
  it('invalid operation and boundary samples remain unknown',()=>{
    expect(arbitrate({operation:'corrupt' as never,delivery:'amused'}).operation).toBe('unknown');
    expect(arbitrate(neutral,{...clear,availability:'corrupt' as never}).operation).toBe('unknown');
  });
});
