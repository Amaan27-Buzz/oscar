import {useEffect,useState} from 'react';
import type {Command,ConnectionsView,View} from './bridge';
import {Disclosure} from './UIControls';

type Run=(command:Command)=>Promise<boolean>;
type Provider=NonNullable<ConnectionsView['providers']>[number];
const identityLabels:Record<string,string>={'oscar-owned':'OSCAR’s account','owner-delegated':'Owner-delegated account',service:'Service identity',workload:'Workload identity','resource-grant':'MCP resource access · person identity not verified'};
function AddAccount({data,busy,run}:{data:ConnectionsView;busy:boolean;run:Run}) {
  const providers=data.providers??[];
  const [providerId,setProvider]=useState(providers[0]?.id??'');
  const [alias,setAlias]=useState('');
  const [accountId,setAccount]=useState('');
  const [identity,setIdentity]=useState('owner-delegated');
  const [scopes,setScopes]=useState<string[]>([]);
  const provider=providers.find(p=>p.id===providerId);
  const resource=provider?.provider==='mcp-resource';
  const existing=data.accounts.find(a=>a.id===accountId);
  return <Disclosure title={<>Connect an account</>}>
    {providers.length===0?<p>Configure a registered provider or MCP resource application on Core before connecting.</p>:<form onSubmit={event=>{event.preventDefault();void run({kind:'manage_connection',operation:'begin_account',id:providerId,value:JSON.stringify({alias:existing?.alias??alias,scopes,identity_class:resource?'resource-grant':existing?.identity_class??identity,...(accountId?{account_id:accountId}:{})})});}}>
      <label htmlFor="account-provider">Service</label><select id="account-provider" value={providerId} onChange={event=>{setProvider(event.target.value);setScopes([]);setAccount('');}}>{providers.map(p=><option key={p.id} value={p.id}>{p.provider} · {p.service}</option>)}</select>
      <label htmlFor="account-existing">Account connection</label><select id="account-existing" value={accountId} onChange={event=>{setAccount(event.target.value);setScopes([]);}}><option value="">Add another account</option>{data.accounts.filter(a=>a.provider===provider?.provider&&(resource?a.identity_class==='resource-grant'&&a.tenant===provider?.issuer&&a.services.some(s=>s.id===provider?.service):['owner-delegated','oscar-owned'].includes(a.identity_class))).map(a=><option key={a.id} value={a.id}>{a.alias} · reconnect or change permissions</option>)}</select>
      {!existing&&<><label htmlFor="account-alias">{resource?'Name for this resource access':'Name for this account'}</label><input id="account-alias" value={alias} maxLength={100} onChange={event=>setAlias(event.target.value)}/>{!resource&&<><label htmlFor="account-identity">Who owns this account?</label><select id="account-identity" value={identity} onChange={event=>setIdentity(event.target.value)}><option value="owner-delegated">My account</option><option value="oscar-owned">OSCAR’s separate account</option></select></>}</>}
      {resource&&<p>Authorize access to {provider?.resource} through {provider?.issuer}. This grant does not verify a provider person identity.</p>}
      <fieldset><legend>Service permissions</legend>{provider?.scopes.map(scope=><label key={scope}><input type="checkbox" checked={scopes.includes(scope)} onChange={event=>setScopes(current=>event.target.checked?[...current,scope]:current.filter(s=>s!==scope))}/>{scope}</label>)}</fieldset>
      <p>Choose only the permissions this service needs. Your browser will ask the provider to authorize the selected account. OSCAR’s action permissions remain separate.</p>
      <button disabled={busy||!provider||!scopes.length||(!existing&&!alias.trim())}>Review connect account</button>
    </form>}
  </Disclosure>;
}

function AddPlugin({data,busy,run}:{data:ConnectionsView;busy:boolean;run:Run}) {
  const [registration,setRegistration]=useState<{id:string;name:string;command?:string;url?:string;reviewed:Record<string,string[]>;value:string}|null>(null);
  const [error,setError]=useState('');
  const [trusted,setTrusted]=useState(false);
  return <Disclosure title={<>Add an MCP server</>}>
    <p>Import the server’s registration file to inspect its publisher endpoint, account and exact tool permissions before approval.</p>
    <label htmlFor="mcp-registration">Server registration file</label><input id="mcp-registration" type="file" accept="application/json,.json" disabled={busy} onChange={async event=>{
      setRegistration(null);setError('');setTrusted(false);const file=event.target.files?.[0];if(!file)return;
      try {if(file.size>20000)throw Error('Choose a registration file smaller than 20 KB.');const value=await file.text();const parsed=JSON.parse(value);const c=parsed.config;if(!c||typeof c.id!=='string'||typeof c.name!=='string'||!parsed.reviewed||typeof parsed.reviewed!=='object')throw Error('Choose a valid MCP registration file.');if(!data.accounts.some(a=>a.id===c.account_id&&a.generation===c.account_generation&&a.status==='connected'))throw Error('This server needs a current connected account.');setRegistration({id:c.id,name:c.name,command:c.command,url:c.url,reviewed:parsed.reviewed,value});}catch(e){setError(e instanceof Error?e.message:'Unable to read the server registration.');}
    }}/>
    {error&&<p role="alert">{error}</p>}
    {registration&&<><p><strong>{registration.name}</strong></p><p>{registration.url??registration.command}</p><p>Reviewed tools: {Object.entries(registration.reviewed).map(([tool,risks])=>tool+' ('+(Array.isArray(risks)?risks.join(', '):'Invalid permissions')+')').join('; ')}</p>
      {registration.command&&<label><input type="checkbox" checked={trusted} onChange={event=>setTrusted(event.target.checked)}/>I trust this local server. It runs with the Core host’s user permissions and can access its files and network.</label>}
      <button disabled={busy||!!registration.command&&!trusted} onClick={()=>run({kind:'manage_connection',operation:'register_plugin',id:registration.id,value:registration.value})}>Review add server</button></>}
  </Disclosure>;
}

function Account({account,busy,run,deletionAvailable,providers}:{account:ConnectionsView['accounts'][number];busy:boolean;run:Run;deletionAvailable:boolean;providers:Provider[]}) {
  const [alias,setAlias]=useState(account.alias);
  useEffect(()=>setAlias(account.alias),[account.alias]);
  return <Disclosure title={<>{account.alias} · {account.status==='connected'?'Connected':'Disabled'}</>}>
    <p>{account.provider} · {identityLabels[account.identity_class]??'Account identity'}</p>
    <dl><div><dt>{account.identity_class==='resource-grant'?'Grant ID':'Account'}</dt><dd>{account.subject}</dd></div><div><dt>{account.identity_class==='resource-grant'?'Authorization issuer':'Organization'}</dt><dd>{account.tenant}</dd></div></dl>
    <form onSubmit={event=>{event.preventDefault();void run({kind:'manage_connection',operation:'rename_account',id:account.id,value:alias});}}>
      <label htmlFor={'account-'+account.id}>Account name</label><input id={'account-'+account.id} value={alias} maxLength={100} onChange={event=>setAlias(event.target.value)}/>
      <button disabled={busy||!alias.trim()||alias===account.alias}>Review name change</button>
    </form>
    {account.services.map(service=><div key={service.id}><p><strong>{service.id}</strong> · {service.expires_at&&service.expires_at*1000<Date.now()?'Expired':'Permission recorded'}</p>
      <p>{service.scopes.length?service.scopes.join(', '):'No service permissions granted'}</p>
      {service.restrictions.length>0&&<p>Organization restrictions: {service.restrictions.join(', ')}</p>}
      <button disabled={busy||account.status!=='connected'} onClick={()=>run({kind:'manage_connection',operation:'default_account',id:account.id,value:service.id})}>Review use as default</button>
      {providers.some(p=>p.service===service.id&&p.provider===account.provider)&&<button disabled={busy||account.status!=='connected'} onClick={()=>run({kind:'manage_connection',operation:'refresh_account',id:account.id,value:service.id})}>Review refresh {service.id}</button>}
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
    <AddAccount data={data} busy={busy} run={run}/>
    {data.truncated&&<p>Showing {data.accounts.length} of {data.accounts_total} accounts and {data.plugins.length} of {data.plugins_total} tools. Use trusted setup to inspect the full catalog.</p>}
    {data.accounts.length===0?<p>No service accounts connected. {data.enrollment}.</p>:data.accounts.map(account=><Account key={account.id} account={account} busy={busy} run={run} deletionAvailable={data.credential_deletion==='available'} providers={data.providers??[]}/>)}
    <Disclosure title={<>Tools and connectors</>}>
      <AddPlugin data={data} busy={busy} run={run}/>
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
