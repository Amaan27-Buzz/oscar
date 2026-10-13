import {useEffect,useRef,useState} from 'react';
import type {ReactNode} from 'react';
import type {ActForm,Capability,Command} from './bridge';
const labels:Record<string,string>={write_file:'Write exact file',read_file:'Read file',list_files:'List workspace files',
  find_files:'Find files',git_status:'Git status',git_diff:'Git diff',git_log:'Recent commits',git_branches:'Branches',
  git_branch:'Create branch',ps_environment:'PowerShell environment names',ps_file_hash:'File hash',ps_write_utf8:'Write UTF-8 artifact',
  program_version:'Registered program version',inspect_page:'Inspect isolated browser page',list_apps:'Registered applications',
  launch_app:'Launch registered application',worker_tools:'Inspect Worker tools'};
export function describeAction(form:ActForm){return `${labels[form.operation]??'Scoped action'}${'path' in form?`: ${form.path}`:'url' in form?`: ${form.url}`:'name' in form?`: ${form.name}`:''}`;}
export interface ActionDraft {id:string;operation:string;value:string;text:string}
export const emptyActionDraft:ActionDraft={id:'',operation:'',value:'',text:''};
export function Act({capabilities,run,disabled,draft,onDraftChange,context}:{capabilities:Capability[];run:(command:Command)=>void;disabled:boolean;draft?:ActionDraft;onDraftChange?:(draft:ActionDraft)=>void;context?:ReactNode}) {
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
  const writing=['write_file','ps_write_utf8'].includes(operation);
  const valueLabel=operation==='inspect_page'?'HTTP(S) page':operation==='find_files'?'Filename pattern':operation==='git_branch'?'Branch name':'Relative workspace path';
  const nodes=[...new Set(available.map(item=>item.node))];
  const ready=!!selected&&selected.operations.includes(operation)&&(!needsValue||!!value.trim())&&(!['program_version','launch_app'].includes(operation)||!!value);
  return <section className="action-form" aria-label="Act">
    {(available.length>1||!selected||!!selected&&selected.operations.length>1)&&<div className="action-choice-bar">
      {(available.length>1||!selected)&&<label>Action<select aria-label="Available capability" value={id} onChange={e=>choose(e.target.value)}><option value="">Choose an action</option>{available.map(c=><option key={c.id} value={c.id}>{c.label}{nodes.length>1?` · Executor ${nodes.indexOf(c.node)+1}`:''}</option>)}</select></label>}
      {!!selected&&selected.operations.length>1&&<label>Operation<select aria-label="Operation" value={operation} onChange={e=>chooseOperation(e.target.value)}>{selected.operations.map(o=><option key={o} value={o}>{labels[o]??o}</option>)}</select></label>}
    </div>}
    <div className="action-composition"><div className="action-main">
      <div className="action-editor"><header className="action-editor-title"><span className="action-document-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h8l4 4v14H6V3Zm8 0v5h4M9 12h6m-6 4h6"/></svg></span><div><h2>{selected?labels[operation]??selected.label:'Choose an action'}</h2><p>{writing?'Create a file with the content you provide.':selected?.summary??'Select an available action to get started.'}</p></div></header>
      {needsValue&&<div className="action-destination"><label>{writing?'File destination':valueLabel}<input aria-label={valueLabel} maxLength={200} placeholder={operation==='inspect_page'?'https://example.com':operation==='find_files'?'*.md':operation==='git_branch'?'feature-name':'notes/summary.txt'} value={value} onChange={e=>update({value:e.target.value})}/></label>{writing&&<small>A path inside the permitted workspace.</small>}</div>}
      {writing&&<div className="file-content-editor"><label>File contents<textarea aria-label="Exact content" rows={9} maxLength={4096} placeholder="Write or paste the file contents…" value={text} onChange={e=>update({text:e.target.value})}/></label><div><span>Exact text</span><span>{text.length} / 4096</span></div></div>}
      {operation==='program_version'&&<label>Registered program<select aria-label="Registered program" value={value} onChange={e=>update({value:e.target.value})}><option value="">Choose a registered program</option>{selected?.programs.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>}
      {operation==='launch_app'&&<label>Authorized application<select aria-label="Authorized application" value={value} onChange={e=>update({value:e.target.value})}><option value="">Choose a registered application</option>{selected?.applications.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>}
      </div>
      <div className="action-review-bar"><button className="leaf-primary" disabled={disabled||!ready} onClick={submit}>Prepare action</button><span>{disabled?'Action preparation is currently unavailable.':!selected?'Choose an action to continue.':!ready?'Complete the destination to continue.':'Ready for exact review.'}</span></div>
    </div><aside className="action-support"><h2>Before you continue</h2><p>Preparing an action does not run it. You’ll review exactly what will happen.</p>
      {context}
      {selected&&<details className="action-permissions"><summary>Permissions</summary><dl><div><dt>Executor</dt><dd>{selected.node}</dd></div><div><dt>Risk</dt><dd>{selected.risk}</dd></div><div><dt>Required scopes</dt><dd>{selected.permissions?.join(', ')||'Checked for this request'}</dd></div></dl></details>}
    </aside></div>
  </section>;
}
