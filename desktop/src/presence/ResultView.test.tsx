import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {afterEach,describe,expect,it,vi} from 'vitest';
import type {Task} from '../bridge';
import {ResultView} from './ResultView';
afterEach(cleanup);
const task:Task={task_id:'real',state:'partially_verified',description:'Reference result',target:'fixture',blocker:null,actions:[],generation:1,evidence_ids:[],response:'long line '.repeat(300),response_status:'REPORTED',value:null,epistemic:null};
describe('bounded Core response',()=>{
  it('short multiline text is complete rather than falsely marked truncated',()=>{
    const response='one\n\ntwo\n\nthree\n\nfour';
    render(<ResultView task={{...task,response}} expanded={false} read={()=>{}} inspect={()=>{}} askAgain={()=>{}}/>);
    expect(screen.getByRole('region',{name:'OSCAR response'}).textContent).toBe(response);
  });
  it('shows an excerpt and an explicit reading path without fabricating verification',()=>{
    const read=vi.fn();render(<ResultView task={task} expanded={false} read={read} inspect={()=>{}} askAgain={()=>{}}/>);
    expect(screen.getByRole('region',{name:'OSCAR response'}).textContent!.length).toBe(601);
    expect(screen.getByText('REPORTED')).toBeTruthy();fireEvent.click(screen.getByRole('button',{name:'Read response'}));expect(read).toHaveBeenCalledOnce();
  });
  it('expanded recall stays sourced and announces Core truncation rather than claiming complete output',()=>{
    render(<ResultView task={{...task,response_status:'RECALLED',source_event_ids:['event-1'],response_truncated:true}} expanded read={()=>{}} inspect={()=>{}} askAgain={()=>{}}/>);
    const region=screen.getByRole('region',{name:'OSCAR response'});expect(region.textContent).toBe(task.response);expect(document.activeElement).toBe(region);
    expect(screen.getByText(/Earlier retained evidence/)).toBeTruthy();expect(screen.getByText(/Only an excerpt is available/)).toBeTruthy();fireEvent.click(screen.getByRole('button',{name:'Recall sources'}));expect(screen.getByText('event-1')).toBeTruthy();
  });
});
