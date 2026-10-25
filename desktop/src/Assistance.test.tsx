import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {OperatingSettings} from './OperatingSettings';
import {Automations,assistanceSummary} from './Automations';
import {initialView} from './bridge';
const management={version:1 as const,relationship_id:'owner',core_node_id:'core',ask_rules:['review-rule'],authority:{mode:'ask' as const,status:'inactive'},capabilities:[{id:'files.write',node_id:'core',session_id:'session',input_kind:'file_write',risk:'medium',permissions:['files:write']}],sentry:{mode:'manual',state:'passive',generation:0,source_ids:[],trigger_keys:[],allow_interrupt:false,sources:[{id:'synthetic-events',perceive:false,retain:false,act:false,simulated:true,epoch:1}]}};
const executive={version:1 as const,health:'operational',running:true,management,goals:[],workers:[]};
afterEach(cleanup);
it('reviews a pending action through the existing signed assistance command',()=>{
 const run=vi.fn();const pending={...executive,management:{...management,pending_actions:[{task_id:'task',goal_id:'goal'}]},goals:[{id:'goal',goal:'Write note',state:'enabled',verified_runs:0,max_runs:1,task_ids:['task']}]};
 render(<Automations discuss={()=>{}} executive={pending} run={run}/>);
 expect(run).not.toHaveBeenCalled();fireEvent.click(screen.getByRole('button',{name:'Review next action'}));
 expect(run).toHaveBeenCalledExactlyOnceWith({kind:'manage_assistance',operation:'confirm_task',id:'task',value:{}});
 for(const pending_actions of [[{task_id:'',goal_id:'goal'}],[{task_id:'task',goal_id:'goal'},{task_id:'task',goal_id:'goal'}],[{task_id:'task',goal_id:'bad\nidentity'}]])expect(assistanceSummary({...management,pending_actions})).toBeNull();
});
it('requires explicit signed activation and sends exact coverage without action approval',()=>{
 const run=vi.fn();render(<OperatingSettings view={{...initialView,link:'online',executive,operating:{access:'Ask',secure:'signed_delegation_available',full_access:'signed_delegation_available',awareness:'manual',sentry:'passive',worker_autonomy:'scoped',automations:'signed_authoring'}}} busy={false} run={run}/>);
 expect(run).not.toHaveBeenCalled();fireEvent.click(screen.getByRole('button',{name:'Access modes'}));fireEvent.click(screen.getByRole('button',{name:'Review Full Access activation'}));
 expect(run).toHaveBeenCalledWith({kind:'set_access',relationship_id:'owner',value:{mode:'full',lifetime_seconds:3600,capabilities:[{node_id:'core',session_id:'session',capability_id:'files.write'}],account_ids:[],resolve_ask_rules:['review-rule']}});
 fireEvent.click(screen.getByRole('button',{name:'Return to Ask'}));expect(run).toHaveBeenLastCalledWith({kind:'revoke_access'});
});
it('source perception changes do not implicitly grant retention or action',()=>{
 const run=vi.fn();render(<OperatingSettings view={{...initialView,link:'online',executive}} busy={false} run={run}/>);
 fireEvent.click(screen.getByRole('button',{name:'synthetic-events · Simulated'}));fireEvent.click(screen.getByLabelText('Observe current context'));
 expect(run).toHaveBeenCalledWith({kind:'manage_assistance',operation:'source',id:'synthetic-events',value:{perceive:true,retain:false,act:false}});
});
it('authors a real scheduled file objective without running it from the renderer',()=>{
 const run=vi.fn();render(<Automations discuss={()=>{}} executive={executive} run={run}/>);
 fireEvent.click(screen.getByRole('button',{name:'Create a responsibility'}));
 fireEvent.click(screen.getByRole('button',{name:'Describe responsibility'}));fireEvent.click(screen.getByRole('radio',{name:'Write exact file contents'}));
 for(const [label,value] of [['Responsibility name','Agenda'],['What should OSCAR handle?','Write my agenda'],['Workspace file','agenda.txt'],['File contents','Reviewed notes']])fireEvent.change(screen.getByLabelText(label),{target:{value}});
 fireEvent.click(screen.getByRole('button',{name:'Review responsibility'}));
 expect(run).toHaveBeenCalledOnce();expect(run.mock.calls[0][0]).toMatchObject({kind:'manage_assistance',operation:'create',id:'new',value:{name:'Agenda',goal:'Write my agenda',steps:[{id:'write',intent:{text:'Write my agenda',kind:'file_write',path:'agenda.txt',content:'Reviewed notes'},node_id:'core',capability_id:'files.write',depends_on:[]}],start_at:null,interval_seconds:null,max_runs:1}});
});
it('omits signed controls for unavailable or malformed Core metadata',()=>{
 expect(assistanceSummary({...management,truncated:true})).toBeNull();
 expect(assistanceSummary({...management,capabilities:[{...management.capabilities[0],permissions:'all'}]})).toBeNull();
 const run=vi.fn();render(<OperatingSettings view={{...initialView,link:'offline',executive}} busy={false} run={run}/>);fireEvent.click(screen.getByRole('button',{name:'Access modes'}));expect(screen.queryByRole('button',{name:'Review Full Access activation'})).toBeNull();expect(run).not.toHaveBeenCalled();
});
it('authors a remote file responsibility using the exact selected device',()=>{
 const run=vi.fn();const remote={...executive,management:{...management,capabilities:[{...management.capabilities[0],id:'machine.files.write',node_id:'desktop',session_id:'remote-session'}]}};
 render(<Automations discuss={()=>{}} executive={remote} run={run}/>);
 fireEvent.click(screen.getByRole('button',{name:'Create a responsibility'}));
 fireEvent.click(screen.getByRole('button',{name:'Describe responsibility'}));fireEvent.click(screen.getByRole('radio',{name:'Write exact file contents'}));
 for(const [label,value] of [['Responsibility name','Remote agenda'],['What should OSCAR handle?','Write remote agenda'],['Workspace file','agenda.txt'],['File contents','Reviewed remote notes']])fireEvent.change(screen.getByLabelText(label),{target:{value}});
 fireEvent.click(screen.getByRole('button',{name:'Review responsibility'}));
 expect(run.mock.calls[0][0].value.steps[0]).toMatchObject({node_id:'desktop',capability_id:'machine.files.write'});
});
it('submits natural action lines only for Core compilation and signed review',()=>{
 const run=vi.fn();render(<Automations discuss={()=>{}} executive={executive} run={run}/>);
 fireEvent.click(screen.getByRole('button',{name:'Create a responsibility'}));
 fireEvent.change(screen.getByLabelText('Responsibility name'),{target:{value:'Agenda'}});
 fireEvent.change(screen.getByLabelText('What should OSCAR handle?'),{target:{value:'Write agenda.txt with text Reviewed\nRead file agenda.txt'}});
 expect(run).not.toHaveBeenCalled();fireEvent.click(screen.getByRole('button',{name:'Review responsibility'}));
 expect(run).toHaveBeenCalledExactlyOnceWith({kind:'manage_assistance',operation:'create_natural',id:'new',value:{name:'Agenda',instruction:'Write agenda.txt with text Reviewed\nRead file agenda.txt',node_id:'',start_at:null,interval_seconds:null,max_runs:1,priority:0,conditions:[]}});
});
it('requires a separate retention choice before saving a verified procedure',()=>{
 const run=vi.fn();const completed={...executive,goals:[{id:'goal',goal:'2 + 2',state:'completed',verified_runs:1,max_runs:1,task_ids:['task']}]};
 render(<Automations discuss={()=>{}} executive={completed} run={run}/>);
 expect(screen.getByRole('button',{name:'Review saving this procedure'}).hasAttribute('disabled')).toBe(true);
 fireEvent.click(screen.getByRole('button',{name:'Reusable procedures'}));
 fireEvent.click(screen.getByLabelText('Allow saving reviewed steps and evidence for up to seven days'));
 expect(run).not.toHaveBeenCalled();fireEvent.click(screen.getByRole('button',{name:'Review saving this procedure'}));
 expect(run).toHaveBeenCalledExactlyOnceWith({kind:'manage_assistance',operation:'learn',id:'goal',value:{retain:true}});
});
it('reuses a candidate only through a fresh exact one-time review',()=>{
 const run=vi.fn();const saved={...executive,management:{...management,procedures:[{id:'procedure',goal:'2 + 2',source_goal_id:'source',state:'candidate' as const,event_id:'event'}]}};
 render(<Automations discuss={()=>{}} executive={saved} run={run}/>);
 fireEvent.click(screen.getByRole('button',{name:'Reusable procedures'}));
 expect(screen.getByText('Candidate from verified work')).toBeTruthy();expect(run).not.toHaveBeenCalled();
 fireEvent.click(screen.getByRole('button',{name:'Review one-time replay'}));
 expect(run).toHaveBeenCalledExactlyOnceWith({kind:'manage_assistance',operation:'reuse',id:'procedure',value:{start_at:null,interval_seconds:null,max_runs:1,priority:0}});
});

it('reviews model input separately from reported suggested actions',()=>{
 const run=vi.fn();const planned={...executive,management:{...management,planner_drafts:[{id:'draft',goal:'Make a plan',state:'reported'}],capabilities:[...management.capabilities,{id:'models.reason',node_id:'core',session_id:'session',input_kind:'model_reasoning',risk:'model',permissions:['models']}]}};
 render(<Automations discuss={()=>{}} executive={planned} run={run}/>);
 fireEvent.click(screen.getByRole('button',{name:'Create a responsibility'}));
 fireEvent.click(screen.getByRole('button',{name:'Describe responsibility'}));fireEvent.click(screen.getByRole('radio',{name:'Ask OSCAR to propose a plan'}));
 fireEvent.change(screen.getByLabelText('Responsibility name'),{target:{value:'Planner'}});
 fireEvent.change(screen.getByLabelText('What should OSCAR handle?'),{target:{value:'Make a plan'}});
 fireEvent.click(screen.getByLabelText('core · files.write'));fireEvent.click(screen.getByLabelText('core · models.reason'));
 expect(run).not.toHaveBeenCalled();fireEvent.click(screen.getByRole('button',{name:'Review model planning request'}));
 expect(run).toHaveBeenLastCalledWith({kind:'manage_assistance',operation:'plan_draft',id:'new',value:{name:'Planner',goal:'Make a plan',mode:'private',capabilities:[{node_id:'core',capability_id:'files.write'},{node_id:'core',capability_id:'models.reason'}]}});
 fireEvent.click(screen.getByRole('button',{name:'Review suggested actions'}));
 expect(run).toHaveBeenLastCalledWith({kind:'manage_assistance',operation:'plan_accept',id:'draft',value:{start_at:null,interval_seconds:null,max_runs:1,priority:0}});
 expect(assistanceSummary({...management,planner_drafts:[{id:'draft',goal:'Missing state'}]})).toBeNull();
});
