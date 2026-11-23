// Verifies every built page carries the mandatory demo labels and no forbidden content.
import { readdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';

const dist = new URL('../dist/', import.meta.url).pathname;

async function htmlFiles(dir) {
  const out = [];
  for (const e of await readdir(dir, { withFileTypes: true })) {
    const p = join(dir, e.name);
    if (e.isDirectory()) out.push(...(await htmlFiles(p)));
    else if (e.name.endsWith('.html')) out.push(p);
  }
  return out;
}

const rules = [
  ['demo bar', (h) => h.includes('class="demobar"') && h.includes('Fiktive Firma')],
  ['footer disclaimer', (h) => h.includes('existiert nicht')],
  ['title suffix', (h) => /<title>[^<]*\(Demo\)<\/title>/.test(h)],
  ['no tel: links', (h) => !/href="tel:/i.test(h)],
  ['no forms', (h) => !/<form[\s>]/i.test(h)],
  ['no LocalBusiness schema', (h) => !/LocalBusiness/i.test(h)],
  ['every photo slot labelled', (h) => (h.match(/class="photo__frame/g) || []).length === (h.match(/class="photo__ki"/g) || []).length],
];

let failed = 0;
const files = await htmlFiles(dist);
for (const f of files) {
  const html = await readFile(f, 'utf8');
  for (const [name, ok] of rules) {
    if (!ok(html)) { failed++; console.error(`FAIL ${f.replace(dist, '')}: ${name}`); }
  }
}
console.log(`${files.length} pages checked, ${failed} failures`);
process.exit(failed ? 1 : 0);
