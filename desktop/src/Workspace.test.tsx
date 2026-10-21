import {afterEach,it,expect,vi} from 'vitest';
import {act,render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import {Workspace} from './Workspace';
import {initialView} from './bridge';
import type {Command,View} from './bridge';
Object.defineProperty(HTMLElement.prototype,'scrollTo',{configurable:true,value:vi.fn()});
afterEach(cleanup);
it('keeps Core task history in Activity instead of a chat-list sidebar',async()=>{
 const task={task_id:'past-work',state:'verified',description:'Earlier work',target:'worker',actions:[],blocker:null,generation:1,evidence_ids:[],response:'An outcome',response_status:'REPORTED',value:null,epistemic:null};
 const port=mount({tasks:[task]});await waitFor(()=>expect(port).toHaveBeenCalled());
 expect(screen.queryByText('Recent work')).toBeNull();expect(screen.queryByText('Earlier work')).toBeNull();
 expect(screen.getByRole('region',{name:'Conversation scroll area'})).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'Activity'}));
 expect(screen.getByText('Earlier work')).toBeTruthy();
});
function mount(extra:Partial<View>={}) {
  const now=Date.now();let view:View={...initialView,link:'online',window:'interaction',expression:{epoch:'a'.repeat(32),generation:1,observed_at_ms:now,voice_observed_at_ms:now,tasks_observed_at_ms:now,current_observed_at_ms:now},...extra};
  const port=vi.fn(async(c:Command)=>{if(c.kind==='interact')view={...view,current:{task_id:'actual',state:'planned',description:'Core task',target:'worker',actions:['approve'],blocker:null,generation:1,evidence_ids:[],response:null,response_status:null,value:null,epistemic:null}};return view;});
  let notify:(next:View)=>void=()=>{};
  render(<Workspace port={port} events={async callback=>{notify=callback;return()=>{};}}/>);
  return Object.assign(port,{emit:(partial:Partial<View>)=>{view={...view,...partial};notify(view);}});
}
it('preserves Ask and moves text/actions/activity to the full workspace',async()=>{
  const port=mount();await waitFor(()=>expect(port).toHaveBeenCalled());
  fireEvent.change(screen.getByLabelText('Ask OSCAR'),{target:{value:'2 + 3'}});fireEvent.click(screen.getByRole('button',{name:'Send'}));
  await screen.findByText('2 + 3');expect(port).toHaveBeenCalledWith({kind:'interact',mode:'Ask',text:'2 + 3',context_id:''});
  expect(screen.queryByRole('button',{name:'Dictate or edit'})).toBeNull();expect(screen.queryByRole('button',{name:'Discuss with OSCAR'})).toBeNull();
  fireEvent.click(screen.getByRole('button',{name:'Automations'}));expect(screen.getByText(/Automation readback.+available on this connection/)).toBeTruthy();
});
it('an expired review never offers enabled native confirmation',async()=>{
  mount({current:{task_id:'task',state:'planned',description:'Exact task',target:'worker',actions:['approve'],blocker:null,generation:1,evidence_ids:[],response:null,response_status:null,value:null,epistemic:null},review:{review_id:'expired',task_id:'task',operation:'approve',description:'Exact task',target:'worker',capability:'math',reason:'request',consequence:'add',policy_reason:'scope',evidence_state:'planned',review:'2 + 3',expires_at_ms:Date.now()-1}});
  const confirm=await screen.findByRole('button',{name:'Continue to confirmation'});expect((confirm as HTMLButtonElement).disabled).toBe(true);
});
it('stale observations disable submission and never claim monitoring or persistent mute',async()=>{
  mount({expression:{epoch:'b'.repeat(32),generation:1,observed_at_ms:Date.now()-10000,voice_observed_at_ms:0,tasks_observed_at_ms:0,current_observed_at_ms:0}});
  await screen.findByText(/OSCAR is offline/);fireEvent.change(screen.getByLabelText('Ask OSCAR'),{target:{value:'hello'}});
  expect((screen.getByRole('button',{name:'Send'}) as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getByRole('button',{name:'Preferences'}));fireEvent.click(screen.getByRole('button',{name:'Sentry and listening controls'}));expect(screen.getByText(/Configure available Sentry sources separately/)).toBeTruthy();
});
it('Activity discard clears unsent private drafts across navigation',async()=>{
  const port=mount();await waitFor(()=>expect(port).toHaveBeenCalled());
  fireEvent.change(screen.getByLabelText('Ask OSCAR'),{target:{value:'private draft'}});
  fireEvent.click(screen.getByRole('button',{name:'Activity'}));
  fireEvent.click(screen.getByRole('button',{name:'Clear drafts and context'}));
  fireEvent.click(screen.getByRole('button',{name:'Conversation'}));
  expect((screen.getByLabelText('Ask OSCAR') as HTMLTextAreaElement).value).toBe('');
  expect(port).toHaveBeenCalledWith({kind:'discard'});
});
it('a delayed open readback preserves the page selected by the owner',async()=>{
  const port=mount();await waitFor(()=>expect(port).toHaveBeenCalled());
  fireEvent.click(screen.getByRole('button',{name:'Preferences'}));
  act(()=>port.emit({window:'interaction',window_revision:1}));
  expect(screen.getByRole('button',{name:'Quit OSCAR'})).toBeTruthy();
});
it('Preferences shows native shortcut state, theme selection and unavailable awareness',async()=>{
  const port=mount({theme:'dark',shortcut:'Ctrl+Alt+K',shortcut_enabled:true});
  await waitFor(()=>expect(port).toHaveBeenCalled());
  fireEvent.click(screen.getByRole('button',{name:'Preferences'}));
  expect(screen.getByRole('switch',{name:'Global shortcut'}).getAttribute('aria-checked')).toBe('true');
  expect(screen.getByRole('button',{name:'Dark'}).getAttribute('aria-pressed')).toBe('true');
  expect(screen.getByLabelText('Configured shortcut: Ctrl+Alt+K')).toBeTruthy();
  act(()=>port.emit({shortcut_enabled:false}));
  expect(screen.getByRole('switch',{name:'Global shortcut'}).getAttribute('aria-checked')).toBe('false');
  expect(screen.getByText(/Voice is not available on this device/)).toBeTruthy();
});
it('Devices reveals real capability scope and prepares without executing',async()=>{
  const port=mount({capabilities:[{id:'files',node:'desktop-1',kind:'native',label:'Write exact file',summary:'Scoped file creation',risk:'low',operations:['write_file'],programs:[],applications:[],permissions:['files.write']}]});
  await waitFor(()=>expect(port).toHaveBeenCalled());
  fireEvent.click(screen.getByRole('button',{name:'Devices'}));
  fireEvent.click(screen.getByRole('button',{name:'Connection details'}));expect(screen.getByText('desktop-1')).toBeTruthy();expect(screen.getByText('files.write')).toBeTruthy();
  fireEvent.click(screen.getByRole('button',{name:'Discuss with OSCAR'}));
  expect((screen.getByLabelText('Ask OSCAR') as HTMLTextAreaElement).value).toBe('Help me write exact file. ');expect(screen.queryByLabelText('Operation')).toBeNull();
  expect(port.mock.calls.some(([c])=>c.kind==='act')).toBe(false);
});
it('keeps review-session metadata out of the product composer',async()=>{
 const port=mount({reference:true});await waitFor(()=>expect(port).toHaveBeenCalled());
 expect(screen.queryByText(/REFERENCE CORE|owner acceptance|disposable tasks/i)).toBeNull();
 expect(screen.getByLabelText('Ask OSCAR').getAttribute('rows')).toBe('2');
 expect(screen.getByText(/Shift\+Enter for a new line/)).toBeTruthy();
});

it('loads canonical chronological turns and requests older history without a frontend store',async()=>{
 const port=mount({conversation:{turns:[{id:'first',task_id:'old',role:'owner',text:'Earlier question',status:'REPORTED',occurred_at:1,retained:true},{id:'second',task_id:'old',role:'oscar',text:'Earlier answer',status:'REPORTED',occurred_at:2,retained:true}],before:12,persistence:'authorized',revision:1,retention:true}});
 await screen.findByText('Earlier question');expect(screen.getByText('Earlier answer')).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'Load earlier conversation'}));await waitFor(()=>expect(port).toHaveBeenCalledWith({kind:'history',before:12}));
 expect(screen.queryByText(/Canonical history|retention granted|Private session|Saved reply|REPORTED/)).toBeNull();
 expect(screen.queryByRole('button',{name:'Text tools'})).toBeNull();expect(screen.queryByRole('button',{name:'Act'})).toBeNull();
});
it('shows independent Core operating dimensions without claiming unavailable autonomy',async()=>{
 const port=mount({operating:{access:'Ask',secure:'unavailable',full_access:'unavailable',awareness:'Trigger-only',sentry:'unavailable',worker_autonomy:'Manual',automations:'task_foundation'}});
 await waitFor(()=>expect(port).toHaveBeenCalled());fireEvent.click(screen.getByRole('button',{name:'Preferences'}));
 expect(screen.getByText('Ask')).toBeTruthy();expect(screen.getByText('Waits for your review')).toBeTruthy();expect(screen.getByText('Only when you start it')).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'Access modes'}));expect(screen.getByText(/unrestricted owner-delegated autonomy/)).toBeTruthy();
 expect(port.mock.calls.some(([c])=>['access','grant','approve'].includes(c.kind))).toBe(false);
});

it('retiring an old review preserves a manually selected page',async()=>{
 const port=mount({window:'activity',review:{review_id:'old',task_id:'task',operation:'approve',description:'Task',target:'worker',capability:'math',reason:'request',consequence:'add',policy_reason:'scope',evidence_state:'planned',review:'2 + 3',expires_at_ms:Date.now()+30000}});
 await screen.findByRole('heading',{name:'Activity'});fireEvent.click(screen.getByRole('button',{name:'Preferences'}));
 act(()=>port.emit({review:null}));expect(screen.getByRole('heading',{name:'Preferences'})).toBeTruthy();
});

it('a retention grant never claims that history read was granted',async()=>{
 const port=mount({conversation:{turns:[],before:null,persistence:'session_only',revision:0,retention:true}});await waitFor(()=>expect(port).toHaveBeenCalled());
 expect(screen.queryByText(/Private session|retention|Canonical history/)).toBeNull();fireEvent.click(screen.getByRole('button',{name:'Preferences'}));expect(screen.getByText('Previously saved conversation is not available on this connection.')).toBeTruthy();
});

it('only offers a microphone for real available voice and sends bounded native commands',async()=>{
 const port=mount({voice_available:true});await screen.findByRole('button',{name:'Use voice'});fireEvent.click(screen.getByRole('button',{name:'Use voice'}));await waitFor(()=>expect(port).toHaveBeenCalledWith({kind:'voice_start',context_id:'',mode:'Ask'}));
 act(()=>port.emit({voice:'listening'}));fireEvent.click(screen.getByRole('button',{name:'Finish voice message'}));await waitFor(()=>expect(port).toHaveBeenCalledWith({kind:'voice_stop'}));
});
it('keeps empty Conversation free of utility controls, headings and memory/debug metadata',async()=>{
 const port=mount();await screen.findByText('What’s on your mind?');
 expect(screen.queryByRole('heading',{name:'Conversation'})).toBeNull();expect(screen.queryByRole('button',{name:'Use voice'})).toBeNull();
 expect(screen.queryByText(/Canonical history|Private session|retention granted|Prepare an action|Dictate or edit/)).toBeNull();
 expect(port.mock.calls.some(([c])=>c.kind==='act'||c.kind==='voice_start')).toBe(false);
});
it('keeps direct operations behind Preferences without losing their typed path',async()=>{
 const port=mount();await waitFor(()=>expect(port).toHaveBeenCalled());fireEvent.click(screen.getByRole('button',{name:'Preferences'}));fireEvent.click(screen.getByRole('button',{name:'Advanced controls'}));
 expect(screen.getByRole('tab',{name:'Dictate'})).toBeTruthy();fireEvent.click(screen.getByRole('button',{name:'Direct device operations'}));expect(screen.getByText(/No actions are available/)).toBeTruthy();
});

it('describes live information in plain language and keeps provider details inspectable',async()=>{
 const port=mount({capabilities:[{id:'sources',node:'desktop-1',kind:'live_source',label:'Live retrieval',summary:'Provider-native inventories and replaceable public-web retrieval',risk:'low',operations:[],programs:[],applications:[]}]});await waitFor(()=>expect(port).toHaveBeenCalled());fireEvent.click(screen.getByRole('button',{name:'Devices'}));
 expect(screen.getByRole('button',{name:'Find information'})).toBeTruthy();expect(screen.queryByText(/Provider-native/)).toBeNull();fireEvent.click(screen.getByRole('button',{name:'Connection details'}));expect(screen.getByText(/Provider-native/)).toBeTruthy();
});
