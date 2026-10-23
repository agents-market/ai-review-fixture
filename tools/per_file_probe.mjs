// One measurement of the audit pipeline: the whole diff against the diff
// file by file.
//
//   node tools/per_file_probe.mjs --mode whole|per-file [--spec PATH] [--truth PATH]
//                                 [--base main] [--head feature/large-diff]
//
// The question: does a review that sees one file at a time cover more of a
// change than a review that sees the whole change at once? One pipeline, one
// model, one prompt — the only thing that differs is the size of the diff
// handed over.
//
// Needs the pipeline runtime built next to this checkout:
//   PIPELINE_RUNTIME=/path/to/.wt-am/packages/pipeline-runtime/dist
// and MINIMAX_API_KEY in the environment.

import { execFileSync } from 'node:child_process';
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

const MODE = arg('mode', 'whole');
const SPEC_FILE = arg('spec',
  '/home/vladimirmyshkovski/Programs/TypeScript/github-workflows/pipelines/code-review-security-audit/pipeline.yaml');
const TRUTH_FILE = arg('truth', '.github/ground-truth-large.json');
const BASE = arg('base', 'main');
const HEAD = arg('head', 'origin/feature/large-diff');
const SEVERITY = arg('severity', 'medium');
const LANGUAGE = 'generic'; // what the CI run sends
const OUT = arg('out', null);

const { runPipelineV2 } = await import(`${RUNTIME}/stages.js`);
const { MiniMaxProvider } = await import(`${RUNTIME}/adapters/minimax.js`);
const { LLMProviderRegistry } = await import(`${RUNTIME}/provider-registry.js`);
const { StaticPricingResolver } = await import(`${RUNTIME}/pricing.js`);
const { createModelResolver } = await import(`${RUNTIME}/model-resolver.js`);
const YAML = (await import(`${YAML_DIR}/index.js`)).default;

const SPEC = YAML.parse(readFileSync(SPEC_FILE, 'utf-8'));
const TRUTH = JSON.parse(readFileSync(TRUTH_FILE, 'utf-8')).vulnerabilities;

const git = (...a) => execFileSync('git', a, { encoding: 'utf-8', maxBuffer: 64 * 1024 * 1024 });

const diff = git('diff', '--no-color', `${BASE}...${HEAD}`);
if (!diff.trim()) {
  console.error(`  no diff between ${BASE} and ${HEAD}`);
  process.exit(1);
}

// The diff, split into one chunk per file — the same chunks GitHub shows.
const chunks = [];
for (const part of diff.split(/^(?=diff --git )/m)) {
  if (!part.trim()) continue;
  const m = /^diff --git a\/(.+?) b\/(.+)$/m.exec(part);
  if (!m) continue;
  chunks.push({ file: m[2], text: part });
}

const provider = new MiniMaxProvider({ apiKey: process.env.MINIMAX_API_KEY });
const pricing = new StaticPricingResolver({ 'MiniMax-M3': { input: 0.000002, output: 0.000008 } });
const modelResolver = createModelResolver({ hardcodedDefault: 'MiniMax-M3' });

const deps = {
  provider,
  registry: new LLMProviderRegistry([provider]),
  pricing,
  modelResolver,
  fetchSkill: async () => null,
  getCurrentAgentId: () => '0xcaller',
  getPipelineAuthorId: () => '0xauthor',
  isLocal: true,
};

async function review(text) {
  const result = await runPipelineV2({
    spec: SPEC,
    inputs: { code_diff: text, language: LANGUAGE, severity_threshold: SEVERITY, focus_area: 'security' },
    deps,
  });
  const read = (name) => {
    if (!result.outputs[name]) return [];
    try { return JSON.parse(result.outputs[name]).findings || []; } catch { return []; }
  };
  return [...read('deep_review'), ...read('gap_review')];
}

// What the reader sees: the Action merges the stages' findings and keeps one
// comment per file, line and class.
const cweOf = (f) => String(f.cwe_id ?? f.cwe ?? '').trim().toUpperCase();
const visible = (findings) => {
  const merged = new Map();
  for (const f of findings) {
    const k = `${f.file}::${f.line ?? ''}::${cweOf(f)}`;
    if (!merged.has(k)) merged.set(k, f);
  }
  return [...merged.values()];
};

// The truth: a comment names the same weakness class on the same file.
const canon = { 'CWE-330': 'CWE-338', 'CWE-259': 'CWE-798', 'CWE-915': 'CWE-1321' };
const plantedOf = (f) => {
  const id = cweOf(f);
  const cls = canon[id] || id;
  const v = TRUTH.find((t) => t.cwe.toUpperCase() === cls && t.file === f.file);
  return v || null;
};

function report(findings, label, calls, started) {
  const seen = visible(findings);
  const found = new Map();
  for (const f of seen) {
    const v = plantedOf(f);
    if (v && !found.has(v.id)) found.set(v.id, v);
  }
  const extra = seen.filter((f) => !plantedOf(f));
  const missed = TRUTH.filter((v) => !found.has(v.id));
  const secs = ((Date.now() - started) / 1000).toFixed(0);
  console.log(`\n  ${label}`);
  console.log(`    вызовов модели: ${calls}   времени: ${secs}s   находок: ${findings.length} → комментариев: ${seen.length}`);
  console.log(`    НАЙДЕНО ${found.size}/${TRUTH.length}   лишних ${extra.length}   не найдено ${missed.length}`);
  const byFile = {};
  for (const f of seen) byFile[f.file] = (byFile[f.file] || 0) + 1;
  console.log(`    по файлам: ${Object.entries(byFile).map(([k, v]) => `${k}=${v}`).join(' ')}`);
  if (missed.length) {
    console.log(`    не найдено: ${missed.map((v) => `${v.cwe} ${v.file}:${v.line}`).join(', ')}`);
  }
  for (const f of extra) {
    console.log(`    лишний: ${f.file}:${f.line} ${cweOf(f)} — ${String(f.description ?? '').slice(0, 100)}`);
  }
  return { found: found.size, extra: extra.length, missed: missed.length, comments: seen.length, calls, secs };
}

const started = Date.now();
let findings = [];
let calls = 0;

if (MODE === 'whole') {
  findings = await review(diff);
  calls = 2; // deep_review and gap_review
} else {
  for (const chunk of chunks) {
    process.stdout.write(`    ${chunk.file} …`);
    try {
      const got = await review(chunk.text);
      calls += 2;
      findings.push(...got);
      console.log(` ${got.length} находок`);
    } catch (e) {
      console.log(` ОШИБКА: ${String(e.message).slice(0, 120)}`);
    }
    await new Promise((r) => setTimeout(r, 1500));
  }
}

const summary = report(findings, MODE === 'whole' ? 'ВЕСЬ ДИФФ, один вызов' : 'ПО ФАЙЛАМ', calls, started);
if (OUT) {
  writeFileSync(OUT, JSON.stringify({ mode: MODE, findings, summary }, null, 2));
  console.log(`\n  находки сохранены: ${OUT}`);
}
