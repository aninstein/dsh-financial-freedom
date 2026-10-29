import test from 'node:test';
import assert from 'node:assert/strict';
import {Readable} from 'node:stream';
import {apply} from '../ui/host.mjs';

const headers={host:'127.0.0.1:3080',origin:'http://127.0.0.1:3080','x-finfreedom-client':'1','content-type':'application/json'};
test('guide endpoint routes only validated requests to the owner-scoped MCP tools', async()=>{
 const routes=[],calls=[];
 apply({webServer:{host:'127.0.0.1',port:3080,register:r=>{routes.push(r);return()=>{}}},systemPrompt:{section:()=>()=>{}},effect:fn=>fn(),tools:{execute:async args=>{calls.push(args);return {value:{structuredContent:{version:1}}}}}});
 const handler=routes.find(r=>r.path==='/finfreedom/api/guide').handler;
 const response=()=>({writeHead(status){this.status=status},end(body){this.body=JSON.parse(body)}});
 let req=Readable.from([]);req.method='GET';req.url='/finfreedom/api/guide?view=all';req.headers=headers;let res=response();await handler(req,res);
 assert.equal(res.status,200);assert.equal(calls[0].name,'mcp__finfreedom__list_guide_entries');assert.equal(calls[0].arguments.view,'all');
 req=Readable.from([JSON.stringify({action:'create',data:{markdown:'# Test',expected_version:0}})]);req.method='POST';req.url='/finfreedom/api/guide';req.headers=headers;res=response();await handler(req,res);
 assert.equal(res.status,200);assert.equal(calls[1].name,'mcp__finfreedom__manage_guide_entry');assert.equal(calls[1].arguments.action,'create');
 req=Readable.from([]);req.method='GET';req.url='/finfreedom/api/guide?view=all';req.headers={...headers,origin:'https://other.example'};res=response();await handler(req,res);assert.equal(res.status,403);assert.equal(calls.length,2);
});
