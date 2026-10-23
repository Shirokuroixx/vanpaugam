import re, os, sys, hashlib, html, shutil, json
import xml.etree.ElementTree as ET
from urllib.parse import unquote

SRC, OUT, CSS = sys.argv[1], sys.argv[2], sys.argv[3]
SITE = "https://vanpaugam.com"
NS = {"content":"http://purl.org/rss/1.0/modules/content/","excerpt":"http://wordpress.org/export/1.2/excerpt/",
      "wp":"http://wordpress.org/export/1.2/","dc":"http://purl.org/dc/elements/1.1/"}
IG="https://www.instagram.com/vanpaugam/"; FB="https://www.facebook.com/vanpaugam"
SP="https://open.spotify.com/user/925qp40lrceautk2wzvnkdmwq"
HERO="/img/e0b5460d12093f.jpg"

for p in os.listdir(OUT):
    if p not in ("img",".git",".netlify","_build","netlify","netlify.toml"): shutil.rmtree(os.path.join(OUT,p),ignore_errors=True) if os.path.isdir(os.path.join(OUT,p)) else os.remove(os.path.join(OUT,p))

images={}
import json as _json
_RP=os.path.join(os.path.dirname(os.path.abspath(__file__)),"img-renames.json")
RENAMES=_json.load(open(_RP)) if os.path.exists(_RP) else {}
_REN_RE=re.compile("|".join(re.escape(k) for k in sorted(RENAMES,key=len,reverse=True))) if RENAMES else None
def ren_img(t): return _REN_RE.sub(lambda m:RENAMES[m.group(0)],t) if _REN_RE else t
def local_img(url):
    url=url.replace("http://","https://").split("?")[0]
    if url not in images:
        ext=os.path.splitext(unquote(url.rsplit("/",1)[-1]))[1].lower()
        if ext not in (".jpg",".jpeg",".png",".gif",".webp",".jfif",".svg"): ext=".jpg"
        images[url]="/img/"+hashlib.sha1(url.encode()).hexdigest()[:14]+ext
    return images[url]
ATTR_D=re.compile(r'\s(?:data-[a-z0-9-]+|class|id|style|aria-hidden)\s*=\s*"[^"]*"',re.S)
ATTR_S=re.compile(r"\s(?:data-[a-z0-9-]+|class|id|style|aria-hidden)\s*=\s*'[^']*'",re.S)
IMG_RE=re.compile(r'https?://images\.squarespace-cdn\.com/[^"\'\s)>]+')

def clean(body):
    body=re.sub(r"<style.*?</style>","",body,flags=re.S)
    def cap(m):
        inner=m.group(1).strip(); txt=re.sub(r"<[^>]+>","",inner).strip()
        return f"<figure>{re.sub(r'\\s*[^<>]*$','',inner)}<figcaption>{html.escape(txt)}</figcaption></figure>"
    body=re.sub(r"\[caption[^\]]*\](.*?)\[/caption\]",cap,body,flags=re.S)
    def embedly(m):
        src=html.unescape(m.group(1))
        y=re.search(r"youtube\.com%2Fembed%2F([A-Za-z0-9_-]{6,})",src) or re.search(r"youtube\.com/embed/([A-Za-z0-9_-]{6,})",src)
        return f'<div class="video"><iframe src="https://www.youtube.com/embed/{y.group(1)}" loading="lazy" allowfullscreen title="Video"></iframe></div>' if y else m.group(0)
    body=re.sub(r'<iframe[^>]*src="([^"]*embedly[^"]*)"[^>]*></iframe>',embedly,body)
    body=re.sub(r'(<iframe[^>]*src=")//',r'\1https://',body)
    body=ATTR_D.sub('',body)
    body=ATTR_S.sub('',body)
    body=re.sub(r"\s(?:data-[a-z0-9-]+)(?=[\s>])","",body)
    # wrap bare video iframes so they get a 16:9 frame
    body=re.sub(r'(?<!<div class="video">)(<iframe[^>]*(?:youtube|vimeo|player)[^>]*></iframe>)',
                r'<div class="video">\1</div>',body)
    body=re.sub(r'<div class="video"><div class="video">(.*?)</div></div>',r'<div class="video">\1</div>',body,flags=re.S)
    # drop wrappers left empty by Squarespace layout markup
    for _ in range(8):
        body=re.sub(r"<(div|section|article|span|p)(?:\s[^>]*)?>\s*</\1>","",body)
    body=re.sub(r'<a href="https://vanpaugam.com/blog\?format=rss"[^>]*>Blog RSS</a>',"",body)
    body=re.sub(r"https?://(www\.)?vanpaugam(\.squarespace)?\.com/","/",body)
    body=re.sub(r"<(div|section|article)>\s*</\1>","",body)
    body=re.sub(r"<(/?)h1(\s|>)",r"<\1h2\2",body)
    body=re.sub(r"<h3[^>]*>\s*AUTHOR\s*</h3>.*$","",body,flags=re.S|re.I)
    return IMG_RE.sub(lambda m: local_img(m.group(0)),body)

NAV=[("/about-van-paugam","About"),("/somehow-city-pop-book","The Book"),("/blog","Writing"),("/blog/2020/10/19/the-top-10-city-pop-albums","Top 10"),
     ("/podcast","Podcast"),("/new-music","New Music"),("/buy-vinyl","Buy Vinyl"),("/latest-news","News"),("/contact","Contact")]

NAV_JP={"About":"略歴","The Book":"書籍","Writing":"記事","Top 10":"名盤","Podcast":"番組","New Music":"新曲","Buy Vinyl":"レコード","News":"情報","Contact":"連絡"}

with open(os.path.join(os.path.dirname(__file__),"social.html"),encoding="utf-8") as social_file:
    SOCIAL_HTML=social_file.read().strip()

def head(path,title,desc,img,date):
    canon=SITE+path
    ld=""
    if date:
        ld=('<script type="application/ld+json">{"@context":"https://schema.org","@type":"BlogPosting","headline":'
            +json.dumps(title)+f',"datePublished":"{date}","author":{{"@type":"Person","name":"Van Paugam"}},"mainEntityOfPage":"{canon}"'
            +(f',"image":"{SITE}{img}"' if img else "")+'}</script>')
    nav="".join(f'<a href="{u}" data-jp="{NAV_JP.get(n,"")}"{" aria-current=\"page\"" if path==u or (u!="/" and path.startswith(u+"/")) else ""}>{n}</a>' for u,n in NAV)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — Van Paugam</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:site_name" content="Van Paugam"><meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{canon}">
<meta property="og:type" content="{'article' if date else 'website'}">{f'<meta property="og:image" content="{SITE}{img}">' if img else ''}
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@400;500;700&family=Zen+Old+Mincho:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css"><script src="/img/kitsune-cursor.js" defer></script>{ld}
<script>try{{var t=localStorage.getItem("vp-theme");if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
</head><body>
<header class="site-head"><div class="wrap"><a class="mark" href="/">VAN PAUGAM</a><button class="nav-btn" type="button" aria-expanded="false" aria-controls="site-nav"><span class="nav-ico" aria-hidden="true"><i></i><i></i><i></i></span><span class="nav-lbl">Menu</span></button><nav class="site-nav" id="site-nav">{nav}{SOCIAL_HTML}<button class="theme" type="button" id="theme" aria-label="Switch between light and dark">Dark</button></nav></div></header>
<main id="main">"""

FOOT=f"""</main>
<footer class="site-foot"><div class="wrap"><!--bkp--><a class="bk-promo" href="/somehow-city-pop-book" aria-label="Somehow, City Pop: the book. Launching on Kickstarter 11 November 2026">
<span class="bkp-art"><img src="/img/book/cover.webp" alt="" width="920" height="1200" loading="lazy"><span class="bkp-obi">初版 · 1ST ED.</span></span>
<span class="bkp-copy"><span class="bkp-kick">Kickstarter · 11 Nov 2026</span><span class="bkp-title">Somehow, City Pop</span>
<span class="bkp-rot"><span>A City Pop reference guide with photographs</span><span>102 records, 1975–1990</span><span>Only 150 numbered copies</span></span></span>
<span class="bkp-cta">See the book <span aria-hidden="true">→</span></span></a>
<!--/bkp--><div class="foot-top"><div class="foot-brand"><h4>VAN PAUGAM <span class="fjp">ヴァン</span></h4><p>Japanese music, writing, and DJ sets from Chicago.</p></div>
<div class="foot-sub"><h4>The mailing list <span class="fjp">メール</span></h4>
<p>New writing, dates, and repress alerts. A few times a year.</p>
<form class="form signup" name="newsletter" method="POST" data-netlify="true" netlify-honeypot="company" action="/subscribed">
<input type="hidden" name="form-name" value="newsletter">
<p class="hp"><label>Leave this empty <input name="company" tabindex="-1"></label></p>
<div class="sub-row"><label class="vh" for="foot-email">Email address</label>
<input id="foot-email" type="email" name="email" required autocomplete="email" placeholder="you@example.com">
<button class="btn" type="submit">Join</button></div></form></div></div>
<div class="foot-grid"><div><h4>Read <span class="fjp">読む</span></h4><ul><li><a href="/blog">Writing</a></li><li><a href="/what-is-city-pop">What is City Pop?</a></li><li><a href="/somehow-city-pop-book">The book</a></li><li><a href="/latest-news">News</a></li></ul></div>
<div><h4>Listen <span class="fjp">聴く</span></h4><ul><li><a href="/podcast">Mayonaka Hour</a></li><li><a href="/buy-vinyl">Buy vinyl</a></li><li><a href="/new-music">New music</a></li><li><a href="{SP}" rel="noopener">Spotify</a></li></ul></div>
<div><h4>Contact <span class="fjp">連絡</span></h4><ul><li><a href="/contact">Booking &amp; press</a></li><li><a href="/media-kit/">Interactive media kit</a></li><li><a href="/media-kit/van-paugam-media-kit.pdf" download>Media kit PDF</a></li><li><a href="mailto:info@vanpaugam.com">info@vanpaugam.com</a></li><li><a href="{IG}" rel="me noopener">Instagram</a></li><li><a href="{FB}" rel="me noopener">Facebook</a></li></ul></div>
</div>
<p class="colophon">© Van Paugam {2026}. Chicago.</p></div></footer>
<script src="/fox.js" defer></script>
<script>(function(){{var h=document.querySelector(".nav-btn");if(!h)return;var r=document.documentElement;function set(o){{r.classList.toggle("nav-open",o);h.setAttribute("aria-expanded",o)}}
h.addEventListener("click",function(){{set(!r.classList.contains("nav-open"))}});document.addEventListener("keydown",function(e){{if(e.key==="Escape")set(false)}});
document.querySelectorAll(".site-nav a").forEach(function(a){{a.addEventListener("click",function(){{set(false)}})}});}})();</script>
<script>(function(){{var r=document.documentElement,b=document.getElementById("theme");if(!b)return;
function dark(){{return r.dataset.theme?r.dataset.theme==="dark":matchMedia("(prefers-color-scheme: dark)").matches}}
function label(){{b.textContent=dark()?"Light":"Dark"}}
label();b.addEventListener("click",function(){{r.dataset.theme=dark()?"light":"dark";
try{{localStorage.setItem("vp-theme",r.dataset.theme)}}catch(e){{}}label()}});}})();</script>
</body></html>"""

def write(path,body,title,desc,img=None,date=None):
    d=os.path.join(OUT,path.strip("/")); os.makedirs(d,exist_ok=True)
    foot=re.sub(r"<!--bkp-->.*?<!--/bkp-->","",FOOT,flags=re.S) if path=="/somehow-city-pop-book" else FOOT
    open(os.path.join(d,"index.html"),"w",encoding="utf-8").write(ren_img(head(path,title,desc,img,date)+body+foot))

def plain(s,n=165):
    s=re.sub(r"<figcaption.*?</figcaption>"," ",s or "",flags=re.S)
    s=re.sub(r"\[/?caption[^\]]*\]"," ",s)
    t=re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",s))).strip()
    return (t[:n].rsplit(" ",1)[0]+"…") if len(t)>n else t

# ---------- "buy her records" blocks on artist articles ----------
EBAY_CAMPID_A="5339222122"; AMAZON_TAG_A="citypop-20"
CDJ_A="https://www.cdjapan.co.jp/aff/click.cgi/e86NDzbdSLQ/7023/A403672/"
TATSURO=[("Circus Town",None),("Spacy",None),("Go Ahead!",None),("Moonglow",None),
 ("Ride on Time",None),("For You",None),("Melodies",None),("Big Wave",None),
 ("Pocket Music",None),("Artisan",None),("Songs (Sugar Babe)",None)]
ANRI=[("Apricot Jam",None),("Feelin'",None),("Heaven Beach",None),("Timely!!",None),
 ("Bi・Ki・Ni",None),("Coool",None),("Mystique",None),("Wave",None),("Circuit of Rainbow",None)]
RECORDS={
 "/blog/how-tatsuro-yamashita-became-the-kind-of-city-pop": ("Tatsuro Yamashita","山下達郎",TATSURO),
 "/blog/copyright-on-time-tatsuro-yamashitas-war-on-overseas-audiences": ("Tatsuro Yamashita","山下達郎",TATSURO),
 "/blog/tatsuro-yamashita-vinyl-repress-pre-order": ("Tatsuro Yamashita","山下達郎",TATSURO),
 "/blog/anri-vinyl-reissue-repress-rerelease-2023": ("Anri","杏里",ANRI),
 "/blog/who-is-miki-matsubara": ("Miki Matsubara", "松原みき", [
   ("Mayonaka no Door / Stay With Me","真夜中のドア"),
   ("Pocket Park",None),("Who Are You?",None),("Cupid",None),("Myself",None),
   ("Aya","彩"),("Revue",None),("Blue Eyes",None),("Cool Cut",None),
   ("Lady Bounce",None),("Wink",None)]),
}
def shop_links(artist,title):
    from urllib.parse import quote
    q=f"{artist} {title}"
    return [("eBay",f"https://www.ebay.com/sch/i.html?_nkw={quote(q+' vinyl')}&mkcid=1&mkrid=711-53200-19255-0&campid={EBAY_CAMPID_A}&toolid=10001&customid=vanpaugam"),
            ("Amazon",f"https://www.amazon.com/s?k={quote(q+' vinyl')}&tag={AMAZON_TAG_A}"),
            ("CDJapan",CDJ_A+quote(f"searches?q={q}",safe=""))]

LEGACY=re.compile(r"<p[^>]*>(?P<in>(?:(?!</p>).)*?)</p>",re.S)
def _links(frag): return re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',frag,re.S)
def strip_legacy(seg):
    found={}
    def repl(m):
        inner=m.group("in"); t=_txt(inner); ls=_links(inner)
        if len(t)<=56 and re.match(r"(?i)^(buy|order|pre-?order|get|available|listen|stream|hmv|tower|cdjapan|\d{4}\s+remaster|remaster)", t):
            for u,_x in ls:
                if "discogs.com" in u.lower(): found.setdefault("Discogs",u)
                else: found.setdefault("Listen",u)
            return ""
        if len(ls)==1 and len(t)<=56 and (":" in t or len(t.split())<=4):
            u=ls[0][0].lower()
            if "discogs.com" in u: found.setdefault("Discogs",ls[0][0])
            elif any(k in u for k in ("lnk.to","spotify","apple","youtube","jvcmusic","tower","linkco")):
                found.setdefault("Listen",ls[0][0])
            return ""
        return m.group(0)
    return LEGACY.sub(repl,seg),found

def buy_row(artist,title,extra):
    parts=[f'<a href="{h}" target="_blank" rel="sponsored noopener">{n}</a>' for n,h in shop_links(artist,title)]
    return f'<p class="buy-row"><span class="fc">Find a copy</span>{"".join(parts)}</p>'

def link_first_img(seg,href):
    def one(m):
        if "<a" in seg[:m.start()][-120:]: return m.group(0)
        return f'<a href="{href}" target="_blank" rel="sponsored noopener">{m.group(0)}</a>'
    return re.sub(r"<img[^>]*>",one,seg,count=1)

def inline_buy(body):
    anchors=[]
    for m in re.finditer(r"<h2[^>]*>(.*?)</h2>",body,re.S):
        t=_txt(m.group(1))
        if not t or len(t)>95 or ":" in t: continue
        pm=PAIR.match(t)
        if pm and ok_pair(pm.group(1).strip(),pm.group(2).strip()): anchors.append((m.end(),pm.group(1).strip(),pm.group(2).strip()))
    if len(anchors)<3:
        anchors=[]
        for m in re.finditer(r"<p[^>]*>(.*?)</p>",body,re.S):
            t=_txt(m.group(1))
            if not t or len(t)>72 or ":" in t or t.endswith("."): continue
            pm=PAIR.match(t)
            if pm and ok_pair(pm.group(1).strip(),pm.group(2).strip()): anchors.append((m.end(),pm.group(1).strip(),pm.group(2).strip()))
    if len(anchors)<3: return body,False
    for i in range(len(anchors)-1,-1,-1):
        start,a,ti=anchors[i]
        end=anchors[i+1][0]-0 if i+1<len(anchors) else len(body)
        if i+1<len(anchors):
            nxt=anchors[i+1][0]
            end=body.rfind("<h2",start,nxt)
            if end==-1: end=body.rfind("<p",start,nxt)
            if end==-1 or end<=start: end=nxt
        seg=body[start:end]
        seg,extra=strip_legacy(seg)
        eb=shop_links(a,ti)[0][1]
        seg=link_first_img(seg,eb)
        body=body[:start]+seg+buy_row(a,ti,extra)+body[end:]
    return body,True


def ckey(x): return re.sub(r"[^a-z0-9]","",re.sub(r"\[[^\]]*\]|\([^)]*\)","",x).lower())
COVERS={ckey("Miki Matsubara"+title):f"/img/miki-matsubara-{filename}.jpg" for title,filename in [
    ("Mayonaka no Door / Stay With Me","stay-with-me"),
    ("Pocket Park","pocketpark"),("Who Are You?","whoareyou"),
    ("Cupid","cupid"),("Myself","myself"),("Aya","aya"),
    ("Revue","revue"),("Blue Eyes","blueeyes"),("Cool Cut","coolcut"),
    ("Lady Bounce","ladybounce"),("Wink","wink")
]}
def find_cover(artist,title):
    for k in (ckey(artist+title), ckey(title)):
        if k and k in COVERS: return COVERS[k]
    return None

DEADTEXT=re.compile(r"(?i)^(pre-?order|order now|price as of|rank(ed)? (on|#)|available (now|for)|out now|release date|never reissued|anri.s \d+(st|nd|rd|th) studio album)")
def artist_post(body, artist, jp, recs):
    used=[]
    # strip dead preorder / price lines
    def dead(m):
        t=_txt(m.group(1))
        return "" if (len(t)<=90 and DEADTEXT.match(t)) else m.group(0)
    body=re.sub(r"<h[2-4][^>]*>(.*?)</h[2-4]>",dead,body,flags=re.S)
    body=re.sub(r"<p[^>]*>(.*?)</p>",dead,body,flags=re.S)
    # anchor on headings naming a known album
    marks=[]
    for m in re.finditer(r"<h[2-4][^>]*>(.*?)</h[2-4]>",body,re.S):
        t=ckey(_txt(m.group(1)))
        if not t: continue
        for title,alt in recs:
            if ckey(title) and ckey(title) in t:
                marks.append((m.end(),title)); break
    seen=set(); marks=[x for x in marks if not (x[1] in seen or seen.add(x[1]))]
    for i in range(len(marks)-1,-1,-1):
        start,title=marks[i]
        end=marks[i+1][0] if i+1<len(marks) else len(body)
        if i+1<len(marks):
            e=body.rfind("<h2",start,end)
            if e>start: end=e
        seg=body[start:end]
        seg,extra=strip_legacy(seg)
        eb=shop_links(artist,title)[0][1]
        # retag any of his old product links on the cover image
        seg=re.sub(r'<a href="[^"]*(?:cdjapan|hmv|amazon|ebay)[^"]*"[^>]*>(\s*<img[^>]*>)\s*</a>',
                   lambda m: f'<a href="{eb}" target="_blank" rel="sponsored noopener">{m.group(1)}</a>', seg, flags=re.S)
        seg=link_first_img(seg,eb)
        im=re.search(r'<img[^>]+src="([^"]+)"',seg)
        if im: COVERS.setdefault(ckey(artist+title),im.group(1))
        body=body[:start]+seg+buy_row(artist,title,extra)+body[end:]
        used.append(title)
    return body, used

def discography_block(artist, jp, recs, skip):
    rest=[(t,a) for t,a in recs if t not in skip]
    if not rest: return ""
    cards=""
    for title,alt in rest:
        cov=find_cover(artist,title)
        art=(f'<img src="{cov}" alt="{html.escape(artist+" — "+title+" cover artwork",quote=True)}" loading="lazy">' if cov
             else f'<div class="sleeve-ph"><span>{html.escape(title)}</span></div>')
        eb=shop_links(artist,title)[0][1]
        shops="".join(f'<a href="{h}" target="_blank" rel="sponsored noopener">{n}</a>' for n,h in shop_links(artist,title))
        cards+=(f'<li><a class="disc-art" href="{eb}" target="_blank" rel="sponsored noopener">{art}</a>'
                f'<h4>{html.escape(title)}{f" <span class=\'meta\'>{alt}</span>" if alt else ""}</h4>'
                f'<p class="shops">{shops}</p></li>')
    credit=('<p class="note">Cover artwork: <a href="https://miki-matsubara-45th.ponycanyon.co.jp/" target="_blank" rel="noopener">Pony Canyon</a>; '
            '<a href="https://www.jvcmusic.co.jp/flyingdog/-/Discography/A000440/VEATP-37913.html" target="_blank" rel="noopener">Victor / FlyingDog (Wink)</a>.</p>'
            if artist=="Miki Matsubara" else "")
    return (f'<div class="records"><h2 style="margin:0">The rest of the {html.escape(artist)} catalogue '
            f'<span class="jp">{jp}</span></h2><ul class="disc-grid">{cards}</ul>'
            f'{credit}'
            f'<p class="note">Each cover opens a search on that store, so you see what is in stock today. '
            f'These are affiliate links: buying through them may earn me a small commission at no extra cost to you. '
            f'As an Amazon Associate I earn from qualifying purchases.</p></div>')

TOP10="/blog/2020/10/19/the-top-10-city-pop-albums"
def top10_layout(body):
    body=re.sub(r'<div class="video">.*?</iframe></div>','',body,flags=re.S)
    rank=re.compile(r"<h2[^>]*>\s*#?\s*(\d+)\s*\.?\s*</h2>")
    ranks=list(rank.finditer(body))
    if len(ranks)<8: return body,False
    intro=body[:ranks[0].start()]
    intro=re.sub(r"<h2[^>]*>\s*The Top 10[^<]*</h2>","",intro)
    intro=re.sub(r"</?div>","",intro)
    out=[intro]; outro=""
    for i,r in enumerate(ranks):
        end=ranks[i+1].start() if i+1<len(ranks) else len(body)
        seg=body[r.end():end]
        seg=re.sub(r'<p class="buy-row">.*?</p>',"",seg,flags=re.S)
        seg=re.sub(r"</?div>","",seg)
        hm=re.search(r"<h2[^>]*>(.*?)</h2>",seg,re.S)
        if not hm: continue
        t=_txt(hm.group(1)); pm=PAIR.match(t)
        if not pm: continue
        a,ti=pm.group(1).strip(),pm.group(2).strip(); yr=pm.group(3) or ""
        if not yr:
            ym=re.search(r"\((\d{4})\)",t); yr=ym.group(1) if ym else ""
        rest=seg[hm.end():]
        im=re.search(r"<img[^>]*>",rest)
        img=im.group(0) if im else ""
        paras=re.findall(r"<p[^>]*>.*?</p>",rest,re.S)
        txt=paras[0] if paras else ""
        outro+="".join(p for p in paras[1:] if not re.match(r"<p[^>]*>\s*(Buy it on|Pre-?order|Listen)",p) and not (len(_txt(p))<70 and ":" in _txt(p) and "<a " in p))
        eb=shop_links(a,ti)[0][1]
        fig=(f'<a class="al-cover" href="{eb}" target="_blank" rel="sponsored noopener">{img}</a>' if img else "")
        out.append(f'<section class="album"><header class="al-head"><span class="rank">{int(r.group(1)):02d}</span>'
                   f'<h2><span class="al-artist">{html.escape(a)}</span><span class="al-title">{html.escape(ti)}</span>'
                   f'<span class="al-year">{yr}</span></h2></header>'
                   f'<div class="al-main">{fig}<div class="al-text">{txt}</div></div>{buy_row(a,ti,None)}</section>')
    out.append(f'<div class="al-outro">{outro}</div>')
    return "".join(out),True

LISTPOST="/blog/city-pop-top-albums-list"
LISTPOSTS=(LISTPOST,"/blog/2020/10/20/city-pop-summer")
def list_layout(body):
    body=re.sub(r'<div class="video">.*?</iframe></div>','',body,flags=re.S)
    body=re.sub(r'<p class="buy-row">.*?</p>',"",body,flags=re.S)
    heads=[]
    for m in re.finditer(r"<h2[^>]*>(.*?)</h2>",body,re.S):
        t=_txt(m.group(1)); pm=PAIR.match(t) if t else None
        if pm and ok_pair(pm.group(1).strip(),pm.group(2).strip()): heads.append((m,pm))
    if len(heads)<8:
        heads=[]
        for m in re.finditer(r"<p[^>]*>(.*?)</p>",body,re.S):
            t=_txt(m.group(1))
            if not t or len(t)>72 or ":" in t or t.endswith("."): continue
            pm=PAIR.match(t)
            if pm and ok_pair(pm.group(1).strip(),pm.group(2).strip()): heads.append((m,pm))
    if len(heads)<8: return body,False
    intro=re.sub(r"<h2[^>]*>\s*(City Pop Songs[^<]*)?</h2>","",body[:heads[0][0].start()])
    intro=re.sub(r"</?div>","",intro)
    out=[intro]; outro=""
    for i,(m,pm) in enumerate(heads):
        end=heads[i+1][0].start() if i+1<len(heads) else len(body)
        rest=re.sub(r"</?div>","",body[m.end():end])
        a,ti=pm.group(1).strip(),pm.group(2).strip(); yr=pm.group(3) or ""
        if not yr:
            ym=re.search(r"\((\d{4})\)",_txt(m.group(1))); yr=ym.group(1) if ym else ""
        im=re.search(r"<img[^>]*>",rest); img=im.group(0) if im else ""
        paras=re.findall(r"<p[^>]*>.*?</p>",rest,re.S)
        txt=paras[0] if paras else ""
        outro+="".join(p for p in paras[1:] if not re.match(r"<p[^>]*>\s*(Buy it on|Pre-?order|Listen)",p) and not (len(_txt(p))<70 and ":" in _txt(p) and "<a " in p))
        eb=shop_links(a,ti)[0][1]
        if not img:
            _c=find_cover(a,ti); img=f'<img src="{_c}" alt="">' if _c else ""
        fig=(f'<a class="al-cover" href="{eb}" target="_blank" rel="sponsored noopener">{img}</a>' if img else "")
        out.append(f'<section class="album"><header class="al-head"><span class="rank">{i+1:02d}</span>'
                   f'<h2><span class="al-artist">{html.escape(a)}</span><span class="al-title">{html.escape(ti)}</span>'
                   f'<span class="al-year">{yr}</span></h2></header>'
                   f'<div class="al-main{"" if fig else " nocover"}">{fig}<div class="al-text">{txt}</div></div>{buy_row(a,ti,None)}</section>')
    if outro: out.append(f'<div class="al-outro">{outro}</div>')
    return "".join(out),True

MORE={"/blog/2020/10/19/the-top-10-city-pop-albums":[
  ("/blog/2020/10/20/city-pop-summer","10 City Pop Songs About Summer","/img/1c88cb968d75f0.jpg"),
  ("/blog/city-pop-top-albums-list","Another Top 10 City Pop Songs List","/img/bf1d1fb833caeb.jpg")]}
def more_block(link):
    if link not in MORE: return ""
    cards="".join(f'<li><a href="{l}"><img src="{im}" alt="" loading="lazy"><span>{html.escape(t)}</span></a></li>' for l,t,im in MORE[link])
    return f'<div class="more-reads"><h2>Keep reading <span class="jp">続き</span></h2><ul>{cards}</ul></div>'

AUTO={"/blog/2020/10/19/the-top-10-city-pop-albums":"Buy these albums",
      "/blog/city-pop-top-albums-list":"Buy these albums",
      "/blog/2020/10/20/city-pop-summer":"Buy these records"}
PAIR=re.compile(r"^(?:#?\s*\d+[.)]\s*)?([^-\u2013\u2014]{2,45}?)\s*[-\u2013\u2014]\s*([^-\u2013\u2014]{2,70}?)(?:\s*[\(\[](\d{4})[\)\]])?\s*$")
def _txt(x): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>","",x)).replace("\ufeff","")).strip()
BADSTART=re.compile(r"(?i)^(pre-?order|order|buy|get|listen|stream|price|available|click|shop|find|here|out now|new)\b")
def ok_pair(a,ti):
    return (a and ti and not BADSTART.match(a) and not BADSTART.match(ti)
            and len(a.split())<=5 and len(ti.split())<=9)

def auto_records(body):
    out=[]; seen=set()
    for frag in re.findall(r"<h[1-4][^>]*>(.*?)</h[1-4]>|<p[^>]*>(.*?)</p>",body,re.S):
        t=_txt(frag[0] or frag[1])
        if not t or len(t)>95 or t.endswith(".") or t.count(",")>1 or ":" in t: continue
        m=PAIR.match(t)
        if not m: continue
        a,ti=m.group(1).strip(),m.group(2).strip()
        if not ok_pair(a,ti): continue
        k=(a.lower(),ti.lower())
        if k in seen: continue
        seen.add(k); out.append((a,ti))
    return out[:15]

def auto_block(path,body):
    if path not in AUTO: return ""
    recs=auto_records(body)
    if len(recs)<3: return ""
    rows=""
    for a,t in recs:
        shops="".join(f'<a href="{h}" target="_blank" rel="sponsored noopener">{n}</a>' for n,h in shop_links(a,t))
        rows+=(f'<li><span class="rec-t">{html.escape(t)}</span>'
               f'<span class="shops">{shops}</span></li>'
               if False else
               f'<li><span class="rec-t">{html.escape(a)} — {html.escape(t)}</span><span class="shops">{shops}</span></li>')
    return (f'<div class="records"><h2 style="margin:0">{AUTO[path]} <span class="jp">レコード</span></h2>'
            f'<ul>{rows}</ul>'
            f'<p class="note">Each title opens a search on that store, so you see what is in stock today. '
            f'These are affiliate links: buying through them may earn me a small commission at no extra cost to you. '
            f'As an Amazon Associate I earn from qualifying purchases.</p></div>')

def records_block(path):
    if path not in RECORDS: return ""
    artist,jp,recs=RECORDS[path]
    rows=""
    for title,alt in recs:
        shops="".join(f'<a href="{h}" target="_blank" rel="sponsored noopener">{n}</a>' for n,h in shop_links(artist,title))
        label=html.escape(title)+(f' <span class="meta">{alt}</span>' if alt else "")
        rows+=f'<li><span class="rec-t">{label}</span><span class="shops">{shops}</span></li>'
    return (f'<div class="records"><h2 style="margin:0">Buy {html.escape(artist)} on vinyl <span class="jp">{jp}</span></h2>'
            f'<ul>{rows}</ul>'
            f'<p class="note">Each title opens a search on that store, so you see whatever is in stock today — '
            f'original pressings turn up most often on eBay, current repressings on CDJapan. '
            f'These are affiliate links: buying through them may earn me a small commission at no extra cost to you. '
            f'As an Amazon Associate I earn from qualifying purchases.</p></div>')

# ---------- podcast players: Apple Podcasts episode ids for each post ----------
PODSHOW="1533448486"; PODSPOT="https://open.spotify.com/show/61mrej1uf1xmFyo7tSHC3C"
EPISODES={"/podcast/2020/9/22/episode-1-city-pop-genre-overview":"1000492519458",
          "/podcast/2020/9/27/-city-pop-podcast-the-king-of-city-pop":"1000492869996",
          "/podcast/2020/10/26/-city-pop-podcast-mariya-takeuchi":"1000496198255",
          "/podcast/city-pop-podcast-miki-matsubara":"1000532022511",
          "/podcast/city-pop-podcast-toshiki-kadomatsu":"1000535356536",
          "/podcast/city-pop-podcast-momoko-kikuchi":"1000538143553",
          "/podcast/city-pop-podcast-hideki-saijo":"1000542582468"}
def episode_player(i):
    return (f'<div class="episode"><iframe class="ap" src="https://embed.podcasts.apple.com/us/podcast/id{PODSHOW}?i={i}&amp;theme=auto" '
            f'height="175" frameborder="0" loading="lazy" title="Play this episode" allow="autoplay *; encrypted-media *; fullscreen *; clipboard-write" '
            f'sandbox="allow-forms allow-popups allow-same-origin allow-scripts allow-storage-access-by-user-activation allow-top-navigation-by-user-activation"></iframe>'
            f'<p class="also">Also on <a href="{PODSPOT}" target="_blank" rel="noopener">Spotify</a> and '
            f'<a href="https://podcasts.apple.com/us/podcast/id{PODSHOW}?i={i}" target="_blank" rel="noopener">Apple Podcasts</a></p></div>')

# ---------- parse ----------
root=ET.parse(SRC).getroot(); items=root.find("channel").findall("item")
attach={it.findtext("wp:post_id",namespaces=NS):it.findtext("wp:attachment_url",namespaces=NS)
        for it in items if it.findtext("wp:post_type",namespaces=NS)=="attachment"}

for it in items:
    if it.findtext("wp:post_type",namespaces=NS)!="post": continue
    _l=it.findtext("link") or ""
    if not _l.startswith("/vinyl"): continue
    _t=html.unescape(html.unescape(it.findtext("title") or ""))
    for pm in it.findall("wp:postmeta",NS):
        if pm.findtext("wp:meta_key",namespaces=NS)=="_thumbnail_id":
            u=attach.get(pm.findtext("wp:meta_value",namespaces=NS))
            if u:
                c=local_img(u); parts=[x.strip() for x in re.split(r"\s+-\s+",_t,1)]
                COVERS.setdefault(ckey(_t),c)
                if len(parts)==2: COVERS.setdefault(ckey(parts[0]+parts[1]),c); COVERS.setdefault(ckey(parts[1]),c)

cols={}; urls=[]; redirects=[]; pages={}
for it in items:
    typ=it.findtext("wp:post_type",namespaces=NS)
    if typ not in ("post","page") or it.findtext("wp:status",namespaces=NS)!="publish": continue
    link=it.findtext("link") or ""
    if link.startswith("http") or link=="/home": continue
    title=html.unescape(html.unescape(it.findtext("title") or ""))
    title=re.sub(r"([\u3040-\u30ff\u4e00-\u9fff])([A-Za-z(])",r"\1 \2",title)
    title=re.sub(r"([A-Za-z)])([\u3040-\u30ff\u4e00-\u9fff])",r"\1 \2",title)
    raw=it.findtext("content:encoded",namespaces=NS) or ""
    date=(it.findtext("wp:post_date",namespaces=NS) or "")[:10]
    thumb=None
    for pm in it.findall("wp:postmeta",NS):
        if pm.findtext("wp:meta_key",namespaces=NS)=="_thumbnail_id":
            u=attach.get(pm.findtext("wp:meta_value",namespaces=NS))
            if u: thumb=local_img(u)
    body=clean(raw); desc=plain(it.findtext("excerpt:encoded",namespaces=NS) or "") or plain(body)
    _inlined=False; _disc=""
    if link in RECORDS:
        _a,_jp,_recs=RECORDS[link]
        body,_used=artist_post(body,_a,_jp,_recs)
        _disc=discography_block(_a,_jp,_recs,set(_used)); _inlined=True
    elif link in LISTPOSTS:
        body=body.replace("As an added feature to these kinds of posts, I am hyperlinking the lyrics and also the Discogs page for each one, where you can see purchase options for every record if you’re in the market for picking up one of these on wax.","Each song links to its lyrics where I could find them, and every entry has quick links to hunt down a copy on vinyl if you want to pick one up on wax.")
        body,_inlined=list_layout(body)
        if not _inlined: body,_inlined=inline_buy(body)
    elif link==TOP10:
        body,_inlined=top10_layout(body)
        if not _inlined: body,_inlined=inline_buy(body)
    elif link in AUTO:
        body,_inlined=inline_buy(body)
    if typ=="post":
        col="/"+link.strip("/").split("/")[0]
        if link in EPISODES: body=episode_player(EPISODES[link])+body
        cover=f'<figure class="cover"><img src="{thumb}" alt="" loading="lazy"></figure>' if thumb and thumb not in body else ""
        art=(f'<div class="wrap narrow"><div class="article-head"><p class="meta">{date}</p>'
             f'<h1>{html.escape(title)}</h1><div class="lede-rule"></div></div>{cover}'
             f'<div class="prose{" top10" if link in (TOP10,)+LISTPOSTS else ""}">{body}</div>{_disc or ("" if _inlined else auto_block(link,body))}'
             f'{more_block(link)}<p style="padding:1.5rem 0 2rem"><a href="{col}">← All {dict(NAV).get(col,"posts").lower()}</a></p></div>')
        write(link,art,title,desc,thumb,date)
        cols.setdefault(col,[]).append((date,link,title,desc,thumb)); urls.append((link,date))
    else:
        if not re.sub(r"<[^>]+>","",body).strip(): continue
        pages[link]=(title,desc,body,thumb)


reissues_link="/latest-news/japanese-city-pop-vinyl-reissues"
reissues_title="Japanese City Pop Vinyl Reissues: Where to Find the Best Japanese Records Online"
reissues_desc="Explore Japanese City Pop vinyl reissues, original pressings, and a guide to finding Japanese records online. Start digging with our Buy Vinyl directory."
reissues_date="2026-10-14"
reissues_thumb="/img/anri-timely-wikipedia.png"
with open(os.path.join(os.path.dirname(__file__),"reissues.html"),encoding="utf-8") as reissues_file:
    reissues_body=reissues_file.read()
reissues_art=(f'<div class="wrap narrow"><div class="article-head"><p class="meta">{reissues_date}</p>'
              f'<h1>{reissues_title}</h1><div class="lede-rule"></div></div><div class="prose">{reissues_body}</div>'
              '<p style="padding:1.5rem 0 2rem"><a href="/latest-news">← All news</a></p></div>')
write(reissues_link,reissues_art,reissues_title,reissues_desc,reissues_thumb,reissues_date)
cols.setdefault("/latest-news",[]).append((reissues_date,reissues_link,reissues_title,reissues_desc,reissues_thumb))
urls.append((reissues_link,reissues_date))

names={"/blog":("Writing","記事","Essays and reporting on Japanese City Pop — its records, its people, and how a 1980s genre found a second life."),
       "/latest-news":("News","最新情報","Press, interviews, and upcoming dates."),
       "/news1":("Archive","記録","Earlier press and event notes, 2017–2020."),
       "/podcast":("Mayonaka Hour","真夜中アワー","A City Pop podcast: one artist, one era, one record at a time."),
       "/vinyl":("Vinyl","レコード","Japanese reissues and pressings worth your shelf space.")}

def short(t):
    return re.sub(r"^Mayonaka Hour\s*真夜中アワー\s*City Pop Podcast\s*","",t).strip() or t

# Mayonaka Hour episodes: (Spotify episode id, Apple Podcasts episode id)
POD_SHOW_SP="https://open.spotify.com/show/61mrej1uf1xmFyo7tSHC3C"
POD_SHOW_AP="https://podcasts.apple.com/us/podcast/id1533448486"
LISTEN={"/podcast/city-pop-podcast-hideki-saijo":("2rh4hjqs6WV9RQMVnNAZg9","1000542582468"),
        "/podcast/city-pop-podcast-momoko-kikuchi":("0XprwvkXjp6WmcnHMlr5Aa","1000538143553"),
        "/podcast/city-pop-podcast-toshiki-kadomatsu":("75KXeet7uJ7MyYgUnHGrpQ","1000535356536"),
        "/podcast/city-pop-podcast-miki-matsubara":("7buCAgg5m8PskwE8f7SG87","1000532022511"),
        "/podcast/2020/10/26/-city-pop-podcast-mariya-takeuchi":("4tKkDMssgq50fPLvzbZMwh","1000496198255"),
        "/podcast/2020/9/27/-city-pop-podcast-the-king-of-city-pop":("6m0pehX03LQO8cBHZjWQxi","1000492869996"),
        "/podcast/2020/9/22/episode-1-city-pop-genre-overview":("6KFUd6dMHJpSmcjEA08c5v","1000492519458")}

def listen_row(l,t):
    if l not in LISTEN: return ""
    s,a=LISTEN[l]; t=html.escape(t)
    return (f'<p class="listen"><a class="sp" href="https://open.spotify.com/episode/{s}" target="_blank" rel="noopener" '
            f'aria-label="Play {t} on Spotify">▶ Play on Spotify</a>'
            f'<a href="{POD_SHOW_AP}?i={a}" target="_blank" rel="noopener" aria-label="Play {t} on Apple Podcasts">Apple Podcasts</a></p>')

def entry_li(d,l,t,x,th):
    t=short(t)
    im=f'<img src="{th}" alt="" loading="lazy">' if th else '<div class="no-img"></div>'
    return (f'<li><a class="entry" href="{l}">{im}<div><p class="meta">{d}</p><h3>{html.escape(t)}</h3>'
            f'<p>{html.escape(x)}</p></div></a>{listen_row(l,t)}</li>')

def card(l,t,th,d=""):
    t=short(t)
    im=f'<img src="{th}" alt="" loading="lazy">' if th else '<div class="no-img" style="width:100%;aspect-ratio:1"></div>'
    return f'<li><a class="card" href="{l}">{im}<h3>{html.escape(t)}</h3><p class="meta">{d}</p></a></li>'

pod_follow=(f'<div class="btn-row" style="margin-top:1.25rem"><a class="btn" href="{POD_SHOW_SP}" target="_blank" rel="noopener">Follow on Spotify</a>'
            f'<a class="btn btn-ghost" href="{POD_SHOW_AP}" target="_blank" rel="noopener">Apple Podcasts</a></div>')

# ---------- blog index: bubble blocks in the homepage style ----------
BL_JS=r"""
(function(){
  var d=document,rm=matchMedia('(prefers-reduced-motion: reduce)').matches,root=d.querySelector('.bl');if(!root)return;
  d.documentElement.classList.add('bk-js');
  var items=Array.from(root.querySelectorAll('.bl-item')),io;
  function show(list){if(io)io.disconnect();list.forEach(function(c,i){c.classList.remove('in');c.style.setProperty('--dl',(i%4)*80+'ms')});
    if(rm||!('IntersectionObserver' in window)){list.forEach(function(c){c.classList.add('in')});return}
    io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{rootMargin:'0px 0px -6% 0px'});
    list.forEach(function(c){io.observe(c)})}
  show(items);
  root.querySelectorAll('.bk-rv').forEach(function(n){n.classList.add('in')});
  var chips=Array.from(root.querySelectorAll('.bl-chip'));
  chips.forEach(function(b){b.addEventListener('click',function(){
    chips.forEach(function(x){x.setAttribute('aria-pressed',x===b)});var y=b.dataset.y,vis=[];
    items.forEach(function(c){var on=y==='all'||c.dataset.y===y;c.hidden=!on;if(on)vis.push(c)});
    root.querySelector('.bl-count').textContent=vis.length+(vis.length===1?' story':' stories');show(vis)})});
})();
"""
def gacha_page(posts,blurb):
    years=sorted({d[:4] for d,*_ in posts if d},reverse=True)
    chips='<button type="button" class="bl-chip" data-y="all" aria-pressed="true">All</button>'+"".join(f'<button type="button" class="bl-chip" data-y="{y}" aria-pressed="false">{y}</button>' for y in years)
    cards=""
    for i,(d,l,t,x,th) in enumerate(posts):
        im=f'<img src="{th}" alt="" loading="{"eager" if i<2 else "lazy"}">' if th else '<span class="bl-ph"></span>'
        cards+=(f'<li class="bl-item{" bl-big" if i==0 else ""}" data-y="{d[:4]}"><a class="bl-bub" href="{l}"><span class="bl-img">{im}</span>'
                f'<span class="bl-txt"><span class="bl-meta">No.{len(posts)-i:03d} · {d}</span><h3>{html.escape(short(t))}</h3>'
                f'<span class="bl-ex">{html.escape(x)}</span><span class="bl-go">Read →</span></span></a></li>')
    return ('<div class="wrap bk hm bl"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;1,6..72,400&family=Space+Grotesk:wght@500;700&family=Space+Mono&display=swap">'
      f'<section class="bk-rv bk-frame bl-head"><p class="bk-label">Writing <span class="jp">記事</span></p><h1>Writing</h1><p class="bl-lede">{html.escape(blurb)}</p>'
      f'<div class="bl-bar"><div class="bl-chips" role="group" aria-label="Filter by year">{chips}</div><span class="bl-count">{len(posts)} stories</span></div></section>'
      f'<ul class="bl-grid">{cards}</ul></div><script>{BL_JS}</script>')
for col,posts in cols.items():
    posts.sort(reverse=True)
    nm,jp,blurb=names.get(col,(col.strip("/").title(),"",""))
    if col == "/blog":
        write(col,gacha_page(posts,blurb),nm,blurb,None,None); urls.append((col,posts[0][0]))
        redirects += [(f"{col}/category/*",col),(f"{col}/tag/*",col)]
        continue
    if col == "/vinyl":
        listing=f'<ul class="grid">{"".join(card(l,t,th,d) for d,l,t,x,th in posts)}</ul>'
    else:
        listing=f'<ul class="entries">{"".join(entry_li(d,l,t,x,th) for d,l,t,x,th in posts)}</ul>'
    body=(f'<div class="wrap"><div class="page-head"><div class="band-head"><h1>{nm}</h1><span class="jp">{jp}</span></div>'
          f'<p class="hero-lede">{html.escape(blurb)}</p>{pod_follow if col=="/podcast" else ""}</div>'
          f'<div style="padding-bottom:3rem">{listing}</div></div>')
    write(col,body,nm,blurb,None,None); urls.append((col,posts[0][0]))
    redirects += [(f"{col}/category/*",col),(f"{col}/tag/*",col)]

SPOT="https://open.spotify.com/user/925qp40lrceautk2wzvnkdmwq"
OTONAMI_RE=re.compile(r'<a href="(https://otonami\.io/submit/[^"]+)"[^>]*>.*?</a>',re.S)

def sp(kind,i,h=352):
    return (f'<iframe class="sp" style="border-radius:12px" src="https://open.spotify.com/embed/{kind}/{i}" width="100%" height="{h}" '
            f'frameborder="0" allowfullscreen allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy" title="Spotify"></iframe>')
PLAYLIST=sp("playlist","6US7ZVtZ163U0ylpB0vBdb")
ARTISTS="".join(sp("artist",a) for a in ("070Fcof8UsnauUrWgURSMd","6YdN2wFgj8ChwVhSkVQJOD","7b7UbINKyRM9cq1Au8kRK3"))

def page_extras(link,body):
    if link!="/new-music": return body
    body=OTONAMI_RE.sub(lambda m:
        f'<p class="cta"><a class="btn btn-xl" href="{m.group(1)}" target="_blank" rel="noopener">'
        f'Submit your music<span>♪ OTONAMI</span></a></p>', body, count=1)
    body+=(f'<div class="records"><h2 style="margin:0">Listen <span class="jp">試聴</span></h2>'
           f'<p style="max-width:40rem">Everything I am playing out, and the new Japanese records worth your time, '
           f'collected on Spotify.</p>'
           f'<p class="cta"><a class="btn btn-xl" href="{SPOT}" target="_blank" rel="noopener">'
           f'Listen on Spotify<span>Van Paugam</span></a></p>'
           f'<div class="sp-grid">{ARTISTS}</div>'
           f'<h3 style="margin:2rem 0 .8rem">The playlist</h3>{PLAYLIST}</div>')
    return body

for link,(title,desc,body,thumb) in pages.items():
    if link=="/what-is-city-pop":
        with open(os.path.join(os.path.dirname(__file__),"what-is-city-pop.html"),encoding="utf-8") as city_pop_file:
            city_pop_body=city_pop_file.read()
        write(link,city_pop_body,title,"An introduction to City Pop: the sound, history, English lyrics, and global rediscovery of Japanese pop from the 1970s and 1980s.",thumb)
        urls.append((link,""))
        continue
    if link=="/somehow-city-pop-book":
        with open(os.path.join(os.path.dirname(__file__),"book.html"),encoding="utf-8") as book_file:
            book_body=book_file.read()
        write(link,book_body,title,"Somehow, City Pop: Japanese Records, 1975–1990. A 208-page hardcover City Pop reference guide with photographs, by Chicago City Pop DJ Van Paugam. Kickstarter launches 11 November 2026.","/img/book/cover.webp")
        urls.append((link,""))
        continue
    if link=="/about-van-paugam":
        with open(os.path.join(os.path.dirname(__file__),"about.html"),encoding="utf-8") as about_file:
            about_body=about_file.read()
        write(link,about_body,title,"Chicago-based City Pop DJ, writer, and vinyl collector. Explore Van Paugam’s approach, selected work, international coverage, and booking information.",thumb)
        urls.append((link,""))
        continue
    body=page_extras(link,body)
    if not re.search(r"<h1",body): body=f"<h1>{html.escape(title)}</h1>"+body
    body=re.sub(r"<h1[^>]*>(.*?)</h1>",lambda m:f'<div class="article-head"><h1>{m.group(1)}</h1><div class="lede-rule"></div></div>',body,count=1,flags=re.S)
    write(link,f'<div class="wrap narrow"><div class="prose" style="padding-top:2rem">{body}</div></div>',title,desc,thumb)
    urls.append((link,""))

# ---------- home ----------
def strip_from(col,n):
    return sorted(cols.get(col,[]),reverse=True)[:n]
blog=strip_from("/blog",5); news=strip_from("/latest-news",3); pod=strip_from("/podcast",3); vin=strip_from("/vinyl",24)
_seen=set(); _v=[]
for r in vin:
    k=re.sub(r"[^a-z0-9]","",re.sub(r"\[[^\]]*\]","",r[2]).lower())[:40]
    if k in _seen: continue
    _seen.add(k); _v.append(r)
vin=_v[:14]
book_img=None
if "/somehow-city-pop-book" in pages:
    book_img="/img/book/cover.webp"

FEATURED=[r[1] for r in sorted(cols.get("/blog",[]),reverse=True)]
_byl={r[1]:r for r in cols.get("/blog",[])}
_slides=""; _dots=""
for _i,_p in enumerate([x for x in FEATURED if x in _byl][:8]):
    _d,_l,_t,_x,_th=_byl[_p]
    _slides+=(f'<article class="slide{" on" if _i==0 else ""}" data-i="{_i}">'
      f'<a class="ttl" href="{_l}"><img src="{_th}" alt=""{" fetchpriority=\"high\"" if _i==0 else " loading=\"lazy\""}></a>'
      f'<div><span class="hm-no">No.{_i+1:02d}</span><a class="ttl" href="{_l}"><h2>{html.escape(_t)}</h2></a>'
      f'<p class="meta" style="margin:-.3rem 0 1rem">{_d}</p><p>{html.escape(_x)}</p>'
      f'<div class="btn-row"><a class="btn" href="{_l}">Read the story</a></div></div></article>')
    _dots+=f'<button type="button" class="dot{" on" if _i==0 else ""}" data-i="{_i}" aria-label="Featured story {_i+1}">{_i+1:02d}</button>'
FEATURED_HTML=(f'<section class="bk-rv bk-frame hm-feat" id="featured" aria-labelledby="hm-feat-h">'
   f'<div class="hm-head"><p class="bk-label" id="hm-feat-h">01 · Featured writing <span class="jp">特集</span></p><a class="hm-more" href="/blog">All writing →</a></div>'
   f'<div class="slides">{_slides}</div><div class="hm-ctl"><button type="button" class="hm-arw" data-step="-1" aria-label="Previous story">←</button>'
   f'<div class="dots" aria-label="Choose a featured story">{_dots}</div><button type="button" class="hm-arw" data-step="1" aria-label="Next story">→</button></div>'
   f'<div class="hm-bar" aria-hidden="true"><i></i></div></section>') if _slides else ""

def tick_link(t):
    a,_,ti = t.partition(" - ")
    q = t if not ti else f"{a} {ti}"
    q = re.sub(r"\s*\[[^\]]*\]","",q).strip()
    h = shop_links("", q)[0][1]
    return f'<i>&#9679;</i><a href="{h}" target="_blank" rel="sponsored noopener">{html.escape(short(t))}</a>'
TICKER="".join(tick_link(t) for _,_,t,_,_ in vin) or "<i>&#9679;</i>Japanese City Pop on original pressings"

TRACKS=[("A1","Writing","記事","/blog","Essays on the records, the people, and how a 1980s genre found a second life."),
        ("A2","Somehow, City Pop","書籍","/somehow-city-pop-book","A City Pop reference guide with photographs."),
        ("A3","About","略歴","/about-van-paugam","A decade of nights, a board seat, and a wall of Japanese pressings."),
        ("B1","Buy vinyl","レコード","/buy-vinyl","Where to find reissues and originals, plus what was pressed this month."),
        ("B2","Mayonaka Hour","真夜中アワー","/podcast","One artist, one era, one record at a time."),
        ("B3","Booking","出演依頼","/contact","Clubs, festivals, private rooms. Tell me the date."),]

RECORD_ICON = '<svg viewBox="0 0 64 64" fill="none" aria-hidden="true" focusable="false"><g stroke="currentColor" stroke-width="1.3"><circle cx="32" cy="32" r="30"/><circle cx="32" cy="32" r="25"/><circle cx="32" cy="32" r="21"/><circle cx="32" cy="32" r="13"/><path d="M9 25a24 24 0 0 1 16-16m14 46a24 24 0 0 0 16-16" stroke-width="2.2" stroke-linecap="round"/></g></svg>'

def track_row(c,t,jp,href,d):
    return (f'<a class="track" href="{href}"><span class="record-mark">{RECORD_ICON}<span class="cue">{c}</span></span>'
            f'<h3>{html.escape(t)} <em>{jp}</em></h3><p>{html.escape(d)}</p></a>')

# pixel fox that lives by the mailing list
_PX=[".K..........K.",
     ".KK........KK.",
     ".KOK......KOK.",
     "RKOOKKKKKKOOKR",
     "RKOOOOOOOOOOKR",
     "RKOEEOOOOEEOKR",
     ".KWWOOOOOOWWK.",
     "..KWWWKKWWWK..",
     "...KWWWWWWK...",
     "..KOOWWWWOOK..",
     "..KOOWWWWOOK..",
     "..KKKKKKKKKK.."]
_PXC={"K":"#0E1626","W":"#F3F2ED","R":"#C2422B","O":"#E8772E","E":"#0E1626"}
def _px_rects(keys):
    out=""
    for y,row in enumerate(_PX):
        x=0
        while x<len(row):
            c=row[x]
            if c in keys:
                e=x
                while e<len(row) and row[e]==c: e+=1
                out+=f'<rect x="{x}" y="{y}" width="{e-x}" height="1" fill="{_PXC[c]}"/>'
                x=e
            else: x+=1
    return out
PIXEL_CAT=('<button type="button" class="px-cat" aria-label="Pet the record fox">'
  '<span class="px-bubble" aria-hidden="true">コン!</span><span class="px-note" aria-hidden="true">♪</span><span class="px-note n2" aria-hidden="true">♫</span>'
  '<svg viewBox="-1 -1 17 13" shape-rendering="crispEdges" aria-hidden="true">'
  '<g class="px-tail"><rect x="12" y="9" width="2" height="2" fill="#E8772E"/><rect x="13" y="7" width="2" height="2" fill="#E8772E"/><rect x="14" y="5" width="1" height="2" fill="#F3F2ED"/></g>'
  f'<g class="px-body">{_px_rects("KWRO")}<g class="px-eyes">{_px_rects("E")}</g></g></svg></button>')

def prog_tile(i,c,t,jp,href,d):
    return (f'<a class="hm-tile" href="{href}"><span class="hm-n">{i+1:02d}</span><span class="hm-jp" aria-hidden="true">{jp}</span>'
            f'<strong>{html.escape(t)}</strong><span class="hm-d">{html.escape(d)}</span></a>')

def hm_row(d,l,t,x,th):
    im=f'<img src="{th}" alt="" loading="lazy">' if th else '<span class="ph"></span>'
    return f'<li><a href="{l}">{im}<span><small>{d}</small><b>{html.escape(short(t))}</b></span></a></li>'

def strip_li(l,t,th):
    im=f'<img src="{th}" alt="" loading="lazy">' if th else '<div class="ph"></div>'
    return f'<li><a href="/buy-vinyl">{im}<h4>{html.escape(short(t))}</h4></a></li>'

def lead_card(d,l,t,x,th,big=False):
    im=f'<img src="{th}" alt="" loading="lazy">' if th else ""
    return (f'<a class="lead" href="{l}">{im}<p class="meta">{d}</p><h3>{html.escape(t)}</h3>'
            + (f'<p>{html.escape(x)}</p>' if big else "") + '</a>')

HOME_JS = """
(function(){
  var box=document.getElementById('featured');
  if(!box) return;
  var sl=Array.from(box.querySelectorAll('.slide')), dt=Array.from(box.querySelectorAll('.dot'));
  var i=0, timer, opener, request=0, rm=matchMedia('(prefers-reduced-motion: reduce)');
  var dialog=document.createElement('dialog');
  dialog.className='story-reader';
  dialog.setAttribute('aria-labelledby','reader-title');
  dialog.innerHTML='<div class="reader-toolbar"><a class="reader-link">Open full page</a><button type="button" class="btn reader-close" autofocus>Close</button></div><div class="reader-content" aria-live="polite"></div>';
  document.body.appendChild(dialog);
  var content=dialog.querySelector('.reader-content');
  function stop(){clearInterval(timer);timer=0;box.classList.remove('run')}
  function start(){stop(); if(sl.length>1 && !rm.matches && !dialog.open && !box.matches(':hover') && !box.contains(document.activeElement) && !document.hidden) {timer=setInterval(function(){go(i+1)},7000);box.classList.remove('run');void box.offsetWidth;box.classList.add('run')}}
  function go(n){
    i=(n+sl.length)%sl.length;
    sl.forEach(function(s,k){s.classList.toggle('on',k===i);s.inert=k!==i;s.setAttribute('aria-hidden',String(k!==i))});
    dt.forEach(function(d,k){d.classList.toggle('on',k===i);d.setAttribute('aria-pressed',String(k===i))});
    box.classList.remove('run');void box.offsetWidth;if(timer)box.classList.add('run');
  }
  function openStory(slide){
    if(typeof dialog.showModal!=='function'){location.href=slide.querySelector('a').href;return}
    stop(); opener=slide;
    var url=slide.querySelector('a').href, title=slide.querySelector('h2').textContent, token=++request;
    dialog.querySelector('.reader-link').href=url;
    content.replaceChildren();
    var heading=document.createElement('h1');heading.id='reader-title';heading.textContent=title;
    var status=document.createElement('p');status.textContent='Loading story…';
    content.append(heading,status);content.setAttribute('aria-busy','true');
    dialog.showModal();document.documentElement.classList.add('reading-story');dialog.scrollTop=0;
    fetch(url).then(function(r){if(!r.ok)throw new Error();return r.text()}).then(function(text){
      if(token!==request || !dialog.open)return;
      var doc=new DOMParser().parseFromString(text,'text/html'), article=doc.querySelector('main .narrow');
      if(!article)throw new Error();
      article.querySelectorAll('script').forEach(function(el){el.remove()});
      content.innerHTML=article.innerHTML;
      var h=content.querySelector('h1');if(h)h.id='reader-title';
      content.querySelectorAll('a[target="_blank"]').forEach(function(a){a.rel+=' noopener'});
    }).catch(function(){if(token===request && dialog.open)status.textContent='This story could not be loaded. Use “Open full page” to keep reading.'}).finally(function(){if(token===request)content.removeAttribute('aria-busy')});
  }
  dialog.querySelector('.reader-close').addEventListener('click',function(){dialog.close()});
  dialog.addEventListener('click',function(e){if(e.target===dialog){var r=dialog.getBoundingClientRect();if(e.clientX<r.left || e.clientX>r.right || e.clientY<r.top || e.clientY>r.bottom)dialog.close()}});
  dialog.addEventListener('close',function(){request++;document.documentElement.classList.remove('reading-story');if(opener)opener.focus();start()});
  sl.forEach(function(s){
    s.tabIndex=0;s.setAttribute('aria-label','Read '+s.querySelector('h2').textContent);s.setAttribute('aria-haspopup','dialog');
    s.addEventListener('click',function(e){if(e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey)return;e.preventDefault();openStory(s)});
    s.addEventListener('keydown',function(e){if(e.target===s && (e.key==='Enter'||e.key===' ')){e.preventDefault();openStory(s)}});
  });
  dt.forEach(function(d,k){d.addEventListener('click',function(){go(k);start()})});
  box.querySelectorAll('.hm-arw').forEach(function(b){b.addEventListener('click',function(){go(i+(+b.dataset.step));start()})});
  box.addEventListener('mouseenter',stop);box.addEventListener('mouseleave',start);
  box.addEventListener('focusin',stop);box.addEventListener('focusout',function(){setTimeout(start,0)});
  document.addEventListener('visibilitychange',start);rm.addEventListener('change',start);
  go(0);start();
})();
(function(){
  var d=document, rm=matchMedia('(prefers-reduced-motion: reduce)').matches;
  d.documentElement.classList.add('bk-js');
  var els=d.querySelectorAll('.bk-rv');
  if('IntersectionObserver' in window && !rm){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{threshold:.12,rootMargin:'0px 0px -6% 0px'});
    els.forEach(function(n){io.observe(n)});
  } else els.forEach(function(n){n.classList.add('in')});
  if (!rm){
    var plat=d.querySelector('.platter'), slv=d.querySelector('.sleeve'), tick=false;
    if(plat) addEventListener('scroll',function(){
      if(tick) return; tick=true;
      requestAnimationFrame(function(){
        var y=Math.min(scrollY,700);
        plat.style.marginTop=(y*0.07)+'px';
        if(slv) slv.style.transform='translateY('+(y*-0.045)+'px)';
        tick=false;
      });
    },{passive:true});
  }
  var tabs=Array.from(d.querySelectorAll('.hm-tablist [role=tab]'));
  function sel(t,focus){tabs.forEach(function(x){var on=x===t;x.setAttribute('aria-selected',on);x.tabIndex=on?0:-1;d.getElementById(x.getAttribute('aria-controls')).hidden=!on});if(focus)t.focus()}
  tabs.forEach(function(t,k){t.addEventListener('click',function(){sel(t)});t.addEventListener('keydown',function(e){var n=e.key==='ArrowRight'?1:e.key==='ArrowLeft'?-1:0;if(n){e.preventDefault();sel(tabs[(k+n+tabs.length)%tabs.length],true)}})});
  var cat=d.querySelector('.px-cat');
  if(cat){var poke=function(k){cat.classList.remove('hop','happy');void cat.offsetWidth;cat.classList.add(k)};
    cat.addEventListener('click',function(){poke('hop')});
    var em=d.getElementById('nl-email');
    if(em){em.addEventListener('focus',function(){cat.classList.add('look')});em.addEventListener('blur',function(){cat.classList.remove('look')});
      em.form.addEventListener('submit',function(){poke('happy')})}}
  var c=d.querySelector('.bk-count');
  if(c){var t=Date.parse(c.dataset.launch),f=function(){var x=Math.max(0,t-Date.now()),u={d:Math.floor(x/864e5),h:Math.floor(x/36e5)%24,m:Math.floor(x/6e4)%60,s:Math.floor(x/1e3)%60};
    for(var k in u){var e=c.querySelector('[data-u="'+k+'"]');if(e)e.textContent=String(u[k]).padStart(2,'0')}};f();setInterval(f,1000)}
  fetch('/api/reissues').then(function(r){ if(!r.ok) throw 0; return r.json() }).then(function(j){
    var it=(j.items||[]).slice(0,6); if(!it.length) throw 0;
    var ul=d.getElementById('strip'); ul.innerHTML='';
    it.forEach(function(r){
      var li=d.createElement('li'), a=d.createElement('a');
      a.href='/buy-vinyl'; a.innerHTML=(r.cover?'<img src="'+r.cover+'" alt="" loading="lazy" referrerpolicy="no-referrer">':'<div class="ph"></div>')+'<h4></h4><p></p>';
      a.querySelector('h4').textContent=r.title; a.querySelector('p').textContent=r.artist;
      li.appendChild(a); ul.appendChild(li);
    });
  }).catch(function(){});
})();
"""

with open(os.path.join(os.path.dirname(__file__),"photo-slides.html"),encoding="utf-8") as photo_file:
    PHOTO_SLIDES_HTML=photo_file.read().strip()

home=f"""<section class="sideA"><div class="wrap sideA-in">
<div><p class="kicker">SIDE A — 和製ポップス</p>
<h1><span class="ln"><span>Japanese City Pop:</span></span><span class="ln"><span>records, writing,</span></span><span class="ln"><span>and DJ sets.</span></span></h1>
<p class="lede">Van Paugam is the DJ, writer, and vinyl specialist widely credited with the global revival of Japanese City Pop — over a hundred nights in Chicago, Paris, Berlin, and Tokyo, all of it from original Japanese pressings.</p>
<div class="btn-row"><a class="btn" href="/contact">Book a set</a><a class="btn btn-ghost" href="/buy-vinyl">Buy vinyl</a></div></div>
<div class="turntable"><div class="platter" aria-hidden="true"></div>
{PHOTO_SLIDES_HTML}</div>
</div>
<div class="ticker"><div class="ticker-track"><span>{TICKER}</span><span aria-hidden="true">{TICKER}</span></div></div>
</section>

<div class="wrap bk hm">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;1,6..72,400&family=Space+Grotesk:wght@500;700&family=Space+Mono&display=swap">
<nav class="bk-rv hm-prog" aria-label="Sections"><p class="hm-prog-h"><span>番組表</span> Programme</p>
<div class="hm-tiles">{"".join(prog_tile(i,*t) for i,t in enumerate(TRACKS))}</div></nav>

{FEATURED_HTML}

<div class="hm-duo">
<section class="bk-rv bk-frame hm-tabs" aria-labelledby="hm-tabs-h"><p class="bk-label" id="hm-tabs-h">02 · On the shelf <span class="jp">棚</span></p>
<div class="hm-tablist" role="tablist" aria-label="On the shelf">
<button type="button" role="tab" id="t-pr" aria-controls="p-pr" aria-selected="true">Just pressed <span class="jp">新譜</span></button>
<button type="button" role="tab" id="t-po" aria-controls="p-po" aria-selected="false" tabindex="-1">Podcast <span class="jp">真夜中</span></button>
<button type="button" role="tab" id="t-nw" aria-controls="p-nw" aria-selected="false" tabindex="-1">News <span class="jp">情報</span></button></div>
<div class="hm-panel" role="tabpanel" id="p-pr" aria-labelledby="t-pr"><ul class="hm-covers" id="strip">{"".join(strip_li(l,t,th) for _,l,t,_,th in vin[:6])}</ul>
<a class="hm-more" href="/buy-vinyl">Buy vinyl →</a></div>
<div class="hm-panel" role="tabpanel" id="p-po" aria-labelledby="t-po" hidden><ul class="hm-rows">{"".join(hm_row(*x) for x in pod)}</ul><a class="hm-more" href="/podcast">All episodes →</a></div>
<div class="hm-panel" role="tabpanel" id="p-nw" aria-labelledby="t-nw" hidden><ul class="hm-rows">{"".join(hm_row(*x) for x in news)}</ul><a class="hm-more" href="/latest-news">All news →</a></div>
</section>

<section class="bk-rv hm-book" aria-labelledby="hm-book-h"><div class="hm-sun" aria-hidden="true"></div>
<p class="bk-label">03 · The book <span class="jp">書籍</span></p>
<div class="hm-book-in">{f'<a class="hm-cover" href="/somehow-city-pop-book"><img src="{book_img}" alt="Cover of Somehow, City Pop" loading="lazy"><span>KICKSTARTER 11.11</span></a>' if book_img else ''}
<div><h2 id="hm-book-h">Somehow, City Pop</h2><p>A City Pop reference guide with photographs. 102 records, launching on Kickstarter 11 November 2026 with a $4,000 goal.</p></div></div>
<div class="bk-count" data-launch="2026-11-11T16:00:00Z" aria-label="Time until the Kickstarter launch"><div><b data-u="d">--</b><span>Days</span></div><div><b data-u="h">--</b><span>Hrs</span></div><div><b data-u="m">--</b><span>Min</span></div><div><b data-u="s">--</b><span>Sec</span></div></div>
<div class="btn-row"><a class="btn" href="/somehow-city-pop-book">About the book</a></div></section>
</div>

<div class="hm-duo hm-duo-b">
<section class="bk-rv bk-frame hm-play" aria-labelledby="hm-play-h"><div class="hm-head"><p class="bk-label" id="hm-play-h">04 · On the turntable <span class="jp">選曲</span></p><a class="hm-more" href="/new-music">New music →</a></div>
{PLAYLIST}</section>
<section class="bk-rv hm-mail" id="newsletter" aria-labelledby="hm-mail-h"><p class="hm-v" aria-hidden="true">お便り</p>
<p class="bk-label">05 · The mailing list</p><h2 id="hm-mail-h">Letters from the crate</h2>
<p>New writing, upcoming dates, and a note when something worth owning gets repressed. A few times a year, never more.</p>
<form class="form signup" name="newsletter" method="POST" data-netlify="true" netlify-honeypot="company" action="/subscribed">
<input type="hidden" name="form-name" value="newsletter">
<p class="hp"><label>Leave this empty <input name="company" tabindex="-1"></label></p>
<label for="nl-email">Email address</label><input id="nl-email" type="email" name="email" required autocomplete="email" placeholder="you@example.com">
<button class="btn" type="submit">Join the list</button></form>{PIXEL_CAT}</section>
</div>
</div>
<script>{HOME_JS}</script>"""
write("/",home,"Van Paugam — Japanese City Pop DJ, Writer & Vinyl Specialist",
      "Van Paugam is the DJ, writer, and vinyl specialist widely credited with the global revival of Japanese City Pop. Booking, writing, podcast, and records.",HERO)
urls.append(("/",""))

# ---------- contact ----------
contact=f"""<div class="wrap narrow"><div class="article-head"><h1>Booking &amp; press</h1><div class="lede-rule"></div></div>
<p class="hero-lede">For club nights, festivals, private events, interviews, and licensing. Tell me the date and the room, and I'll come back to you with availability and a rate.</p>
<div class="btn-row" style="margin-bottom:2rem"><a class="btn" href="/media-kit/van-paugam-media-kit.pdf" download>Download media kit PDF</a><a class="btn btn-ghost" href="/media-kit/">View interactive media kit</a></div>
<form class="form" name="contact" method="POST" data-netlify="true" netlify-honeypot="company" action="/thank-you">
<input type="hidden" name="form-name" value="contact">
<input type="hidden" name="subject" value="New contact form message — %{{siteName}}">
<p class="hp"><label>Leave this empty <input name="company" tabindex="-1" autocomplete="off"></label></p>
<label for="name">Your name</label><input id="name" name="name" required autocomplete="name">
<label for="email">Email</label><input id="email" type="email" name="email" required autocomplete="email">
<label for="kind">What is this about?</label><select id="kind" name="kind">
<option>Booking a DJ set</option><option>Press or interview</option><option>The book</option><option>Music submission</option><option>Something else</option></select>
<label for="date">Event date (if you have one)</label><input id="date" type="date" name="date">
<label for="message">Details</label><textarea id="message" name="message" required placeholder="Venue, city, audience size, set length."></textarea>
<button class="btn" type="submit">Send message</button></form>
<p style="padding:2rem 0 3rem;color:var(--mute)">Prefer email? <a href="mailto:info@vanpaugam.com">info@vanpaugam.com</a></p></div>"""
write("/contact",contact,"Booking & press","Book Van Paugam for a City Pop DJ set, or get in touch about press, the book, and music submissions.")
urls.append(("/contact",""))

# ---------- buy vinyl ----------
EBAY_CAMPID="5339222122"; AMAZON_TAG="citypop-20"; CDJ="https://www.cdjapan.co.jp/aff/click.cgi/e86NDzbdSLQ/7023/A403672/"
def store_search(term):
    from urllib.parse import quote
    q=quote(term)
    return (f"https://www.ebay.com/sch/i.html?_nkw={q}&mkcid=1&mkrid=711-53200-19255-0&campid={EBAY_CAMPID}&toolid=10001&customid=vanpaugam",
            f"https://www.amazon.com/s?k={q}&tag={AMAZON_TAG}",
            CDJ+quote(f"searches?q={term}",safe=""))
eb,am,cd=store_search("japanese city pop vinyl")
buy_js = """
(function(){
  var E="%s",A="%s",C="%s";
  var enc=encodeURIComponent;
  function links(r){
    var q=((r.artist&&r.artist!=="Various Artists"?r.artist:"")+" "+r.title).trim();
    return [["eBay","https://www.ebay.com/sch/i.html?_nkw="+enc(q+" vinyl")+"&mkcid=1&mkrid=711-53200-19255-0&campid="+E+"&toolid=10001&customid=vanpaugam"],
            ["Amazon","https://www.amazon.com/s?k="+enc(q+" vinyl")+"&tag="+A],
            ["CDJapan",C+enc("searches?q="+q)]];
  }
  function card(r){
    var li=document.createElement("li"); li.className="rel";
    var cover=r.cover?'<img src="'+r.cover+'" alt="" loading="lazy" referrerpolicy="no-referrer">':'<div class="ph"></div>';
    var meta=[r.label,r.catno,(r.formats||[]).filter(function(f){return !/^\\d+$/.test(f)}).slice(0,4).join(" / ")].filter(Boolean).join(" · ");
    var buy=links(r).map(function(b){return '<a href="'+b[1]+'" target="_blank" rel="sponsored noopener">'+b[0]+'</a>'}).join("");
    li.innerHTML=cover+'<div><p class="meta"><span class="tag'+(r.isReissue?'':' new')+'">'+(r.isReissue?'Reissue':'New release')+'</span>'+
      r.year+(r.country?" · "+r.country:"")+'</p><h3>'+esc(r.title)+'</h3><p class="who">'+esc(r.artist)+'</p>'+
      '<p class="meta">'+esc(meta)+'</p><p class="buy">'+buy+
      '</p></div>';
    return li;
  }
  function esc(t){var d=document.createElement("div");d.textContent=t==null?"":t;return d.innerHTML}
  fetch("/api/reissues").then(function(r){ if(!r.ok) throw 0; return r.json() }).then(function(d){
    var items=(d.items||[]); if(!items.length) throw 0;
    var ri=document.getElementById("ri"), nr=document.getElementById("nr");
    var a=0,b=0;
    items.forEach(function(r){ (r.isReissue?(a++,ri):(b++,nr)).appendChild(card(r)) });
    document.getElementById("ri-n").textContent=a; document.getElementById("nr-n").textContent=b;
    document.getElementById("feed").hidden=false;
    document.getElementById("feed-wait").hidden=true;
  }).catch(function(){
    document.getElementById("feed-wait").innerHTML='The release feed is taking a moment. <a href="https://citypopwiki.org/reissues" rel="noopener">See the full list on City Pop Wiki</a>.';
  });
})();
""" % (EBAY_CAMPID,AMAZON_TAG,CDJ)
buyp=f"""<div class="wrap"><div class="page-head"><div class="band-head"><h1>Buy vinyl</h1><span class="jp">レコード</span></div>
<p class="hero-lede">Where I actually look for City Pop records — and a live feed of what has just been reissued or newly pressed, straight from the Discogs database.</p></div>

<ul class="stores">
<li><a class="store" href="{eb}" target="_blank" rel="sponsored noopener"><h3>eBay</h3><p>Original Japanese pressings, obi strips intact. The deepest pool, and where most of my shelf came from.</p></a></li>
<li><a class="store" href="{am}" target="_blank" rel="sponsored noopener"><h3>Amazon</h3><p>Modern reissues and remasters. Fastest shipping if you want the music more than the artifact.</p></a></li>
<li><a class="store" href="{cd}" target="_blank" rel="sponsored noopener"><h3>CDJapan</h3><p>New Japanese reissues at Japanese retail, shipped from Japan. First stop for a current repress.</p></a></li>
</ul>

<section class="band" style="border-top:0;padding-bottom:1rem"><div class="band-head"><h2>Just reissued</h2><span class="jp">新譜</span>
<a class="more" href="https://citypopwiki.org/reissues" rel="noopener">City Pop Wiki</a></div>
<p id="feed-wait" class="meta">Loading the latest releases…</p>
<div id="feed" hidden><div class="cols">
<section><h3 style="margin-top:0">Reissues <span class="meta">· <span id="ri-n">0</span></span></h3><ul id="ri" style="list-style:none;padding:0;margin:0"></ul></section>
<section><h3 style="margin-top:0">New releases <span class="meta">· <span id="nr-n">0</span></span></h3><ul id="nr" style="list-style:none;padding:0;margin:0"></ul></section>
</div></div></section>

<p class="feed-note">Release data from Discogs, by way of <a href="https://citypopwiki.org/reissues" rel="noopener">City Pop Wiki</a>, refreshed every few hours.
Links to eBay, Amazon and CDJapan are affiliate links: buying through them may earn a small commission at no extra cost to you.
As an Amazon Associate I earn from qualifying purchases.</p>
</div><script>{buy_js}</script>"""
write("/buy-vinyl",buyp,"Buy vinyl","Where to buy Japanese City Pop records — eBay, Amazon and CDJapan — plus a live feed of the latest reissues and new pressings.")
urls.append(("/buy-vinyl",""))

write("/subscribed",'<div class="wrap narrow"><div class="article-head"><h1>You are on the list</h1><div class="lede-rule"></div></div>'
      '<p class="hero-lede">Thanks for subscribing. Next dispatch when there is something worth sending.</p>'
      '<div class="btn-row" style="padding-bottom:3rem"><a class="btn" href="/">Back to the homepage</a></div></div>',
      "You are on the list","You have subscribed to the Van Paugam mailing list.")
write("/thank-you",'<div class="wrap narrow"><div class="article-head"><h1>Message sent</h1><div class="lede-rule"></div></div>'
      '<p class="hero-lede">Thanks — it landed. I answer booking enquiries within a few days.</p>'
      '<div class="btn-row" style="padding-bottom:3rem"><a class="btn" href="/">Back to the homepage</a></div></div>',
      "Message sent","Your message has been sent.")

# ---------- media kit ----------
os.makedirs(os.path.join(OUT,"media-kit"),exist_ok=True)
for asset in ("index.html","van-paugam-media-kit.pdf"):
    shutil.copy(os.path.join(os.path.dirname(SRC),"media-kit",asset),os.path.join(OUT,"media-kit",asset))
urls.append(("/media-kit/",""))

# ---------- assets ----------
shutil.copy(CSS,os.path.join(OUT,"style.css"))
shutil.copy(os.path.join(os.path.dirname(CSS),"fox.js"),os.path.join(OUT,"fox.js"))
open(os.path.join(OUT,"sitemap.xml"),"w").write(
  '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
  +"".join(f"  <url><loc>{SITE}{u}</loc>{f'<lastmod>{d}</lastmod>' if d else ''}</url>\n" for u,d in sorted(set(urls)))
  +"</urlset>\n")
open(os.path.join(OUT,"robots.txt"),"w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
extra=[("/home","/"),("/contact-1","/contact"),("/blog-1","/blog"),("/new","/latest-news"),("/city-pop-blog","/blog"),("/new-page-1","/"),("/member-site-homepage-1","/")]
extra.append(("/blog/rare-city-pop-vinyl-repress","/blog/tatsuro-yamashita-vinyl-repress-pre-order"))
open(os.path.join(OUT,"_headers"),"w").write(
  "/img/*\n  Cache-Control: public, max-age=31536000, immutable\n\n"
  "/style.css\n  Cache-Control: public, max-age=3600\n\n"
  "/*\n  X-Content-Type-Options: nosniff\n")
open(os.path.join(OUT,"_redirects"),"w").write(
  "# /api/reissues is served by netlify/functions/reissues.mjs\n"
  "# Squarespace -> static. 301 keeps Google rankings.\n"
  "https://www.vanpaugam.com/*  https://vanpaugam.com/:splat  301!\n"
  +"".join(f"{a}  {b}  301\n" for a,b in redirects+extra if a!=b)
  +"# Serve generated blog pages directly without directory slash redirects.\n"
  +"/blog  /blog/index.html  200!\n"
  +"/blog/*  /blog/:splat/index.html  200!\n")
missing=[u for u in images.values() if not os.path.exists(os.path.join(OUT,RENAMES.get(u,u).lstrip("/")))]
print(len(urls),"pages,",len(images),"images referenced,",len(missing),"missing images")
