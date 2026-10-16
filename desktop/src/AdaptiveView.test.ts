import {expect,it} from 'vitest';
import {adaptiveDescriptor} from './AdaptiveView';
const valid=()=>({version:1,view_id:'view',task_id:'task',revision:1,observed_at_ms:100,expires_at_ms:200,fallback:'Task reported',components:[{type:'task_progress',text:'Working',source_ids:[]}],actions:[{type:'inspect_task',task_id:'task'}]});
it('accepts only bounded typed read-only descriptors',()=>{
  expect(adaptiveDescriptor(valid())).not.toBeNull();
  for(const patch of [{version:2},{script:'run()'},{actions:[null]},{actions:[{type:'approve',task_id:'task'}]},{expires_at_ms:99000},{components:[{type:'webview',text:'data',source_ids:[]}]}])expect(adaptiveDescriptor({...valid(),...patch})).toBeNull();
  expect(adaptiveDescriptor({...valid(),components:Array.from({length:8},()=>({type:'prose',text:'x'.repeat(1024),source_ids:[]}))})).toBeNull();
});
