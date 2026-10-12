import {act,cleanup,fireEvent,render,screen} from '@testing-library/react';
import {afterEach,describe,expect,it,vi} from 'vitest';
import {App} from './main';

vi.mock('@oscar/expression/react',()=>({ExpressionPresence:()=> <span>Existing Orb renderer</span>}));
afterEach(()=>{cleanup();vi.useRealTimers();});
describe('isolated Aperture interaction study',()=>{
 it('opens a pending decision even when work finished in another view',()=>{
  vi.useFakeTimers();render(<App/>);
  fireEvent.click(screen.getByRole('button',{name:/05\s*Work/}));
  fireEvent.click(screen.getByRole('button',{name:'Text tools'}));
  act(()=>vi.advanceTimersByTime(5200));
  fireEvent.keyDown(window,{key:'Escape'});
  fireEvent.click(screen.getByRole('button',{name:'Invoke OSCAR'}));
  expect(screen.getByRole('button',{name:'Approve example'})).toBeTruthy();
  fireEvent.click(screen.getByRole('button',{name:'Approve example'}));
  expect(screen.getByText('Simulated result · no file was created.')).toBeTruthy();
 });
 it('cancellation cannot later become a pending approval',()=>{
  vi.useFakeTimers();render(<App/>);
  fireEvent.click(screen.getByRole('button',{name:/05\s*Work/}));
  fireEvent.click(screen.getByRole('button',{name:'Cancel task'}));
  act(()=>vi.advanceTimersByTime(10000));
  expect(screen.getByText('Cancelled · nothing changed')).toBeTruthy();
  expect(screen.queryByRole('button',{name:'Approve example'})).toBeNull();
 });
 it('pin keeps the panel open when returning to the example document',()=>{
  render(<App/>);fireEvent.click(screen.getByRole('button',{name:'Invoke OSCAR'}));
  fireEvent.click(screen.getByRole('button',{name:'Pin prototype panel'}));
  fireEvent.click(screen.getByRole('region',{name:'Example document, not a connected application'}));
  expect(screen.getByRole('button',{name:'Minimize OSCAR'})).toBeTruthy();
  fireEvent.click(screen.getByRole('button',{name:'Unpin prototype panel'}));
  fireEvent.click(screen.getByRole('region',{name:'Example document, not a connected application'}));
  expect(screen.getByRole('button',{name:'Invoke OSCAR'})).toBeTruthy();
 });
 it('voice preview remains explicit and Escape restores the invoker',()=>{
  render(<App/>);fireEvent.click(screen.getByRole('button',{name:'Preview voice interaction'}));
  expect(screen.getByText('Simulated transcript. Microphone is off.')).toBeTruthy();
  fireEvent.keyDown(window,{key:'Escape'});
  expect(document.activeElement).toBe(screen.getByRole('button',{name:'Invoke OSCAR'}));
 });
});
