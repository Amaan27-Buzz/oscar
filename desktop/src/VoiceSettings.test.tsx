import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {VoiceSettings} from './VoiceSettings';
import {initialView} from './bridge';
const settings={muted:true,input_device:2,output_device:null,continuous_available:true,continuous_active:false,continuous_granted:true,persisted:true};
const devices=[{id:2,name:'Synthetic microphone',input:true,output:false},{id:3,name:'Synthetic speaker',input:false,output:true}];
afterEach(cleanup);
it('queries devices explicitly and saves selected devices without starting capture',()=>{
 const run=vi.fn();render(<VoiceSettings view={{...initialView,link:'online',voice_available:true,voice_settings:settings,voice_devices:devices}} busy={false} run={run}/>);
 expect(run).not.toHaveBeenCalled();fireEvent.click(screen.getByRole('button',{name:'Find audio devices'}));expect(run).toHaveBeenLastCalledWith({kind:'voice_devices'});
 fireEvent.click(screen.getByLabelText('Keep microphone muted'));
 fireEvent.click(screen.getByRole('button',{name:'Save audio settings'}));
 expect(run).toHaveBeenLastCalledWith({kind:'voice_configure',muted:false,input_device:2,output_device:null});
 expect((screen.getByRole('button',{name:'Start local wake listening'}) as HTMLButtonElement).disabled).toBe(true);
});
it('requires current models, separate grant and explicit start, with persistent mute available',()=>{
 const run=vi.fn();const {rerender}=render(<VoiceSettings view={{...initialView,link:'online',voice_available:true,voice_settings:{...settings,muted:false,continuous_granted:false}}} busy={false} run={run}/>);
 expect((screen.getByRole('button',{name:'Start local wake listening'}) as HTMLButtonElement).disabled).toBe(true);
 expect(screen.getByText(/no continuous microphone grant/)).toBeTruthy();
 rerender(<VoiceSettings view={{...initialView,link:'online',voice_available:true,voice_settings:{...settings,muted:false}}} busy={false} run={run}/>);
 fireEvent.click(screen.getByRole('button',{name:'Start local wake listening'}));expect(run).toHaveBeenLastCalledWith({kind:'voice_listen'});
 fireEvent.click(screen.getByRole('button',{name:'Mute microphone'}));expect(run).toHaveBeenLastCalledWith({kind:'voice_mute'});
});
it('withdraws stale audio controls after connection loss and never invents device indices',()=>{
 const run=vi.fn();render(<VoiceSettings view={{...initialView,voice_available:true,voice_settings:{...settings,muted:false,continuous_active:true},voice_devices:devices}} busy={false} run={run}/>);
 expect(screen.queryByRole('button',{name:'Start local wake listening'})).toBeNull();expect(screen.queryByText('Synthetic microphone')).toBeNull();expect(run).not.toHaveBeenCalled();
 expect((screen.getByRole('button',{name:'Check audio controls'}) as HTMLButtonElement).disabled).toBe(true);
});
