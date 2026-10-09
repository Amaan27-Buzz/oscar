import {vi} from 'vitest';
vi.stubGlobal('matchMedia',vi.fn((media:string)=>({matches:false,media,addEventListener:vi.fn(),removeEventListener:vi.fn()})));
