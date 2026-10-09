import React from 'react';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {Lab} from './Lab';

beforeEach(()=>{
  vi.stubGlobal('matchMedia',()=>({matches:false,addEventListener:vi.fn(),removeEventListener:vi.fn()}));
  vi.stubGlobal('requestAnimationFrame',vi.fn(()=>1));vi.stubGlobal('cancelAnimationFrame',vi.fn());
});
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
describe('review instrument',()=>{
  it('selects channels independently, resolves conflict and interrupts without automatic listening',()=>{
    render(<Lab/>);
    fireEvent.change(screen.getByLabelText('Expressive delivery'),{target:{value:'amused'}});
    expect(screen.getByLabelText('Operational state')).toHaveProperty('value','available');
    fireEvent.change(screen.getByLabelText('Operational state'),{target:{value:'speaking'}});
    fireEvent.click(screen.getByLabelText('Conversational mute'));
    expect(screen.getByTestId('resolved').textContent).toBe('muted / composed');
    fireEvent.click(screen.getByText('Interrupt',{selector:'button'}));
    expect(screen.getByTestId('resolved').textContent).toBe('muted / composed');
    fireEvent.click(screen.getByLabelText('Conversational mute'));
    expect(screen.getByTestId('resolved').textContent).toBe('available / interrupted');
  });
  it('scrubs, pauses and exposes all actual sizes with synthetic labels',()=>{
    render(<Lab/>);
    fireEvent.click(screen.getByText('Run sequence',{selector:'button'}));
    expect(screen.getByText('Pause',{selector:'button'})).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Scrub transition'),{target:{value:'2400'}});
    expect(screen.getByText('Play',{selector:'button'})).toBeTruthy();
    expect(screen.getByTestId('resolved').textContent).toBe('listening / attentive');
    for(const size of [32,48,64,96,128,192])expect(screen.getByRole('img',{name:`OSCAR at ${size} pixels: listening`}).getAttribute('width')).toBe(String(size));
    expect(screen.getAllByText('SIMULATED VISUAL STATE — NO CORE EXECUTION')).toHaveLength(2);
  });
  it('honors system reduced motion and keeps controls available',()=>{
    vi.stubGlobal('matchMedia',()=>({matches:true,addEventListener:vi.fn(),removeEventListener:vi.fn()}));
    render(<Lab/>);
    expect(screen.getByLabelText('Reduced motion')).toHaveProperty('checked',true);
    expect(screen.getByLabelText('Reduced motion')).toHaveProperty('disabled',true);
    expect(screen.getByText('Static equivalent')).toBeTruthy();
    expect(screen.getByText('Run sequence',{selector:'button'})).toBeTruthy();
  });
  it('physical control labels target sliders rather than their value outputs',()=>{
    render(<Lab/>);
    for(const name of ['Expression intensity','Puck weight','Gaze horizontal','Gaze vertical']) {
      expect(screen.getByRole('slider',{name}).tagName).toBe('INPUT');
    }
    fireEvent.change(screen.getByRole('slider',{name:'Expression intensity'}),{target:{value:'.35'}});
    expect(screen.getByRole('slider',{name:'Expression intensity'})).toHaveProperty('value','0.35');
  });
});
