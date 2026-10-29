import test from 'node:test';
import assert from 'node:assert/strict';
import {apply} from '../ui/skills.mjs';

test('plugin registers its bundled skills for all DSH agents', async () => {
  let provider;
  const controller = new AbortController();
  const ctx = {skills:{registerProvider(factory) { provider = factory({signal:controller.signal, invalidate(){}}); }}, effect(){}, on(){}, get(){ return undefined; }};
  apply(ctx);
  try {
    const result = await provider.list({});
    const candidates = Array.isArray(result) ? result : result.candidates;
    const names = candidates.map(candidate => candidate.name || candidate.summary?.name);
    for (const name of ['install-futu-opend', 'futuapi', 'finfreedom-research', 'sector-overview', 'thesis-tracker', 'earnings-preview', 'morning-note', 'finfreedom-portfolio-risk', 'finfreedom-financial-analysis', 'finfreedom-fund-analysis', 'finfreedom-strategy-research', 'earnings-analysis', 'catalyst-calendar', 'idea-generation', 'investskill-bear-case', 'investskill-fact-check', 'investskill-financial-report-analyst']) assert.ok(names.includes(name), `missing ${name}: ${names}`);
  } finally { await provider.dispose(); }
});
