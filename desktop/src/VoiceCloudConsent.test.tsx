import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {VoiceSettings} from './VoiceSettings';
import {initialView} from './bridge';
afterEach(cleanup);
it('requires explicit cloud audio consent before enrolling controls',()=>{
 const run=vi.fn();
 render(<VoiceSettings view={{...initialView,link:'online',voice_available:false,setup:{voice:{available:true}}}} busy={false} run={run}/>);
 expect((screen.getByRole('button',{name:'Enable voice controls'}) as HTMLButtonElement).disabled).toBe(true);
 fireEvent.click(screen.getByLabelText('Allow microphone controls and Groq transcription for explicit voice turns.'));
 fireEvent.click(screen.getByRole('button',{name:'Enable voice controls'}));
 expect(run).toHaveBeenCalledWith({kind:'enable_voice',enabled:true});
 expect(run).not.toHaveBeenCalledWith(expect.objectContaining({kind:'voice_start'}));
});
it('lets the owner withdraw cloud audio authority separately from mute',()=>{
 const run=vi.fn();
 render(<VoiceSettings view={{...initialView,link:'online',voice_available:true}} busy={false} run={run}/>);
 fireEvent.click(screen.getByRole('button',{name:'Disable voice and cloud audio consent'}));
 expect(run).toHaveBeenCalledWith({kind:'enable_voice',enabled:false});
});
