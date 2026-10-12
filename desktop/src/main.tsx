import {createRoot} from 'react-dom/client';
import {App} from './App';
import {LivingPresence} from './presence/Living';
import './style.css';
const root=createRoot(document.getElementById('root')!);
if(import.meta.env.DEV && new URLSearchParams(location.search).has('foundation')) {
  root.render(<App/>);
} else if(import.meta.env.DEV && new URLSearchParams(location.search).has('living')) {
  document.documentElement.dataset.living='true';
  void import('./presence/Living').then(({Living})=>root.render(<Living/>));
} else if(import.meta.env.DEV && new URLSearchParams(location.search).has('integration')) {
  void import('./integration-fixture').then(({IntegrationFixture})=>root.render(<IntegrationFixture/>));
} else if(import.meta.env.DEV && new URLSearchParams(location.search).has('presence')) {
  void import('./presence/Exploration').then(({Exploration})=>{
    document.title='OSCAR 10R.1 — synthetic / no execution';
    document.documentElement.dataset.presence='exploration';
    root.render(<Exploration/>);
  });
} else if(import.meta.env.DEV && new URLSearchParams(location.search).has('showcase')) {
  void import('./showcase').then(({Showcase,fixtures})=>{
    const fixture=fixtures.find(f=>f.id===new URLSearchParams(location.search).get('showcase'));
    if(!fixture)throw new Error('Unknown bounded showcase fixture');
    document.title='OSCAR DEVELOPMENT SHOWCASE — synthetic / no execution';
    document.documentElement.dataset.showcase=fixture.id;
    root.render(<Showcase fixture={fixture}/>);
  });
} else {
  document.documentElement.dataset.living='true';
  root.render(<LivingPresence/>);
}
