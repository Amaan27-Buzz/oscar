import {useEffect,useState} from 'react';
import type {Command,ConnectionsView,View} from './bridge';
import {Disclosure} from './UIControls';

type Run=(command:Command)=>Promise<boolean>;
const identityLabels:Record<string,string>={'oscar-owned':'OSCAR’s account','owner-delegated':'Owner-delegated account',service:'Service identity',workload:'Workload identity'};
function Account({account,busy,run,deletionAvailable}:{account:ConnectionsView['accounts'][number];busy:boolean;run:Run;deletionAvailable:boolean}) {
  const [alias,setAlias]=useState(account.alias);
  useEffect(()=>setAlias(account.alias),[account.alias]);
  return <Disclosure title={<>{account.alias} · {account.status==='connected'?'Connected':'Disabled'}</>}>
    <p>{account.provider} · {identityLabels[account.identity_class]??'Account identity'}</p>
    <dl><div><dt>Account</dt><dd>{account.subject}</dd></div><div><dt>Organization</dt><dd>{account.tenant}</dd></div></dl>
    <form onSubmit={event=>{event.preventDefault();void run({kind:'manage_connection',operation:'rename_account',id:account.id,value:alias});}}>
      <label htmlFor={'account-'+account.id}>Account name</label><input id={'account-'+account.id} value={alias} maxLength={100} onChange={event=>setAlias(event.target.value)}/>
      <button disabled={busy||!alias.trim()||alias===account.alias}>Review name change</button>
    </form>
    {account.services.map(service=><div key={service.id}><p><strong>{service.id}</strong> · {service.expires_at&&service.expires_at*1000<Date.now()?'Expired':'Permission recorded'}</p>
      <p>{service.scopes.length?service.scopes.join(', '):'No service permissions granted'}</p>
      {service.restrictions.length>0&&<p>Organization restrictions: {service.restrictions.join(', ')}</p>}
      <button disabled={busy||account.status!=='connected'} onClick={()=>run({kind:'manage_connection',operation:'default_account',id:account.id,value:service.id})}>Review use as default</button>
    </div>)}
    <p>Provider revocation: {account.remote_revocation.replaceAll('_',' ').toLowerCase()}.</p>
    <p>{deletionAvailable?'Disabling blocks new operations and deletes local service credentials.':'Disabling blocks new operations. Local credential deletion is unavailable.'} Provider revocation must be checked separately.</p>
    {account.local_credentials&&<p>Local credentials: {account.local_credentials.replaceAll('_',' ')}.</p>}
    <button disabled={busy||account.status!=='connected'} onClick={()=>run({kind:'manage_connection',operation:'disconnect_account',id:account.id,value:''})}>Review disable account</button>
  </Disclosure>;
}

export function Connections({view,busy,run}:{view:View;busy:boolean;run:Run}) {
  const data=view.link==='online'?view.connections:null;
  if(!data)return <section className="settings-group"><h2>Accounts and connections</h2><p>Connect to OSCAR to inspect your accounts and tools.</p></section>;
  return <section className="settings-group connection-setting" aria-labelledby="accounts-title">
    <h2 id="accounts-title">Accounts and connections</h2>
    <p>Choose which identity acts. Changes use your current Ask review.</p>
    <Disclosure title={<>{data.identity.display_name} · Operational identity</>}><p>{data.identity.operational_email??'No operational mailbox configured.'}</p><p>OSCAR’s own identity has separate accounts and permissions.</p></Disclosure>
    {data.truncated&&<p>Showing {data.accounts.length} of {data.accounts_total} accounts and {data.plugins.length} of {data.plugins_total} tools. Use trusted setup to inspect the full catalog.</p>}
    {data.accounts.length===0?<p>No service accounts connected. {data.enrollment}.</p>:data.accounts.map(account=><Account key={account.id} account={account} busy={busy} run={run} deletionAvailable={data.credential_deletion==='available'}/>)}
    <Disclosure title={<>Tools and connectors</>}>
      {data.plugins.length===0?<p>No MCP servers installed. A trusted operator must review the server and its permissions before registration.</p>:data.plugins.map(plugin=><Disclosure key={plugin.id} title={<>{plugin.name} · {plugin.health==='ready'?'Connected':plugin.enabled?'Disconnected':'Disabled'}</>}>
        <p>{plugin.transport==='stdio'?'Runs on the Core host':'Remote connection'} · {data.accounts.find(a=>a.id===plugin.account_id)?.alias??'Account unavailable'}</p>
        <p>Permitted tools: {Object.entries(plugin.permissions).map(([tool,permissions])=>tool+' ('+permissions.join(', ')+')').join('; ')}</p>
        {plugin.tools.length>0&&<p>Discovered: {plugin.tools.map(tool=>tool.name).join(', ')}</p>}
        <button disabled={busy||!plugin.enabled||plugin.health==='ready'} onClick={()=>run({kind:'manage_connection',operation:'connect_plugin',id:plugin.id,value:''})}>Review connect and discover</button>
        <button disabled={busy} onClick={()=>run({kind:'manage_connection',operation:plugin.enabled?'disable_plugin':'enable_plugin',id:plugin.id,value:''})}>{plugin.enabled?'Review disable':'Review enable'}</button>
        <button disabled={busy} onClick={()=>run({kind:'manage_connection',operation:'remove_plugin',id:plugin.id,value:''})}>Review remove</button>
        <p>Recent activity: {plugin.activity.slice(-5).map(item=>item.event?.replaceAll('_',' ')).filter(Boolean).join(', ')||'No recent activity'}</p>
      </Disclosure>)}
    </Disclosure>
  </section>;
}
