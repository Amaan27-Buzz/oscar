import {useState} from 'react';
import type {Command,View,WorkerConfig} from './bridge';
import {Disclosure} from './UIControls';
import './WorkerSharing.css';

const capabilities=[
  ['machine.files.read','Read workspace files'],['machine.files.write','Write workspace files'],
  ['machine.files.list','List workspace folders'],['machine.files.search','Find workspace files'],
  ['machine.executables','Find installed executables'],['machine.command','Allowlisted commands'],
  ['machine.git','Git operations'],['machine.repository','Repository tasks'],['machine.powershell','PowerShell'],
  ['machine.desktop','Windows app controls'],['machine.apps','Launch registered apps'],
  ['machine.clipboard','Read and write clipboard'],['machine.browser','Isolated browser'],
  ['machine.screen','Save selected-window screenshots'],['machine.visual','Click within reviewed window screenshots'],
  ['machine.controls','Read selected-window controls'],
  ['machine.agent.codex','Installed Codex'],['machine.agent.claude-code','Installed Claude Code'],
  ['machine.agent.opencode','Installed OpenCode'],['machine.agent.gemini-cli','Installed Gemini CLI'],
];
const host=(id:string)=>!id.startsWith('machine.files.')&&id!=='machine.executables';
const lines=(value:string)=>value.split(/\r?\n/).map(v=>v.trim()).filter(Boolean);

export function WorkerSharing({view,busy,run}:{view:View;busy:boolean;run:(command:Command)=>Promise<boolean>}) {
  const [config,setConfig]=useState<WorkerConfig>({python:'',workspace:'',capabilities:[],trusted_host_execution:false,allowed_executables:[],desktop_app_ids:[]});
  const [executables,setExecutables]=useState(''),[apps,setApps]=useState('');
  const sharing=view.worker_sharing;
  const running=!!sharing&&!['stopped','unavailable'].includes(sharing.status);
  const connected=view.link==='online'&&!!view.connection?.node_id;
  const bound=!!view.connection?.workspace;
  const disabled=busy||running;
  return <section className="settings-group desktop-sharing" aria-labelledby="desktop-sharing-title">
    <h2 id="desktop-sharing-title">Use this Desktop</h2>
    <p>Let your OSCAR Core use selected capabilities while this app is running. Every task keeps its Core approval, policy and revocation checks.</p>
    <p role="status">{sharing?.status==='online'?'Desktop execution connected':running?`Desktop execution: ${sharing?.status.replaceAll('_',' ')}`:'Desktop execution stopped'}</p>
    {sharing?.message&&<p className="leaf-secondary">{sharing.message}</p>}
    {running?<><p>Shared workspace: {sharing?.workspace}</p><p>{sharing?.capabilities.map(id=>capabilities.find(c=>c[0]===id)?.[1]??id).join(', ')}</p><button disabled={busy} onClick={()=>run({kind:'worker_stop'})}>Stop Desktop sharing</button></>:
      <Disclosure title={<>Set up Desktop sharing</>}>
        {!connected&&<p>Connect this Desktop to your Core before starting.</p>}
        {view.connection&&!bound&&<p>Reconnect with a new device invitation to bind an execution workspace.</p>}
        <p>Use an existing Python installation with the OSCAR package and its required executors installed. Nothing starts automatically.</p>
        {bound&&<p>Enrolled workspace: {view.connection?.workspace}</p>}
        <form onSubmit={event=>{event.preventDefault();void run({kind:'worker_start',config:{...config,allowed_executables:lines(executables),desktop_app_ids:lines(apps)}});}}>
          <label htmlFor="sharing-python">Installed Python executable</label><input id="sharing-python" value={config.python} maxLength={2048} disabled={disabled} placeholder="C:\Python\python.exe" spellCheck={false} onChange={event=>setConfig({...config,python:event.target.value})}/>
          <label htmlFor="sharing-workspace">Shared workspace folder</label><input id="sharing-workspace" value={config.workspace} maxLength={2048} disabled={disabled} placeholder="C:\OSCAR\workspace" spellCheck={false} onChange={event=>setConfig({...config,workspace:event.target.value})}/>
          <p className="leaf-secondary">Choose an existing absolute folder. OSCAR's private configuration, execution journal and browser profiles stay outside it.</p>
          <fieldset disabled={disabled}><legend>Capabilities to share</legend>{capabilities.map(([id,label])=><label className="sharing-check" key={id}><input type="checkbox" checked={config.capabilities.includes(id)} disabled={host(id)&&!config.trusted_host_execution} onChange={event=>setConfig({...config,capabilities:event.target.checked?[...config.capabilities,id]:config.capabilities.filter(v=>v!==id)})}/>{label}</label>)}</fieldset>
          <label className="sharing-check"><input type="checkbox" checked={config.trusted_host_execution} disabled={disabled} onChange={event=>setConfig({...config,trusted_host_execution:event.target.checked,capabilities:event.target.checked?config.capabilities:config.capabilities.filter(id=>!host(id))})}/>Allow execution with this Windows account's permissions</label>
          <p className="leaf-secondary">Commands, browser and app control use your Windows account's access. This local grant does not activate Secure or Full Access. Uninstalled or unenrolled capabilities remain unavailable.</p>
          {config.trusted_host_execution&&<><label htmlFor="sharing-executables">Allowed executable paths, one per line</label><textarea id="sharing-executables" rows={3} maxLength={8192} value={executables} disabled={disabled} spellCheck={false} onChange={event=>setExecutables(event.target.value)}/><label htmlFor="sharing-apps">Registered application IDs, one per line</label><textarea id="sharing-apps" rows={2} maxLength={2048} value={apps} disabled={disabled} spellCheck={false} onChange={event=>setApps(event.target.value)}/></>}
          <button className="leaf-primary" disabled={disabled||!connected||!bound||!config.python.trim()||!config.workspace.trim()||!config.capabilities.length||(config.capabilities.includes('machine.command')&&!lines(executables).length)}>Review and start sharing</button>
        </form>
      </Disclosure>}
  </section>;
}
