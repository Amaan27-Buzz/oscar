import type {CoreClockObservation} from './bridge';

const invalidTime=Number.MAX_SAFE_INTEGER;
const integer=(value:number)=>Number.isSafeInteger(value)&&value>=0;

/** Native HTTPS observation, advanced only by this WebView's monotonic clock. */
export class CoreClock {
  private constructor(private coreAt:number,private elapsedAt:number,private monotonic:()=>number) {}
  static observe(observation:CoreClockObservation,localWall:number,monotonic:()=>number,previous?:CoreClock):CoreClock|null {
    const {observed_at_ms:core,received_at_ms:received,transport_ms:transport}=observation;
    const elapsed=monotonic(),bridgeAge=localWall-received;
    if(![core,received,transport,localWall].every(integer)||core===0||
      Math.abs(core-received)>30000||transport>15000||bridgeAge<0||bridgeAge>15000||
      !Number.isFinite(elapsed)||elapsed<0)return null;
    // Charging the full native round trip and IPC age cannot extend the lease.
    const prior=previous?.now()??0;
    const floor=prior===invalidTime?previous!.coreAt+30000:prior;
    return new CoreClock(Math.max(core+transport+bridgeAge,floor),elapsed,monotonic);
  }
  readonly now=():number=>{
    const elapsed=this.monotonic()-this.elapsedAt;
    // Suspension/rollback must not renew a cached publication.
    return !Number.isFinite(elapsed)||elapsed<0||elapsed>30000?invalidTime:Math.floor(this.coreAt+elapsed);
  };
}
