#!/usr/bin/env python3
"""Build ONE self-contained reading-room page for a course, with in-page search.

Usage: make_pages.py "<Page Title>" <texts_dir> <output_html>

Design notes:
- LockDown Browser blocks page-to-page navigation AND the browser's built-in
  Cmd/Ctrl+F. So: one page, no links, and a custom search box per text.
- Each PDF is embedded as base64 (decoded to a Blob on open — avoids the ~2MB
  data-URL cap). Per-page plain text is extracted at build time (pdftotext) and
  embedded as JSON so the search box can find terms and jump to the page via the
  PDF viewer's #page=N fragment.
- StatiCrypt injects the decrypted HTML with document.write(), so the <script>
  below runs normally after the password is entered.
- In inline handlers bare `URL` means `document.URL`; the script uses window.URL.
"""
import base64, glob, html, json, os, re, subprocess, sys

title_text = sys.argv[1]
texts_dir = sys.argv[2]
out_path = sys.argv[3]
TITLE = html.escape(title_text)


def clean_title(fn):
    t = re.sub(r"\.pdf$", "", fn, flags=re.I)
    t = re.sub(r"\.docx", "", t, flags=re.I)
    t = re.sub(r"\([^)]*\)", "", t)
    t = re.split(r"\s*-\s", t)[0]  # split only on "- " so hyphenated words survive
    return re.sub(r"\s+", " ", t).strip(" -_")


def extract_pages(pdf):
    """Return a list of per-page plain text (whitespace-collapsed)."""
    try:
        r = subprocess.run(["pdftotext", "-q", pdf, "-"],
                           capture_output=True, timeout=180)
        txt = r.stdout.decode("utf-8", "ignore")
    except Exception:
        return []
    return [re.sub(r"\s+", " ", pg).strip() for pg in txt.split("\f")]


def json_for_script(obj):
    # Safe to embed inside <script>: keep "</" from closing the tag.
    return json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")


CSS = """
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
 .empty{text-align:center;color:var(--muted);font-style:italic;padding:2.5rem 1rem;border:2px dashed var(--line);border-radius:10px}
 footer{margin-top:3rem;text-align:center;color:var(--muted);font-size:.8rem;font-family:-apple-system,system-ui,sans-serif}
 .viewer{position:fixed;inset:0;background:#525659;display:none;flex-direction:column;z-index:50}
 .vbar{flex:0 0 auto;background:var(--accent);color:#fff;padding:.5rem 1rem;display:flex;align-items:center;gap:.9rem;font-family:-apple-system,system-ui,sans-serif}
 .vbar button{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.55);padding:.3rem .7rem;border-radius:6px;font-size:.9rem;cursor:pointer;white-space:nowrap}
 .vbar b{font-size:1rem;font-family:Georgia,serif;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:30vw}
 .search{flex:1 1 auto;max-width:320px;margin-left:auto;border:0;border-radius:6px;padding:.45rem .7rem;font-size:.95rem;font-family:inherit}
 .define{flex:0 0 auto;width:190px;border:0;border-radius:6px;padding:.45rem .7rem;font-size:.95rem;font-family:inherit}
 .results{display:none;position:absolute;top:46px;right:0;width:min(440px,92vw);max-height:72vh;overflow:auto;background:#fff;color:var(--ink);border-left:1px solid var(--line);border-bottom:1px solid var(--line);box-shadow:-4px 6px 20px rgba(0,0,0,.25);z-index:60;font-family:-apple-system,system-ui,sans-serif}
 .results .res{display:block;width:100%;text-align:left;background:#fff;border:0;border-bottom:1px solid var(--line);padding:.6rem .8rem;cursor:pointer;font-size:.88rem;line-height:1.45;color:var(--ink)}
 .results .res:hover{background:#f3eee5}
 .results .pg{display:inline-block;font-weight:700;color:var(--accent);margin-right:.4rem}
 .results mark{background:#ffe08a;padding:0 1px}
 .results .nores,.results .hint{padding:.8rem;color:var(--muted);font-style:italic;font-size:.85rem}
 .results .reshdr{padding:.5rem .8rem;font-size:.8rem;font-weight:700;color:var(--muted);border-bottom:1px solid var(--line);background:#faf7f1;position:sticky;top:0}
 .results .res.active{background:#fbf0d8}
 .defpop{display:none;position:absolute;top:46px;right:0;width:min(380px,92vw);max-height:62vh;overflow:auto;background:#fff;color:var(--ink);border-left:1px solid var(--line);border-bottom:1px solid var(--line);box-shadow:-4px 6px 20px rgba(0,0,0,.25);z-index:62;padding:.85rem 1rem;font-family:-apple-system,system-ui,sans-serif}
 .defpop .dword{font-weight:700;font-size:1.05rem;color:var(--accent);margin-bottom:.25rem}
 .defpop .ddef{font-size:.92rem;line-height:1.5}
 .defpop .nores,.defpop .hint{color:var(--muted);font-style:italic;font-size:.85rem}
 .defpop .findbtn{margin-top:.7rem;display:inline-block;background:var(--accent);color:#fff;border:0;border-radius:6px;padding:.4rem .7rem;font-size:.85rem;cursor:pointer;font-family:-apple-system,system-ui,sans-serif}
 .viewer iframe{flex:1 1 auto;border:0;width:100%;background:#525659}
"""

APP = r"""
<script>
(function(){
  var BLOBS={}, STATE={};
  // In LockDown Browser, fullscreen hides the toolbar/tabs and strands students.
  // The iframes already deny fullscreen; if anything still enters it, exit at once.
  document.addEventListener('fullscreenchange',function(){
    if(document.fullscreenElement){
      try{ document.exitFullscreen().catch(function(){}); }catch(e){}
    }
  });
  function blobURL(i){
    if(BLOBS[i]) return BLOBS[i];
    var s=document.getElementById('d'+i).textContent.trim();
    var b=atob(s); var a=new Uint8Array(b.length);
    for(var k=0;k<b.length;k++)a[k]=b.charCodeAt(k);
    BLOBS[i]=window.URL.createObjectURL(new window.Blob([a],{type:'application/pdf'}));
    return BLOBS[i];
  }
  function pages(i){
    var el=document.getElementById('tx'+i); if(!el) return [];
    try{return JSON.parse(el.textContent);}catch(e){return [];}
  }
  function esc(s){return s.replace(/[&<>"]/g,function(c){return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c];});}
  window.openText=function(i){
    document.getElementById('picker').style.display='none';
    var f=document.getElementById('f'+i);
    if(!f.dataset.loaded){ f.src=blobURL(i); f.dataset.loaded='1'; }
    document.getElementById('v'+i).style.display='flex';
    var q=document.getElementById('q'+i); if(q){ q.value=''; render(i,''); }
    var w=document.getElementById('w'+i); if(w){ w.value=''; }
    var dp=document.getElementById('def'+i); if(dp){ dp.style.display='none'; dp.innerHTML=''; }
    STATE[i]={matches:[],cur:-1,curPage:1,lastWord:''};
    loadDict();  // warm the dictionary in the background so the first lookup is instant
  };
  window.closeText=function(i){
    document.getElementById('v'+i).style.display='none';
    document.getElementById('picker').style.display='block';
  };
  window.gotoPage=function(i,p){
    var f=document.getElementById('f'+i);
    var u=blobURL(i)+'#page='+p;
    // A fragment-only change won't move an already-loaded PDF viewer, so force a
    // fresh load at the target page.
    f.src='about:blank';
    setTimeout(function(){ f.src=u; f.dataset.loaded='1'; }, 40);
  };
  function render(i,query){
    var panel=document.getElementById('res'+i);
    var dp=document.getElementById('def'+i); if(dp){ dp.style.display='none'; }   // one panel at a time
    var prevPage=(STATE[i]&&STATE[i].curPage)||1, lastW=(STATE[i]&&STATE[i].lastWord)||'';
    STATE[i]={matches:[],cur:-1,curPage:prevPage,lastWord:lastW};
    var q=(query||'').trim().toLowerCase();
    if(q.length<2){ panel.style.display='none'; panel.innerHTML=''; return; }
    var ps=pages(i);
    if(!ps.length){ panel.innerHTML='<div class="hint">Search isn\'t available for this text.</div>'; panel.style.display='block'; return; }
    var out=[], count=0, CAP=80;
    for(var pg=0; pg<ps.length && count<CAP; pg++){
      var text=ps[pg], low=text.toLowerCase(), pos=low.indexOf(q);
      while(pos!==-1 && count<CAP){
        var a=Math.max(0,pos-45), b=Math.min(text.length,pos+q.length+45);
        var snip=(a>0?'…':'')+esc(text.slice(a,pos))+'<mark>'+esc(text.slice(pos,pos+q.length))+'</mark>'+esc(text.slice(pos+q.length,b))+(b<text.length?'…':'');
        var mi=STATE[i].matches.length; STATE[i].matches.push(pg+1);
        out.push('<button class="res" id="r'+i+'_'+mi+'" onclick="gotoMatch('+i+','+mi+')"><span class="pg">p.'+(pg+1)+'</span>'+snip+'</button>');
        count++; pos=low.indexOf(q,pos+q.length);
      }
    }
    var n=STATE[i].matches.length;
    if(!n){ panel.innerHTML='<div class="nores">No matches for &ldquo;'+esc(query)+'&rdquo;.</div>'; panel.style.display='block'; return; }
    var hdr='<div class="reshdr" id="hdr'+i+'">'+n+(count>=CAP?'+':'')+' match'+(n===1?'':'es')+' — press Enter to step through</div>';
    panel.innerHTML=hdr+out.join('');
    panel.style.display='block';
  }
  function setActive(i,mi){
    var prev=document.querySelector('#res'+i+' .res.active'); if(prev) prev.classList.remove('active');
    var el=document.getElementById('r'+i+'_'+mi); if(el){ el.classList.add('active'); el.scrollIntoView({block:'nearest'}); }
    var hdr=document.getElementById('hdr'+i); if(hdr) hdr.textContent='Match '+(mi+1)+' of '+STATE[i].matches.length;
  }
  window.gotoMatch=function(i,mi){
    var st=STATE[i]; if(!st||!st.matches.length) return;
    st.cur=mi; var p=st.matches[mi];
    setActive(i,mi);
    if(p!==st.curPage){ gotoPage(i,p); st.curPage=p; }   // skip reload if already on that page
  };
  window.searchStep=function(i){
    var st=STATE[i]; if(!st||!st.matches.length) return;
    gotoMatch(i,(st.cur+1)%st.matches.length);           // next match, wrapping around
  };
  window.searchText=function(i){ render(i, document.getElementById('q'+i).value); };
  window.findInText=function(i,word){
    var q=document.getElementById('q'+i); if(!q) return;
    q.value=word; render(i,word);
    if(STATE[i].matches.length){ gotoMatch(i,0); }
  };
  window.findLast=function(i){ var w=STATE[i]&&STATE[i].lastWord; if(w) findInText(i,w); };

  // ---- Dictionary lookup (loaded once, on demand; same-origin file) ----
  var DICT=null, DICTP=null;
  function loadDict(){
    if(DICTP) return DICTP;
    DICTP=fetch('/class-texts/dictionary.json').then(function(r){return r.json();})
      .then(function(j){ DICT=j; return j; })
      .catch(function(){ DICT={}; return {}; });
    return DICTP;
  }
  function findDef(d,w){
    if(d[w]) return d[w];
    var t=[];
    if(w.length>3){
      if(w.slice(-2)==="'s") t.push(w.slice(0,-2));
      if(w.slice(-3)==='ies') t.push(w.slice(0,-3)+'y');
      if(w.slice(-2)==='es') t.push(w.slice(0,-2));
      if(w.slice(-1)==='s') t.push(w.slice(0,-1));
      if(w.slice(-3)==='ied') t.push(w.slice(0,-3)+'y');
      if(w.slice(-2)==='ed'){ t.push(w.slice(0,-1)); t.push(w.slice(0,-2)); }
      if(w.slice(-3)==='ing'){ t.push(w.slice(0,-3)+'e'); t.push(w.slice(0,-3)); }
      if(w.slice(-2)==='er'){ t.push(w.slice(0,-2)); t.push(w.slice(0,-1)); }
      if(w.slice(-3)==='est'){ t.push(w.slice(0,-3)); t.push(w.slice(0,-2)); }
    }
    for(var k=0;k<t.length;k++){ if(d[t[k]]) return d[t[k]]; }
    return null;
  }
  function clean(s){ return (s||'').trim().toLowerCase().replace(/[^a-z'-]/g,''); }
  window.defineWord=function(i){
    var raw=document.getElementById('w'+i).value.trim();
    var w=clean(raw);
    var pop=document.getElementById('def'+i);
    var sr=document.getElementById('res'+i); if(sr){ sr.style.display='none'; }  // one panel at a time
    if(w.length<2){ pop.style.display='none'; pop.innerHTML=''; return; }
    pop.style.display='block';
    pop.innerHTML='<div class="hint">Looking up…</div>';
    loadDict().then(function(d){
      if(clean(document.getElementById('w'+i).value)!==w) return;  // a newer keystroke won
      if(!STATE[i]) STATE[i]={matches:[],cur:-1,curPage:1,lastWord:''};
      STATE[i].lastWord=w;
      var def=findDef(d,w);
      var findBtn='<button class="findbtn" onclick="findLast('+i+')">Find &ldquo;'+esc(w)+'&rdquo; in the text →</button>';
      pop.innerHTML = (def
        ? '<div class="dword">'+esc(w)+'</div><div class="ddef">'+esc(def)+'</div>'
        : '<div class="nores">No definition found for &ldquo;'+esc(raw)+'&rdquo;.</div>') + findBtn;
    });
  };
})();
</script>
"""

HEAD = (
    '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
    '<meta name="robots" content="noindex,nofollow">\n'
    "<title>%TITLE%</title>\n<style>" + CSS + "</style></head>\n"
    '<body><div class="wrap">\n'
    "<header><h1>%TITLE%</h1><p class=\"subtitle\">Texts available during this quiz</p></header>\n"
    '<p class="note">Click a text below to read it. Inside a text, use the search box to jump to a page, or the define box to look up a word.</p>\n'
).replace("%TITLE%", TITLE)

FOOT = "<footer>Mountain View High School · English</footer>\n</div>" + APP + "\n</body></html>\n"

pdfs = sorted(glob.glob(os.path.join(texts_dir, "*.pdf")))
buttons, viewers, datablocks = [], [], []
for i, p in enumerate(pdfs):
    t = html.escape(clean_title(os.path.basename(p)))
    with open(p, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    pg = extract_pages(p)
    pages_json = json_for_script(pg)
    buttons.append(
        f'<button class="card" onclick="openText({i})">'
        f'<span class="tag">OPEN</span><span class="title">{t}</span></button>'
    )
    viewers.append(
        f'<div class="viewer" id="v{i}">'
        f'<div class="vbar"><button onclick="closeText({i})">&larr; All texts</button>'
        f'<b>{t}</b>'
        f'<input id="q{i}" class="search" type="search" placeholder="Search this text…" '
        f'oninput="searchText({i})" '
        f'onkeydown="if(event.key===\'Enter\'){{event.preventDefault();searchStep({i});}}" '
        f'autocomplete="off">'
        f'<input id="w{i}" class="define" type="search" placeholder="Define a word…" '
        f'oninput="defineWord({i})" autocomplete="off"></div>'
        f'<div class="results" id="res{i}"></div>'
        f'<div class="defpop" id="def{i}"></div>'
        f'<iframe id="f{i}" title="{t}" allow="fullscreen \'none\'"></iframe></div>'
    )
    datablocks.append(f'<script type="text/plain" id="d{i}">{b64}</script>')
    datablocks.append(f'<script type="application/json" id="tx{i}">{pages_json}</script>')
    nonblank = sum(1 for x in pg if x)
    print(f"    {clean_title(os.path.basename(p))}  ({len(b64)//1024} KB, {nonblank} pages indexed)")

if pdfs:
    picker = '<div id="picker">\n' + "\n".join(buttons) + "\n</div>\n"
else:
    picker = '<div id="picker"><div class="empty">No texts have been added yet.</div></div>\n'

page = HEAD + picker + "\n".join(viewers) + "\n" + "\n".join(datablocks) + "\n" + FOOT
os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
with open(out_path, "w") as f:
    f.write(page)
print(f"  -> {out_path}  ({len(pdfs)} text(s))")
