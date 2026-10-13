import {vi} from 'vitest';
vi.stubGlobal('ResizeObserver',class {observe(){}unobserve(){}disconnect(){}});
vi.stubGlobal('matchMedia',vi.fn((media:string)=>({matches:false,media,addEventListener:vi.fn(),removeEventListener:vi.fn()})));

Element.prototype.scrollIntoView=vi.fn();
Element.prototype.hasPointerCapture=()=>false;
Element.prototype.setPointerCapture=()=>{};
Element.prototype.releasePointerCapture=()=>{};
