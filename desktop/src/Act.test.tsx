import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {afterEach,describe,expect,it,vi} from 'vitest';
import {Act} from './Act';
import type {Capability} from './bridge';
afterEach(cleanup);
const cap:Capability={id:'worker::write',node:'worker',kind:'file_write',label:'Write exact file',summary:'Scoped workspace',risk:'low',permissions:['files:write'],operations:['write_file'],programs:[],applications:[]};
describe('scoped typed action',()=>{
  it('requires a path, exposes scope and proposes only exact typed fields',async()=>{
    const run=vi.fn();render(<Act capabilities={[cap]} run={run} disabled={false}/>);
    const button=await screen.findByRole('button',{name:'Prepare action'});await waitFor(()=>expect(screen.getByLabelText('Relative workspace path')).toBeTruthy());
    expect((button as HTMLButtonElement).disabled).toBe(true);expect(screen.getByText(/required scopes: files:write/)).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Relative workspace path'),{target:{value:'proof.txt'}});fireEvent.change(screen.getByLabelText('Exact content'),{target:{value:'exact reference'}});
    fireEvent.click(button);expect(run).toHaveBeenCalledWith({kind:'act',capability_id:cap.id,form:{operation:'write_file',path:'proof.txt',text:'exact reference'}});
  });
  it('withdrawal clears private values and does not silently select a different executor',async()=>{
    const {rerender}=render(<Act capabilities={[cap]} run={()=>{}} disabled={false}/>);await screen.findByLabelText('Exact content');
    fireEvent.change(screen.getByLabelText('Exact content'),{target:{value:'private sentinel'}});
    rerender(<Act capabilities={[{...cap,id:'other::write',node:'other'}]} run={()=>{}} disabled={false}/>);
    await waitFor(()=>expect((screen.getByLabelText('Available capability') as HTMLSelectElement).value).toBe(''));
    expect(screen.queryByDisplayValue('private sentinel')).toBeNull();expect((screen.getByRole('button',{name:'Prepare action'}) as HTMLButtonElement).disabled).toBe(true);
  });
  it('disabled source never sends an action even with filled draft',()=>{
    const run=vi.fn();render(<Act capabilities={[cap]} run={run} disabled draft={{id:cap.id,operation:'write_file',value:'proof.txt',text:'reference'}} onDraftChange={()=>{}}/>);
    fireEvent.click(screen.getByRole('button',{name:'Prepare action'}));expect(run).not.toHaveBeenCalled();
  });
});
