import {useId} from 'react';
import type {Pose} from './model';

export function Orb({pose:p,size=320,label='OSCAR expressive derivative v2'}:{pose:Pose;size?:number;label?:string}) {
  const id=useId().replaceAll(':','');
  const ref=(name:string)=>`url(#${id}-${name})`;
  const left=426+(1-p.span)*29.5,right=485-(1-p.span)*29.5;
  const lidY=233+(1-Math.min(1,p.eye))*42;
  const bottom=317-(1-Math.min(1,p.eye))*42;
  const open=Math.max(0,Math.min(1,p.opening));
  const arcY=261+(p.arc+16),arcY2=258+(p.arc+16)+(p.slant+4)/2,endY=272+(p.slant+4);
  const closedOpacity=Math.max(0,1-p.eye/.15);
  // Equal-topology cubic outlines unfold the source wink; the second eye stays smaller.
  const a=[left,276],b=[left+18*p.span,arcY],c=[right-20*p.span,arcY2],d=[right,endY];
  const midpoint=(u:number[],v:number[])=>u.map((n,i)=>(n+v[i])/2);
  const ab=midpoint(a,b),bc=midpoint(b,c),cd=midpoint(c,d),abc=midpoint(ab,bc),bcd=midpoint(bc,cd),tip=midpoint(abc,bcd);
  const original=[a,ab,abc,tip,bcd,cd,d,cd,bcd,tip,abc,ab,a];
  const cx=(left+right)/2,rx=(right-left)/2*.9,cy=274,ry=29,k=.55228475;
  const ellipse=[[cx-rx,cy],[cx-rx,cy-k*ry],[cx-k*rx,cy-ry],[cx,cy-ry],[cx+k*rx,cy-ry],[cx+rx,cy-k*ry],[cx+rx,cy],[cx+rx,cy+k*ry],[cx+k*rx,cy+ry],[cx,cy+ry],[cx-k*rx,cy+ry],[cx-rx,cy+k*ry],[cx-rx,cy]];
  const points=original.map((point,i)=>point.map((n,j)=>n+(ellipse[i][j]-n)*open).join(' '));
  const wink=open===0?`M${left} 276 C${left+18*p.span} ${arcY},${right-20*p.span} ${arcY2},${right} ${endY}`:`M${points[0]} C${points.slice(1,4).join(',')} C${points.slice(4,7).join(',')} C${points.slice(7,10).join(',')} C${points.slice(10,13).join(',')} Z`;
  return <svg className="orb" width={size} height={size} viewBox="0 0 582 582" role="img" aria-label={label} data-derivative="v2">
    <defs>
      <radialGradient id={`${id}-shell`} cx="36%" cy="17%" r="84%"><stop offset="0" stopColor="#4A93C9"/><stop offset=".42" stopColor="#3786C5"/><stop offset="1" stopColor="#3282C1"/></radialGradient>
      <linearGradient id={`${id}-side`} x1="0" y1="0" x2=".88" y2="1"><stop offset="0" stopColor="#EEB035"/><stop offset=".55" stopColor="#E9AC2D"/><stop offset="1" stopColor="#DFAE42"/></linearGradient>
      <radialGradient id={`${id}-face`} cx="42%" cy="32%" r="76%"><stop offset="0" stopColor="#FACA43"/><stop offset=".7" stopColor="#F9C840"/><stop offset="1" stopColor="#F8C441"/></radialGradient>
      <filter id={`${id}-shadow`} x="-35%" y="-35%" width="180%" height="190%"><feDropShadow dx="-7" dy="15" stdDeviation="7" floodColor="#17669F" floodOpacity=".58"/></filter>
      <clipPath id={`${id}-lid`}><path d={`M240 ${lidY-p.lid} L360 ${lidY+p.lid} L360 ${bottom} L240 ${bottom} Z`}/></clipPath>
    </defs>
    <g transform={`rotate(${p.body} 288 292)`}>
      <circle cx="288" cy="292" r="264" fill={ref('shell')}/>
      <g transform={`translate(${p.x} ${p.y}) rotate(${p.tilt} 374 289)`} filter={ref('shadow')} data-puck="true">
        <circle cx="374" cy="289" r="187" fill={ref('side')}/>
        <circle cx="381" cy="289" r="177" fill={ref('face')}/>
        <g fill="#E74A49" stroke="#E74A49" transform={`translate(${p.gx} ${p.gy})`} data-marks="true">
          <circle cx="299" cy="275" r={42*p.width} stroke="none" clipPath={p.eye>=1?undefined:ref('lid')} opacity={1-closedOpacity}/>
          <path d="M274 275 C288 281,310 281,324 274" fill="none" strokeWidth="16" strokeLinecap="round" opacity={closedOpacity}/>
          <path d={wink} fill={open===0?'none':'#E74A49'} strokeWidth={21*(1-open)} strokeLinecap="round" strokeLinejoin="round"/>
        </g>
      </g>
    </g>
  </svg>;
}
