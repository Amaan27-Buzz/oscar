import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {MemorySettings,memoryView} from './MemorySettings';
import {initialView} from './bridge';
afterEach(cleanup);
const record={id:'synthetic-memory',content:'The project is named Copper',digest:'a'.repeat(64),kind:'episodic',status:'REPORTED',source_event_ids:['source'],excerpt:false,can_manage:true,can_correct:true};
const memory={available:true,generation:1,truncated:false,records:[record]};
const management={version:1 as const,relationship_id:'owner',core_node_id:'core',ask_rules:[],authority:{mode:'ask' as const,status:'inactive'},capabilities:[],sentry:{mode:'manual',state:'sleep',source_ids:[],trigger_keys:[],allow_interrupt:false,generation:1,sources:[]},memory};
it('requires bounded scope-backed records and hides saved memory offline',()=>{
 expect(memoryView(memory)).toEqual(memory);
 expect(memoryView({...memory,available:false})).toBeNull();
 expect(memoryView({...memory,records:[{...record,digest:'bad'}]})).toBeNull();
 render(<MemorySettings view={{...initialView,link:'unavailable'}} busy={false} run={vi.fn()}/>);
 expect(screen.getByText(/separate memory read grant/)).toBeTruthy();
 expect(screen.queryByText(record.content)).toBeNull();
});
it('stages exact correction and explicit source forgetting without activating them',()=>{
 const run=vi.fn();render(<MemorySettings view={{...initialView,link:'online',executive:{version:1,health:'ready',running:true,goals:[],workers:[],management}}} busy={false} run={run}/>);
 fireEvent.click(screen.getByText(record.content,{selector:'span'}));
 fireEvent.change(screen.getByLabelText('Corrected statement'),{target:{value:'The project is named Silver'}});
 expect((screen.getByRole('button',{name:'Review memory correction'}) as HTMLButtonElement).disabled).toBe(true);
 fireEvent.click(screen.getByLabelText('Retain this exact correction'));
 fireEvent.click(screen.getByRole('button',{name:'Review memory correction'}));
 expect(run).toHaveBeenLastCalledWith({kind:'manage_assistance',operation:'memory_correct',id:record.id,value:{digest:record.digest,content:'The project is named Silver',retain:true}});
 fireEvent.click(screen.getByLabelText('Also forget the retained source statements and dependent memories'));
 fireEvent.click(screen.getByRole('button',{name:'Review forgetting this memory'}));
 expect(run).toHaveBeenLastCalledWith({kind:'manage_assistance',operation:'memory_forget',id:record.id,value:{digest:record.digest,forget_sources:true}});
});
