import test from 'node:test';
import assert from 'node:assert/strict';
import {validateRecommendations} from '../ui/recommendations.mjs';

test('recommendations require four to six grounded, usable entries',()=>{
 const news=[{title:'新闻',content:'内容',source:'来源',published_at:'2026-10-29T12:00:00+08:00',url:'https://example.com/news'}];
 const row={title:'产业研究',description:'检查新闻及产业影响',prompt:'使用 finfreedom-research 核实事件',source_index:1};
 const output=validateRecommendations(JSON.stringify([row,row,row,row]),news);
 assert.equal(output.length,4);assert.match(output[0].markdown,/https:\/\/example.com\/news/);assert.equal(output[0].source.name,'来源');
 assert.throws(()=>validateRecommendations(JSON.stringify([row]),news));
 assert.throws(()=>validateRecommendations(JSON.stringify(Array(4).fill({...row,source_index:2})),news));
 assert.throws(()=>validateRecommendations('not-json',news));
});
