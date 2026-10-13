import {afterEach,it,expect,vi} from 'vitest';
import {act,render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import {Workspace} from './Workspace';
import {initialView} from './bridge';
import type {Command,View} from './bridge';
afterEach(cleanup);
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
  fireEvent.click(screen.getByRole('button',{name:'Text tools'}));expect(screen.getByRole('tab',{name:'Dictate'})).toBeTruthy();
  fireEvent.click(screen.getByRole('button',{name:'Act'}));expect(screen.getByText(/No eligible action capability/)).toBeTruthy();
});
it('an expired review never offers enabled native confirmation',async()=>{
  mount({current:{task_id:'task',state:'planned',description:'Exact task',target:'worker',actions:['approve'],blocker:null,generation:1,evidence_ids:[],response:null,response_status:null,value:null,epistemic:null},review:{review_id:'expired',task_id:'task',operation:'approve',description:'Exact task',target:'worker',capability:'math',reason:'request',consequence:'add',policy_reason:'scope',evidence_state:'planned',review:'2 + 3',expires_at_ms:Date.now()-1}});
  const confirm=await screen.findByRole('button',{name:'Continue to native confirmation'});expect((confirm as HTMLButtonElement).disabled).toBe(true);
});
it('stale observations disable submission and never claim monitoring or persistent mute',async()=>{
  mount({expression:{epoch:'b'.repeat(32),generation:1,observed_at_ms:Date.now()-10000,voice_observed_at_ms:0,tasks_observed_at_ms:0,current_observed_at_ms:0}});
  await screen.findByText(/Core unavailable or observation expired/);fireEvent.change(screen.getByLabelText('Ask OSCAR'),{target:{value:'hello'}});
  expect((screen.getByRole('button',{name:'Send'}) as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getByRole('button',{name:'Preferences'}));expect(screen.getByText('Persistent mute')).toBeTruthy();expect(screen.getByText('Sentry / acoustic awareness')).toBeTruthy();expect(screen.getAllByText('unavailable')).toHaveLength(2);
});
it('Activity discard clears unsent private drafts across navigation',async()=>{
  const port=mount();await waitFor(()=>expect(port).toHaveBeenCalled());
  fireEvent.change(screen.getByLabelText('Ask OSCAR'),{target:{value:'private draft'}});
  fireEvent.click(screen.getByRole('button',{name:'Activity'}));
  fireEvent.click(screen.getByRole('button',{name:'Clear private drafts and context'}));
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
  expect(screen.getAllByText('unavailable')).toHaveLength(2);
});
