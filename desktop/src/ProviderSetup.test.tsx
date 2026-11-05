import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {ProviderSetup} from './ProviderSetup';
import {initialView} from './bridge';
afterEach(cleanup);
const view={...initialView,link:'online',models:{selected:'',available:[],credential_slots:[{id:'fixture-slot',provider:'fixture',configured:false}]}};
it('masks the key and clears the field before awaiting secure admission',()=>{
  const run=vi.fn(()=>new Promise(()=>{}));
  render(<ProviderSetup view={view} busy={false} run={run}/>);
  fireEvent.click(screen.getByRole('button',{name:'Add provider key'}));
  const field=screen.getByLabelText('API key') as HTMLInputElement;
  expect(field.type).toBe('password');
  fireEvent.change(field,{target:{value:'synthetic-only'}});
  fireEvent.click(screen.getByRole('button',{name:'Save key securely'}));
  expect(run).toHaveBeenCalledWith({kind:'setup_provider',slot:'fixture-slot',secret:'synthetic-only'});
  expect(field.value).toBe('');
  expect(screen.queryByText('synthetic-only')).toBeNull();
});
it('preserves existing configured slots and clears a cancelled entry',()=>{
  const run=vi.fn();
  render(<ProviderSetup view={{...view,models:{...view.models,credential_slots:[...view.models.credential_slots,{id:'existing',provider:'existing',configured:true}]}}} busy={false} run={run}/>);
  fireEvent.click(screen.getByRole('button',{name:'Add provider key'}));
  expect(screen.queryByRole('option',{name:'existing'})).toBeNull();
  fireEvent.change(screen.getByLabelText('API key'),{target:{value:'synthetic-only'}});
  fireEvent.click(screen.getByRole('button',{name:'Cancel'}));
  fireEvent.click(screen.getByRole('button',{name:'Add provider key'}));
  expect((screen.getByLabelText('API key') as HTMLInputElement).value).toBe('');
  expect(run).not.toHaveBeenCalled();
});
it('withdraws a credential draft when its Core connection is lost',()=>{
  const run=vi.fn();
  const {rerender}=render(<ProviderSetup view={view} busy={false} run={run}/>);
  fireEvent.click(screen.getByRole('button',{name:'Add provider key'}));
  fireEvent.change(screen.getByLabelText('API key'),{target:{value:'synthetic-only'}});
  rerender(<ProviderSetup view={{...view,link:'offline'}} busy={false} run={run}/>);
  expect(screen.queryByLabelText('API key')).toBeNull();
  expect(run).not.toHaveBeenCalled();
});
