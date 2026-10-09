import {useEffect,useState} from 'react';
import type {ActForm,Capability,Command} from './bridge';
const labels:Record<string,string>={write_file:'Write exact file',read_file:'Read file',list_files:'List workspace files',
  find_files:'Find files',git_status:'Git status',git_diff:'Git diff',git_log:'Recent commits',git_branches:'Branches',
  git_branch:'Create branch',ps_environment:'PowerShell environment names',ps_file_hash:'File hash',ps_write_utf8:'Write UTF-8 artifact',
  program_version:'Registered program version',inspect_page:'Inspect isolated browser page',list_apps:'Registered applications',
  launch_app:'Launch registered application',worker_tools:'Inspect Worker tools'};
export function Act({capabilities,run,disabled}:{capabilities:Capability[];run:(command:Command)=>void;disabled:boolean}) {
  const [id,setId]=useState('');const [operation,setOperation]=useState('');
  const [value,setValue]=useState('');const [text,setText]=useState('');
  const available=capabilities.filter(c=>c.operations.length);
  const selected=available.find(c=>c.id===id);
  useEffect(()=>{if(!selected){setId(available[0]?.id??'');setOperation('');}},[capabilities,id]);
  useEffect(()=>{setOperation(selected?.operations[0]??'');setValue('');},[id]);
  useEffect(()=>{if(operation==='launch_app')setValue(selected?.applications[0]?.id??'');
    if(operation==='program_version')setValue(selected?.programs[0]?.id??'');},[operation,id]);
  function submit(){
    if(!selected||!selected.operations.includes(operation))return;
    let form:ActForm;
    switch(operation){
      case 'write_file':case 'ps_write_utf8':form={operation,path:value,text};break;
      case 'read_file':case 'ps_file_hash':form={operation,path:value};break;
      case 'find_files':form={operation,pattern:value};break;
      case 'git_branch':form={operation,name:value};break;
      case 'program_version':form={operation,program_id:value};break;
      case 'inspect_page':form={operation,url:value};break;
      case 'launch_app':form={operation,app_id:value};break;
      case 'list_files':case 'git_status':case 'git_diff':case 'git_log':case 'git_branches':
      case 'ps_environment':case 'list_apps':case 'worker_tools':form={operation};break;
      default:return;
    }
    run({kind:'act',capability_id:selected.id,form});
  }
  if(!available.length)return <p role="status">No eligible action capability is advertised. Nothing will be queued.</p>;
  const needsValue=['write_file','ps_write_utf8','read_file','ps_file_hash','find_files','git_branch','inspect_page'].includes(operation);
  return <section aria-label="Act"><label>Available capability<select value={id} onChange={e=>setId(e.target.value)}>
    {available.map(c=><option key={c.id} value={c.id}>{c.label} · {c.node}</option>)}</select></label>
    <label>Operation<select value={operation} onChange={e=>setOperation(e.target.value)}>
      {selected?.operations.map(o=><option key={o} value={o}>{labels[o]??o}</option>)}</select></label>
    {needsValue&&<label>{operation==='inspect_page'?'HTTP(S) page':operation==='find_files'?'Filename pattern':operation==='git_branch'?'Branch name':'Relative workspace path'}
      <input maxLength={200} value={value} onChange={e=>setValue(e.target.value)} /></label>}
    {['write_file','ps_write_utf8'].includes(operation)&&<label>Exact content<textarea maxLength={4096} value={text} onChange={e=>setText(e.target.value)}/></label>}
    {operation==='program_version'&&<label>Registered program<select value={value} onChange={e=>setValue(e.target.value)}>
      {selected?.programs.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>}
    {operation==='launch_app'&&<label>Authorized application<select value={value} onChange={e=>setValue(e.target.value)}>
      {selected?.applications.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>}
    <p className="secondary">{selected?.summary} · Core policy and owner review apply.</p>
    <button disabled={disabled||!operation||(operation==='program_version'&&!value)||(operation==='launch_app'&&!value)} onClick={submit}>Prepare action</button>
  </section>;
}
