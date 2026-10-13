import {afterEach,describe,it,expect,vi} from 'vitest';
import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import {App} from './App';
import {initialView,stateLabel} from './bridge';
import type {View,Command} from './bridge';
afterEach(cleanup);
function mount(overrides:Partial<View>={}) {
  let view:View={...initialView,window:'interaction',link:'online',orb:'idle',...overrides};
  let update:(v:View)=>void=()=>{};
  const port=vi.fn(async(command:Command)=>{
    if(command.kind==='discard')view={...view,context:null,preview:null,review:null};
    if(command.kind==='window')view={...view,window:command.mode};
    return view;
  });
  render(<App port={port} events={async callback=>{update=callback;return()=>{};}}/>);
  return {port,emit:(v:Partial<View>)=>{view={...view,...v};update(view);}};
}
describe('OSCAR surface contract',()=>{
  it('the presence handoff focuses the actual review without making a decision',async()=>{
    const review={review_id:'review',task_id:'exact',operation:'approve',description:'Add 2 and 3',target:'worker',capability:'math.add',reason:'Owner request',consequence:'Add integers',policy_reason:'Scoped grant',evidence_state:'planned',review:'2 + 3',expires_at_ms:Date.now()+30000};
    const port=vi.fn(async()=>({...initialView,window:'approval' as const,link:'online',review}));
    const scroll=vi.fn();
    const original=HTMLElement.prototype.scrollIntoView;HTMLElement.prototype.scrollIntoView=scroll;
    try {
      render(<App port={port} events={async()=>()=>{}} focusReview/>);
      const section=await screen.findByRole('region',{name:'Owner approval'});
      await waitFor(()=>expect(document.activeElement).toBe(section));
      expect(scroll).toHaveBeenCalledWith({block:'start'});
      expect(port.mock.calls).toHaveLength(1);
      expect(screen.getByText('2 + 3')).toBeTruthy();
    } finally {HTMLElement.prototype.scrollIntoView=original;}
  });
  it('supports keyboard mode navigation and visible semantic focus',async()=>{
    mount();const ask=await screen.findByRole('tab',{name:'Ask'});ask.focus();
    fireEvent.keyDown(ask,{key:'ArrowRight'});
    expect(screen.getByRole('tab',{name:'Dictate'}).getAttribute('aria-selected')).toBe('true');
    expect(document.activeElement).toBe(screen.getByRole('tab',{name:'Dictate'}));
  });
  it('keeps modes distinct and sends bounded semantic requests without authority',async()=>{
    const {port}=mount();await screen.findByRole('tab',{name:'Ask'});
    fireEvent.change(screen.getByLabelText('Ask OSCAR'),{target:{value:'2 + 3'}});
    fireEvent.click(screen.getByRole('button',{name:'Ask'}));
    await waitFor(()=>expect(port).toHaveBeenCalledWith({kind:'interact',mode:'Ask',text:'2 + 3',context_id:''}));
    fireEvent.click(screen.getByRole('tab',{name:'Dictate'}));
    expect(screen.getByRole('button',{name:'Preview text'})).toBeDefined();
    fireEvent.click(screen.getByRole('tab',{name:'Edit'}));
    expect((screen.getByRole('button',{name:'Request transformation'}) as HTMLButtonElement).disabled).toBe(true);
  });
  it('renders an exact owner review without signing material and requests native confirmation',async()=>{
    const {port}=mount({review:{review_id:'review',operation:'approve',description:'Write exact file',target:'worker',capability:'file_write',
      reason:'Owner request',consequence:'Write reviewed bytes',policy_reason:'Scoped grant',evidence_state:'planned',review:'fixture.txt',expires_at_ms:Date.now()+30000}});
    await screen.findByRole('region',{name:'Owner approval'});
    expect(screen.getByText('Scoped grant')).toBeDefined();expect(screen.queryByText('signing_payload')).toBeNull();
    fireEvent.click(screen.getByRole('button',{name:'Continue to native confirmation'}));
    await waitFor(()=>expect(port).toHaveBeenCalledWith({kind:'confirm',review_id:'review',accept:true}));
  });
  it('withdraws vanished capabilities and disables work when Core degrades',async()=>{
    const {emit}=mount({capabilities:[{id:'worker::read',node:'worker',kind:'file_read',label:'Read',summary:'Scoped files',risk:'low',operations:['read_file'],programs:[],applications:[]}]});
    await screen.findByRole('tab',{name:'Act'});fireEvent.click(screen.getByRole('tab',{name:'Act'}));
    expect(await screen.findByRole('button',{name:'Prepare action'})).toBeDefined();
    emit({link:'unavailable',capabilities:[]});
    await screen.findByText(/No actions are available/);
    fireEvent.click(screen.getByRole('tab',{name:'Ask'}));
    expect((screen.getByRole('button',{name:'Ask'}) as HTMLButtonElement).disabled).toBe(true);
  });
  it('shows attachment provenance and discards context immediately through Core',async()=>{
    const {port}=mount({context:{id:'context',source:'selection',timestamp:1,scope:'fixture',provenance:'UIA',permission:'granted',freshness:'fresh',text:'selected fixture',retained:false}});
    await screen.findByText('selected fixture');fireEvent.click(screen.getByRole('button',{name:'Discard now'}));
    await screen.findByText('No context attached.');expect(port).toHaveBeenCalledWith({kind:'discard'});
  });
  it('preserves unknown task truth and clear before/after preview semantics',async()=>{
    mount({current:{task_id:'task',state:'unknown',description:'Reference',target:'worker',blocker:'Readback unavailable',actions:[],generation:1,
      evidence_ids:[],response:null,response_status:null,value:null,epistemic:null},preview:{preview_id:'preview',before:'before fixture',after:'after fixture',epistemic:'REPORTED',expires:Date.now()/1000+15,destinations:['surface']}});
    await screen.findByRole('heading',{name:'Unknown outcome'});expect(screen.getByText('before fixture')).toBeDefined();
    expect(screen.getByText('after fixture')).toBeDefined();expect(screen.getByRole('heading',{name:'After · REPORTED'})).toBeDefined();
    expect(stateLabel({...initialView,link:'unavailable'})).toBe('Core unavailable');
  });
});
