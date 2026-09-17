import {forceCollide,forceSimulation,forceX,forceY} from 'd3-force';
import type {District} from '../types';
import parties from '../../config/parties.json';
export type CartogramNode={id:string;x:number;y:number;r:number;votes:number;anchorX:number;anchorY:number};
export const hasVotes=(d:District)=>d.election_reported!==false&&typeof d.valid_votes==='number'&&Number.isFinite(d.valid_votes)&&d.valid_votes>0;
/** Shares retain the published denominator. Missing counts are never assigned to a party. */
export function voteSlices(d:District){
 if(!hasVotes(d))return [];
 const known=parties.flatMap(p=>{const v=d['vote_'+p.id];return typeof v==='number'&&Number.isFinite(v)&&v>=0?[{id:p.id,color:p.color,votes:v,share:v/d.valid_votes!}]:[];});
 const sum=known.reduce((n,p)=>n+p.votes,0);
 if(sum>d.valid_votes!+.001)return [{id:'missing',color:'#7b8793',votes:d.valid_votes!,share:1}];
 if(sum<d.valid_votes!)known.push({id:'missing',color:'#7b8793',votes:d.valid_votes!-sum,share:(d.valid_votes!-sum)/d.valid_votes!});
 return known.filter(p=>p.votes>0);
}
export function makeCartogramNodes(anchors:{id:string;x:number;y:number;votes:number}[],area=180000):CartogramNode[]{
 const valid=anchors.filter(p=>Number.isFinite(p.votes)&&p.votes>0),total=valid.reduce((n,p)=>n+p.votes,0);
 return valid.sort((a,b)=>a.id.localeCompare(b.id)).map(p=>({...p,anchorX:p.x,anchorY:p.y,r:Math.sqrt(area*p.votes/total/Math.PI)}));
}
export function maximumOverlap(nodes:CartogramNode[]){
 if(!nodes.length)return 0;
 const size=2*Math.max(...nodes.map(n=>n.r)),grid=new Map<string,CartogramNode[]>();let overlap=0;
 for(const n of nodes){const gx=Math.floor(n.x/size),gy=Math.floor(n.y/size);
  for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++)for(const p of grid.get(`${gx+dx},${gy+dy}`)??[])overlap=Math.max(overlap,n.r+p.r-Math.hypot(n.x-p.x,n.y-p.y));
  const key=`${gx},${gy}`,cell=grid.get(key)??[];cell.push(n);grid.set(key,cell);
 }return overlap;
}
/** Screen-filling shelf layout; input order is preserved and every vote retains one area scale. */
export function compactCartogram(input:CartogramNode[],aspect:number):CartogramNode[]{
 if(!input.length)return [];
 const gap=Math.max(...input.map(n=>n.r))*.12,diameter=Math.max(...input.map(n=>2*n.r));
 const place=(width:number)=>{let x=0,y=0,rowHeight=0;return input.map(n=>{const d=2*n.r;if(x&&x+d>width){x=0;y+=rowHeight+gap;rowHeight=0;}const node={...n,x:x+n.r,y:y+n.r};x+=d+gap;rowHeight=Math.max(rowHeight,d);return node;});};
 let lo=diameter,hi=Math.max(diameter,input.reduce((a,n)=>a+2*n.r+gap,0));
 for(let i=0;i<24;i++){const width=(lo+hi)/2,nodes=place(width),height=Math.max(...nodes.map(n=>n.y+n.r));if(width/height>aspect)hi=width;else lo=width;}
 return place(hi);
}
/** Deterministic Dorling layout, calculated off the main browser thread. */
export function layoutCartogram(input:CartogramNode[]){
 const nodes=input.map(p=>({...p}));if(nodes.length<2)return nodes;
 const gap=Math.max(.08,Math.sqrt(nodes.reduce((n,p)=>n+p.r*p.r,0)/nodes.length)*.04);
 const simulation=forceSimulation(nodes).stop().alphaDecay(.025).velocityDecay(.45)
  .force('x',forceX<CartogramNode>(n=>n.anchorX).strength(.07)).force('y',forceY<CartogramNode>(n=>n.anchorY).strength(.07))
  .force('collision',forceCollide<CartogramNode>(n=>n.r+gap).strength(1).iterations(2));
 simulation.tick(120);simulation.force('x',null).force('y',null);simulation.tick(30);simulation.stop();
 // Place larger circles first, resolving soft-force overlaps near their positions.
 // The outward search is unbounded: a dense city never sends a fallback node off-map.
 const maximumRadius=Math.max(...nodes.map(n=>n.r)),cellSize=2*(maximumRadius+gap),grid=new Map<string,CartogramNode[]>();
 for(const n of [...nodes].sort((a,b)=>b.r-a.r||a.id.localeCompare(b.id))){
  const free=(x:number,y:number)=>{const gx=Math.floor(x/cellSize),gy=Math.floor(y/cellSize);for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++)for(const p of grid.get(`${gx+dx},${gy+dy}`)??[])if(Math.hypot(x-p.x,y-p.y)<n.r+p.r+gap)return false;return true;};
  const x=n.x,y=n.y,step=Math.max(n.r,maximumRadius*.5);let attempt=0;
  while(!free(n.x,n.y)){attempt++;const radius=step*Math.sqrt(attempt),angle=attempt*2.399963229728653;n.x=x+radius*Math.cos(angle);n.y=y+radius*Math.sin(angle);}
  const key=`${Math.floor(n.x/cellSize)},${Math.floor(n.y/cellSize)}`,cell=grid.get(key)??[];cell.push(n);grid.set(key,cell);
 }
 return nodes;
}
