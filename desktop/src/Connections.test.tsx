import {fireEvent,render,screen} from '@testing-library/react';
import {describe,expect,it,vi} from 'vitest';
import {Connections} from './Connections';
import {initialView} from './bridge';
import type {ConnectionsView} from './bridge';

const data:ConnectionsView={identity:{id:'oscar-id',display_name:'OSCAR',operational_email:null,status:'active'},accounts:[{id:'stable-account',provider:'fixture',tenant:'tenant',subject:'verified-subject',alias:'Research',identity_class:'owner-delegated',generation:1,status:'connected',remote_revocation:'UNKNOWN',services:[]}],plugins:[],access:'Ask',enrollment:'Trusted setup required',observed_at_ms:100};
describe('Accounts and connections',()=>{
  it('uses actual state and submits a change for signed review',()=>{
    const run=vi.fn().mockResolvedValue(true);
    render(<Connections view={{...initialView,link:'online',connections:data}} busy={false} run={run}/>);
    fireEvent.click(screen.getByRole('button',{name:'Research · Connected'}));
    fireEvent.change(screen.getByLabelText('Account name'),{target:{value:'Renamed'}});
    fireEvent.click(screen.getByRole('button',{name:'Review name change'}));
    expect(run).toHaveBeenCalledWith({kind:'manage_connection',operation:'rename_account',id:'stable-account',value:'Renamed'});
    fireEvent.click(screen.getByRole('button',{name:'Review disable account'}));
    expect(run).toHaveBeenCalledWith({kind:'manage_connection',operation:'disconnect_account',id:'stable-account',value:''});
  });
  it('withdraws accounts immediately when connection is unavailable',()=>{
    render(<Connections view={{...initialView,link:'unavailable',connections:data}} busy={false} run={vi.fn()}/>);
    expect(screen.queryByText('Research')).toBeNull();
    expect(screen.getByText('Connect to OSCAR to inspect your accounts and tools.')).toBeTruthy();
  });
});
