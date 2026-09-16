import {scaleLinear} from 'd3-scale';

/** Fit every available observation, with padding and readable ticks. */
export function historyScale(values:number[],unit:string,fromZero=false){
 const finite=values.filter(Number.isFinite),min=finite.length?Math.min(...finite):0,max=finite.length?Math.max(...finite):1;
 const resolution=unit==='SEK'?1000:unit==='%'?.2:1;
 const padding=Math.max((max-min)*.12,resolution/2);
 let low=min-padding,high=max+padding;
 if(min>=0)low=Math.max(0,low);
 if(fromZero){low=Math.min(0,low);high=Math.max(0,high);}
 const scale=scaleLinear().domain([low,high]).nice(4);
 let [bottom,top]=scale.domain();
 if(unit==='%'&&min>=0&&max<=100){bottom=Math.max(0,bottom);top=Math.min(100,top);}
 scale.domain([bottom,top]).range([200,21]);
 const ticks=scale.ticks(4),step=(ticks[1]??top)-(ticks[0]??bottom),displayStep=unit==='SEK'?step/1000:step;
 const decimals=Math.max(0,Math.min(6,-Math.floor(Math.log10(displayStep||1))));
 return {scale,ticks,bottom,top,decimals};
}
