import {useEffect,useRef,useState} from 'react';
import type {ActForm,Capability,Command} from './bridge';
const labels:Record<string,string>={write_file:'Write exact file',read_file:'Read file',list_files:'List workspace files',
  find_files:'Find files',git_status:'Git status',git_diff:'Git diff',git_log:'Recent commits',git_branches:'Branches',
  git_branch:'Create branch',ps_environment:'PowerShell environment names',ps_file_hash:'File hash',ps_write_utf8:'Write UTF-8 artifact',
  program_version:'Registered program version',inspect_page:'Inspect isolated browser page',list_apps:'Registered applications',
  launch_app:'Launch registered application',worker_tools:'Inspect Worker tools'};
export function describeAction(form:ActForm){return `${labels[form.operation]??'Scoped action'}${'path' in form?`: ${form.path}`:'url' in form?`: ${form.url}`:'name' in form?`: ${form.name}`:''}`;}
export interface ActionDraft {id:string;operation:string;value:string;text:string}
export const emptyActionDraft:ActionDraft={id:'',operation:'',value:'',text:''};
export function Act({capabilities,run,disabled,draft,onDraftChange}:{capabilities:Capability[];run:(command:Command)=>void;disabled:boolean;draft?:ActionDraft;onDraftChange?:(draft:ActionDraft)=>void}) {
  const [local,setLocal]=useState(emptyActionDraft),initial=useRef(true);
  const {id,operation,value,text}=draft??local;
  const update=(patch:Partial<ActionDraft>)=>onDraftChange?onDraftChange({...draft!,...patch}):setLocal(state=>({...state,...patch}));
  const available=capabilities.filter(c=>c.operations.length);
  const selected=available.find(c=>c.id===id);
  useEffect(()=>{if(initial.current&&available.length){initial.current=false;if(!id)update({id:available[0].id,operation:available[0].operations[0],value:'',text:''});}
    else if(id&&!selected)update(emptyActionDraft);},[capabilities,id]);
  function choose(next:string){const cap=available.find(item=>item.id===next);update({id:next,operation:cap?.operations[0]??'',value:'',text:''});}
  function chooseOperation(next:string){update({operation:next,value:next==='launch_app'?selected?.applications[0]?.id??'':next==='program_version'?selected?.programs[0]?.id??'':'',text:''});}
  function submit(){
    if(disabled||!selected||!selected.operations.includes(operation)||(needsValue&&!value.trim())||(['launch_app','program_version'].includes(operation)&&!value))return;
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
  if(!available.length)return <p role="status">No actions are available on your connected devices.</p>;
  const needsValue=['write_file','ps_write_utf8','read_file','ps_file_hash','find_files','git_branch','inspect_page'].includes(operation);
  return <section className="action-form" aria-label="Act"><div className="action-fields"><label>Available capability<select aria-label="Available capability" value={id} onChange={e=>choose(e.target.value)}>
    <option value="">Choose an executor</option>
    {available.map(c=><option key={c.id} value={c.id}>{c.label}{new Set(available.map(item=>item.node)).size>1?` · Executor ${[...new Set(available.map(item=>item.node))].indexOf(c.node)+1}`:''}</option>)}</select></label>
    <label>Operation<select aria-label="Operation" value={operation} onChange={e=>chooseOperation(e.target.value)}>
      {selected?.operations.map(o=><option key={o} value={o}>{labels[o]??o}</option>)}</select></label></div>
    {needsValue&&<label>{operation==='inspect_page'?'HTTP(S) page':operation==='find_files'?'Filename pattern':operation==='git_branch'?'Branch name':'Relative workspace path'}
      <input maxLength={200} value={value} onChange={e=>update({value:e.target.value})} /></label>}
    {['write_file','ps_write_utf8'].includes(operation)&&<label>Exact content<textarea rows={6} maxLength={4096} value={text} onChange={e=>update({text:e.target.value})}/></label>}
    {operation==='program_version'&&<label>Registered program<select aria-label="Registered program" value={value} onChange={e=>update({value:e.target.value})}>
      <option value="">Choose a registered program</option>
      {selected?.programs.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>}
    {operation==='launch_app'&&<label>Authorized application<select aria-label="Authorized application" value={value} onChange={e=>update({value:e.target.value})}>
      <option value="">Choose a registered application</option>
      {selected?.applications.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>}
    {selected&&<details className="action-permissions"><summary>Permission and destination</summary><dl><div><dt>Executor</dt><dd>{selected.node}</dd></div><div><dt>Risk</dt><dd>{selected.risk}</dd></div><div><dt>Required scopes</dt><dd>{selected.permissions?.join(', ')||'Checked for this request'}</dd></div></dl><p>{selected.summary}</p></details>}
    <div className="action-submit">    <button disabled={disabled||!selected||!operation||(needsValue&&!value.trim())||(operation==='program_version'&&!value)||(operation==='launch_app'&&!value)} onClick={submit}>Prepare action</button><span>You’ll review the exact action before it runs.</span></div>
  </section>;
}
