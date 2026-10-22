// One measurement of the audit pipeline on this repository's own diff.
//
//   node tools/probe.mjs [--spec <pipeline.yaml>] [--severity medium] [--prev findings.json]
//
// It runs the pipeline locally (no GitHub, no pull request) and reports how many
// of the planted weaknesses the run found. The ground truth comes from the
// `# VULN CWE-xxx` markers in `src/` — the same source `tools/ground_truth.py`
// reads, so the two tools cannot disagree about what was planted.
//
// The planted set is eleven weaknesses. A single review pass finds eight of
// them and which eight changes from run to run; the second pass inside the
// pipeline is told what the first pass found and goes looking for the gaps.
//
// Needs the pipeline runtime built next to this checkout:
//   PIPELINE_RUNTIME=/path/to/.wt-am/packages/pipeline-runtime/dist
// and MINIMAX_API_KEY in the environment.

import { readFileSync, writeFileSync } from 'node:fs';

const RUNTIME = process.env.PIPELINE_RUNTIME
  ?? '/home/vladimirmyshkovski/Programs/TypeScript/.wt-am/packages/pipeline-runtime/dist';
const YAML_DIR = process.env.PIPELINE_YAML_DIR
  ?? '/home/vladimirmyshkovski/Programs/TypeScript/.wt-am/node_modules/yaml/dist';

const args = process.argv.slice(2);
const arg = (name, fallback) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 && args[i + 1] ? args[i + 1] : fallback;
};

const SPEC_FILE = arg('spec',
  '/home/vladimirmyshkovski/Programs/TypeScript/github-workflows/pipelines/code-review-security-audit/pipeline.yaml');
const DIFF_FILE = arg('diff', '/tmp/opencode/diff.txt');
const SEVERITY = arg('severity', 'medium');
const PREV = arg('prev', null);
const OUT = arg('out', null);
const RAW = arg('raw', null);

const { runPipelineV2 } = await import(`${RUNTIME}/stages.js`);
const { MiniMaxProvider } = await import(`${RUNTIME}/adapters/minimax.js`);
const { LLMProviderRegistry } = await import(`${RUNTIME}/provider-registry.js`);
const { StaticPricingResolver } = await import(`${RUNTIME}/pricing.js`);
const { createModelResolver } = await import(`${RUNTIME}/model-resolver.js`);
const YAML = (await import(`${YAML_DIR}/index.js`)).default;

const SPEC = YAML.parse(readFileSync(SPEC_FILE, 'utf-8'));
const DIFF = readFileSync(DIFF_FILE, 'utf-8');

if (PREV) {
  const prev = JSON.parse(readFileSync(PREV, 'utf-8'));
  const stage = SPEC.stages.find((s) => s.id === 'gap_review');
  const list = prev
    .map((f) => `- ${f.file}:${f.line ?? '?'} ${f.cwe_id ?? ''} ${f.description ?? ''}`.trim())
    .join('\n');
  stage.prompt +=
    `\n\nA previous pass of this same review already reported the weaknesses below.\n` +
    `Do NOT report them again — not with a different line number, not with a different\n` +
    `CWE id, not with a different wording. Your job is the gaps.\n\n` +
    `Already reported:\n${list}\n`;
}

const provider = new MiniMaxProvider({ apiKey: process.env.MINIMAX_API_KEY });
const result = await runPipelineV2({
  spec: SPEC,
  inputs: { code_diff: DIFF, language: 'typescript', severity_threshold: SEVERITY, focus_area: 'security' },
  deps: {
    provider,
    registry: new LLMProviderRegistry([provider]),
    pricing: new StaticPricingResolver({ 'MiniMax-M3': { input: 0.000002, output: 0.000008 } }),
    modelResolver: createModelResolver({ hardcodedDefault: 'MiniMax-M3' }),
    fetchSkill: async () => null,
    getCurrentAgentId: () => '0xcaller',
    getPipelineAuthorId: () => '0xauthor',
    isLocal: true,
  },
});

const scan = JSON.parse(result.outputs.pattern_scan).candidates || [];
const deep = JSON.parse(result.outputs.deep_review).findings || [];
const rejected = JSON.parse(result.outputs.deep_review).rejected || [];
const gap = result.outputs.gap_review ? (JSON.parse(result.outputs.gap_review).findings || []) : [];

// The eleven planted weaknesses, from the markers in src/.
const TRUTH = [
  ['CWE-79', 'src/api.ts'], ['CWE-918', 'src/api.ts'], ['CWE-338', 'src/api.ts'],
  ['CWE-601', 'src/api.ts'], ['CWE-1321', 'src/api.ts'], ['CWE-1333', 'src/api.ts'],
  ['CWE-798', 'src/orders.py'], ['CWE-89', 'src/orders.py'], ['CWE-78', 'src/orders.py'],
  ['CWE-22', 'src/orders.py'], ['CWE-502', 'src/orders.py'],
];
// CWE-1321 is not in the pipeline's catalogue, so the model names the
// neighbouring class it finds instead.
const ALIAS = { 'CWE-1321': ['CWE-915'] };

const found = new Set();
const ids = [];
for (const f of [...deep, ...gap]) {
  const id = String(f.cwe_id ?? f.cwe ?? '').toUpperCase();
  ids.push(id);
  for (const [truth, file] of TRUTH) {
    const match = id === truth || (ALIAS[truth] || []).includes(id);
    if (match && String(f.file || '').includes(file)) found.add(truth);
  }
}

console.log(`  severity=${SEVERITY}  сканер: ${scan.length} кандидатов, deep_review: ${deep.length} находок, gap_review: ${gap.length} находок, отклонено: ${rejected.length}`);
console.log(`  накрыто закладок: ${found.size}/11  → ${[...found].sort().join(', ')}`);
const missing = TRUTH.map(([t]) => t).filter((t) => !found.has(t));
console.log(`  не накрыто: ${missing.join(', ') || '—'}`);
console.log(`  коды: ${ids.join(' ')}`);

// A finding at a line the other pass already reported is a duplicate in the
// reader's eye, even when the class differs.
const key = (f) => `${f.file}::${f.line ?? ''}`;
const deepKeys = new Set(deep.map(key));
const clash = gap.filter((f) => deepKeys.has(key(f)));
if (gap.length) {
  console.log(`  второе проходом повторил строку первого: ${clash.length ? clash.map((f) => `${f.file}:${f.line} ${f.cwe_id}`).join(', ') : '—'}`);
  console.log(`  находок всего: ${deep.length + gap.length}`);
}

if (OUT) {
  writeFileSync(OUT, JSON.stringify({ deep, gap }, null, 2));
  console.log(`  находки сохранены: ${OUT}`);
}
if (RAW) {
  writeFileSync(RAW, JSON.stringify(result.outputs, null, 2));
  console.log(`  сырые выходы сохранены: ${RAW}`);
}
