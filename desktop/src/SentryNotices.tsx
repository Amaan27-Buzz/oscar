import {useEffect,useState} from 'react';
import {CoreClock} from './core-clock';
import type {View} from './bridge';

function object(value:unknown):Record<string,unknown>|null{return value!==null&&typeof value==='object'&&!Array.isArray(value)?value as Record<string,unknown>:null;}
export function SentryNotices({value,observation}:{value:unknown;observation?:View['core_clock']}){
  const [clock,setClock]=useState<CoreClock|null>(null),[,tick]=useState(0);
  useEffect(()=>{setClock(previous=>observation?CoreClock.observe(observation,Date.now(),()=>performance.now(),previous??undefined):null);},[observation]);
  useEffect(()=>{const timer=setInterval(()=>tick(value=>value+1),1000);return()=>clearInterval(timer);},[]);
  const sentry=object(value),now=clock?.now();
  if(!sentry||now===undefined||sentry.mode==='manual'||sentry.state==='sleep'||sentry.allow_interrupt!==true||!Array.isArray(sentry.alerts)||sentry.alerts.length>16||!Array.isArray(sentry.sources)||!Array.isArray(sentry.source_ids)||!Array.isArray(sentry.trigger_keys))return null;
  const notices=sentry.alerts.map(object).filter((alert):alert is Record<string,unknown>=>{
    if(!alert||typeof alert.id!=='string'||!/^[a-f0-9]{64}$/.test(alert.id)||typeof alert.source_id!=='string'||typeof alert.key!=='string'||alert.source_id.length>160||alert.key.length>160||typeof alert.simulated!=='boolean'||typeof alert.fresh_until!=='number'||!Number.isFinite(alert.fresh_until)||alert.fresh_until*1000<=now||alert.fresh_until*1000-now>60000||alert.generation!==sentry.generation||!Array.isArray(alert.policy_ids)||!alert.policy_ids.length)return false;
    const source=(sentry.sources as unknown[]).map(object).find(source=>source?.id===alert.source_id);
    return source?.perceive===true&&source.act===true&&source.epoch===alert.source_epoch&&(sentry.source_ids as unknown[]).includes(alert.source_id)&&(sentry.trigger_keys as unknown[]).includes(alert.key);
  });
  if(!notices.length)return null;
  return <section role="status" aria-label="Awareness notices"><h3>Needs your attention</h3>{notices.map(notice=><p key={String(notice.id)}>{notice.simulated?'Simulated · ':''}{String(notice.source_id)} · {String(notice.key)}</p>)}<p>A selected source triggered an authorized notice. Check current context before acting.</p></section>;
}
