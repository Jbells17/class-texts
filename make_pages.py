#!/usr/bin/env python3
"""Build ONE self-contained reading-room page from the PDFs in texts/.

Design notes (why it's built this way):
- LockDown Browser blocks page-to-page navigation, even within an allowed
  domain. So there are NO links and NO separate pages — everything lives on the
  single URL https://jbells17.github.io/class-texts/.
- Each text is shown in place via buttons that use inline onclick handlers
  (plain DOM calls, no reliance on <script> re-running after decryption).
- build.sh then encrypts this single page with the class password, producing
  the published index.html. The raw PDFs never sit at a public URL.
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
    t = re.sub(r"\([^)]*\)", "", t)
    t = t.split(",")[0]
    return re.sub(r"\s+", " ", t).strip(" -_")


HEAD = """<!DOCTYPE html>
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
 .card{display:flex;align-items:center;gap:1rem;width:100%;text-align:left;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1.1rem 1.3rem;margin:0 0 1rem;cursor:pointer;font-family:inherit;color:var(--ink)}
 .card:hover{border-color:var(--accent);box-shadow:0 4px 14px rgba(0,0,0,.06)}
 .tag{font-size:.7rem;font-weight:700;letter-spacing:.5px;color:#fff;background:var(--accent);padding:.3rem .5rem;border-radius:5px;font-family:-apple-system,system-ui,sans-serif}
 .title{font-size:1.15rem;font-weight:700}
 footer{margin-top:3rem;text-align:center;color:var(--muted);font-size:.8rem;font-family:-apple-system,system-ui,sans-serif}
 .viewer{position:fixed;inset:0;background:#525659;display:none;flex-direction:column;z-index:50}
 .vbar{flex:0 0 auto;background:var(--accent);color:#fff;padding:.55rem 1rem;display:flex;align-items:center;gap:1rem}
 .vbar button{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.55);padding:.3rem .7rem;border-radius:6px;font-size:.9rem;cursor:pointer;font-family:-apple-system,system-ui,sans-serif}
 .vbar b{font-size:1rem}
 .viewer iframe{flex:1 1 auto;border:0;width:100%;background:#525659}
</style></head>
<body><div class="wrap">
<header><h1>Reading Room</h1><p class="subtitle">Texts available during this quiz</p></header>
<p class="note">Click a text below to read it. If the reading area is blank, tell your teacher.</p>
"""

FOOT = """<footer>Mountain View High School · English</footer>
</div></body></html>
"""

pdfs = sorted(glob.glob(os.path.join(TEXTS, "*.pdf")))
if not pdfs:
    print("No PDFs found in texts/ — nothing to build.")

buttons, viewers, datablocks = [], [], []
for i, p in enumerate(pdfs):
    title = html.escape(clean_title(os.path.basename(p)))
    with open(p, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    # Button: hide picker; on first open, decode this PDF's base64 into a Blob and
    # point the iframe at a blob: URL (no data-URL size cap); show the viewer.
    onclick_open = (
        f"document.getElementById('picker').style.display='none';"
        f"var f=document.getElementById('f{i}');"
        f"if(!f.dataset.loaded){{"
        f"var s=document.getElementById('d{i}').textContent.trim();"
        f"var b=atob(s);var a=new Uint8Array(b.length);"
        f"for(var k=0;k<b.length;k++)a[k]=b.charCodeAt(k);"
        f"f.src=window.URL.createObjectURL(new window.Blob([a],{{type:'application/pdf'}}));"
        f"f.dataset.loaded='1';}}"
        f"document.getElementById('v{i}').style.display='flex';"
    )
    buttons.append(
        f'<button class="card" onclick="{onclick_open}">'
        f'<span class="tag">OPEN</span><span class="title">{title}</span></button>'
    )
    onclick_back = (
        f"document.getElementById('v{i}').style.display='none';"
        f"document.getElementById('picker').style.display='block';"
    )
    viewers.append(
        f'<div class="viewer" id="v{i}">'
        f'<div class="vbar"><button onclick="{onclick_back}">&larr; All texts</button>'
        f'<b>{title}</b></div>'
        f'<iframe id="f{i}" title="{title}"></iframe></div>'
    )
    # Base64 stored in a non-executing script block (browsers never run text/plain).
    datablocks.append(f'<script type="text/plain" id="d{i}">{b64}</script>')
    print(f"  embedded {clean_title(os.path.basename(p))}  ({len(b64)//1024} KB base64)")

page = (
    HEAD
    + '<div id="picker">\n'
    + "\n".join(buttons)
    + "\n</div>\n"
    + "\n".join(viewers)
    + "\n"
    + "\n".join(datablocks)
    + "\n"
    + FOOT
)
with open(os.path.join(SRC, "index.html"), "w") as f:
    f.write(page)
print(f"Wrote single-page reading room with {len(pdfs)} text(s).")
