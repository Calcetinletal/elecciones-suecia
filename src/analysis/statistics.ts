import {finite} from '../utils/data';
export function pearson(x:number[],y:number[]):number|null{
 if(x.length!==y.length||x.length<3)return null;
 const mx=x.reduce((s,v)=>s+v,0)/x.length,my=y.reduce((s,v)=>s+v,0)/y.length;
 let xx=0,yy=0,xy=0;for(let i=0;i<x.length;i++){xx+=(x[i]-mx)**2;yy+=(y[i]-my)**2;xy+=(x[i]-mx)*(y[i]-my);}
 return xx>1e-12&&yy>1e-12?Math.max(-1,Math.min(1,xy/Math.sqrt(xx*yy))):null;
}
export function ranks(a:number[]):number[]{const order=a.map((v,i)=>({v,i})).sort((a,b)=>a.v-b.v),r=new Array(a.length);for(let i=0;i<order.length;){let j=i+1;while(j<order.length&&order[j].v===order[i].v)j++;for(let k=i;k<j;k++)r[order[k].i]=(i+j+1)/2;i=j;}return r;}
export const spearman=(x:number[],y:number[])=>pearson(ranks(x),ranks(y));
export function linear(x:number[],y:number[]){if(x.length<3)return null;const mx=x.reduce((a,b)=>a+b)/x.length,my=y.reduce((a,b)=>a+b)/y.length;const den=x.reduce((s,v)=>s+(v-mx)**2,0);if(den<1e-12)return null;const slope=x.reduce((s,v,i)=>s+(v-mx)*(y[i]-my),0)/den;return {slope,intercept:my-slope*mx};}
export function quantile(a:number[],p:number){if(!a.length)return null;const x=[...a].sort((a,b)=>a-b),i=(x.length-1)*p,j=Math.floor(i);return x[j]+(x[Math.min(j+1,x.length-1)]-x[j])*(i-j);}
/** OLS via QR, standardized predictors. Coefficients are percentage points per predictor SD. */
export function regression(data:number[][],y:number[]):{coefficients:number[];r2:number;n:number;sd:number[]}|null{
 const n=y.length,p=data[0]?.length??0;if(n<=p+2||p===0||data.some(row=>row.length!==p||row.some(x=>!finite(x)))||y.some(x=>!finite(x)))return null;
 const means=Array.from({length:p},(_,j)=>data.reduce((s,row)=>s+row[j],0)/n);
 const sd=means.map((m,j)=>Math.sqrt(data.reduce((s,row)=>s+(row[j]-m)**2,0)/(n-1)));
 if(sd.some(v=>v<1e-9))return null;
 const columns=[Array(n).fill(1),...means.map((m,j)=>data.map(row=>(row[j]-m)/sd[j]))];
 const q:number[][]=[],r=Array.from({length:p+1},()=>Array(p+1).fill(0));
 for(let j=0;j<=p;j++){const v=[...columns[j]];for(let k=0;k<j;k++){r[k][j]=q[k].reduce((s,x,i)=>s+x*v[i],0);for(let i=0;i<n;i++)v[i]-=r[k][j]*q[k][i];}r[j][j]=Math.hypot(...v);if(r[j][j]<1e-8)return null;q.push(v.map(x=>x/r[j][j]));}
 const b=q.map(col=>col.reduce((s,x,i)=>s+x*y[i],0));for(let i=p;i>=0;i--){for(let j=i+1;j<=p;j++)b[i]-=r[i][j]*b[j];b[i]/=r[i][i];}
 const mean=y.reduce((s,v)=>s+v,0)/n,sst=y.reduce((s,v)=>s+(v-mean)**2,0);if(sst<1e-12)return null;
 const sse=y.reduce((s,v,i)=>s+(v-columns.reduce((s,col,j)=>s+col[i]*b[j],0))**2,0);
 return {coefficients:b,r2:1-sse/sst,n,sd};
}
