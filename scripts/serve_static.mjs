import http from 'node:http';
import {readFile,stat} from 'node:fs/promises';
import {resolve,extname} from 'node:path';
const root=resolve('dist'),port=4173,base='/atlas/';
const types={'.html':'text/html; charset=utf-8','.js':'application/javascript','.css':'text/css','.json':'application/json','.gz':'application/gzip','.csv':'text/csv','.md':'text/plain; charset=utf-8'};
http.createServer(async(req,res)=>{try{const path=decodeURIComponent(new URL(req.url,'http://localhost').pathname);if(!path.startsWith(base))throw new Error('outside base');let file=resolve(root,path.slice(base.length));if(file!==root&&!file.startsWith(root+'/'))throw new Error('outside root');if((await stat(file)).isDirectory())file=resolve(file,'index.html');const data=await readFile(file);res.writeHead(200,{'Content-Type':types[extname(file)]||'application/octet-stream'});res.end(data);}catch{res.writeHead(404);res.end('Not found');}}).listen(port,'127.0.0.1',()=>console.log(`Static QA: http://127.0.0.1:${port}${base}`));
