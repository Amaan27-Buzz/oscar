// Maintainer generation of deterministic, synthetic cross-language controller traces.
import {createServer} from 'vite';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve('../..');
const server=await createServer({root:process.cwd(),configFile:false,server:{middlewareMode:true,fs:{allow:[root]}}});
try {
  const {ExpressionController}=await server.ssrLoadModule(resolve(root,'expression/core/controller.ts'));
  const file=resolve(root,'expression/fixtures/reference-v1.json');
  const fixtures=JSON.parse(readFileSync(file,'utf8'));
  const base=1000000,source={kind:'fixture',id:'cross-v1'};
  const e=(generation,at=0,changes={})=>({version:1,source,generation,transitionId:`event-${generation}`,eventTime:base+at,expiresAt:base+at+30000,kind:'state',priority:'normal',operation:'idle',delivery:'composed',availability:'available',muted:false,attention:'none',reducedMotion:false,...changes});
  const traces=[
    {name:'long-speech-and-explicit-accent',steps:[{at:0,event:e(1,0,{operation:'speaking'})},{at:700},{at:10000},{at:10000,event:e(2,10000,{operation:'speaking',transitionId:'event-1'})},{at:10000,event:e(3,10000,{operation:'speaking',kind:'accent',accent:'phrase'})},{at:11200},{at:12300},{at:15200},{at:25000},{at:31000,event:e(4,31000)},{at:31700}]},
    {name:'stale-muted-approval-expiry',steps:[{at:0,event:e(1,0,{operation:'speaking'})},{at:1000,event:e(2,1000,{operation:'speaking',kind:'accent',accent:'phrase'})},{at:2200},{at:2200,event:e(3,2200,{operation:'unavailable'})},{at:2300,event:e(2,1000,{operation:'speaking',kind:'accent',accent:'phrase'})},{at:2700,event:e(4,2700,{operation:'listening',muted:true})},{at:3000,event:e(5,3000,{operation:'executing',muted:true,attention:'owner',priority:'urgent'})},{at:31000,event:e(2,1000,{operation:'speaking',kind:'accent',accent:'phrase'})},{at:33000}]},
    {name:'reaction-lifecycle-reduced',steps:[{at:0,event:e(1,0,{delivery:'amused'})},{at:600},{at:3200},{at:4000,event:e(2,4000,{delivery:'amused',transitionId:'event-1'})},{at:5000,suspend:true},{at:5100,event:e(2,4000,{delivery:'amused',transitionId:'event-1'})},{at:5500,event:e(3,5500,{operation:'attentive'})},{at:5600},{at:5700,reduce:true},{at:20000,event:e(4,20000,{delivery:'surprised',reducedMotion:true})},{at:20400},{at:21000},{at:22700},{at:22800,reduce:false},{at:23000,event:e(5,23000,{delivery:'surprised'})},{at:23200,reduce:true},{at:24000},{at:25700}]},
    {name:'invalid-source-and-presentation-cancel',steps:[{at:0,event:e(1,0,{operation:'listening'})},{at:200,event:{...e(2,200),privateText:'synthetic-must-reject'}},{at:300,event:e(2,300,{source:{kind:'lab',id:'cross-v1'}})},{at:400,event:e(3,400,{operation:'speaking'})},{at:800,event:e(4,800,{operation:'speaking',kind:'cancel'})},{at:1200}]},
    {name:'reduced-phrase-and-blink',steps:[{at:0,event:e(1,0,{operation:'speaking',reducedMotion:true})},{at:500,event:e(2,500,{operation:'speaking',reducedMotion:true,kind:'accent',accent:'phrase'})},{at:5200},{at:6000,event:e(3,6000,{operation:'speaking'})},{at:6700},{at:6700,event:e(4,6700,{operation:'speaking',kind:'accent',accent:'blink'})},{at:6860},{at:7400}]},
  ];
  const encoded=JSON.stringify(e(1));
  fixtures.malformedInputs=[
    {name:'trailing-garbage',raw:encoded+' trailing garbage'},
    {name:'unquoted-key',raw:encoded.replace('"version":','version:')},
    {name:'single-quotes',raw:encoded.replaceAll('"',"'")},
    {name:'leading-zero',raw:encoded.replace('"version":1','"version":01')},
    {name:'private-field',raw:JSON.stringify({...e(1),privateText:'synthetic-must-reject'})},
    {name:'string-boolean',raw:JSON.stringify({...e(1),muted:'false'})},
    {name:'legacy-wire-operation',raw:JSON.stringify({...e(1),operation:'available'})},
    {name:'unsafe-generation',raw:JSON.stringify({...e(1),generation:9007199254740992})},
  ];
  fixtures.traces=traces.map(trace=>{
    const engine=new ExpressionController(source);
    return {...trace,steps:trace.steps.map(step=>{
      const now=base+step.at;
      const admission=step.event?engine.receive(step.event,now):null;
      if(step.suspend)engine.suspend();if('reduce'in step)engine.setReducedMotion(step.reduce,now);
      const value=engine.snapshot(now);
      return {...step,expected:{admission,operation:value.resolved.operation,delivery:value.resolved.delivery,muted:value.resolved.muted,generation:value.generation,priority:value.priority,animation:value.animation,moving:value.moving,pose:value.pose,records:engine.takeAnimationRecords()}};
    })};
  });
  writeFileSync(file,JSON.stringify(fixtures,null,2)+'\n');
  console.log(`Generated ${fixtures.poseCases.length} historical pose cases and ${fixtures.traces.length} controller traces`);
} finally {await server.close();}
