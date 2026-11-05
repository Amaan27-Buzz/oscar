import type {View,Command} from './bridge';

export function ModelSettings({view,busy,run}:{view:View;busy:boolean;run:(command:Command)=>unknown}) {
  const models=view.models;
  return <section className="settings-group" aria-labelledby="models-title">
    <div className="setting-heading"><h2 id="models-title">Intelligence</h2><p>Choose how OSCAR reasons. Conversation history stays with your Core. Cloud inference shares your messages and relevant conversation context with the selected provider.</p></div>
    <label htmlFor="reasoning-model">Model</label>
    <select id="reasoning-model" value={models?.selected??''} disabled={busy||view.link!=='online'||(!models?.free_only&&!models?.available.length)} onChange={event=>run({kind:'select_model',model:event.target.value})}>
      {models?.free_only&&<option value="">Automatic - verified free</option>}
      {models?.selected&&!models.available.includes(models.selected)&&<option value={models.selected} disabled>{models.selected.replace('::',' / ')} - unavailable</option>}
      {!models?.available.length&&!models?.free_only&&<option value="">No eligible models available</option>}
      {models?.available.map(model=><option key={model} value={model}>{model.replace('::',' / ')}</option>)}
    </select>
    <p className="leaf-secondary">{models?.free_only?'Cloud models with current zero-price evidence only. Paid calls and local fallback are disabled. Availability and free quotas can change.':'Availability follows your Core’s routing policy.'}</p>
  </section>;
}
