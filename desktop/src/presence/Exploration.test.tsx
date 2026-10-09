import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import orb from '../../../assets/brand/oscar-orb.svg';
import {Exploration,Presence,dimensions,presentation,views} from './Exploration';
vi.mock('@tauri-apps/api/core',()=>({invoke:()=>{throw new Error('Native IPC forbidden');}}));
vi.mock('@tauri-apps/api/event',()=>({listen:()=>{throw new Error('Native events forbidden');}}));
afterEach(()=>{cleanup();history.replaceState({},'', '/');});
it('keeps availability and owner attention distinct from activity, including stale offline tasks',()=>{
  expect(presentation(views.idle)).toMatchObject({state:'idle',working:false,attention:0});
  expect(presentation(views.active)).toMatchObject({state:'active',working:true,attention:1});
  expect(presentation(views.waiting)).toMatchObject({state:'waiting',working:false,attention:0});
  expect(presentation(views.offline)).toMatchObject({state:'offline',label:'Core unavailable',working:false,attention:0});
  expect(presentation({...views.active,tasks:[{...views.active.current!,state:'blocked'}],current:{...views.active.current!,state:'blocked'}})).toMatchObject({label:'Blocked',working:false});
  expect(presentation({...views.active,tasks:[{...views.active.current!,actions:[]}]}).attention).toBe(0);
});
it('renders every concept/state with the unchanged Orb and an accessible opener',()=>{
  for(const concept of ['a','b','c'] as const)for(const view of Object.values(views)) {
    const onOpen=vi.fn();const {container}=render(<Presence concept={concept} view={view} onOpen={onOpen}/>);
    expect(screen.getByAltText('OSCAR Orb').getAttribute('src')).toBe(orb);
    expect(container.querySelector('[data-working]')?.getAttribute('data-working')).toBe(String(presentation(view).working));
    fireEvent.click(screen.getByRole('button',{name:'Open OSCAR interaction'}));expect(onOpen).toHaveBeenCalledOnce();
    if(view.link!=='online')expect(screen.queryByRole('button',{name:/require owner attention/})).toBeNull();
    cleanup();
  }
  expect(dimensions('c','idle')).toEqual([192,112]);expect(dimensions('c','active')).toEqual([364,164]);
});
it('expands into existing App using only synthetic state and returns without a native bridge',async()=>{
  history.replaceState({},'','/?presence=c&state=offline&tools');render(<Exploration/>);
  fireEvent.click(screen.getByRole('button',{name:'Open OSCAR interaction'}));
  await screen.findByText('Synthetic expansion · existing interaction UI · no execution');
  await waitFor(()=>expect((screen.getByRole('button',{name:'Ask'}) as HTMLButtonElement).disabled).toBe(true));
  fireEvent.click(screen.getByRole('button',{name:'Compact presence'}));
  expect(screen.getByRole('button',{name:'Open OSCAR interaction'})).toBeDefined();
});
it('switches fixtures without faking work or approvals and supports Escape',async()=>{
  history.replaceState({},'','/?presence=a&tools');render(<Exploration/>);
  fireEvent.click(screen.getByRole('button',{name:'active'}));expect(screen.getByText('Running')).toBeDefined();
  fireEvent.click(screen.getByRole('button',{name:'waiting'}));expect(screen.getByText('Waiting for result')).toBeDefined();
  fireEvent.click(screen.getByRole('button',{name:'offline'}));expect(screen.getByText('Core unavailable')).toBeDefined();
  fireEvent.click(screen.getByRole('button',{name:'Open OSCAR interaction'}));
  await screen.findByRole('button',{name:'Compact presence'});
  fireEvent.keyDown(screen.getByRole('button',{name:'Compact presence'}),{key:'Escape'});
  expect(screen.getByRole('button',{name:'Open OSCAR interaction'})).toBeDefined();
});
