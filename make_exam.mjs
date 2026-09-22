#!/usr/bin/env node
/* Build ONE self-contained Exam Room page for a section.
 *
 * Usage: node make_exam.mjs "<Page Title>" <texts_dir> <output_html> <slips_html>
 *
 * Same premise as the quiz/research rooms (one page, no links, LockDown-safe),
 * with one difference: every student's exam PDF is INDIVIDUALLY encrypted
 * (AES-256-GCM, key derived from that student's personal password via
 * PBKDF2-SHA256/600k). The student clicks their name, types their personal
 * password, and only their own exam decrypts — a classmate's password opens
 * nothing. build-exam.sh then wraps the whole page with the class password
 * (StatiCrypt) so the roster of names is never on the public web either.
 *
 * PDFs go in <texts_dir> named:  First.LastName.pdf   (or  First.LastName - anything.pdf)
 *
 * Personal passwords live in <texts_dir>/.passwords.csv (texts/ is gitignored,
 * so they are never published). Existing entries are reused on rebuild; new
 * students get a fresh three-word password. Delete a student's row to rotate
 * their password on the next build.
 */
import { webcrypto as crypto } from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const [, , TITLE, TEXTS_DIR, OUT_HTML, SLIPS_HTML] = process.argv;
if (!SLIPS_HTML) {
  console.error('Usage: node make_exam.mjs "<Title>" <texts_dir> <output_html> <slips_html>');
  process.exit(1);
}

const WORDS = ("acorn amber anchor apple arrow aspen autumn badge bagel " +
  "balsa banjo barley basil beacon berry birch bison blaze bloom bluff brass bravo breeze brick bridge " +
  "brook bruin bubble butter cabin cactus camel candle canoe canyon carbon cedar cello chalk cherry " +
  "chess cider cinder citrus clover cobalt cocoa comet compass copper coral cotton cougar cove crane " +
  "creek cricket crimson crystal cypress daisy dapple deacon delta denim dewdrop dingo dome drift " +
  "dune eagle ember falcon feather fennel fern fiddle finch fjord flint fossil fox galaxy garnet " +
  "gecko geyser ginger glacier glade goose gourd granite grape grove gull harbor hazel heron hickory " +
  "holly honey horizon iceberg indigo iris island ivory jade jasper jetty juniper kayak kelp kiwi " +
  "lagoon lantern larch laurel lava lemon lilac lily linen lotus lunar lynx magnet magpie mango maple " +
  "marble marsh meadow mesa mint mocha molar monsoon moose moss mural myrtle nebula nectar newt noble " +
  "nutmeg oasis ocean olive onyx opal orbit orchid osprey otter owl oyster palm panda pantry papaya " +
  "parka pebble pecan pelican penguin peony pepper petal pewter pine pistachio planet plum pollen " +
  "pond poplar poppy prairie prism pueblo puffin pumpkin quail quartz quill quilt raccoon raft rain " +
  "raven reed ridge river robin rocket rowan ruby saffron sage salmon sandal sapphire scallop scout " +
  "sequoia shale shore sierra silver sleet slope smelt snow solar sonnet sorrel spark sparrow spruce " +
  "squash starling steam stone stork storm summit sunda sunflower swan sycamore taffy talon tamarind " +
  "tangelo teal tempo terrace thistle thunder tiger timber topaz totem toucan trellis trout truffle " +
  "tulip tundra turnip umber valley vanilla velvet violet vista wagon walnut wander willow winter " +
  "wren yarrow yonder zephyr zinnia").split(/\s+/);

function newPassword() {
  const pick = () => WORDS[crypto.getRandomValues(new Uint32Array(1))[0] % WORDS.length];
  return `${pick()}-${pick()}-${pick()}`;
}

const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/* filename -> student display name + sort key (same convention as research rooms) */
function parseName(fn) {
  let base = fn.replace(/\.pdf$/i, "");
  if (base.includes(" - ")) base = base.split(" - ")[0];
  const parts = base.trim().split(/[.\s]+/).filter(Boolean);
  const display = parts.join(" ") || base.trim();
  const sort = parts.length >= 2
    ? parts[parts.length - 1].toLowerCase() + " " + parts[0].toLowerCase()
    : display.toLowerCase();
  return { display, sort };
}

/* ---- passwords file: reuse existing, add new, never publish (texts/ is gitignored) ---- */
const pwPath = path.join(TEXTS_DIR, ".passwords.csv");
const passwords = new Map();
if (fs.existsSync(pwPath)) {
  for (const line of fs.readFileSync(pwPath, "utf8").split("\n")) {
    const i = line.indexOf(",");
    if (i > 0) passwords.set(line.slice(0, i).trim(), line.slice(i + 1).trim());
  }
}

const PBKDF2_ITER = 600000;
async function encryptPdf(bytes, password) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const keyMaterial = await crypto.subtle.importKey("raw", new TextEncoder().encode(password), "PBKDF2", false, ["deriveKey"]);
  const key = await crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: PBKDF2_ITER, hash: "SHA-256" },
    keyMaterial, { name: "AES-GCM", length: 256 }, false, ["encrypt"]);
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, bytes));
  const blob = new Uint8Array(salt.length + iv.length + ct.length);
  blob.set(salt, 0); blob.set(iv, 16); blob.set(ct, 28);
  return Buffer.from(blob).toString("base64");
}

const pdfs = fs.readdirSync(TEXTS_DIR).filter((f) => /\.pdf$/i.test(f)).sort();
const students = pdfs.map((f) => ({ file: path.join(TEXTS_DIR, f), ...parseName(f) }))
  .sort((a, b) => a.sort.localeCompare(b.sort));

const cards = [], panels = [], datablocks = [];
let totalKb = 0;
for (let i = 0; i < students.length; i++) {
  const s = students[i];
  if (!passwords.has(s.display)) passwords.set(s.display, newPassword());
  const pw = passwords.get(s.display);
  const b64 = await encryptPdf(fs.readFileSync(s.file), pw.toLowerCase());
  totalKb += Math.floor(b64.length / 1024);
  const d = esc(s.display);
  cards.push(`<button class="card" onclick="showStudent(${i})"><span class="tag">MY EXAM</span><span class="title">${d}</span></button>`);
  panels.push(`<div class="student" id="student-${i}">
<button class="back" onclick="showPicker()">&larr; All students</button>
<h2 class="who">${d}</h2>
<p class="hint">Type your personal password to open your exam. Only your own password will work.</p>
<div class="pwrow"><input type="password" id="pw-${i}" placeholder="your personal password" autocomplete="off"
 onkeydown="if(event.key==='Enter')openExam(${i})"><button class="go" id="go-${i}" onclick="openExam(${i})">Open</button></div>
<p class="err" id="err-${i}"></p>
</div>
<div class="viewer" id="v-${i}"><div class="vbar"><button onclick="showStudent(${i})">&larr; Back</button><b>${d} &mdash; ${esc(TITLE)}</b></div><iframe id="f-${i}" title="${d}"></iframe></div>`);
  datablocks.push(`<script type="text/plain" id="d-${i}">${b64}</script>`);
  console.log(`    ${s.display}`);
}

const picker = students.length
  ? `<div id="picker">\n${cards.join("\n")}\n</div>`
  : `<div id="picker"><div class="empty">No exams have been added yet.</div></div>`;

const page = `<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>${esc(TITLE)}</title>
<style>
 :root{--ink:#1f2933;--muted:#5a6672;--accent:#2e4a7a;--bg:#f4f6f9;--card:#fff;--line:#dde3ea;--bad:#a13030}
 *{box-sizing:border-box}
 body{margin:0;font-family:'Cabin',sans-serif;background:var(--bg);color:var(--ink);line-height:1.6}
 .wrap{max-width:760px;margin:0 auto;padding:3rem 1.5rem 5rem}
 header{border-bottom:2px solid var(--accent);padding-bottom:1.25rem;margin-bottom:2rem}
 h1{font-size:2rem;margin:0 0 .25rem;letter-spacing:.5px}
 .subtitle{color:var(--muted);font-style:italic;margin:0}
 .note{background:#eef3fb;border:1px solid var(--line);border-left:4px solid var(--accent);padding:.9rem 1.1rem;border-radius:6px;font-size:.95rem;color:var(--muted);margin-bottom:2rem}
 .card{display:flex;align-items:center;gap:1rem;width:100%;text-align:left;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1.1rem 1.3rem;margin:0 0 1rem;cursor:pointer;font-family:inherit;color:var(--ink)}
 .card:hover{border-color:var(--accent);box-shadow:0 4px 14px rgba(0,0,0,.06)}
 .tag{font-size:.7rem;font-weight:700;letter-spacing:.5px;color:#fff;background:var(--accent);padding:.3rem .5rem;border-radius:5px;white-space:nowrap}
 .title{font-size:1.15rem;font-weight:700}
 .who{font-size:1.4rem;margin:.25rem 0 .5rem}
 .hint{color:var(--muted);font-size:.95rem;margin:.25rem 0 1rem}
 .pwrow{display:flex;gap:.6rem}
 .pwrow input{flex:1;font-family:inherit;font-size:1.05rem;padding:.7rem .9rem;border:1px solid var(--line);border-radius:8px;background:var(--card)}
 .pwrow input:focus{outline:2px solid var(--accent)}
 .go{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:.7rem 1.4rem;font-family:inherit;font-size:1rem;font-weight:700;cursor:pointer}
 .go[disabled]{opacity:.55;cursor:wait}
 .err{color:var(--bad);font-weight:700;min-height:1.4em;margin:.6rem 0 0}
 .back{background:transparent;border:1px solid var(--line);color:var(--muted);padding:.45rem .8rem;border-radius:6px;font-size:.85rem;cursor:pointer;font-family:inherit;margin-bottom:1.25rem}
 .back:hover{border-color:var(--accent);color:var(--accent)}
 .empty{text-align:center;color:var(--muted);font-style:italic;padding:2.5rem 1rem;border:2px dashed var(--line);border-radius:10px}
 .student{display:none}
 footer{margin-top:3rem;text-align:center;color:var(--muted);font-size:.8rem}
 .viewer{position:fixed;inset:0;background:#525659;display:none;flex-direction:column;z-index:50}
 .vbar{flex:0 0 auto;background:var(--accent);color:#fff;padding:.55rem 1rem;display:flex;align-items:center;gap:1rem}
 .vbar button{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.55);padding:.3rem .7rem;border-radius:6px;font-size:.9rem;cursor:pointer;font-family:inherit}
 .vbar b{font-size:1rem}
 .viewer iframe{flex:1 1 auto;border:0;width:100%;background:#525659}
</style></head>
<body><div class="wrap">
<header><h1>${esc(TITLE)}</h1><p class="subtitle">Exam Room</p></header>
<p class="note">Click your name, then type your <b>personal password</b> (on the slip you were given) to open your exam. Your password only opens your own exam.</p>
${picker}
${panels.join("\n")}
${datablocks.join("\n")}
<script>
function hideAll(){
  document.getElementById('picker').style.display='none';
  var st=document.getElementsByClassName('student');
  for(var i=0;i<st.length;i++)st[i].style.display='none';
  var vw=document.getElementsByClassName('viewer');
  for(var j=0;j<vw.length;j++)vw[j].style.display='none';
}
function showPicker(){hideAll();document.getElementById('picker').style.display='block';window.scrollTo(0,0);}
function showStudent(i){hideAll();var p=document.getElementById('student-'+i);p.style.display='block';
  document.getElementById('err-'+i).textContent='';window.scrollTo(0,0);
  var inp=document.getElementById('pw-'+i);inp.value='';setTimeout(function(){inp.focus();},50);}
async function openExam(i){
  var err=document.getElementById('err-'+i),go=document.getElementById('go-'+i),f=document.getElementById('f-'+i);
  var pw=document.getElementById('pw-'+i).value.trim().toLowerCase();
  if(!pw){err.textContent='Please type your password.';return;}
  err.textContent='';go.disabled=true;go.textContent='Opening\\u2026';
  try{
    if(!f.dataset.loaded){
      var raw=atob(document.getElementById('d-'+i).textContent.trim());
      var all=new Uint8Array(raw.length);
      for(var k=0;k<raw.length;k++)all[k]=raw.charCodeAt(k);
      var salt=all.slice(0,16),iv=all.slice(16,28),ct=all.slice(28);
      var km=await crypto.subtle.importKey('raw',new TextEncoder().encode(pw),'PBKDF2',false,['deriveKey']);
      var key=await crypto.subtle.deriveKey({name:'PBKDF2',salt:salt,iterations:${PBKDF2_ITER},hash:'SHA-256'},km,{name:'AES-GCM',length:256},false,['decrypt']);
      var pdf=await crypto.subtle.decrypt({name:'AES-GCM',iv:iv},key,ct);
      f.src=window.URL.createObjectURL(new window.Blob([pdf],{type:'application/pdf'}));
      f.dataset.loaded='1';
    }
    hideAll();document.getElementById('v-'+i).style.display='flex';
  }catch(e){
    err.textContent="That password didn't work. Check your slip and try again \\u2014 only your own password opens your exam.";
  }
  go.disabled=false;go.textContent='Open';
}
</script>
<footer>Mountain View High School &middot; English</footer>
</div></body></html>
`;

fs.mkdirSync(path.dirname(OUT_HTML) || ".", { recursive: true });
fs.writeFileSync(OUT_HTML, page);

/* save passwords (only students present in this build, plus any pre-existing rows) */
const rows = [...passwords.entries()].map(([n, p]) => `${n},${p}`).join("\n") + "\n";
fs.writeFileSync(pwPath, rows);

/* printable slips — one per student, for cutting apart and handing out */
const slipCards = students.map((s) => `<div class="slip"><div class="nm">${esc(s.display)}</div>
<div class="lbl">Your personal exam password</div><div class="pw">${esc(passwords.get(s.display))}</div>
<div class="lbl">${esc(TITLE)}</div></div>`).join("\n");
fs.writeFileSync(SLIPS_HTML, `<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Password slips &mdash; ${esc(TITLE)}</title>
<style>
 body{font-family:'Cabin',sans-serif;margin:.5in;color:#1f2933}
 h1{font-size:14pt} p{font-size:10pt;color:#5a6672}
 .grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:.18in}
 .slip{border:1.5px dashed #9aa7b4;border-radius:8px;padding:.16in .2in;break-inside:avoid}
 .nm{font-weight:700;font-size:12pt}
 .lbl{font-size:8pt;color:#5a6672;margin-top:.06in}
 .pw{font-family:Menlo,monospace;font-size:12pt;font-weight:700;letter-spacing:.5px}
 @media print{h1,p{display:none}}
</style></head><body>
<h1>Password slips — ${esc(TITLE)}</h1><p>Print this page, cut apart, hand each student their slip. (This file is never published.)</p>
<div class="grid">${slipCards}</div></body></html>
`);

console.log(`  -> ${OUT_HTML}  (${students.length} student(s), ~${Math.floor(totalKb / 1024)} MB embedded)`);
console.log(`  -> ${SLIPS_HTML}  (printable password slips)`);
console.log(`  -> ${pwPath}  (passwords — gitignored, never published)`);
if (totalKb / 1024 >= 45) console.log("  !! WARNING: page is large (>45 MB). Consider splitting by period.");
