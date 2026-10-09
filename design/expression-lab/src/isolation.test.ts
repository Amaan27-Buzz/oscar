import {readFileSync,readdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve} from 'node:path';
import {describe,it,expect} from 'vitest';

describe('synthetic instrument boundaries',()=>{
  it('leaves canonical artwork byte-identical',()=>{
    const bytes=readFileSync(resolve('../../assets/brand/oscar-orb.svg'));
    expect(createHash('sha256').update(bytes).digest('hex')).toBe('728aeac3c9aa590b67d45c469735e919ede93a8503964e24f0f4af18cda066c5');
  });
  it('runtime imports only local lab code, React and canonical SVG; no execution/data adapters',()=>{
    const dir=resolve('src');
    const allowed=new Set(['react','react-dom/client','./Lab','./Orb','./model','./style.css','../../../assets/brand/oscar-orb.svg']);
    for(const file of readdirSync(dir).filter(f=>/\.tsx?$/.test(f)&&!f.includes('.test.'))) {
      const source=readFileSync(resolve(dir,file),'utf8');
      for(const match of source.matchAll(/(?:from\s*|import\s*)['"]([^'"]+)['"]/g))expect(allowed.has(match[1]),`${file}: ${match[1]}`).toBe(true);
      expect(source).not.toMatch(/\b(fetch|WebSocket|XMLHttpRequest|Worker|EventSource|eval)\s*\(|navigator\.|localStorage|sessionStorage|indexedDB|@tauri|oscar\//);
    }
  });
  it('built preview policy denies network, devices, frames and media',()=>{
    const html=readFileSync(resolve('index.html'),'utf8');
    for(const rule of ["connect-src 'none'","media-src 'none'","frame-src 'none'","object-src 'none'","script-src 'self'"])expect(html).toContain(rule);
    expect(html).not.toContain("script-src 'self' 'unsafe-inline'");
  });
});
