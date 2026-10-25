import {expect,it} from 'vitest';
import {executiveSummary} from './Automations';
it('admits reported Core responsibilities without inventing execution state',()=>{
  const input={version:1,health:'operational',running:true,goals:[{id:'g',goal:'Reviewed work',state:'completed',verified_runs:1,max_runs:1,task_ids:['t']}],workers:[]};
  expect(executiveSummary(input)?.goals[0].verified_runs).toBe(1);
  const reported={...input,goals:[{...input.goals[0],state:'reported',verified_runs:0}]};
  expect(executiveSummary(reported)?.goals[0]).toMatchObject({state:'reported',verified_runs:0});
  expect(executiveSummary({...reported,goals:[{...reported.goals[0],state:'invented'}]})).toBeNull();
  for(const patch of [{goals:null},{version:2},{running:'true'},{goals:[{...input.goals[0],verified_runs:2}]}])expect(executiveSummary({...input,...patch})).toBeNull();
});
