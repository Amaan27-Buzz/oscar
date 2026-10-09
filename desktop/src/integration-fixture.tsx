// Development-only readback fixtures. No native IPC, Core, audio or execution.
import {App} from './App';
import {initialView} from './bridge';
import type {Task,View} from './bridge';
export function IntegrationFixture() {
  const state=new URLSearchParams(location.search).get('integration')??'available';
  const task=(state:string,actions:string[]=[]):Task=>({task_id:'fixture',state,actions,description:'Disposable integration fixture',target:'fixture',blocker:null,generation:1,evidence_ids:[],response:null,response_status:null,value:null,epistemic:null});
  const now=Date.now();
  const view:View={...initialView,window:'compact',link:state==='unavailable'?'unavailable':'online',
    orb:state==='available'?'attentive':state==='speaking'?'speaking':state==='interrupted'?'attentive':'unavailable',reference:true,voice:state==='speaking'?'speaking':state==='interrupted'?'interrupted':'idle',
    current:state==='working'?task('executing'):state==='waiting'?task('planned',['approve']):null,
    expression:{epoch:'f'.repeat(32),generation:1,observed_at_ms:now,voice_observed_at_ms:now,tasks_observed_at_ms:now,current_observed_at_ms:now}};
  return <><p className="reference">SIMULATED DESKTOP EVENTS · no Core execution · {state}</p>
    <App expressionKind="fixture" port={async()=>view} events={async callback=>{callback(view);return()=>{};}}/></>;
}
