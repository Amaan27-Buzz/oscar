export function Automations({discuss}:{discuss:()=>void}) {
  return <section className="automations-page" aria-label="Automations">
    <div className="section-heading"><h1>Automations</h1><p className="leaf-secondary">Work OSCAR keeps track of for you.</p></div>
    <div className="automation-introduction"><h2>Give OSCAR a responsibility.</h2><p>A routine, a watch, or a named Worker starts with a conversation. OSCAR coordinates the work and remains responsible for its authority and results.</p><button onClick={discuss}>Discuss a responsibility</button></div>
    <section className="automation-availability" aria-label="Automation availability"><h2>What’s available today</h2><p>Immediate delegated tasks use the existing Core runtime. Review their progress and verified results in Activity.</p><p>Scheduled routines, event triggers, conditional watches, persistent named Workers and stateful Protocol management are not connected to this Workspace yet.</p><p className="leaf-secondary">Pause, resume, schedules and Worker autonomy controls will appear when Core supports those operations. A prepared file write is an immediate action.</p></section>
  </section>;
}
