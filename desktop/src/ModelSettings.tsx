import type {View,Command} from './bridge';
import {useState} from 'react';
import {ProviderSetup} from './ProviderSetup';
import './model-settings.css';

export function ModelSettings({view,busy,run}:{view:View;busy:boolean;run:(command:Command)=>unknown}) {
  const models=view.models;
  const [plan,setPlan]=useState(''),[confirmed,setConfirmed]=useState(false);
  return <section className="settings-group" aria-labelledby="models-title">
    <div className="setting-heading"><h2 id="models-title">Intelligence</h2><p>Choose how OSCAR reasons. Conversation history stays with your Core. Cloud inference shares your messages and relevant conversation context with the selected provider.</p></div>
    <label htmlFor="reasoning-model">Model</label>
    <select id="reasoning-model" value={models?.selected??''} disabled={busy||view.link!=='online'||(!models?.free_only&&!models?.available.length)} onChange={event=>run({kind:'select_model',model:event.target.value})}>
      {models?.free_only&&<option value="">Automatic - zero cost</option>}
      {models?.selected&&!models.available.includes(models.selected)&&<option value={models.selected} disabled>{models.selected.replace('::',' / ')} - unavailable</option>}
      {!models?.available.length&&!models?.free_only&&<option value="">No eligible models available</option>}
      {models?.available.map(model=><option key={model} value={model}>{model.replace('::',' / ')}</option>)}
    </select>
    <p className="leaf-secondary">{models?.free_only?models.local_available?'Verified free cloud and installed local models. Paid calls are disabled. Local models run on your Core host; cloud choices share context with that provider.':'Cloud models with current zero-price evidence only. Paid calls and local fallback are disabled. Availability and free quotas can change.':'Availability follows your Core’s routing policy.'}</p>
    <ProviderSetup view={view} busy={busy} run={run}/>
    {models?.provider_plans?.map(provider=><div className="setting-line" key={provider.id}><div><h3>{provider.id==='google'?'Google Gemini':'Groq'}</h3><p>{provider.confirmed?'Owner-confirmed Free plan. Model availability is checked separately.':'Free-plan confirmation needed before tier-based free models can be used.'}</p></div><button disabled={busy||view.link!=='online'} onClick={()=>{setPlan(provider.id);setConfirmed(false);}}>Review free plan</button></div>)}
    {plan&&<fieldset className="model-plan-review"><legend>Confirm {plan==='google'?'Google Gemini':'Groq'} account plan</legend><p>This records your current account status for 24 hours. It does not change billing, buy credits or activate paid usage.</p><label><input type="checkbox" checked={confirmed} onChange={event=>setConfirmed(event.target.checked)}/>This account is on its Free plan and billing is disabled.</label><div className="actions"><button disabled={busy||!confirmed} onClick={async()=>{const result=await run({kind:'configure_setup',section:'provider_plan',value:{provider:plan,plan:'free',billing_enabled:false}});if(result!==false)setPlan('');}}>Confirm free plan</button><button onClick={()=>setPlan('')}>Cancel</button></div></fieldset>}
  </section>;
}
