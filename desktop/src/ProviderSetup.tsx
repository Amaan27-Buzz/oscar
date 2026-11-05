import {useEffect,useState} from 'react';
import type {Command,View} from './bridge';

export function ProviderSetup({view,busy,run}:{view:View;busy:boolean;run:(command:Command)=>unknown}) {
  const slots=view.models?.credential_slots??[];
  const available=slots.filter((slot,index)=>!slot.configured&&slots.findIndex(other=>other.provider===slot.provider&&!other.configured)===index);
  const [open,setOpen]=useState(false),[chosen,setChosen]=useState(''),[secret,setSecret]=useState('');
  const slot=available.find(item=>item.id===chosen)??available[0];
  const close=()=>{setSecret('');setOpen(false);};
  useEffect(()=>{setSecret('');setOpen(false);},[view.link,view.connection?.endpoint]);
  if(view.connection)return <p className="leaf-secondary">Provider keys are managed securely on your Core host. This device can choose the shared model.</p>;
  return <div className="provider-setup">
    <div className="setting-line"><div><h3>Provider keys</h3><p>Keys are saved in Windows Credential Manager. They stay out of conversation history and project files. Saving a key does not verify inference or enable paid usage.</p></div><button disabled={busy||view.link!=='online'||!available.length} onClick={()=>setOpen(true)}>Add provider key</button></div>
    {slots.some(item=>item.configured)&&<p className="leaf-secondary">Configured: {[...new Set(slots.filter(item=>item.configured).map(item=>item.provider))].join(', ')}. Availability is checked separately.</p>}
    {open&&<form className="model-plan-review" onSubmit={async event=>{
      event.preventDefault();if(!slot||!secret||busy||view.link!=='online')return;
      const value=secret;setSecret('');
      const result=await run({kind:'setup_provider',slot:slot.id,secret:value});
      if(result!==false)setOpen(false);
    }}>
      <label htmlFor="provider-choice">Provider</label><select id="provider-choice" disabled={busy} value={slot?.id??''} onChange={event=>{setChosen(event.target.value);setSecret('');}}>{available.map(item=><option key={item.id} value={item.id}>{item.provider}</option>)}</select>
      <label htmlFor="provider-secret">API key</label><input id="provider-secret" type="password" autoComplete="off" spellCheck={false} value={secret} maxLength={2000} disabled={busy||view.link!=='online'} onChange={event=>setSecret(event.target.value)}/>
      <p>Use a free account with billing disabled. Gemini and Groq also need the free-plan confirmation below. Existing keys are preserved.</p>
      <div className="actions"><button type="submit" disabled={busy||!secret||!slot||view.link!=='online'}>Save key securely</button><button type="button" onClick={close}>Cancel</button></div>
    </form>}
  </div>;
}
