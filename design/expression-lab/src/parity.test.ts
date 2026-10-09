import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {describe,it,expect} from 'vitest';
import {canonical,defaults,sample,study} from '../../../expression/core/motion';
import {ExpressionController} from '../../../expression/core/controller';
import {validateEvent} from '../../../expression/core/contract';
const fixtures=JSON.parse(readFileSync(resolve('../../expression/fixtures/reference-v1.json'),'utf8'));
describe('shared cross-language references',()=>{
  it('rejects the shared malformed-wire corpus',()=>{
    expect(fixtures.malformedInputs).toHaveLength(8);
    for(const fixture of fixtures.malformedInputs)expect(validateEvent(fixture.raw,1000000),fixture.name).toBeNull();
  });
  it('retains all sixteen reviewed v3 pose cases after extraction',()=>{
    expect(fixtures.poseCases).toHaveLength(16);
    for(const fixture of fixtures.poseCases) {
      const pose=sample(study(canonical,fixture.scene),fixture.at,defaults,fixture.reduced).pose;
      for(const key of Object.keys(fixture.expected))expect(pose[key as keyof typeof pose],`${fixture.name}: ${key}`).toBeCloseTo(fixture.expected[key],6);
    }
  });
  it('replays the same admission, state, priority, geometry and animation outcomes',()=>{
    expect(fixtures.traces).toHaveLength(5);
    for(const trace of fixtures.traces) {
      const engine=new ExpressionController({kind:'fixture',id:'cross-v1'});
      for(const step of trace.steps) {
        const now=1000000+step.at,admission=step.event?engine.receive(step.event,now):null;
        if(step.suspend)engine.suspend();if('reduce'in step)engine.setReducedMotion(step.reduce,now);
        const value=engine.snapshot(now),expected=step.expected;
        const {pose:ignored,...state}=expected;
        expect({admission,operation:value.resolved.operation,delivery:value.resolved.delivery,muted:value.resolved.muted,generation:value.generation,priority:value.priority,animation:value.animation,moving:value.moving,records:engine.takeAnimationRecords()}).toEqual(state);
        for(const key of Object.keys(expected.pose))expect(value.pose[key as keyof typeof value.pose]).toBeCloseTo(expected.pose[key],6);
      }
    }
  });
});
