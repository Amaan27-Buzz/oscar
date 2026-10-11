import {act,cleanup,fireEvent,render,screen} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import {initialView} from '../bridge';
import type {Task,Review} from '../bridge';
import {Activity} from './Activity';
afterEach(()=>{cleanup();vi.useRealTimers();});
const task:Task={task_id:'one',state:'planned',description:'Scoped file task',target:'worker',blocker:null,actions:['approve','deny'],generation:1,evidence_ids:[],response:null,response_status:null,value:null,epistemic:null};
const review:Review={review_id:'exact',task_id:'one',operation:'approve',description:'Scoped file task',target:'worker',capability:'file_write',reason:'Owner request',consequence:'Write scoped file',policy_reason:'Current grant',evidence_state:'planned',review:'{"path":"proof.txt"}',expires_at_ms:Date.now()+30000};
it('opening Activity does not request approval and only uses exact advertised controls',()=>{
  const run=vi.fn();render(<Activity view={{...initialView,tasks:[task],current:task}} available busy={false} run={run} back={vi.fn()}/>);
  expect(run).not.toHaveBeenCalled();fireEvent.click(screen.getByRole('button',{name:'Review denial'}));
  expect(run).toHaveBeenCalledWith({kind:'review',task_id:'one',operation:'deny'});
  expect(screen.queryByRole('button',{name:/Retry|Resume/})).toBeNull();
});
it('a fresh current task appears before the next shared poll without duplication',()=>{
  render(<Activity view={{...initialView,tasks:[],current:task}} available busy={false} run={vi.fn()} back={vi.fn()}/>);
  expect(screen.getByRole('region',{name:'Active work'}).textContent).toContain('Approval required');
  expect(screen.getByRole('region',{name:'Active work'}).textContent).toContain('1');
});
it('expired or changed approval cannot reach native confirmation; dismissal grants nothing',()=>{
  vi.useFakeTimers();const run=vi.fn();const view={...initialView,tasks:[task],current:task,review:{...review,expires_at_ms:Date.now()+1000}};
  const {rerender}=render(<Activity view={view} available busy={false} run={run} back={vi.fn()}/>);
  const button=screen.getByRole('button',{name:'Continue to native confirmation'}) as HTMLButtonElement;
  expect(button.disabled).toBe(false);act(()=>vi.advanceTimersByTime(1001));expect(button.disabled).toBe(true);
  fireEvent.click(button);expect(run).not.toHaveBeenCalled();
  rerender(<Activity view={{...view,review:{...review,task_id:'other'}}} available busy={false} run={run} back={vi.fn()}/>);
  expect(button.disabled).toBe(true);fireEvent.click(screen.getByRole('button',{name:'Dismiss review'}));expect(run).toHaveBeenCalledWith({kind:'confirm',review_id:'exact',accept:false});
});
it('offline history and unadvertised actions never grant control',()=>{
  const run=vi.fn();render(<Activity view={{...initialView,current:{...task,state:'partially_verified',actions:[],response:'reported only',response_status:'REPORTED'},tasks:[{...task,state:'partially_verified',actions:[]}]}} available={false} busy={false} run={run} back={vi.fn()}/>);
  expect(screen.getByText('REPORTED')).toBeTruthy();expect(screen.getByText(/Displayed history grants no authority/)).toBeTruthy();expect(screen.queryByRole('button',{name:'Review approval'})).toBeNull();
});
it.each(['RECALLED','INFERRED'])('preserves %s recall sources and temporal uncertainty when inspecting a result',status=>{
  render(<Activity view={{...initialView,current:{...task,state:'partially_verified',actions:[],response:'Historical reference',response_status:status,source_event_ids:['canonical-event']}}} available busy={false} run={vi.fn()} back={vi.fn()}/>);
  expect(screen.getByText(status)).toBeTruthy();expect(screen.getByText(/Earlier retained evidence; current facts may differ/)).toBeTruthy();expect(screen.getByText('canonical-event')).toBeTruthy();
});
