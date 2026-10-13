import {act,cleanup,fireEvent,render,screen} from '@testing-library/react';
import {afterEach,describe,expect,it,vi} from 'vitest';
import {initialView} from '../bridge';
import {TextTools} from './TextTools';
afterEach(()=>{cleanup();vi.useRealTimers();});
const context={id:'focused',source:'focused',timestamp:Date.now()/1000,expires_at:Date.now()/1000+10,scope:'owned reference field',provenance:'UIA',permission:'granted',freshness:'fresh',text:'Before ',retained:false};
const preview={preview_id:'exact',before:'Before ',after:'spoken',focused_before:'Before ',focused_after:'Before spoken',mode:'Dictate',epistemic:'REPORTED',expires:Date.now()/1000+10,destinations:['surface','focused']};
describe('explicit text tools',()=>{
  it('shows the actual complete focused replacement and sends only that offered destination',()=>{
    const run=vi.fn(async()=>true);render(<TextTools view={{...initialView,context,preview}} available busy={false} mode="Dictate" setMode={()=>{}} draft="" setDraft={()=>{}} run={run} discard={()=>{}}/>);
    fireEvent.keyDown(screen.getByLabelText('Destination'),{key:'ArrowDown'});fireEvent.click(screen.getByRole('radio',{name:'Selected app field'}));
    expect(screen.getByText('Complete field after')).toBeTruthy();expect(screen.getByText('Before spoken')).toBeTruthy();
    fireEvent.click(screen.getByRole('button',{name:'Apply reviewed text'}));expect(run).toHaveBeenCalledWith({kind:'apply',preview_id:'exact',destination:'focused'});
  });
  it('expired preview cannot be applied or automatically retried',()=>{
    vi.useFakeTimers();const run=vi.fn(async()=>true);render(<TextTools view={{...initialView,preview:{...preview,expires:Date.now()/1000+1}}} available busy={false} mode="Dictate" setMode={()=>{}} draft="spoken" setDraft={()=>{}} run={run} discard={()=>{}}/>);
    act(()=>vi.advanceTimersByTime(1100));expect((screen.getByRole('button',{name:'Apply reviewed text'}) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByText(/Preview expired/)).toBeTruthy();expect(run).not.toHaveBeenCalled();
  });
  it('opening Dictate does not start a microphone and unavailable editing stays disabled',()=>{
    const run=vi.fn(async()=>true);const {rerender}=render(<TextTools view={initialView} available busy={false} mode="Dictate" setMode={()=>{}} draft="" setDraft={()=>{}} run={run} discard={()=>{}}/>);
    expect(run).not.toHaveBeenCalled();fireEvent.click(screen.getByRole('button',{name:'Start dictation'}));expect(run).toHaveBeenCalledWith({kind:'voice_start',context_id:''});
    rerender(<TextTools view={initialView} available busy={false} mode="Edit" setMode={()=>{}} draft="shorten" setDraft={()=>{}} run={run} discard={()=>{}}/>);
    expect((screen.getByRole('button',{name:'Request transformation'}) as HTMLButtonElement).disabled).toBe(true);
  });
  it('a new preview resets a previously selected destination and active voice offers explicit cancel',()=>{
    const run=vi.fn(async()=>true);const props={available:true,busy:false,mode:'Dictate' as const,setMode:()=>{},draft:'spoken',setDraft:()=>{},run,discard:()=>{}};
    const {rerender}=render(<TextTools {...props} view={{...initialView,context,preview}}/>);
    fireEvent.keyDown(screen.getByLabelText('Destination'),{key:'ArrowDown'});fireEvent.click(screen.getByRole('radio',{name:'Selected app field'}));
    rerender(<TextTools {...props} view={{...initialView,voice:'processing',preview:{...preview,preview_id:'new',destinations:['surface']}}}/>);
    expect(screen.getByLabelText('Destination').getAttribute('data-value')).toBe('surface');fireEvent.click(screen.getByRole('button',{name:'Cancel dictation'}));expect(run).toHaveBeenCalledWith({kind:'voice_cancel'});
  });
});

it('contextual review preserves apply checks without exposing a utility tab or instruction form',()=>{
 const run=vi.fn(async()=>true);render(<TextTools reviewOnly view={{...initialView,context,preview}} available busy={false} mode="Dictate" setMode={()=>{}} draft="" setDraft={()=>{}} run={run} discard={()=>{}}/>);
 expect(screen.queryByRole('tablist')).toBeNull();expect(screen.queryByLabelText('Dictation draft')).toBeNull();expect(screen.getByRole('button',{name:'Apply reviewed text'})).toBeTruthy();
});
