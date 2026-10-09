import {createRoot} from 'react-dom/client';
import {App} from './App';
import './style.css';
const root=createRoot(document.getElementById('root')!);
if(import.meta.env.DEV && new URLSearchParams(location.search).has('presence')) {
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
} else root.render(<App/>);
