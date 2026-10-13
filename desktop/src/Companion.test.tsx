import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {Companion} from './Companion';
import {initialView} from './bridge';
import {surface} from './surfaces';
vi.mock('./surfaces',async original=>({...await original<typeof import('./surfaces')>(),surface:vi.fn(),companionEvents:async()=>()=>{}}));
const native=vi.mocked(surface);
beforeEach(()=>{const now=Date.now();native.mockReset();native.mockResolvedValue({...initialView,link:'online',shortcut_enabled:true,expression:{epoch:'a'.repeat(32),generation:1,observed_at_ms:now,voice_observed_at_ms:now,tasks_observed_at_ms:now,current_observed_at_ms:now}});});
afterEach(cleanup);
it('reveals icon controls on hover and retracts when the pointer leaves',async()=>{
 render(<Companion/>);await screen.findByText('Ready');const companion=screen.getByRole('main',{name:'OSCAR Companion'});
 expect(companion.classList.contains('is-hovered')).toBe(false);fireEvent.pointerEnter(companion);expect(companion.classList.contains('is-hovered')).toBe(true);
 fireEvent.pointerLeave(companion);expect(companion.classList.contains('is-hovered')).toBe(false);expect(screen.queryByText('Shortcut on')).toBeNull();
 expect((screen.getByRole('button',{name:'Use voice'}) as HTMLButtonElement).disabled).toBe(true);
});
it('right click and keyboard controls request the bounded native menu only',async()=>{
 render(<Companion/>);await screen.findByText('Ready');const companion=screen.getByRole('main',{name:'OSCAR Companion'});
 fireEvent.contextMenu(companion);await waitFor(()=>expect(native).toHaveBeenCalledWith({kind:'companion_menu'}));
 fireEvent.keyDown(companion,{key:'F10',shiftKey:true});expect(native.mock.calls.filter(([c])=>c.kind==='companion_menu')).toHaveLength(2);
});
it('moves shortcut management into overflow and opens bounded access/Sentry selectors',async()=>{
 render(<Companion/>);await screen.findByText('Ready');expect(screen.queryByRole('button',{name:'Shortcut on'})).toBeNull();fireEvent.click(screen.getByRole('button',{name:'Companion controls'}));expect(native).toHaveBeenCalledWith({kind:'companion_menu'});
 fireEvent.click(screen.getByRole('button',{name:/Access mode/}));expect(native).toHaveBeenCalledWith({kind:'access_menu'});fireEvent.click(screen.getByRole('button',{name:'Sentry'}));expect(native).toHaveBeenCalledWith({kind:'sentry_menu'});
 fireEvent.click(screen.getByRole('button',{name:'Open Workspace'}));expect(native).toHaveBeenCalledWith({kind:'open_workspace'});expect(native.mock.calls.every(([c])=>!('review_id' in c)&&!('mode' in c))).toBe(true);
});
