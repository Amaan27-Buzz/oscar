import type {ExecutiveSummary} from './Automations';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
export type WindowMode='compact'|'interaction'|'approval'|'activity'|'preferences'|'reading'|'tools'|'actions';
export type ContextChoice='none'|'selection'|'focused'|'foreground';
export type Mode='Ask'|'Dictate'|'Edit'|'Act';
export interface Task { task_id:string; state:string; retained_available?:boolean|null; description:string; target:string; blocker:string|null;
  actions:string[]; generation:number; evidence_ids:string[]; response:string|null; response_status:string|null;
  value:string|null; epistemic:string|null;progress?:{fraction:number;step:string;status:string}|null;
  mode?:string;response_truncated?:boolean;source_event_ids?:string[];
  evidence?:{id:string;source:string;method:string;observed_at:number;matches:boolean|null;status:string}[];
  artifacts?:{id:string;kind:string;status:string;content_hash:string|null}[] }
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
export interface VoiceSettings {muted:boolean;input_device:number|null;output_device:number|null;continuous_available:boolean;continuous_active:boolean;continuous_granted:boolean;persisted:boolean}
export interface AudioDevice {id:number;name:string;input:boolean;output:boolean}
export interface VoiceSupport {persistent_mute:'unavailable'|'available';sentry:'unavailable';acoustic_awareness:'unavailable';wake_word:'unavailable'|'available'}
export interface ConversationTurn {id:string;task_id:string;role:'owner'|'oscar';text:string;status:string;occurred_at:number;retained:boolean}
export interface ConversationHistory {turns:ConversationTurn[];before:number|null;persistence:string;revision:number;retention?:boolean}
export interface Operating {access:string;secure:string;full_access:string;awareness:string;sentry:string;worker_autonomy:string;automations:string}
export interface GridNode {id:string;role:string;status:string}
export interface CoreClockObservation {observed_at_ms:number;received_at_ms:number;transport_ms:number}
export interface ConnectionView {endpoint:string;installation_id:string;node_id:string|null;workspace?:string|null;public_key:string;owner_public_key:string;status:string}
export interface WorkerConfig {python:string;workspace:string;capabilities:string[];trusted_host_execution:boolean;allowed_executables:string[];desktop_app_ids:string[]}
export interface WorkerSharingView {status:string;workspace:string;capabilities:string[];message:string}
export interface ConnectionsView {
  identity:{id:string;display_name:string;operational_email:string|null;status:string};
  accounts:{id:string;provider:string;tenant:string;subject:string;alias:string;identity_class:string;generation:number;status:string;remote_revocation:string;local_credentials?:string;services:{id:string;scopes:string[];expires_at:number|null;restrictions:string[]}[]}[];
  plugins:{id:string;name:string;account_id:string;enabled:boolean;health:string;transport:string;permissions:Record<string,string[]>;tools:{name:string}[];activity:{event?:string;observed_at?:number}[]}[];
  providers?:{id:string;provider:string;service:string;scopes:string[];redirect_uri:string;configured:boolean;resource?:string;issuer?:string}[];
  access:string;enrollment:string;observed_at_ms:number;
  credential_deletion?:'available'|'unavailable';accounts_total?:number;plugins_total?:number;truncated?:boolean;
}
export interface View {voice_settings?:VoiceSettings|null;voice_devices?:AudioDevice[];connections?:ConnectionsView|null;day_brief?:Record<string,unknown>|null;worker_sharing?:WorkerSharingView|null}
export interface View {connection?:ConnectionView|null;nodes?:GridNode[];core_clock?:CoreClockObservation|null;executive?:ExecutiveSummary|null;presence?:{version:1;visible:boolean;expression:unknown}|null;setup?:Record<string,{configured?:boolean;operational?:boolean}>|null;adaptive_views?:unknown[];access_mode?:string|null;voice_available?:boolean;conversation?:ConversationHistory;operating?:Operating|null;theme?:'light'|'dark';expression:ExpressionReadback|null;link:string;orb:string;window:WindowMode;tasks:Task[];capabilities:Capability[];
  context:Context|null;preview:Preview|null;review:Review|null;current:Task|null;message:string|null;
  voice:string;voice_support?:VoiceSupport;shortcut:string;shortcut_enabled?:boolean;capture_choice?:ContextChoice;observed_at_ms:number;reference:boolean;window_revision?:number;feedback?:RequestFeedback|null}
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
  |{kind:'voice_settings'|'voice_devices'|'voice_listen'|'voice_mute'}
  |{kind:'voice_configure';muted:boolean;input_device:number;output_device:number|null}
  |{kind:'worker_start';config:WorkerConfig}|{kind:'worker_stop'}
  |{kind:'manage_assistance';operation:string;id:string;value:Record<string,unknown>}
  |{kind:'set_access';relationship_id:string;value:Record<string,unknown>}
  |{kind:'revoke_access'}
  |{kind:'manage_connection';operation:'begin_account'|'refresh_account'|'register_plugin'|'rename_account'|'default_account'|'disconnect_account'|'connect_plugin'|'disable_plugin'|'enable_plugin'|'remove_plugin';id:string;value:string}
  |{kind:'connection_prepare';url:string}|{kind:'connection_enroll';invitation:string}|{kind:'connection_logout'}|{kind:'cancel_remote';task_id:string}
  |{kind:'history';before:number}
  |{kind:'ready'|'refresh'|'day_brief'|'discard'|'voice_stop'|'voice_cancel'}|{kind:'window';mode:WindowMode}
  |{kind:'capture_choice'|'capture';source:ContextChoice}
  |{kind:'interact';mode:Exclude<Mode,'Act'>;text:string;context_id:string}
  |{kind:'act';capability_id:string;form:ActForm}
  |{kind:'inspect'|'preview';task_id:string}
  |{kind:'review';task_id:string;operation:'approve'|'deny'|'cancel'}
  |{kind:'confirm';review_id:string;accept:boolean}
  |{kind:'apply';preview_id:string;destination:'surface'|'clipboard'|'focused'}
  |{kind:'voice_start';context_id:string;mode?:'Ask'|'Dictate'}|{kind:'shortcut';accelerator:string};
export type Send=(command:Command)=>Promise<View>;
export const send:Send=command=>invoke<View>('desktop_command',{request:command});
export const subscribe=(callback:(view:View)=>void)=>listen<View>('desktop-state',event=>callback(event.payload));
export const statuses:Record<string,string>={planned:'Approval required',executing:'Running',awaiting_result:'Waiting for result',
  result_received:'Result reported',verifying:'Verifying',verified:'Verified',partially_verified:'Partially verified',
  failed:'Failed',blocked:'Blocked',cancelled:'Cancelled',unknown:'Unknown outcome'};
export const taskStatus=(task:Task)=>task.retained_available===false?'Evidence unavailable':statuses[task.state]??'Unknown outcome';
export function stateLabel(view:View){return view.link!=='online'?'Core unavailable':view.current?
  taskStatus(view.current):view.orb==='idle'?'I’m here.':view.orb;}

export const epistemicLabel=(state:string|null|undefined)=>({VERIFIED:'Verified',REPORTED:'Not independently checked',RECALLED:'From earlier conversation',INFERRED:'An interpretation',UNKNOWN:'Not established'}[state??'UNKNOWN']??'Not established');
