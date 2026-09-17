import {layoutCartogram,maximumOverlap,type CartogramNode} from '../utils/cartogram';
self.onmessage=(event:MessageEvent<{nodes:CartogramNode[]}>)=>{
 try{const nodes=layoutCartogram(event.data.nodes);self.postMessage({nodes,overlap:maximumOverlap(nodes)});}
 catch(error){self.postMessage({error:String(error)});}
};
