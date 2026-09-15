import {afterEach,describe,expect,it,vi} from 'vitest';
import {gzipSync} from 'node:zlib';
import {compressedJSON} from '../src/utils/format';
const data=[{district_id:'01800101',pct_S:22.4}];
afterEach(()=>vi.unstubAllGlobals());
describe('static and HTTP gzip delivery',()=>{
 it('reads an opaque gzip file served by a static host',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(new Uint8Array(gzipSync(JSON.stringify(data))).buffer,{headers:{'Content-Type':'application/gzip'}})));
  expect(await compressedJSON('/districts.json.gz')).toEqual(data);
 });
 it('does not decompress again after the browser decodes Content-Encoding gzip',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify(data),{headers:{'Content-Type':'application/json','Content-Encoding':'gzip'}})));
  expect(await compressedJSON('/districts.json.gz')).toEqual(data);
 });
 it('reports an HTTP error before trying to decode it',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response('Not found',{status:404})));
  await expect(compressedJSON('/missing.gz')).rejects.toThrow('404');
 });
});
