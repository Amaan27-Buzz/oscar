import {useState} from 'react';
import type {Command,View} from './bridge';
import {Disclosure} from './UIControls';

export function ConnectionSettings({view,busy,run}:{view:View;busy:boolean;run:(command:Command)=>Promise<boolean>}) {
  const [endpoint,setEndpoint]=useState(''),[invitation,setInvitation]=useState('');
  const connection=view.connection;
  return <section className="settings-group connection-setting" aria-labelledby="connection-title">
    <h2 id="connection-title">Connect your OSCAR</h2>
    <p>Use your trusted Core address and a device invitation approved by its owner.</p>
    {connection?<><dl><div><dt>Core</dt><dd>{connection.endpoint}</dd></div><div><dt>This device</dt><dd>{connection.node_id??'Awaiting enrollment'}</dd></div><div><dt>Connection</dt><dd>{connection.status.replaceAll('_',' ')}</dd></div></dl>
      {connection.status==='awaiting_enrollment'&&<><Disclosure title={<>Public enrollment details</>}><p>Give these public keys and this installation identity to your trusted Core operator. They contain no private credential.</p><label htmlFor="enrollment-public">Device registration</label><textarea id="enrollment-public" rows={5} readOnly value={JSON.stringify({installation_id:connection.installation_id,public_key:connection.public_key,owner_public_key:connection.owner_public_key},null,2)}/></Disclosure>
      <form onSubmit={event=>{event.preventDefault();void run({kind:'connection_enroll',invitation}).then(ok=>{if(ok)setInvitation('');});}}><label htmlFor="core-invitation">Approved device invitation</label><textarea id="core-invitation" rows={4} maxLength={16384} value={invitation} onChange={event=>setInvitation(event.target.value)} spellCheck={false}/><button className="leaf-primary" disabled={busy||!invitation.trim()}>Review and connect</button></form></>}
      <button disabled={busy} onClick={()=>run({kind:'connection_logout'})}>Disconnect and forget this device</button></>:
      <form onSubmit={event=>{event.preventDefault();void run({kind:'connection_prepare',url:endpoint});}}><label htmlFor="core-address">Core address</label><input id="core-address" type="url" placeholder="https://your-core.example" maxLength={2048} value={endpoint} onChange={event=>setEndpoint(event.target.value)} spellCheck={false}/><button disabled={busy||!endpoint.trim()}>Prepare this device</button></form>}
    {view.message&&<p role="status">{view.message}</p>}
  </section>;
}
