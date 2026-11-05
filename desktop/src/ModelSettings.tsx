import type {View,Command} from './bridge';

export function ModelSettings({view,busy,run}:{view:View;busy:boolean;run:(command:Command)=>unknown}) {
  const models=view.models;
  return <section className="settings-group" aria-labelledby="models-title">
    <div className="setting-heading"><h2 id="models-title">Intelligence</h2><p>Choose a model running on this computer. Your conversations stay in OSCAR.</p></div>
    <label htmlFor="local-model">Local model</label>
    <select id="local-model" value={models?.selected??''} disabled={busy||view.link!=='online'||!models?.available.length} onChange={event=>run({kind:'select_model',model:event.target.value})}>
      {!models?.available.length&&<option value="">No local models available</option>}
      {models?.available.map(model=><option key={model} value={model}>{model}</option>)}
    </select>
    <p className="leaf-secondary">Local inference uses your computer, with no paid provider calls. Start Ollama and refresh the connection if your model is unavailable.</p>
  </section>;
}
