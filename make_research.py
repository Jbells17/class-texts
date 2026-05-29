#!/usr/bin/env python3
"""Build ONE self-contained Senior Thesis Research Room page for a section.

Usage: make_research.py "<Page Title>" <texts_dir> <output_html>

Two-level, no-navigation design (LockDown-safe, same approach as make_pages.py):
    students  ->  that student's sources  ->  the PDF opened in place.

Files are auto-grouped by student from the filename convention:

    First.LastName - Source Title.pdf

The part before the first ' - ' (space-hyphen-space) is the student; the rest is
the source title. A file with no ' - ' lands under an "Unsorted" student so it's
never silently dropped. As with the quiz rooms, each PDF is embedded as base64
and revealed in place via a blob: URL (data: URIs are capped at ~2MB), and
build-research.sh then encrypts the whole page with the class password.
"""
import base64, glob, html, os, re, sys

title_text = sys.argv[1]
texts_dir = sys.argv[2]
out_path = sys.argv[3]
TITLE = html.escape(title_text)

HEAD = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{title}</title>
<style>
 :root{{--ink:#1f2933;--muted:#5a6672;--accent:#2e4a7a;--bg:#f4f6f9;--card:#fff;--line:#dde3ea}}
 *{{box-sizing:border-box}}
 body{{margin:0;font-family:Georgia,'Times New Roman',serif;background:var(--bg);color:var(--ink);line-height:1.6}}
 .wrap{{max-width:760px;margin:0 auto;padding:3rem 1.5rem 5rem}}
 header{{border-bottom:2px solid var(--accent);padding-bottom:1.25rem;margin-bottom:2rem}}
 h1{{font-size:2rem;margin:0 0 .25rem;letter-spacing:.5px}}
 .subtitle{{color:var(--muted);font-style:italic;margin:0}}
 .note{{background:#eef3fb;border:1px solid var(--line);border-left:4px solid var(--accent);padding:.9rem 1.1rem;border-radius:6px;font-size:.95rem;color:var(--muted);margin-bottom:2rem}}
 .who{{font-size:1.4rem;margin:.25rem 0 1.25rem}}
 .card{{display:flex;align-items:center;gap:1rem;width:100%;text-align:left;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1.1rem 1.3rem;margin:0 0 1rem;cursor:pointer;font-family:inherit;color:var(--ink)}}
 .card:hover{{border-color:var(--accent);box-shadow:0 4px 14px rgba(0,0,0,.06)}}
 .tag{{font-size:.7rem;font-weight:700;letter-spacing:.5px;color:#fff;background:var(--accent);padding:.3rem .5rem;border-radius:5px;font-family:-apple-system,system-ui,sans-serif;white-space:nowrap}}
 .title{{font-size:1.15rem;font-weight:700}}
 .count{{margin-left:auto;font-size:.8rem;color:var(--muted);font-family:-apple-system,system-ui,sans-serif}}
 .back{{background:transparent;border:1px solid var(--line);color:var(--muted);padding:.45rem .8rem;border-radius:6px;font-size:.85rem;cursor:pointer;font-family:-apple-system,system-ui,sans-serif;margin-bottom:1.25rem}}
 .back:hover{{border-color:var(--accent);color:var(--accent)}}
 .empty{{text-align:center;color:var(--muted);font-style:italic;padding:2.5rem 1rem;border:2px dashed var(--line);border-radius:10px}}
 .student{{display:none}}
 footer{{margin-top:3rem;text-align:center;color:var(--muted);font-size:.8rem;font-family:-apple-system,system-ui,sans-serif}}
 .viewer{{position:fixed;inset:0;background:#525659;display:none;flex-direction:column;z-index:50}}
 .vbar{{flex:0 0 auto;background:var(--accent);color:#fff;padding:.55rem 1rem;display:flex;align-items:center;gap:1rem}}
 .vbar button{{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.55);padding:.3rem .7rem;border-radius:6px;font-size:.9rem;cursor:pointer;font-family:-apple-system,system-ui,sans-serif}}
 .vbar b{{font-size:1rem}}
 .viewer iframe{{flex:1 1 auto;border:0;width:100%;background:#525659}}
</style></head>
<body><div class="wrap">
<header><h1>{title}</h1><p class="subtitle">Your saved research sources</p></header>
<p class="note">Click your name, then click a source to read it.</p>
""".format(title=TITLE)

FOOT = """<footer>Mountain View High School · English</footer>
</div></body></html>
"""

SCRIPT = """
<script>
function hideAll(){
  document.getElementById('picker').style.display='none';
  var st=document.getElementsByClassName('student');
  for(var i=0;i<st.length;i++)st[i].style.display='none';
  var vw=document.getElementsByClassName('viewer');
  for(var j=0;j<vw.length;j++)vw[j].style.display='none';
}
function showPicker(){hideAll();document.getElementById('picker').style.display='block';window.scrollTo(0,0);}
function showStudent(id){hideAll();document.getElementById(id).style.display='block';window.scrollTo(0,0);}
function openSrc(fid){
  hideAll();
  var f=document.getElementById('f'+fid);
  if(!f.dataset.loaded){
    var s=document.getElementById('d'+fid).textContent.trim();
    var b=atob(s);var a=new Uint8Array(b.length);
    for(var k=0;k<b.length;k++)a[k]=b.charCodeAt(k);
    f.src=window.URL.createObjectURL(new window.Blob([a],{type:'application/pdf'}));
    f.dataset.loaded='1';
  }
  document.getElementById('v'+fid).style.display='flex';
}
</script>
"""


def parse(fn):
    """-> (student_key, student_display, sort_key, source_title)"""
    base = re.sub(r"\.pdf$", "", fn, flags=re.I)
    base = re.sub(r"\.docx", "", base, flags=re.I)
    if " - " in base:
        namepart, titlepart = base.split(" - ", 1)
    else:
        namepart, titlepart = "Unsorted", base
    namepart = namepart.strip()
    title = re.sub(r"\s+", " ", titlepart).strip(" -_") or "Untitled source"
    parts = [p for p in re.split(r"[.\s]+", namepart) if p]
    display = " ".join(parts) if parts else namepart
    if namepart.lower() == "unsorted":
        sort_key = ("zzzz", "")           # always last
    elif len(parts) >= 2:
        sort_key = (parts[-1].lower(), parts[0].lower())   # by last name, then first
    else:
        sort_key = (namepart.lower(), "")
    return namepart, display, sort_key, title


pdfs = sorted(glob.glob(os.path.join(texts_dir, "*.pdf")))

# group by student
students = {}   # key -> {"display":..., "sort":..., "sources":[(title, path)]}
for p in pdfs:
    key, display, sort_key, title = parse(os.path.basename(p))
    s = students.setdefault(key, {"display": display, "sort": sort_key, "sources": []})
    s["sources"].append((title, p))

ordered = sorted(students.values(), key=lambda s: s["sort"])

picker_buttons, panels, viewers, datablocks = [], [], [], []
fid = 0
total_kb = 0
for sidx, s in enumerate(ordered):
    disp = html.escape(s["display"])
    n = len(s["sources"])
    picker_buttons.append(
        f'<button class="card" onclick="showStudent(\'student-{sidx}\')">'
        f'<span class="tag">VIEW</span><span class="title">{disp}</span>'
        f'<span class="count">{n} source{"s" if n != 1 else ""}</span></button>'
    )
    src_buttons = []
    for title, p in sorted(s["sources"], key=lambda x: x[0].lower()):
        t = html.escape(title)
        with open(p, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        total_kb += len(b64) // 1024
        src_buttons.append(
            f'<button class="card" onclick="openSrc({fid})">'
            f'<span class="tag">OPEN</span><span class="title">{t}</span></button>'
        )
        viewers.append(
            f'<div class="viewer" id="v{fid}">'
            f'<div class="vbar"><button onclick="showStudent(\'student-{sidx}\')">&larr; {disp}</button>'
            f'<b>{t}</b></div>'
            f'<iframe id="f{fid}" title="{t}"></iframe></div>'
        )
        datablocks.append(f'<script type="text/plain" id="d{fid}">{b64}</script>')
        fid += 1
    panels.append(
        f'<div class="student" id="student-{sidx}">'
        f'<button class="back" onclick="showPicker()">&larr; All students</button>'
        f'<h2 class="who">{disp}</h2>' + "\n".join(src_buttons) + "</div>"
    )
    print(f"    {s['display']}  ({n} source{'s' if n != 1 else ''})")

if ordered:
    picker = '<div id="picker">\n' + "\n".join(picker_buttons) + "\n</div>\n"
else:
    picker = '<div id="picker"><div class="empty">No research has been added yet.</div></div>\n'

page = (HEAD + picker + "\n".join(panels) + "\n"
        + "\n".join(viewers) + "\n" + "\n".join(datablocks) + "\n" + SCRIPT + FOOT)
os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
with open(out_path, "w") as f:
    f.write(page)

print(f"  -> {out_path}  ({len(ordered)} student(s), {fid} source(s), ~{total_kb//1024} MB embedded)")
if total_kb // 1024 >= 45:
    print("  !! WARNING: page is large (>45 MB). Consider splitting this section "
          "or trimming large PDFs; GitHub rejects any single file over 100 MB.")
