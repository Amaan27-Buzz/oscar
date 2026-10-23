import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {afterEach,describe,expect,it,vi} from 'vitest';
import {Connections} from './Connections';
import {initialView} from './bridge';
import type {ConnectionsView} from './bridge';

const data:ConnectionsView={identity:{id:'oscar-id',display_name:'OSCAR',operational_email:null,status:'active'},accounts:[{id:'stable-account',provider:'fixture',tenant:'tenant',subject:'verified-subject',alias:'Research',identity_class:'owner-delegated',generation:1,status:'connected',remote_revocation:'UNKNOWN',services:[]}],plugins:[],access:'Ask',enrollment:'Trusted setup required',observed_at_ms:100};
describe('Accounts and connections',()=>{
  afterEach(cleanup);
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
  it('reviews resource access without claiming a verified person and can reconnect the same grant',()=>{
    const run=vi.fn().mockResolvedValue(true);
    const provider={id:'resource-app',provider:'mcp-resource',service:'mcp:resource-app',scopes:['files:read'],resource:'https://mcp.example/mcp',issuer:'https://auth.example/tenant',redirect_uri:'http://127.0.0.1:48123/oauth/callback',configured:true};
    const grant={...data.accounts[0],id:'grant',provider:'mcp-resource',tenant:provider.issuer,subject:'opaque-local-grant',alias:'Resource access',identity_class:'resource-grant',services:[{id:provider.service,scopes:['files:read'],expires_at:null,restrictions:[]}]};
    render(<Connections view={{...initialView,link:'online',connections:{...data,accounts:[grant,{...grant,id:'other',alias:'Other resource',services:[]}],providers:[provider]}}} busy={false} run={run}/>);
    fireEvent.click(screen.getByRole('button',{name:'Connect an account'}));
    expect(screen.queryByLabelText('Who owns this account?')).toBeNull();
    expect(screen.getByText(/This grant does not verify a provider person identity/)).toBeTruthy();
    expect(screen.queryByRole('option',{name:/Other resource/})).toBeNull();
    fireEvent.change(screen.getByLabelText('Account connection'),{target:{value:'grant'}});
    fireEvent.click(screen.getByLabelText('files:read'));
    fireEvent.click(screen.getByRole('button',{name:'Review connect account'}));
    expect(run).toHaveBeenCalledWith({kind:'manage_connection',operation:'begin_account',id:'resource-app',value:JSON.stringify({alias:'Resource access',scopes:['files:read'],identity_class:'resource-grant',account_id:'grant'})});
    fireEvent.click(screen.getByRole('button',{name:'Resource access · Connected'}));
    expect(screen.getByText('MCP resource access · person identity not verified',{exact:false})).toBeTruthy();
    expect(screen.getByText('Grant ID')).toBeTruthy();
  });
});
