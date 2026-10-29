import test from 'node:test';
import assert from 'node:assert/strict';
import { decodeToolResult, isTrustedRequest } from '../ui/host.mjs';

const text = value => ({type:'text', text:JSON.stringify(value)});

test('MCP list resources preserve zero, one and multiple results', () => {
  assert.deepEqual(decodeToolResult({content:[]}, 'documents', {}), []);
  assert.deepEqual(decodeToolResult({content:[text({id:1})]}, 'documents', {}), [{id:1}]);
  assert.deepEqual(decodeToolResult({content:[text({id:1}), text({id:2})]}, 'documents', {}), [{id:1}, {id:2}]);
  assert.deepEqual(decodeToolResult({content:[text([{id:1}])]}, 'holdings', {}), [{id:1}]);
  assert.deepEqual(decodeToolResult({content:[text({answer:'ok'})]}, 'research', {run_id:'R-1'}), {answer:'ok'});
  assert.deepEqual(decodeToolResult({structuredContent:{rows:[]}}, 'quotes', {}), {rows:[]});
});

test('read adapter accepts only the loopback browser origin and required header', () => {
  const server = {host:'127.0.0.1', port:3080};
  const headers = {host:'127.0.0.1:3080', origin:'http://127.0.0.1:3080', 'x-finfreedom-client':'1', 'sec-fetch-site':'same-origin'};
  assert.equal(isTrustedRequest(server, headers), true);
  assert.equal(isTrustedRequest(server, {...headers, origin:'https://example.com'}), false);
  assert.equal(isTrustedRequest(server, {...headers, host:'example.com:3080'}), false);
  assert.equal(isTrustedRequest(server, {...headers, 'x-finfreedom-client':undefined}), false);
  assert.equal(isTrustedRequest({...server, host:'0.0.0.0'}, headers), false);
});

test('holdings write routes only a trusted, versioned snapshot through the MCP tool', async () => {
  const {apply} = await import('../ui/host.mjs');
  const {Readable} = await import('node:stream');
  const routes = [];
  let call;
  const ctx = {webServer:{host:'127.0.0.1',port:3080,register:r => {routes.push(r); return () => {}; }},
    systemPrompt:{section:() => () => {}},
    tools:{execute:async args => {call = args; return {value:{content:[text({currency:'CNY'})]}};}},
    effect:fn => fn()};
  apply(ctx);
  const handler = routes.find(r => r.path === '/finfreedom/api/holdings').handler;
  const snapshot = {cash:100, expected_updated_at:'v1', positions:[]};
  const req = Readable.from([JSON.stringify({currency:'CNY',snapshot})]);
  req.method = 'PUT'; req.headers = {host:'127.0.0.1:3080',origin:'http://127.0.0.1:3080','x-finfreedom-client':'1','content-type':'application/json'};
  const res = {writeHead(status){this.status=status;},end(body){this.body=body;}};
  await handler(req,res);
  assert.equal(res.status,200);
  assert.equal(call.name,'mcp__finfreedom__write');
  assert.deepEqual(call.arguments.data.snapshot,snapshot);
  const bad = Readable.from([]); bad.method='PUT'; bad.headers={...req.headers, origin:'https://example.com'};
  const denied = {writeHead(status){this.status=status;},end(body){this.body=body;}};
  await handler(bad,denied);
  assert.equal(denied.status,403);
});

test('registers investment memory guidance for the DSH agent', async () => {
  const {apply} = await import('../ui/host.mjs');
  const sections=[];
  apply({webServer:{register:() => () => {}},tools:{},systemPrompt:{section:s => {sections.push(s); return () => {}; }},effect:fn=>fn()});
  assert.equal(sections[0].name,'finfreedom:investment-memory');
  assert.match(sections[0].text,/get_investment_memory/);
  assert.match(sections[0].text,/remember_investment_memory/);
});
