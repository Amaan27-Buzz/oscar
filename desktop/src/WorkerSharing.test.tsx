import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {WorkerSharing} from './WorkerSharing';
import {initialView} from './bridge';
const connection={endpoint:'https://core.example',installation_id:'synthetic',node_id:'desktop',workspace:'actual-enrolled-workspace',public_key:'public',owner_public_key:'public',status:'online'};
afterEach(cleanup);
it('requires explicit workspace, installed runtime and capability review',()=>{
 const run=vi.fn();render(<WorkerSharing view={{...initialView,link:'online',connection}} busy={false} run={run}/>);
 fireEvent.click(screen.getByRole('button',{name:'Set up Desktop sharing'}));
 const start=screen.getByRole('button',{name:'Review and start sharing'}) as HTMLButtonElement;
 expect(start.disabled).toBe(true);
 fireEvent.change(screen.getByLabelText('Installed Python executable'),{target:{value:'C:\\Python\\python.exe'}});
 fireEvent.change(screen.getByLabelText('Shared workspace folder'),{target:{value:'C:\\OSCAR\\work'}});
 fireEvent.click(screen.getByLabelText('Read workspace files'));
 expect(start.disabled).toBe(false);fireEvent.click(start);
 expect(run).toHaveBeenCalledWith({kind:'worker_start',config:{python:'C:\\Python\\python.exe',workspace:'C:\\OSCAR\\work',capabilities:['machine.files.read'],trusted_host_execution:false,allowed_executables:[],desktop_app_ids:[]}});
 expect((screen.getByLabelText('Allowlisted commands') as HTMLInputElement).disabled).toBe(true);
});
it('requires command allowlists and removes host selections when their grant is removed',()=>{
 const run=vi.fn();render(<WorkerSharing view={{...initialView,link:'online',connection}} busy={false} run={run}/>);
 fireEvent.click(screen.getByRole('button',{name:'Set up Desktop sharing'}));
 fireEvent.click(screen.getByLabelText("Allow execution with this Windows account's permissions"));
 fireEvent.click(screen.getByLabelText('Allowlisted commands'));
 fireEvent.click(screen.getByLabelText("Allow execution with this Windows account's permissions"));
 expect((screen.getByLabelText('Allowlisted commands') as HTMLInputElement).checked).toBe(false);
 expect(run).not.toHaveBeenCalled();
});
it('permits local stop during Core loss and cannot fabricate a missing enrollment workspace',()=>{
 const run=vi.fn();const {rerender}=render(<WorkerSharing view={{...initialView,worker_sharing:{status:'degraded',workspace:'synthetic',capabilities:['machine.files.read'],message:'Network unavailable'}}} busy={false} run={run}/>);
 fireEvent.click(screen.getByRole('button',{name:'Stop Desktop sharing'}));expect(run).toHaveBeenCalledWith({kind:'worker_stop'});
 rerender(<WorkerSharing view={{...initialView,link:'online',connection:{...connection,workspace:null}}} busy={false} run={run}/>);
 fireEvent.click(screen.getByRole('button',{name:'Set up Desktop sharing'}));
 expect(screen.getByText(/Reconnect with a new device invitation/)).toBeTruthy();
 expect((screen.getByRole('button',{name:'Review and start sharing'}) as HTMLButtonElement).disabled).toBe(true);
});
