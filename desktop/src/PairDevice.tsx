import {useState} from 'react';
import type {Command,View} from './bridge';
import {Disclosure} from './UIControls';

export function PairDevice({view,busy,run}:{view:View;busy:boolean;run:(command:Command)=>unknown}) {
 const [registration,setRegistration]=useState(''),[name,setName]=useState(''),[retain,setRetain]=useState(false),[approve,setApprove]=useState(false),[ownerKey,setOwnerKey]=useState(''),[error,setError]=useState('');
 if(!view.connections?.device_pairing)return null;
 return <section className="settings-group pair-device" aria-label="Pair a phone"><h2>Bring your phone along</h2><p>Open Connect Core on OSCAR Mobile and show its public identity. Review that registration here to create a device-bound invitation.</p>
 <p>Your phone still needs a reachable trusted HTTPS Core. The everyday local launcher provides loopback connectivity; issuing an invitation does not configure hosting, network access or a firewall.</p>
 <Disclosure title={<>Pair a phone</>}><form onSubmit={event=>{
  event.preventDefault();setError('');
  try {const value=JSON.parse(registration);if(!value.installation_id||!value.public_key||!/^([a-z0-9][a-z0-9-]{7,63})$/.test(name))throw new Error();
   void run({kind:'manage_connection',operation:'pair_device',id:name,value:JSON.stringify({installation_id:value.installation_id,public_key:value.public_key,owner_public_key:value.owner_public_key??ownerKey,retain,approve})});
  } catch {setError('Use the phone’s public registration and an 8–64 character lowercase device name with letters, numbers or hyphens.');}
 }}><label htmlFor="pair-name">Device name</label><input id="pair-name" value={name} maxLength={64} placeholder="my-oscar-phone" onChange={event=>setName(event.target.value)}/><label htmlFor="pair-registration">Phone public registration</label><textarea id="pair-registration" rows={4} maxLength={12000} value={registration} onChange={event=>setRegistration(event.target.value)} spellCheck={false}/>
 <label className="pair-choice"><input type="checkbox" checked={retain} onChange={event=>setRetain(event.target.checked)}/>Allow shared conversation history and retention</label>
 <label className="pair-choice"><input type="checkbox" checked={approve} onChange={event=>setApprove(event.target.checked)}/>Allow signed owner reviews from this phone</label>
 {approve&&<><label htmlFor="pair-owner-key">Phone owner-review public key</label><textarea id="pair-owner-key" rows={3} maxLength={6000} value={ownerKey} onChange={event=>setOwnerKey(event.target.value)} spellCheck={false}/><p>Use Show public owner identity in the phone’s About settings. This separate key uses Android’s device-lock review; it is not the connection proof key.</p></>}
 <p>Microphone, camera, notification access, Android actions and Full Access are separate grants. Existing device identities cannot be replaced here.</p>
 {error&&<p role="alert">{error}</p>}<button disabled={busy||view.link!=='online'||!registration||!name}>Review invitation</button></form></Disclosure>
 {view.connections.device_invitations?.map(invitation=><Disclosure key={invitation.node_id} title={<>Invitation for {invitation.node_id}</>}><p>Use this on the registered phone within five minutes. Enrollment is not confirmed until the phone proves possession of its private key.</p><label htmlFor={'invite-'+invitation.node_id}>Device-bound invitation</label><textarea id={'invite-'+invitation.node_id} rows={5} readOnly value={JSON.stringify(invitation)}/></Disclosure>)}
 </section>;
}
