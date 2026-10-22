import {afterEach,expect,it,vi} from 'vitest';
import {act,cleanup,fireEvent,render,screen} from '@testing-library/react';
import {DayBrief,OperatingSettings} from './OperatingSettings';
import {initialView} from './bridge';
const management={version:1 as const,relationship_id:'owner',core_node_id:'core',ask_rules:[],authority:{mode:'ask' as const,status:'inactive'},capabilities:[],sentry:{mode:'manual',state:'passive',generation:0,source_ids:[],trigger_keys:[],allow_interrupt:false,sources:[]}};
const executive={version:1 as const,health:'operational',running:true,management,goals:[],workers:[]};
afterEach(()=>{cleanup();vi.useRealTimers();});
it('creates an explicitly reviewed clock source without granting retention or action',()=>{
  const run=vi.fn();render(<OperatingSettings view={{...initialView,link:'online',executive}} busy={false} run={run}/>);
  fireEvent.click(screen.getByRole('button',{name:'Connect a context source'}));
  fireEvent.change(screen.getByLabelText('Source name'),{target:{value:'Daily clock'}});
  fireEvent.change(screen.getByLabelText('Timezone'),{target:{value:'Asia/Kolkata'}});
  fireEvent.click(screen.getByRole('button',{name:'Review context source'}));
  expect(run).toHaveBeenCalledWith({kind:'manage_assistance',operation:'source_create',id:'daily-clock',value:{id:'daily-clock',adapter:'time',entity_id:'core',interval_seconds:30,retain:false,retention_seconds:3600,timezone:'Asia/Kolkata'}});
  fireEvent.click(screen.getByRole('button',{name:'Refresh day briefing'}));
  expect(run).toHaveBeenLastCalledWith({kind:'day_brief'});
});
it('leaves calendar setup unavailable without an explicit connected calendar account',()=>{
  const run=vi.fn();render(<OperatingSettings view={{...initialView,link:'online',executive}} busy={false} run={run}/>);
  fireEvent.click(screen.getByRole('button',{name:'Connect a context source'}));
  fireEvent.change(screen.getByLabelText('Source name'),{target:{value:'calendar'}});
  fireEvent.click(screen.getByRole('button',{name:'Context source'}));
  fireEvent.click(screen.getByRole('radio',{name:'Connected calendar'}));
  expect((screen.getByRole('button',{name:'Review context source'}) as HTMLButtonElement).disabled).toBe(true);
  expect(run).not.toHaveBeenCalled();
});
it('pins the selected calendar account and current generation in native review',()=>{
  const account={id:'google-owner',provider:'google',tenant:'synthetic',subject:'synthetic',alias:'Personal calendar',identity_class:'owner-delegated',generation:7,status:'connected',remote_revocation:'unknown',services:[{id:'google.calendar',scopes:['https://www.googleapis.com/auth/calendar.events.readonly'],expires_at:null,restrictions:[]}]};
  const connections={identity:{id:'owner',display_name:'OSCAR',operational_email:null,status:'active'},accounts:[account],plugins:[],access:'Ask',enrollment:'available',observed_at_ms:Date.now()};
  const run=vi.fn();render(<OperatingSettings view={{...initialView,link:'online',executive,connections}} busy={false} run={run}/>);
  fireEvent.click(screen.getByRole('button',{name:'Connect a context source'}));
  fireEvent.change(screen.getByLabelText('Source name'),{target:{value:'Daily calendar'}});
  fireEvent.click(screen.getByRole('button',{name:'Context source'}));
  fireEvent.click(screen.getByRole('radio',{name:'Connected calendar'}));
  fireEvent.click(screen.getByRole('button',{name:'Calendar account'}));
  fireEvent.click(screen.getByRole('radio',{name:'Personal calendar · google'}));
  fireEvent.click(screen.getByRole('button',{name:'Review context source'}));
  expect(run).toHaveBeenCalledWith({kind:'manage_assistance',operation:'source_create',id:'daily-calendar',value:{id:'daily-calendar',adapter:'calendar',entity_id:'calendar:daily-calendar',interval_seconds:30,retain:false,retention_seconds:3600,account_id:'google-owner',account_generation:7,calendar_id:'primary',horizon_seconds:86400}});
});
it('labels observed reports and hides expired or revoked source content',()=>{
  const now=Date.now()/1000;
  const observation={observed_at_ms:Math.floor(now*1000),received_at_ms:Date.now(),transport_ms:0};
  const source={id:'calendar',epoch:1,adapter:'calendar',state:'current',value:JSON.stringify({events:[{summary:'Synthetic meeting',start:{dateTime:'09:00'},end:{dateTime:'09:30'}}],complete:false}),epistemic:'REPORTED',evidence:[{fresh_until:now+60}]};
  const brief={version:1,observed_at:now,sources:[source],schedule:{overlaps:[{}],incomplete:true}};
  const {rerender}=render(<DayBrief observation={observation} value={brief} accounts={[]} grants={[{id:'calendar',epoch:1,perceive:true}]}/>);
  expect(screen.getByText('Connected source report')).toBeTruthy();
  expect(screen.getByText(/Synthetic meeting/)).toBeTruthy();
  expect(screen.getByText(/free time cannot be assumed/)).toBeTruthy();
  rerender(<DayBrief observation={observation} value={brief} accounts={[]} grants={[{id:'calendar',epoch:2,perceive:false}]}/>);
  expect(screen.queryByText(/Synthetic meeting/)).toBeNull();
  expect(screen.getByText(/Stale or unavailable/)).toBeTruthy();
  rerender(<DayBrief observation={observation} value={{...brief,sources:[{...source,evidence:[{fresh_until:now-1}]}]}} accounts={[]} grants={[{id:'calendar',epoch:1,perceive:true}]}/>);
  expect(screen.queryByText(/Synthetic meeting/)).toBeNull();
  expect(screen.queryByText(/overlapping event pairs/)).toBeNull();
});

it('expires briefing evidence using Core time even if the local wall clock moves backward',()=>{
  vi.useFakeTimers();
  const now=Date.now(),observation={observed_at_ms:now+20000,received_at_ms:now,transport_ms:0};
  const source={id:'clock',epoch:1,adapter:'time',state:'current',value:JSON.stringify({datetime:'Synthetic current time',timezone:'UTC'}),evidence:[{fresh_until:(now+21000)/1000}]};
  render(<DayBrief observation={observation} value={{version:1,observed_at:now/1000,sources:[source],schedule:{}}} accounts={[]} grants={[{id:'clock',epoch:1,perceive:true}]}/>);
  expect(screen.getByText(/Synthetic current time/)).toBeTruthy();
  vi.setSystemTime(now-60000);
  act(()=>vi.advanceTimersByTime(2000));
  expect(screen.queryByText(/Synthetic current time/)).toBeNull();
});

it('reviews only explicit valid weather coordinates and leaves retention off',()=>{
  const run=vi.fn();render(<OperatingSettings view={{...initialView,link:'online',executive}} busy={false} run={run}/>);
  fireEvent.click(screen.getByRole('button',{name:'Connect a context source'}));
  fireEvent.change(screen.getByLabelText('Source name'),{target:{value:'Oslo weather'}});
  fireEvent.click(screen.getByRole('button',{name:'Context source'}));
  fireEvent.click(screen.getByRole('radio',{name:'Weather forecast'}));
  const review=screen.getByRole('button',{name:'Review context source'}) as HTMLButtonElement;
  expect(review.disabled).toBe(true);
  fireEvent.change(screen.getByLabelText('Place name'),{target:{value:'Oslo public reference'}});
  fireEvent.change(screen.getByLabelText('Latitude'),{target:{value:'59.91391'}});
  fireEvent.change(screen.getByLabelText('Longitude'),{target:{value:'10.7522'}});
  expect(review.disabled).toBe(true);
  fireEvent.change(screen.getByLabelText('Latitude'),{target:{value:'59.9139'}});
  expect(review.disabled).toBe(false);
  fireEvent.click(review);
  expect(run).toHaveBeenCalledWith({kind:'manage_assistance',operation:'source_create',id:'oslo-weather',value:{id:'oslo-weather',adapter:'weather',entity_id:'weather:oslo-weather',interval_seconds:600,retain:false,retention_seconds:3600,place:'Oslo public reference',latitude:59.9139,longitude:10.7522}});
  expect(screen.getByText(/MET Norway receives these coordinates/)).toBeTruthy();
});
it('presents current weather as a credited forecast and hides revoked evidence',()=>{
  const now=Date.now(),observation={observed_at_ms:now,received_at_ms:now,transport_ms:0};
  const source={id:'weather',epoch:1,adapter:'weather',state:'current',epistemic:'REPORTED',value:JSON.stringify({place:'Oslo public reference',temperature_c:12.5,wind_mps:3,humidity_percent:62,forecast_time:'2026-10-21T12:00:00Z',updated_at:'2026-10-21T11:30:00Z'}),evidence:[{fresh_until:(now+60000)/1000}]};
  const brief={version:1,observed_at:now/1000,sources:[source],schedule:{}};
  const {rerender}=render(<DayBrief observation={observation} value={brief} accounts={[]} grants={[{id:'weather',epoch:1,perceive:true}]}/>);
  expect(screen.getByText(/Oslo public reference · 12.5 °C/)).toBeTruthy();
  expect(screen.getByText(/Forecast for/)).toBeTruthy();
  expect(screen.getByRole('link',{name:'CC BY 4.0'}).getAttribute('href')).toBe('https://creativecommons.org/licenses/by/4.0/');
  rerender(<DayBrief observation={observation} value={brief} accounts={[]} grants={[{id:'weather',epoch:2,perceive:false}]}/>);
  expect(screen.queryByText(/Oslo public reference/)).toBeNull();
});
