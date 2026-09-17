import {cartogramMunicipalities} from '../utils/cartogram-municipalities';
import {partyBadge} from '../utils/categories';
import type {District,GeoData,State,CartogramMode} from '../types';
import {maximumOverlap,makeCartogramNodes,hasVotes,voteSlices,type CartogramNode} from '../utils/cartogram';
import {parties,legend,metricScale,sequential,divergent} from './palette';
import {blockDefinitions} from '../utils/categories';
import {districtHover} from '../components/hover';
import {escapeHtml as e,number} from '../utils/format';
type Shape={id:string;path:Path2D;x:number;y:number;bounds:number[]};
const project=([lon,lat]:number[])=>[lon*Math.PI/180,-Math.log(Math.tan(Math.PI/4+lat*Math.PI/360))];
function shapesFrom(geometry:GeoData):Shape[]{return geometry.features.flatMap(feature=>{
 const g=feature.geometry;if(g.type!=='Polygon'&&g.type!=='MultiPolygon')return [];
 const polygons=g.type==='Polygon'?[g.coordinates]:g.coordinates,path=new Path2D();
 let xmin=Infinity,ymin=Infinity,xmax=-Infinity,ymax=-Infinity,largest=0,anchor:number[]=[];
 for(const rings of polygons)for(let j=0;j<rings.length;j++){
  const ring=rings[j].map(project);if(!ring.length)continue;path.moveTo(ring[0][0],ring[0][1]);
  let area=0,cx=0,cy=0;
  for(let i=0;i<ring.length;i++){const [x,y]=ring[i],[nx,ny]=ring[(i+1)%ring.length],cross=x*ny-nx*y;path.lineTo(x,y);xmin=Math.min(xmin,x);xmax=Math.max(xmax,x);ymin=Math.min(ymin,y);ymax=Math.max(ymax,y);area+=cross;cx+=(x+nx)*cross;cy+=(y+ny)*cross;}
  path.closePath();if(j===0&&Math.abs(area)>largest){largest=Math.abs(area);anchor=[cx/(3*area),cy/(3*area)];}
 }
 return Number.isFinite(xmin)?[{id:feature.properties.district_id,path,x:anchor[0]??(xmin+xmax)/2,y:anchor[1]??(ymin+ymax)/2,bounds:[xmin,ymin,xmax,ymax]}]:[];
});}
export class VoterCartogram {
 root:HTMLElement;stage:HTMLElement;canvas:HTMLCanvasElement;ctx:CanvasRenderingContext2D;observer:ResizeObserver;
 districtShapes:Shape[];municipalShapes:Shape[];unit:State['cartogramUnit']='municipality';shapes:Shape[];visibleShapes:Shape[]=[];nodes:CartogramNode[]=[];byId:Map<string,District>;s:State;national:District[];visible:District[]=[];
 worker:Worker|null=null;disposed=false;key='';cache=new Map<string,CartogramNode[]>();frame=0;progress=0;pie=0;ready=false;
 geoBounds=[0,0,1000,1000];
 camera={x:0,y:0,k:1};width=0;height=0;worldBounds=[0,0,1000,1000];scopeScale=1;unitRadius=1;pendingFit:string[]|null=null;
 hoverId='';drag:{x:number;y:number;cx:number;cy:number;moved:boolean}|null=null;timers:ReturnType<typeof setTimeout>[]=[];
 colors=new Map<string,string>();slices=new Map<string,ReturnType<typeof voteSlices>>();
 geoCanvas=document.createElement('canvas');geoDirty=true;
 onSelect:(id:string)=>void;onMode:(mode:CartogramMode)=>void;
 constructor(root:HTMLElement,geometry:GeoData,municipalityGeometry:GeoData,rows:District[],state:State,onSelect:(id:string)=>void,onMode:(mode:CartogramMode)=>void,onMunicipality:(id:string)=>void,onUnit:(unit:State['cartogramUnit'])=>void){
  this.root=root;this.stage=root.querySelector('.cartogram-stage')!;this.canvas=root.querySelector('#cartogram-canvas')!;this.ctx=this.canvas.getContext('2d')!;
  this.s={...state};this.national=rows;this.byId=new Map(rows.map(d=>[d.district_id,d]));this.districtShapes=shapesFrom(geometry);this.municipalShapes=shapesFrom(municipalityGeometry);this.shapes=this.districtShapes;this.onSelect=id=>this.unit==='municipality'?onMunicipality(id):onSelect(id);this.onMode=onMode;
  this.slices=new Map(rows.map(d=>[d.district_id,voteSlices(d)]));
  root.addEventListener('click',event=>{const b=(event.target as Element).closest<HTMLButtonElement>('button');if(!b)return;
   if(b.dataset.cartogramMode){this.stopPlay();onMode(b.dataset.cartogramMode as CartogramMode);}
   else if(b.id==='cartogram-play'){this.stopPlay();onMode('geography');this.timers.push(setTimeout(()=>onMode('voters'),1400),setTimeout(()=>onMode('shares'),3400));}
   else if(b.id==='cartogram-reset')this.fit(this.visible.map(d=>d.district_id));
   else if(b.id==='cartogram-expand')this.expand(!this.root.classList.contains('cartogram-expanded'));
   else if(b.dataset.cartogramZoom)this.zoom(Number(b.dataset.cartogramZoom),this.width/2,this.height/2);
  });
  root.querySelector('#cartogram-unit')!.addEventListener('change',event=>onUnit((event.target as HTMLSelectElement).value as State['cartogramUnit']));
  root.addEventListener('keydown',event=>{if(event.key==='Escape')this.expand(false);});
  const reference=root.querySelector<HTMLCanvasElement>('#cartogram-reference-canvas')!;
  reference.addEventListener('pointermove',event=>this.hover(event.offsetX,event.offsetY,true));
  reference.addEventListener('pointerleave',()=>this.hideHover());
  reference.addEventListener('click',event=>{const id=this.hit(event.offsetX,event.offsetY,true);if(id)this.onSelect(id);});
  this.canvas.addEventListener('wheel',event=>{event.preventDefault();this.zoom(Math.exp(-event.deltaY*.0015),event.offsetX,event.offsetY);},{passive:false});
  this.canvas.addEventListener('pointerdown',event=>{this.canvas.setPointerCapture(event.pointerId);this.drag={x:event.offsetX,y:event.offsetY,cx:this.camera.x,cy:this.camera.y,moved:false};});
  this.canvas.addEventListener('pointermove',event=>{if(this.drag){const dx=event.offsetX-this.drag.x,dy=event.offsetY-this.drag.y;this.drag.moved||=Math.hypot(dx,dy)>4;if(this.drag.moved){this.camera.x=this.drag.cx+dx;this.camera.y=this.drag.cy+dy;this.hideHover();this.draw();return;}}this.hover(event.offsetX,event.offsetY);});
  this.canvas.addEventListener('pointerup',event=>{const moved=this.drag?.moved;this.drag=null;if(!moved){const id=this.hit(event.offsetX,event.offsetY);if(id){this.hideHover();this.onSelect(id);}}});
  this.canvas.addEventListener('pointercancel',()=>{this.drag=null;});this.canvas.addEventListener('pointerleave',()=>this.hideHover());
  this.canvas.addEventListener('keydown',event=>{if(['+','=','-','0','ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)){event.preventDefault();if(event.key==='0')this.fit(this.visible.map(d=>d.district_id));else if(['+','=','-'].includes(event.key))this.zoom(event.key==='-'?1/1.5:1.5,this.width/2,this.height/2);else {this.camera.x+=event.key==='ArrowLeft'?30:event.key==='ArrowRight'?-30:0;this.camera.y+=event.key==='ArrowUp'?30:event.key==='ArrowDown'?-30:0;this.draw();}}});
  this.observer=new ResizeObserver(()=>this.resize());this.observer.observe(this.stage);this.resize();
 }
 update(state:State,visible:District[],national:District[]){
  const previous=this.s.cartogramMode;this.s={...state};this.unit=state.district?'district':state.cartogramUnit;
  if(this.unit==='municipality'){national=cartogramMunicipalities(national,state.party);visible=cartogramMunicipalities(visible,state.party);}
  this.shapes=this.unit==='municipality'?this.municipalShapes:this.districtShapes;this.byId=new Map(national.map(d=>[d.district_id,d]));this.slices=new Map(national.map(d=>[d.district_id,voteSlices(d)]));this.national=national;this.visible=visible;
  this.root.querySelector<HTMLSelectElement>('#cartogram-unit')!.value=this.unit;this.stage.dataset.unit=this.unit;
  this.root.querySelector<HTMLOptionElement>('#cartogram-unit option[value=municipality]')!.disabled=state.metric.startsWith('delta_');
  this.domain=metricScale(national,state.metric==='party'?'pct_'+state.party:state.metric);this.colors=new Map(visible.map(d=>[d.district_id,this.color(d)]));this.geoDirty=true;
  this.root.querySelectorAll<HTMLButtonElement>('[data-cartogram-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.cartogramMode===state.cartogramMode)));
  const key=String(state.year)+':'+this.unit+':'+visible.map(d=>d.district_id).join(',');
  if(key!==this.key){this.key=key;this.stopPlay();this.prepare();}else if(previous!==state.cartogramMode){if(previous==='geography'||state.cartogramMode==='geography')this.fitBounds(this.boundsForMode());this.animate();}else this.draw();
  this.updateLabels();
 }
 prepare(){
  this.worker?.terminate();this.worker=null;cancelAnimationFrame(this.frame);this.ready=false;this.hideHover();this.nodes=[];
  const ids=new Set(this.visible.map(d=>d.district_id)),selected=this.shapes.filter(f=>ids.has(f.id));
  this.stage.dataset.ready='false';this.stage.setAttribute('aria-busy','true');this.status('Ajustando círculos sin solapamientos…');
  if(!selected.length){this.visibleShapes=[];this.complete([]);return;}
  const xmin=Math.min(...selected.map(f=>f.bounds[0])),ymin=Math.min(...selected.map(f=>f.bounds[1])),xmax=Math.max(...selected.map(f=>f.bounds[2])),ymax=Math.max(...selected.map(f=>f.bounds[3]));
  const scale=1000/Math.max(xmax-xmin,ymax-ymin,1e-8);this.scopeScale=scale;
  this.visibleShapes=selected.map(f=>{const path=new Path2D();path.addPath(f.path,new DOMMatrix([scale,0,0,scale,-xmin*scale,-ymin*scale]));return {...f,path,x:(f.x-xmin)*scale,y:(f.y-ymin)*scale,bounds:[(f.bounds[0]-xmin)*scale,(f.bounds[1]-ymin)*scale,(f.bounds[2]-xmin)*scale,(f.bounds[3]-ymin)*scale]};});
  this.geoBounds=[0,0,(xmax-xmin)*scale,(ymax-ymin)*scale];this.worldBounds=[...this.geoBounds];this.fitBounds(this.worldBounds);
  const anchors=this.visibleShapes.flatMap(f=>{const d=this.byId.get(f.id)!;return hasVotes(d)?[{id:f.id,x:f.x,y:f.y,votes:d.valid_votes!}]:[];});
  const nodes=makeCartogramNodes(anchors,Math.max(120000,this.worldBounds[2]*this.worldBounds[3]*.28));
  this.unitRadius=nodes.length?nodes[0].r/Math.sqrt(nodes[0].votes):1;
  this.progress=0;this.pie=0;this.draw();
  const cached=this.cache.get(this.key);if(cached){this.complete(cached);return;}
  if(!nodes.length){this.complete([]);return;}
  this.worker=new Worker(new URL('./cartogram.worker.ts',import.meta.url),{type:'module'});
  const key=this.key;
  this.worker.onmessage=event=>{if(this.disposed||this.key!==key)return;if(event.data.error){this.status('No se pudo calcular el cartograma. Prueba otro territorio.');this.stage.setAttribute('aria-busy','false');return;}
   const result=event.data.nodes as CartogramNode[];this.stage.dataset.maxOverlap=String(event.data.overlap);if(this.cache.size>=6)this.cache.delete(this.cache.keys().next().value!);this.cache.set(key,result);this.complete(result);};
  this.worker.onerror=()=>{this.status('No se pudo calcular el cartograma. Prueba otro territorio.');this.stage.setAttribute('aria-busy','false');};
  this.worker.postMessage({nodes});
 }
 complete(nodes:CartogramNode[]){
  this.stage.dataset.maxOverlap=String(maximumOverlap(nodes));
  this.nodes=nodes;this.ready=true;this.stage.dataset.ready='true';this.stage.dataset.nodeCount=String(nodes.length);this.stage.dataset.voteTotal=String(nodes.reduce((n,p)=>n+p.votes,0));this.stage.setAttribute('aria-busy','false');this.status(nodes.length?'':'Sin votos válidos para representar.');
  if(nodes.length)this.worldBounds=[Math.min(this.geoBounds[0],...nodes.map(n=>n.x-n.r)),Math.min(this.geoBounds[1],...nodes.map(n=>n.y-n.r)),Math.max(this.geoBounds[2],...nodes.map(n=>n.x+n.r)),Math.max(this.geoBounds[3],...nodes.map(n=>n.y+n.r))];
  this.stage.dataset.layoutSpan=String(Math.max(this.worldBounds[2]-this.worldBounds[0],this.worldBounds[3]-this.worldBounds[1]));
  this.fitBounds(this.boundsForMode());if(this.pendingFit){const ids=this.pendingFit;this.pendingFit=null;this.fit(ids);}this.animate();this.updateLabels();
 }
 updateLabels(){
  const mode=this.s.cartogramMode;this.stage.dataset.mode=mode;
  this.stage.dataset.layout='geographic';
  this.root.querySelector('#cartogram-pane-title')!.textContent=mode==='geography'?'Superficie':mode==='shares'?'Votos por partido':'Votos válidos';
  this.root.querySelector('.cartogram-explanation')!.textContent=mode==='geography'?'La superficie destaca los distritos grandes, aunque tengan pocos votantes.':mode==='voters'?'Mismos distritos y colores. Ahora el área de cada círculo depende de sus votos válidos.':'Cada sector representa los votos reales de un partido, también donde no ganó.';
  this.root.querySelector('#cartogram-color-key')!.innerHTML=legend({...this.s,view:'electoral',metric:mode==='shares'?'winning_party':this.s.metric},this.national).replace('<b>Partido ganador</b>',mode==='shares'?'<b>Votos de cada partido</b>':'<b>Partido ganador</b>');
  this.root.querySelector('.cartogram-explanation')!.textContent=(this.unit==='municipality'?'Cada círculo es un municipio.':'Cada círculo es un distrito.')+' '+(mode==='shares'?'Cada sector representa sus votos por partido.':'Área proporcional a los votos válidos; posiciones geográficas aproximadas.');
  this.sizeLegend();
 }
 boundsForMode(){return this.worldBounds;}
 status(text:string){this.root.querySelector('.cartogram-status')!.textContent=text;}
 expand(expanded:boolean){this.root.classList.toggle('cartogram-expanded',expanded);const button=this.root.querySelector('#cartogram-expand')!,label=expanded?'Cerrar ampliación':'Ampliar gráfico';button.setAttribute('aria-pressed',String(expanded));button.setAttribute('title',label);button.setAttribute('aria-label',label);}
 stopPlay(){this.timers.forEach(clearTimeout);this.timers=[];}
 animate(){
  cancelAnimationFrame(this.frame);this.hideHover();const start=performance.now(),a=this.progress,b=this.pie,target=this.s.cartogramMode==='geography'?0:1,pie=this.s.cartogramMode==='shares'?1:0;
  const duration=matchMedia('(prefers-reduced-motion: reduce)').matches?0:900;
  const step=()=>{if(this.disposed)return;const t=duration?Math.max(0,Math.min(1,(performance.now()-start)/duration)):1,k=t*t*(3-2*t);this.progress=a+(target-a)*k;this.pie=b+(pie-b)*k;this.draw();if(t<1)this.frame=requestAnimationFrame(step);else this.stage.dataset.animating='false';};
  this.stage.dataset.animating='true';this.frame=requestAnimationFrame(step);
 }
 color(d:District){
  if(this.s.metric==='winning_party')return d.winning_party_tie?'#b1aabb':parties.find(p=>p.id===d.winning_party)?.color??'#7b8793';
  if(this.s.metric==='winning_block')return blockDefinitions.find(b=>b.id===d.winning_block)?.color??(d.winning_block==='tie'?'#b1aabb':'#7b8793');
  const key=this.s.metric==='party'?'pct_'+this.s.party:this.s.metric,v=d[key];if(typeof v!=='number'||!Number.isFinite(v))return '#7b8793';
  if(key.startsWith('delta_'))return divergent(v);
  return sequential(Math.max(0,Math.min(100,100*(v-this.domain.min)/(this.domain.max-this.domain.min))));
 }
 domain={min:0,max:100};
 draw(){
  if(this.disposed||!this.width||!this.height)return;const ctx=this.ctx,dpr=Math.min(devicePixelRatio||1,2);ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,this.width,this.height);ctx.save();ctx.translate(this.camera.x,this.camera.y);ctx.scale(this.camera.k,this.camera.k);
  const p=this.ready?this.progress:0;
  {
   const mapCamera=this.camera;
   const key=[mapCamera.x,mapCamera.y,mapCamera.k,this.canvas.width,this.canvas.height].join(',');
   if(this.geoDirty||this.geoCanvas.dataset.camera!==key){
    this.geoCanvas.width=this.canvas.width;this.geoCanvas.height=this.canvas.height;const g=this.geoCanvas.getContext('2d',{willReadFrequently:true})!;
    g.setTransform(dpr,0,0,dpr,0,0);g.translate(mapCamera.x,mapCamera.y);g.scale(mapCamera.k,mapCamera.k);
    for(const f of this.visibleShapes){g.fillStyle=this.colors.get(f.id)??'#7b8793';g.fill(f.path,'evenodd');g.strokeStyle='#ffffff';g.lineWidth=.25/mapCamera.k;g.stroke(f.path);if(f.id===this.s.district){g.strokeStyle='#132d42';g.lineWidth=2/mapCamera.k;g.stroke(f.path);}}
    this.geoCanvas.dataset.camera=key;this.geoDirty=false;
   }
   const ref=this.root.querySelector<HTMLCanvasElement>('#cartogram-reference-canvas')!;if(ref.width!==this.canvas.width||ref.height!==this.canvas.height){ref.width=this.canvas.width;ref.height=this.canvas.height;}const rctx=ref.getContext('2d')!;rctx.clearRect(0,0,ref.width,ref.height);rctx.drawImage(this.geoCanvas,0,0);
   if(p<1){ctx.save();ctx.setTransform(1,0,0,1,0,0);ctx.globalAlpha=1-p;ctx.drawImage(this.geoCanvas,0,0);ctx.restore();}
  }
  ctx.globalAlpha=1;
  const geoCamera=this.camera;
  if(p>0)for(const n of this.nodes){const ax=(n.anchorX*geoCamera.k+geoCamera.x-this.camera.x)/this.camera.k,ay=(n.anchorY*geoCamera.k+geoCamera.y-this.camera.y)/this.camera.k,x=ax+(n.x-ax)*p,y=ay+(n.y-ay)*p,r=n.r*Math.sqrt(p);ctx.globalAlpha=p;
   ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fillStyle=this.colors.get(n.id)??'#7b8793';ctx.fill();
   if(this.pie>0){let angle=-Math.PI/2;ctx.globalAlpha=p*this.pie;for(const slice of this.slices.get(n.id)??[]){const end=angle+2*Math.PI*slice.share;ctx.beginPath();ctx.moveTo(x,y);ctx.arc(x,y,r,angle,end);ctx.closePath();ctx.fillStyle=slice.color;ctx.fill();angle=end;}}
   if(n.id===this.s.district||n.id===this.hoverId){ctx.globalAlpha=1;ctx.beginPath();ctx.arc(x,y,r+1/this.camera.k,0,Math.PI*2);ctx.strokeStyle='#102d3c';ctx.lineWidth=2/this.camera.k;ctx.stroke();}
  }
  ctx.restore();ctx.globalAlpha=1;
  if(this.ready){const area=this.nodes.reduce((sum,n)=>sum+Math.PI*n.r*n.r,0)*this.camera.k*this.camera.k;this.stage.dataset.circleAreaFraction=String(area/(this.width*this.height));}
 }
 fit(ids:string[]){if(!this.ready){this.pendingFit=ids;return;}if(ids.length!==1){this.fitBounds(this.boundsForMode());return;}const id=ids[0],node=this.nodes.find(n=>n.id===id),shape=this.visibleShapes.find(n=>n.id===id);if(this.s.cartogramMode!=='geography'&&node){const pad=node.r*4,b=shape?.bounds??[node.x,node.y,node.x,node.y];this.fitBounds([Math.min(b[0],node.x-pad),Math.min(b[1],node.y-pad),Math.max(b[2],node.x+pad),Math.max(b[3],node.y+pad)]);}else if(shape)this.fitBounds(shape.bounds);}
 cameraFor(bounds:number[]){const [x0,y0,x1,y1]=bounds,pad=8,top=24,k=Math.min((this.width-2*pad)/Math.max(x1-x0,1),(this.height-top-pad)/Math.max(y1-y0,1));return {x:this.width/2-(x0+x1)/2*k,y:top+(this.height-top-pad)/2-(y0+y1)/2*k,k};}
 fitBounds(bounds:number[]){if(!this.width||!this.height)return;this.camera=this.cameraFor(bounds);this.draw();this.sizeLegend();}
 resize(){const box=this.stage.getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,2);if(this.width===box.width&&this.height===box.height)return;this.width=box.width;this.height=box.height;this.canvas.width=Math.round(box.width*dpr);this.canvas.height=Math.round(box.height*dpr);this.fitBounds(this.boundsForMode());}
 zoom(factor:number,x:number,y:number){const k=Math.max(.02,Math.min(300,this.camera.k*factor)),ratio=k/this.camera.k;this.camera={x:x-(x-this.camera.x)*ratio,y:y-(y-this.camera.y)*ratio,k};this.hideHover();this.draw();this.sizeLegend();}
 sizeLegend(){const el=this.root.querySelector('.cartogram-size-key');if(!el)return;if(!this.ready||this.s.cartogramMode==='geography'){el.innerHTML='';return;}
  const raw=(12/(this.unitRadius*this.camera.k))**2,base=10**Math.floor(Math.log10(raw)),count=Math.max(1,Math.round(raw/base)*base),radius=this.unitRadius*Math.sqrt(count)*this.camera.k;
  el.innerHTML=`<svg width="32" height="32" aria-hidden="true"><circle cx="16" cy="16" r="${radius}" fill="#7395a4"/></svg><span>${number(count)} votos válidos</span>`;
 }
 hit(px:number,py:number,geographic=false){if(this.stage.dataset.animating==='true')return '';const x=(px-this.camera.x)/this.camera.k,y=(py-this.camera.y)/this.camera.k;
  if(!geographic&&this.progress>.5&&this.ready){for(const n of this.nodes){const nx=n.anchorX+(n.x-n.anchorX)*this.progress,ny=n.anchorY+(n.y-n.anchorY)*this.progress;if(Math.hypot(x-nx,y-ny)<=n.r)return n.id;}return '';}
  this.ctx.save();this.ctx.setTransform(1,0,0,1,0,0);let id='';for(const f of this.visibleShapes){const [a,b,c,d]=f.bounds;if(x>=a&&x<=c&&y>=b&&y<=d&&this.ctx.isPointInPath(f.path,x,y,'evenodd')){id=f.id;break;}}this.ctx.restore();return id;
 }
 hover(x:number,y:number,geographic=false){const id=this.hit(x,y,geographic);if(id===this.hoverId)return;this.hoverId=id;const host=this.root.querySelector<HTMLElement>('.cartogram-hover')!;this.canvas.style.cursor=id?'pointer':'grab';host.hidden=!id;if(id){const d=this.byId.get(id)!;host.innerHTML=this.unit==='municipality'?`<div class="cartogram-municipal-hover"><b>${e(d.municipality_name)}</b><small>${number(d.valid_votes)} votos válidos · ${number(d.district_count as number)} distritos</small><div>${voteSlices(d).filter(p=>p.id!=='missing').sort((a,b)=>b.votes-a.votes).slice(0,4).map(p=>`${partyBadge(p.id)} <strong>${number(100*p.share,1)} %</strong>`).join(' ')}</div><small>Pulsa para ver los distritos</small></div>`:districtHover(d,this.s.metric==='party'?'pct_'+this.s.party:this.s.metric).replace('</footer>',` · ${number(d.valid_votes)} votos válidos</footer>`);}this.draw();}
 hideHover(){this.hoverId='';this.root.querySelector<HTMLElement>('.cartogram-hover')!.hidden=true;}
 destroy(){this.disposed=true;this.stopPlay();cancelAnimationFrame(this.frame);this.worker?.terminate();this.observer.disconnect();}
}
