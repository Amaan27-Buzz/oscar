import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
export type WindowMode='compact'|'interaction'|'approval'|'activity'|'reading'|'tools'|'actions';
export type ContextChoice='none'|'selection'|'focused'|'foreground';
export type Mode='Ask'|'Dictate'|'Edit'|'Act';
export interface Task { task_id:string; state:string; description:string; target:string; blocker:string|null;
  actions:string[]; generation:number; evidence_ids:string[]; response:string|null; response_status:string|null;
  value:string|null; epistemic:string|null;progress?:{fraction:number;step:string;status:string}|null;
  mode?:string;response_truncated?:boolean;source_event_ids?:string[] }
export interface Context {id:string;source:string;timestamp:number;expires_at?:number;scope:string;provenance:string;permission:string;
  freshness:string;text:string|null;retained:boolean}
export interface Choice {id:string;name:string}
export interface Capability {id:string;node:string;kind:string;label:string;summary:string;risk:string;
  operations:string[];programs:Choice[];applications:Choice[];permissions?:string[]}
export interface Preview {preview_id:string;before:string|null;after:string;epistemic:string;expires:number;destinations:string[];
  focused_before?:string|null;focused_after?:string|null;mode?:string}
export interface Review {review_id:string;task_id?:string;operation:string;description:string;target:string;capability:string;reason:string;
  consequence:string;policy_reason:string;evidence_state:string;review:string;expires_at_ms:number}
export interface ExpressionReadback {epoch:string;generation:number;observed_at_ms:number;voice_observed_at_ms:number;tasks_observed_at_ms:number;current_observed_at_ms:number}
export interface RequestFeedback {kind:'blocked'|'denied'|'unknown'|'rejected';message:string;observed_at_ms:number}
export interface View {expression:ExpressionReadback|null;link:string;orb:string;window:WindowMode;tasks:Task[];capabilities:Capability[];
  context:Context|null;preview:Preview|null;review:Review|null;current:Task|null;message:string|null;
  voice:string;shortcut:string;observed_at_ms:number;reference:boolean;window_revision?:number;feedback?:RequestFeedback|null}
export const initialView:View={expression:null,link:'unconfigured',orb:'unavailable',window:'compact',tasks:[],capabilities:[],
  context:null,preview:null,review:null,current:null,message:null,voice:'idle',shortcut:'Not registered',observed_at_ms:0,reference:false,window_revision:0,feedback:null};
export type ActForm=
  |{operation:'write_file'|'ps_write_utf8';path:string;text:string}
  |{operation:'read_file'|'ps_file_hash';path:string}
  |{operation:'find_files';pattern:string}|{operation:'git_branch';name:string}
  |{operation:'program_version';program_id:string}|{operation:'inspect_page';url:string}
  |{operation:'launch_app';app_id:string}
  |{operation:'list_files'|'git_status'|'git_diff'|'git_log'|'git_branches'|'ps_environment'|'list_apps'|'worker_tools'};
export type Command=
  |{kind:'ready'|'refresh'|'discard'|'voice_stop'|'voice_cancel'}|{kind:'window';mode:WindowMode}
  |{kind:'capture_choice'|'capture';source:ContextChoice}
  |{kind:'interact';mode:Exclude<Mode,'Act'>;text:string;context_id:string}
  |{kind:'act';capability_id:string;form:ActForm}
  |{kind:'inspect'|'preview';task_id:string}
  |{kind:'review';task_id:string;operation:'approve'|'deny'|'cancel'}
  |{kind:'confirm';review_id:string;accept:boolean}
  |{kind:'apply';preview_id:string;destination:'surface'|'clipboard'|'focused'}
  |{kind:'voice_start';context_id:string}|{kind:'shortcut';accelerator:string};
export type Send=(command:Command)=>Promise<View>;
export const send:Send=command=>invoke<View>('desktop_command',{request:command});
export const subscribe=(callback:(view:View)=>void)=>listen<View>('desktop-state',event=>callback(event.payload));
export const statuses:Record<string,string>={planned:'Approval required',executing:'Running',awaiting_result:'Waiting for result',
  result_received:'Result reported',verifying:'Verifying',verified:'Verified',partially_verified:'Partially verified',
  failed:'Failed',blocked:'Blocked',cancelled:'Cancelled',unknown:'Unknown outcome'};
export function stateLabel(view:View){return view.link!=='online'?'Core unavailable':view.current?
  statuses[view.current.state]??'Unknown':view.orb==='idle'?'I’m here.':view.orb;}
