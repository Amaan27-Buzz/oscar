import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import {Choice,Disclosure} from './UIControls';
afterEach(cleanup);
it('library disclosure exposes its expanded state and hides closed content',()=>{
 render(<Disclosure title="Optional context"><p>Scoped context</p></Disclosure>);
 const trigger=screen.getByRole('button',{name:'Optional context'});
 expect(trigger.getAttribute('aria-expanded')).toBe('false');expect(screen.queryByText('Scoped context')).toBeNull();
 fireEvent.click(trigger);expect(trigger.getAttribute('aria-expanded')).toBe('true');expect(screen.getByText('Scoped context')).toBeTruthy();
 fireEvent.click(trigger);expect(screen.queryByText('Scoped context')).toBeNull();
});
it('library choice offers real values and sends only the selected value',()=>{
 const change=vi.fn();render(<Choice label="Action" value="" onChange={change} placeholder="Choose an action" options={[{value:'write_file',label:'Write a file'}]}/>);
 const trigger=screen.getByRole('button',{name:'Action'});fireEvent.keyDown(trigger,{key:'ArrowDown'});
 expect(screen.getByRole('radiogroup',{name:'Action choices'})).toBeTruthy();fireEvent.click(screen.getByRole('radio',{name:'Write a file'}));
 expect(change).toHaveBeenCalledOnce();expect(change).toHaveBeenCalledWith('write_file');expect(trigger.getAttribute('aria-expanded')).toBe('false');
});
