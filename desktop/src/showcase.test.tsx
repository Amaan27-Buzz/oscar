import {afterEach,expect,it} from 'vitest';
import {cleanup,render,screen,waitFor} from '@testing-library/react';
import {fixtures,Showcase,sizes} from './showcase';
afterEach(cleanup);
it('renders every typed fixture without authority or private data',async()=>{
  const ids=new Set<string>();
  for(const fixture of fixtures){
    expect(ids.has(fixture.id)).toBe(false);ids.add(fixture.id);
    expect(sizes[fixture.view.window]).toBeDefined();
    for(const forbidden of ['bearer','private_key','signing_payload','password'])expect(JSON.stringify(fixture.view)).not.toContain(forbidden);
    const {container}=render(<Showcase fixture={fixture}/>);
    const orb=await screen.findByRole('img',{name:/OSCAR:/});expect(orb.tagName.toLowerCase()).toBe('svg');
    await waitFor(()=>expect(container.querySelector('main')?.classList.contains('compact')).toBe(fixture.view.window==='compact'));
    cleanup();
  }
});
