import {comparisonElectionKey} from '../utils/election-view';
import {districtHover} from '../components/hover';
import {blockDefinitions,originDefinitions} from '../utils/categories';
import {demographicLabel} from '../utils/demography';
import maplibregl, {type ExpressionSpecification, type Map as GLMap, type LngLatBoundsLike} from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import type {District,GeoData,State} from '../types';
import {parties,bivariate,thresholds,numericMetric,metricScale,scaleStops,divergent} from './palette';
import {escapeHtml as e,percent,number,method} from '../utils/format';

export class AtlasMaps {
 currentMetric='foreign_background_pct'; maps:GLMap[]=[]; data:GeoData; byId:Map<string,District>; busy=false;disposed=false;fitFrame=0;latestUpdate:{state:State;visible:District[];national:District[]};onCamera:(v:{lng:number;lat:number;zoom:number})=>void;onSelect:(id:string)=>void;
 constructor(containers:HTMLElement[],geometry:GeoData,rows:District[],state:State,onSelect:(id:string)=>void,onCamera:(v:{lng:number;lat:number;zoom:number})=>void){
  this.byId=new Map(rows.map(d=>[d.district_id,d]));this.onSelect=onSelect;this.onCamera=onCamera;
  this.latestUpdate={state:{...state},visible:rows,national:rows};
  this.data={...geometry,features:geometry.features.map(f=>({...f,id:f.properties.district_id,properties:{...this.byId.get(f.properties.district_id),district_id:f.properties.district_id}}))};
  for(const container of containers){
   container.setAttribute('aria-busy','true');container.dataset.year=String(rows[0]?.geometry_year);
   const map=new maplibregl.Map({container,style:{version:8,sources:{},layers:[{id:'background',type:'background',paint:{'background-color':'#e9eff2'}}]},center:[state.lng,state.lat],zoom:state.zoom,attributionControl:false,minZoom:2,maxZoom:16});
   map.on('idle',()=>{container.setAttribute('aria-busy','false');container.dataset.ready='true';const center=map.getCenter();container.dataset.lng=center.lng.toFixed(5);container.dataset.lat=center.lat.toFixed(5);container.dataset.zoom=map.getZoom().toFixed(3);});
   this.maps.push(map);map.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-right');map.addControl(new maplibregl.ScaleControl({unit:'metric'}),'bottom-left');
   map.on('load',()=>{if(this.disposed)return;map.addSource('districts',{type:'geojson',data:this.data,promoteId:'district_id'});map.addLayer({id:'districts',type:'fill',source:'districts',paint:{'fill-color':'#96a7af','fill-opacity':.92}});map.addLayer({id:'borders',type:'line',source:'districts',paint:{'line-color':'#ffffff','line-width':['interpolate',['linear'],['zoom'],3,.15,8,.55,12,1]}});map.addLayer({id:'selected',type:'line',source:'districts',filter:['==','district_id',''],paint:{'line-color':'#102d3c','line-width':3}});const latest=this.latestUpdate;this.update(latest.state,latest.visible,latest.national);});
   const popup=new maplibregl.Popup({closeButton:false,closeOnClick:false,maxWidth:'340px',className:'atlas-hover',offset:18});
   map.on('mousemove','districts',event=>{map.getCanvas().style.cursor='pointer';const d=this.byId.get(String(event.features?.[0].properties?.district_id));if(!d)return;popup.setLngLat(event.lngLat).setHTML(districtHover(d,map.getContainer().dataset.metric??this.currentMetric)).addTo(map);});
   map.on('mouseleave','districts',()=>{map.getCanvas().style.cursor='';popup.remove();});
   map.on('click','districts',event=>{popup.remove();const id=event.features?.[0].properties?.district_id;if(id)this.onSelect(String(id));});
   // resize() also emits move. A redundant jumpTo would cancel the other map's fit animation.
   map.on('move',()=>{if(this.busy||this.disposed)return;this.busy=true;try{const center=map.getCenter();for(const other of this.maps)if(other!==map&&(other.getCenter().lng!==center.lng||other.getCenter().lat!==center.lat||other.getZoom()!==map.getZoom()||other.getBearing()!==map.getBearing()||other.getPitch()!==map.getPitch()))other.jumpTo({center,zoom:map.getZoom(),bearing:map.getBearing(),pitch:map.getPitch()});}finally{this.busy=false;}});
   map.on('moveend',()=>{if(this.busy||this.disposed)return;const c=map.getCenter();this.onCamera({lng:+c.lng.toFixed(5),lat:+c.lat.toFixed(5),zoom:+map.getZoom().toFixed(3)});});
  }
 }
 update(s:State,visible:District[],national:District[]){
  this.latestUpdate={state:{...s},visible,national};
  this.currentMetric=s.metric;
  const ids=visible.map(d=>d.district_id);
  this.maps.forEach((map,index)=>{
   if(!map.getLayer('districts'))return;
   map.setFilter('districts',['in',['get','district_id'],['literal',ids]]);map.setFilter('borders',['in',['get','district_id'],['literal',ids]]);map.setFilter('selected',['==',['get','district_id'],s.district]);
   const current:State=s.view==='compare'?{...s,view:index===0?'demography':'electoral',metric:index===0?s.metric:s.electionMetric}:s;
   let color:unknown;delete map.getContainer().dataset.scaleMin;delete map.getContainer().dataset.scaleMax;
   if(current.view==='electoral'&&current.metric.startsWith('delta_'))color=['case',['==',['get',current.metric],null],'#777f85',['interpolate',['linear'],['get',current.metric],...[-30,-20,-10,0,10,20,30].flatMap(v=>[v,divergent(v)])]];
   else if(current.view==='electoral'&&current.metric==='winning_block')color=['match',['get','winning_block'],...blockDefinitions.flatMap(b=>[b.id,b.color]),'tie','#b1aabb','#7b8793'];
   else if(current.view==='bivariate'){
    const x=thresholds(national,'foreign_background_pct'),y=thresholds(national,`pct_${s.party}`);
    const bin=(key:string,cuts:number[])=>['case',['<=',['get',key],cuts[0]],0,['<=',['get',key],cuts[1]],1,2];
    const cat=['+',['*',3,bin(`pct_${s.party}`,y)],bin('foreign_background_pct',x)];
    color=['case',['all',['!=',['get','foreign_background_pct'],null],['!=',['get',`pct_${s.party}`],null]],['match',cat,...bivariate.flatMap((c,i)=>[i,c]),'#777f85'],'#777f85'];
   }else if(current.view==='dominant'||(current.view==='electoral'&&current.metric==='winning_party'))color=['case',['==',['get','winning_party_tie'],true],'#b1aabb',['match',['get','winning_party'],...parties.flatMap(p=>[p.id,p.color]),'#777f85']];
   else {const key=numericMetric(current),domain=metricScale(national,key);if(key!=='common_origin'){map.getContainer().dataset.scaleMin=String(domain.min);map.getContainer().dataset.scaleMax=String(domain.max);}color=key==='common_origin'?['match',['get',key],...originDefinitions.flatMap(o=>[o.id,o.color]),'tie','#b1aabb','#7b8793']:['case',['==',['get',key],null],'#777f85',['interpolate',['linear'],['get',key],...scaleStops(domain).flat()]];}
   map.setPaintProperty('districts','fill-color',color as ExpressionSpecification);map.getContainer().dataset.metric=s.view==='compare'&&index===1?comparisonElectionKey(s):current.metric;
  });
 }
 fit(ids:string[]){cancelAnimationFrame(this.fitFrame);const wanted=new Set(ids),coords:number[][]=[];const visit=(a:unknown)=>{if(Array.isArray(a)){if(typeof a[0]==='number')coords.push(a as number[]);else a.forEach(visit);}};for(const f of this.data.features)if(wanted.has(f.properties.district_id)&&'coordinates'in f.geometry)visit(f.geometry.coordinates);if(!coords.length)return;let minX=180,minY=90,maxX=-180,maxY=-90;for(const[x,y]of coords){minX=Math.min(minX,x);minY=Math.min(minY,y);maxX=Math.max(maxX,x);maxY=Math.max(maxY,y);}this.fitFrame=requestAnimationFrame(()=>{if(this.disposed)return;this.resize();this.maps[0]?.fitBounds([[minX,minY],[maxX,maxY]] as LngLatBoundsLike,{padding:35,maxZoom:16,duration:650});});}
 resize(){this.maps.forEach(m=>m.resize());}
 destroy(){this.disposed=true;cancelAnimationFrame(this.fitFrame);this.maps.forEach(m=>m.remove());this.maps=[];}
}
