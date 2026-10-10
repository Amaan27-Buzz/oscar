import {parseEvent} from '@oscar/expression';
import type {ExpressionEvent,OperationalState,Source} from '@oscar/expression';
import type {View} from './bridge';

export const freshnessMs=8000;
/** Trusted native readback only. No context, descriptions, responses or approval material leave this adapter. */
export class DesktopExpressionAdapter {
  private epoch='';
  private retired=new Set<string>();
  private revision=-1;
  private generation=0;
  private intent='';
  private transition=0;
  constructor(private kind:Source['kind']='core') {}
  receive(view:View,now:number):ExpressionEvent|null {
    const r=view.expression;
    if(!r||!/^[a-f0-9]{32}$/.test(r.epoch)||!Number.isSafeInteger(r.generation)||r.generation<0||
      !Number.isSafeInteger(r.observed_at_ms)||r.observed_at_ms<0||
      !Number.isSafeInteger(r.voice_observed_at_ms)||r.voice_observed_at_ms<0)return null;
    if(!Number.isSafeInteger(r.tasks_observed_at_ms)||r.tasks_observed_at_ms<0||!Number.isSafeInteger(r.current_observed_at_ms)||r.current_observed_at_ms<0)return null;
    if(r.epoch!==this.epoch&&(r.observed_at_ms>now+250||r.observed_at_ms+freshnessMs<=now))return null;
    if(this.retired.has(r.epoch))return null;
    if(r.epoch===this.epoch&&r.generation<=this.revision)return null;
    if(r.epoch!==this.epoch) {
      if(this.epoch)this.retired.add(this.epoch);
      this.epoch=r.epoch;this.revision=-1;this.intent='';
    }
    this.revision=r.generation;
    const fresh=r.observed_at_ms<=now+250&&r.observed_at_ms+freshnessMs>now;
    const voiceFresh=r.voice_observed_at_ms<=now+250&&r.voice_observed_at_ms+freshnessMs>now;
    const muted=view.voice==='muted';
    let operation:OperationalState='attentive';
    let availability:ExpressionEvent['availability']=view.link==='online'?'available':'unavailable';
    let attention:ExpressionEvent['attention']='none';
    let kind:ExpressionEvent['kind']='state';
    if(!fresh&&view.link==='online') {operation='unknown';availability='unknown';}
    else if(view.link!=='online')operation='unavailable';
    else {
      const freshTasks=r.tasks_observed_at_ms<=now+250&&r.tasks_observed_at_ms+freshnessMs>now;
      const freshCurrent=r.current_observed_at_ms<=now+250&&r.current_observed_at_ms+freshnessMs>now;
      const tasks=[...(freshCurrent&&view.current?[view.current]:[]),...(freshTasks?view.tasks.filter(t=>!['verified','partially_verified','failed','cancelled'].includes(t.state)):[])];
      const staleTasks=(!freshTasks&&view.tasks.length>0)||(!freshCurrent&&view.current!==null);
      if(staleTasks||tasks.some(t=>t.state==='unknown'||!['planned','executing','awaiting_result','result_received','verifying','verified','partially_verified','failed','blocked','cancelled'].includes(t.state)))operation='unknown';
      else if(tasks.some(t=>t.state==='failed'))operation='error';
      else if(tasks.some(t=>t.actions.includes('approve'))) {operation='waiting';attention='owner';}
      else if(muted)operation='muted';
      else if(view.voice!=='idle') {
        if(!voiceFresh)operation='unknown';
        else if(['interrupted','cancelled'].includes(view.voice)) {operation='attentive';kind=view.voice==='interrupted'?'interrupt':'cancel';}
        else if(['listening','speaking','processing'].includes(view.voice))operation=view.voice as OperationalState;
        else operation='unknown';
      }
      else if(tasks.some(t=>t.state==='verifying'))operation='verifying';
      else if(tasks.some(t=>t.state==='executing'))operation='executing';
      else if(tasks.some(t=>['planned','awaiting_result','blocked'].includes(t.state)))operation='waiting';
      else if(tasks.some(t=>t.state==='result_received'))operation='processing';
      else if(view.current?.state==='cancelled')kind='cancel';
      else if(view.feedback)operation=view.feedback.kind==='unknown'?'unknown':'waiting';
    }
    const intent=[operation,availability,attention,muted,kind].join(':');
    if(intent!==this.intent) {this.intent=intent;this.transition++;} else kind='state';
    const activeVoice=['speaking','listening','processing'].includes(operation)&&view.voice===operation;
    const at=fresh?r.observed_at_ms:now;
    const leases=[at+freshnessMs];
    if(activeVoice)leases.push(r.voice_observed_at_ms+freshnessMs);
    if(availability==='available'&&operation!=='unknown') {
      if(view.current)leases.push(r.current_observed_at_ms+freshnessMs);
      if(view.tasks.some(t=>!['verified','partially_verified','failed','cancelled'].includes(t.state)))leases.push(r.tasks_observed_at_ms+freshnessMs);
    }
    const expiresAt=Math.min(...leases);
    return parseEvent({version:1,source:{kind:this.kind,id:`desktop:${this.epoch}`},
      generation:++this.generation,transitionId:`desktop:${this.transition}`,eventTime:at,expiresAt,
      kind,priority:attention==='owner'?'urgent':'normal',operation,
      delivery:kind==='interrupt'?'interrupted':'composed',availability,muted,attention,reducedMotion:false});
  }
}
