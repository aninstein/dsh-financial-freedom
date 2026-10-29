import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';

async function setup() {
  let plugin, registration;
  const calls=[];
  const window = {__ModuleLoader__:{load: ({factory}) => {plugin=factory(name => name === 'react' ? {createElement(){}} : {});}}};
  vm.runInNewContext(await readFile(new URL('../ui/client.js',import.meta.url),'utf8'),{window});
  const scoped={id:'new-session'};
  const ctx = {effect(){}, layout:{}, slots:{inject(_slot,fn){fn();},register(spec){if(spec.id==='finfreedom-workspace') registration=spec;}},
    sessions:{create:async (...args)=>{calls.push(['create',args]);return 'new-session';},scope:id => id==='new-session'?scoped:undefined,open:id=>calls.push(['open',id])},
    conversation:{input:{for:scope=>({setDraft:text=>calls.push(['draft',scope.id,text])})}}};
  plugin.apply(ctx);
  return {calls,send:registration.inject().sendToAgent,ctx};
}

test('workspace creates an unclassified session and fills its editable draft', async () => {
  const {calls,send}=await setup();
  await send('请分析当前指数');
  assert.deepEqual(calls,[['create',[]],['draft','new-session','请分析当前指数'],['open','new-session']]);
});
test('an unresolved session fails rather than sending into the old conversation', async () => {
  const {calls,send,ctx}=await setup();
  ctx.sessions.scope=()=>undefined;
  await assert.rejects(send('请录入持仓'),/DSH 会话不可用/);
  assert.deepEqual(calls,[['create',[]]]);
});
