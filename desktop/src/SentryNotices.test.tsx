import {afterEach,expect,it} from 'vitest';
import {cleanup,render,screen} from '@testing-library/react';
import {SentryNotices} from './SentryNotices';
afterEach(cleanup);
it('renders authorized generic attention metadata and suppresses stale, changed or revoked notices',()=>{
  const now=Date.now(),observation={observed_at_ms:now,received_at_ms:now,transport_ms:0};
  const source={id:'selected',epoch:1,perceive:true,act:true};
  const alert={id:'a'.repeat(64),source_id:'selected',source_epoch:1,generation:1,key:'status',fresh_until:(now+30000)/1000,simulated:true,policy_ids:['owner-delivery']};
  const sentry={mode:'sentry',state:'aware',allow_interrupt:true,generation:1,source_ids:['selected'],trigger_keys:['status'],sources:[source],alerts:[alert]};
  const {rerender}=render(<SentryNotices value={sentry} observation={observation}/>);
  expect(screen.getByRole('status',{name:'Awareness notices'})).toBeTruthy();
  expect(screen.getByText('Simulated · selected · status')).toBeTruthy();
  for(const update of [{generation:2},{state:'sleep'},{sources:[{...source,act:false}]},{alerts:[{...alert,fresh_until:(now-1)/1000}]},{alerts:[{...alert,policy_ids:[]}]}]){
    rerender(<SentryNotices value={{...sentry,...update}} observation={observation}/>);
    expect(screen.queryByRole('status')).toBeNull();
  }
});
