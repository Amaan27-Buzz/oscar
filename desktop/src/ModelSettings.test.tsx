import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {ModelSettings} from './ModelSettings';
import {initialView} from './bridge';
afterEach(cleanup);
it('selects cloud models and restores automatic free routing through the bridge',()=>{
  const run=vi.fn();
  render(<ModelSettings view={{...initialView,link:'online',models:{selected:'',available:['openrouter::fixture/free'],free_only:true}}} busy={false} run={run}/>);
  fireEvent.change(screen.getByLabelText('Model'),{target:{value:'openrouter::fixture/free'}});
  expect(run).toHaveBeenLastCalledWith({kind:'select_model',model:'openrouter::fixture/free'});
  fireEvent.change(screen.getByLabelText('Model'),{target:{value:''}});
  expect(run).toHaveBeenLastCalledWith({kind:'select_model',model:''});
  expect(screen.getByText(/Paid calls and local fallback are disabled/)).toBeTruthy();
});
