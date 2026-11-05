import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {PairDevice} from './PairDevice';
import {initialView} from './bridge';
import type {View} from './bridge';
afterEach(cleanup);
const view={...initialView,link:'online',connections:{device_pairing:true,device_invitations:[]}} as unknown as View;
it('stages an exact signed review with separate default-off scope choices',()=>{
 const run=vi.fn();render(<PairDevice view={view} busy={false} run={run}/>);
 fireEvent.click(screen.getByText('Pair a phone'));
 fireEvent.change(screen.getByLabelText('Device name'),{target:{value:'new-alpha-phone'}});
 fireEvent.change(screen.getByLabelText('Phone public registration'),{target:{value:JSON.stringify({installation_id:'synthetic',public_key:'synthetic-public'})}});
 fireEvent.click(screen.getByRole('button',{name:'Review invitation'}));
 expect(run).toHaveBeenCalledWith({kind:'manage_connection',operation:'pair_device',id:'new-alpha-phone',value:JSON.stringify({installation_id:'synthetic',public_key:'synthetic-public',owner_public_key:'',retain:false,approve:false})});
});
it('rejects malformed registration and does not fabricate an issued invitation',()=>{
 const run=vi.fn();render(<PairDevice view={view} busy={false} run={run}/>);
 fireEvent.click(screen.getByText('Pair a phone'));
 fireEvent.change(screen.getByLabelText('Device name'),{target:{value:'bad'}});
 fireEvent.change(screen.getByLabelText('Phone public registration'),{target:{value:'not json'}});
 fireEvent.click(screen.getByRole('button',{name:'Review invitation'}));
 expect(screen.getByRole('alert')).toBeTruthy();expect(run).not.toHaveBeenCalled();
 expect(screen.queryByLabelText('Device-bound invitation')).toBeNull();
});
