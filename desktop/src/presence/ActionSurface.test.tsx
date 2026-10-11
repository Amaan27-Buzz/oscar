import {cleanup,render,screen} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import {initialView} from '../bridge';
import type {Task} from '../bridge';
import {ActionSurface} from './ActionSurface';
afterEach(cleanup);
const task:Task={task_id:'active',state:'executing',mode:'Ask',description:'Existing work',target:'worker',blocker:null,actions:[],generation:1,evidence_ids:[],response:null,response_status:null,value:null,epistemic:null};
it.each(['current','other'] as const)('blocks competing proposals for an active %s task across modes',location=>{
  const view={...initialView,capabilities:[{id:'write',node:'worker',kind:'file_write',label:'Write file',summary:'Reference',risk:'low',operations:['write_file'],programs:[],applications:[]}],current:location==='current'?task:null,tasks:location==='other'?[{...task,mode:'Edit',state:'verifying'}]:[]};
  render(<ActionSurface view={view} draft={{id:'write',operation:'write_file',value:'proof.txt',text:'reference'}} setDraft={vi.fn()} available busy={false} run={vi.fn()} discard={vi.fn()}/>);
  expect(screen.getByText('Existing work')).toBeTruthy();
  expect((screen.getByRole('button',{name:'Prepare action'}) as HTMLButtonElement).disabled).toBe(true);
});
