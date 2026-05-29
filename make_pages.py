#!/usr/bin/env python3
"""Build the reading-room pages from PDFs in texts/.

- Writes a public index.html (just a list of titles + links) to the repo root.
- Writes one source page per PDF into _build/src/<slug>.html, with the PDF
  embedded inline as base64. build.sh then ENCRYPTS each of those with the
  class password, so the raw PDF never sits at a public URL.
"""
import base64, glob, html, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
TEXTS = os.path.join(ROOT, "texts")
SRC = os.path.join(ROOT, "_build", "src")
os.makedirs(SRC, exist_ok=True)


def clean_title(fn):
    t = re.sub(r"\.pdf$", "", fn, flags=re.I)
    t = re.sub(r"\.docx", "", t, flags=re.I)
    t = re.sub(r"\s*-\s*AmLit Curriculum Hub", "", t, flags=re.I)
    t = re.sub(r"\([^)]*\)", "", t)          # drop "(Book Text)" etc.
    t = t.split(",")[0]                       # drop ", (Unit 2), _F _L" trailing cruft
    return re.sub(r"\s+", " ", t).strip(" -_")


def slugify(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


VIEWER = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{title}</title>
<style>
 html,body{{margin:0;height:100%}}
 body{{display:flex;flex-direction:column;font-family:-apple-system,system-ui,sans-serif}}
 .bar{{flex:0 0 auto;background:#7a2e2e;color:#fff;padding:.55rem 1rem;display:flex;align-items:center;gap:1rem}}
 .bar a{{color:#fff;text-decoration:none;border:1px solid rgba(255,255,255,.55);padding:.25rem .65rem;border-radius:6px;font-size:.85rem}}
 .bar b{{font-size:1rem}}
 iframe{{flex:1 1 auto;border:0;width:100%}}
</style></head>
<body>
 <div class="bar"><a href="index.html">&larr; All texts</a><b>{title}</b></div>
 <iframe src="data:application/pdf;base64,{b64}" title="{title}"></iframe>
</body></html>
"""

INDEX_HEAD = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Class Texts — Reading Room</title>
<style>
 :root{--ink:#1f2933;--muted:#5a6672;--accent:#7a2e2e;--bg:#f7f4ee;--card:#fff;--line:#e3ddd2}
 *{box-sizing:border-box}
 body{margin:0;font-family:Georgia,'Times New Roman',serif;background:var(--bg);color:var(--ink);line-height:1.6}
 .wrap{max-width:760px;margin:0 auto;padding:3rem 1.5rem 5rem}
 header{border-bottom:2px solid var(--accent);padding-bottom:1.25rem;margin-bottom:2rem}
 h1{font-size:2rem;margin:0 0 .25rem;letter-spacing:.5px}
 .subtitle{color:var(--muted);font-style:italic;margin:0}
 .note{background:#fdf6e3;border:1px solid var(--line);border-left:4px solid var(--accent);padding:.9rem 1.1rem;border-radius:6px;font-size:.95rem;color:var(--muted);margin-bottom:2rem}
 ul.texts{list-style:none;padding:0;margin:0}
 ul.texts li{margin:0 0 1rem}
 a.text-card{display:flex;align-items:center;gap:1rem;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1.1rem 1.3rem;text-decoration:none;color:var(--ink);transition:border-color .15s,transform .15s,box-shadow .15s}
 a.text-card:hover{border-color:var(--accent);transform:translateY(-1px);box-shadow:0 4px 14px rgba(0,0,0,.06)}
 .lock{font-size:.7rem;font-weight:700;letter-spacing:.5px;color:#fff;background:var(--accent);padding:.3rem .5rem;border-radius:5px;flex-shrink:0;font-family:-apple-system,system-ui,sans-serif}
 .text-title{font-size:1.15rem;font-weight:700}
 footer{margin-top:3rem;text-align:center;color:var(--muted);font-size:.8rem;font-family:-apple-system,system-ui,sans-serif}
</style></head>
<body><div class="wrap">
<header><h1>Reading Room</h1><p class="subtitle">Texts available during this quiz</p></header>
<p class="note">Click a text to open it. You'll be asked for the password your teacher gave you.</p>
<ul class="texts">
"""

INDEX_FOOT = """</ul>
<footer>Mountain View High School · English</footer>
</div></body></html>
"""

pdfs = sorted(glob.glob(os.path.join(TEXTS, "*.pdf")))
if not pdfs:
    print("No PDFs found in texts/ — nothing to build.")

items = []
for p in pdfs:
    title = clean_title(os.path.basename(p))
    slug = slugify(title)
    with open(p, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    with open(os.path.join(SRC, slug + ".html"), "w") as f:
        f.write(VIEWER.format(title=html.escape(title), b64=b64))
    items.append((title, slug))
    print(f"  embedded {title}  ->  {slug}.html  ({len(b64)//1024} KB base64)")

rows = []
for title, slug in items:
    rows.append(
        f'  <li><a class="text-card" href="{slug}.html">'
        f'<span class="lock">LOCKED</span>'
        f'<span class="text-title">{html.escape(title)}</span></a></li>'
    )
with open(os.path.join(ROOT, "index.html"), "w") as f:
    f.write(INDEX_HEAD + "\n".join(rows) + "\n" + INDEX_FOOT)
print(f"Wrote index.html listing {len(items)} text(s).")
