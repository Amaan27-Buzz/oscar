import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {FirstRun} from './FirstRun';
import {initialView} from './bridge';
afterEach(cleanup);
it('persists preferences in Core and hands a real request to Workspace',async()=>{
  const run=vi.fn(async()=>true),onClose=vi.fn();
  render(<FirstRun view={{...initialView,link:'online',models:{selected:'',available:['openrouter::fixture:free'],free_only:true}}} busy={false} error="" available={true} run={run} onClose={onClose}/>);
  fireEvent.click(screen.getByRole('button',{name:'Meet OSCAR'}));
  await screen.findByLabelText('Your name, if you like');
  fireEvent.change(screen.getByLabelText('Your name, if you like'),{target:{value:'Synthetic owner'}});
  fireEvent.click(screen.getByRole('button',{name:/Spark/}));
  fireEvent.click(screen.getByLabelText('Reduce motion'));
  fireEvent.click(screen.getByRole('button',{name:'Continue'}));
  await screen.findByRole('heading',{name:'A mind of your choosing.'});
  expect(run).toHaveBeenLastCalledWith({kind:'configure_setup',section:'onboarding',value:{completed:false,step:2,preferred_name:'Synthetic owner',tone:'spark',muted:true,reduced_motion:true}});
  fireEvent.click(screen.getByRole('button',{name:'Continue'}));
  await screen.findByLabelText('Your first request');
  fireEvent.change(screen.getByLabelText('Your first request'),{target:{value:'Explain the seasons.'}});
  fireEvent.click(screen.getByRole('button',{name:'Ask OSCAR in Workspace'}));
  await waitFor(()=>expect(onClose).toHaveBeenCalledWith('Explain the seasons.'));
});
it('allows offline skip without inventing saved setup or a connected Core',()=>{
  const run=vi.fn(async()=>true),onClose=vi.fn();
  render(<FirstRun view={initialView} busy={false} error="" available={false} run={run} onClose={onClose}/>);
  expect((screen.getByRole('button',{name:'Meet OSCAR'}) as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getByRole('button',{name:'Skip introduction'}));
  expect(onClose).toHaveBeenCalled();expect(run).not.toHaveBeenCalled();
});
