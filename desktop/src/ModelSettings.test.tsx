import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {ModelSettings} from './ModelSettings';
import {initialView} from './bridge';
afterEach(cleanup);
it('requires an explicit free-plan assertion before saving account status',async()=>{
  const run=vi.fn(async()=>true);
  render(<ModelSettings view={{...initialView,link:'online',models:{selected:'',available:[],free_only:true,provider_plans:[{id:'google',confirmed:false}]}}} busy={false} run={run}/>);
  fireEvent.click(screen.getByRole('button',{name:'Review free plan'}));
  expect((screen.getByRole('button',{name:'Confirm free plan'}) as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getByLabelText('This account is on its Free plan and billing is disabled.'));
  fireEvent.click(screen.getByRole('button',{name:'Confirm free plan'}));
  expect(run).toHaveBeenCalledWith({kind:'configure_setup',section:'provider_plan',value:{provider:'google',plan:'free',billing_enabled:false}});
});
it('selects cloud models and restores automatic free routing through the bridge',()=>{
  const run=vi.fn();
  render(<ModelSettings view={{...initialView,link:'online',models:{selected:'',available:['openrouter::fixture/free'],free_only:true}}} busy={false} run={run}/>);
  fireEvent.change(screen.getByLabelText('Model'),{target:{value:'openrouter::fixture/free'}});
  expect(run).toHaveBeenLastCalledWith({kind:'select_model',model:'openrouter::fixture/free'});
  fireEvent.change(screen.getByLabelText('Model'),{target:{value:''}});
  expect(run).toHaveBeenLastCalledWith({kind:'select_model',model:''});
  expect(screen.getByText(/Paid calls and local fallback are disabled/)).toBeTruthy();
});
