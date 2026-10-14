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
    if p not in ("img",".git","_build","netlify"): shutil.rmtree(os.path.join(OUT,p),ignore_errors=True) if os.path.isdir(os.path.join(OUT,p)) else os.remove(os.path.join(OUT,p))

images={}
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

def head(path,title,desc,img,date):
    canon=SITE+path
    ld=""
    if date:
        ld=('<script type="application/ld+json">{"@context":"https://schema.org","@type":"BlogPosting","headline":'
            +json.dumps(title)+f',"datePublished":"{date}","author":{{"@type":"Person","name":"Van Paugam"}},"mainEntityOfPage":"{canon}"'
            +(f',"image":"{SITE}{img}"' if img else "")+'}</script>')
    nav="".join(f'<a href="{u}"{" aria-current=\"page\"" if path==u or (u!="/" and path.startswith(u+"/")) else ""}>{n}</a>' for u,n in NAV)
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
<link rel="stylesheet" href="/style.css">{ld}
<script>try{{var t=localStorage.getItem("vp-theme");if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
</head><body>
<header class="site-head"><div class="wrap"><a class="mark" href="/">VAN PAUGAM</a><nav class="site-nav">{nav}<button class="theme" type="button" id="theme" aria-label="Switch between light and dark">Dark</button></nav></div></header>
<main id="main">"""

FOOT=f"""</main>
<footer class="site-foot"><div class="wrap"><div class="foot-grid">
<div><h4>VAN PAUGAM</h4><p style="margin:0;max-width:22rem">Japanese City Pop on original pressings — writing, radio, and records from Chicago.</p></div>
<div><h4>Read</h4><ul><li><a href="/blog">Writing</a></li><li><a href="/what-is-city-pop">What is City Pop?</a></li><li><a href="/somehow-city-pop-book">The book</a></li><li><a href="/latest-news">News</a></li></ul></div>
<div><h4>Listen</h4><ul><li><a href="/podcast">Mayonaka Hour</a></li><li><a href="/buy-vinyl">Buy vinyl</a></li><li><a href="/new-music">New music</a></li><li><a href="{SP}" rel="noopener">Spotify</a></li></ul></div>
<div><h4>Contact</h4><ul><li><a href="/contact">Booking &amp; press</a></li><li><a href="mailto:info@vanpaugam.com">info@vanpaugam.com</a></li><li><a href="{IG}" rel="me noopener">Instagram</a></li><li><a href="{FB}" rel="me noopener">Facebook</a></li></ul></div>
</div>
<div class="foot-sub"><h4>The mailing list</h4>
<p>New writing, upcoming dates, and a note when something worth owning gets repressed.</p>
<form class="form signup" name="newsletter" method="POST" data-netlify="true" netlify-honeypot="company" action="/subscribed">
<input type="hidden" name="form-name" value="newsletter">
<p class="hp"><label>Leave this empty <input name="company" tabindex="-1"></label></p>
<div class="sub-row"><label class="vh" for="foot-email">Email address</label>
<input id="foot-email" type="email" name="email" required autocomplete="email" placeholder="you@example.com">
<button class="btn" type="submit">Join</button></div></form></div>
<p class="colophon">© Van Paugam {2026}. Chicago.</p></div></footer>
<script>(function(){{var r=document.documentElement,b=document.getElementById("theme");if(!b)return;
function dark(){{return r.dataset.theme?r.dataset.theme==="dark":matchMedia("(prefers-color-scheme: dark)").matches}}
function label(){{b.textContent=dark()?"Light":"Dark"}}
label();b.addEventListener("click",function(){{r.dataset.theme=dark()?"light":"dark";
try{{localStorage.setItem("vp-theme",r.dataset.theme)}}catch(e){{}}label()}});}})();</script>
</body></html>"""

def write(path,body,title,desc,img=None,date=None):
    d=os.path.join(OUT,path.strip("/")); os.makedirs(d,exist_ok=True)
    open(os.path.join(d,"index.html"),"w",encoding="utf-8").write(head(path,title,desc,img,date)+body+FOOT)

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


COVERS={}
def ckey(x): return re.sub(r"[^a-z0-9]","",re.sub(r"\[[^\]]*\]|\([^)]*\)","",x).lower())
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
        art=(f'<img src="{cov}" alt="" loading="lazy">' if cov
             else f'<div class="sleeve-ph"><span>{html.escape(title)}</span></div>')
        eb=shop_links(artist,title)[0][1]
        shops="".join(f'<a href="{h}" target="_blank" rel="sponsored noopener">{n}</a>' for n,h in shop_links(artist,title))
        cards+=(f'<li><a class="disc-art" href="{eb}" target="_blank" rel="sponsored noopener">{art}</a>'
                f'<h4>{html.escape(title)}{f" <span class=\'meta\'>{alt}</span>" if alt else ""}</h4>'
                f'<p class="shops">{shops}</p></li>')
    return (f'<div class="records"><h2 style="margin:0">The rest of the {html.escape(artist)} catalogue '
            f'<span class="jp">{jp}</span></h2><ul class="disc-grid">{cards}</ul>'
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
def list_layout(body):
    body=re.sub(r'<div class="video">.*?</iframe></div>','',body,flags=re.S)
    body=re.sub(r'<p class="buy-row">.*?</p>',"",body,flags=re.S)
    heads=[]
    for m in re.finditer(r"<h2[^>]*>(.*?)</h2>",body,re.S):
        t=_txt(m.group(1)); pm=PAIR.match(t) if t else None
        if pm and ok_pair(pm.group(1).strip(),pm.group(2).strip()): heads.append((m,pm))
    if len(heads)<8: return body,False
    intro=re.sub(r"<h2[^>]*>\s*</h2>","",body[:heads[0][0].start()])
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
        fig=(f'<a class="al-cover" href="{eb}" target="_blank" rel="sponsored noopener">{img}</a>' if img else "")
        out.append(f'<section class="album"><header class="al-head"><span class="rank">{i+1:02d}</span>'
                   f'<h2><span class="al-artist">{html.escape(a)}</span><span class="al-title">{html.escape(ti)}</span>'
                   f'<span class="al-year">{yr}</span></h2></header>'
                   f'<div class="al-main">{fig}<div class="al-text">{txt}</div></div>{buy_row(a,ti,None)}</section>')
    if outro: out.append(f'<div class="al-outro">{outro}</div>')
    return "".join(out),True

AUTO={"/blog/2020/10/19/the-top-10-city-pop-albums":"Buy these albums",
      "/blog/city-pop-top-albums-list":"Buy these albums",
      "/blog/2020/10/20/city-pop-summer":"Buy these records"}
PAIR=re.compile(r"^(?:#?\s*\d+[.)]\s*)?([^-\u2013\u2014]{2,45}?)\s*[-\u2013\u2014]\s*([^-\u2013\u2014]{2,70}?)(?:\s*[\(\[](\d{4})[\)\]])?\s*$")
def _txt(x): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>","",x))).strip()
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
    elif link==LISTPOST:
        body,_inlined=list_layout(body)
        if not _inlined: body,_inlined=inline_buy(body)
    elif link==TOP10:
        body,_inlined=top10_layout(body)
        if not _inlined: body,_inlined=inline_buy(body)
    elif link in AUTO:
        body,_inlined=inline_buy(body)
    if typ=="post":
        col="/"+link.strip("/").split("/")[0]
        cover=f'<figure class="cover"><img src="{thumb}" alt="" loading="lazy"></figure>' if thumb and thumb not in body else ""
        art=(f'<div class="wrap narrow"><div class="article-head"><p class="meta">{date}</p>'
             f'<h1>{html.escape(title)}</h1><div class="lede-rule"></div></div>{cover}'
             f'<div class="prose{" top10" if link in (TOP10,LISTPOST) else ""}">{body}</div>{_disc or ("" if _inlined else auto_block(link,body))}'
             f'<p style="padding:1.5rem 0 2rem"><a href="{col}">← All {dict(NAV).get(col,"posts").lower()}</a></p></div>')
        write(link,art,title,desc,thumb,date)
        cols.setdefault(col,[]).append((date,link,title,desc,thumb)); urls.append((link,date))
    else:
        if not re.sub(r"<[^>]+>","",body).strip(): continue
        pages[link]=(title,desc,body,thumb)


names={"/blog":("Writing","記事","Essays and reporting on Japanese City Pop — its records, its people, and how a 1980s genre found a second life."),
       "/latest-news":("News","最新情報","Press, interviews, and upcoming dates."),
       "/news1":("Archive","記録","Earlier press and event notes, 2017–2020."),
       "/podcast":("Mayonaka Hour","真夜中アワー","A City Pop podcast: one artist, one era, one record at a time."),
       "/vinyl":("Vinyl","レコード","Japanese reissues and pressings worth your shelf space.")}

def short(t):
    return re.sub(r"^Mayonaka Hour\s*真夜中アワー\s*City Pop Podcast\s*","",t).strip() or t

def entry_li(d,l,t,x,th):
    t=short(t)
    im=f'<img src="{th}" alt="" loading="lazy">' if th else '<div class="no-img"></div>'
    return (f'<li><a class="entry" href="{l}">{im}<div><p class="meta">{d}</p><h3>{html.escape(t)}</h3>'
            f'<p>{html.escape(x)}</p></div></a></li>')

def card(l,t,th,d=""):
    t=short(t)
    im=f'<img src="{th}" alt="" loading="lazy">' if th else '<div class="no-img" style="width:100%;aspect-ratio:1"></div>'
    return f'<li><a class="card" href="{l}">{im}<h3>{html.escape(t)}</h3><p class="meta">{d}</p></a></li>'

for col,posts in cols.items():
    posts.sort(reverse=True)
    nm,jp,blurb=names.get(col,(col.strip("/").title(),"",""))
    if col == "/vinyl":
        listing=f'<ul class="grid">{"".join(card(l,t,th,d) for d,l,t,x,th in posts)}</ul>'
    else:
        listing=f'<ul class="entries">{"".join(entry_li(d,l,t,x,th) for d,l,t,x,th in posts)}</ul>'
    body=(f'<div class="wrap"><div class="page-head"><div class="band-head"><h1>{nm}</h1><span class="jp">{jp}</span></div>'
          f'<p class="hero-lede">{html.escape(blurb)}</p></div>'
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
    m=re.search(r'src="(/img/[^"]+)"',pages["/somehow-city-pop-book"][2]); book_img=m.group(1) if m else None

FEATURED=["/blog/who-is-miki-matsubara",
          "/blog/2020/10/19/the-top-10-city-pop-albums",
          "/blog/city-pop-top-albums-list"]
_byl={r[1]:r for r in cols.get("/blog",[])}
_slides=""; _dots=""
for _i,_p in enumerate([x for x in FEATURED if x in _byl]):
    _d,_l,_t,_x,_th=_byl[_p]
    _slides+=(f'<article class="slide{" on" if _i==0 else ""}" data-i="{_i}">'
      f'<a class="ttl" href="{_l}"><img src="{_th}" alt=""{" fetchpriority=\"high\"" if _i==0 else " loading=\"lazy\""}></a>'
      f'<div><span class="jp">Featured 特集</span><a class="ttl" href="{_l}"><h2>{html.escape(_t)}</h2></a>'
      f'<p class="meta" style="margin:-.3rem 0 1rem">{_d}</p><p>{html.escape(_x)}</p>'
      f'<div class="btn-row"><a class="btn" href="{_l}">Read the story</a></div></div></article>')
    _dots+=f'<button type="button" class="dot{" on" if _i==0 else ""}" data-i="{_i}" aria-label="Featured story {_i+1}"></button>'
FEATURED_HTML=(f'<section class="featured" id="featured"><div class="wrap">'
   f'<div class="slides">{_slides}</div><div class="dots">{_dots}</div></div></section>') if _slides else ""

def tick_link(t):
    a,_,ti = t.partition(" - ")
    q = t if not ti else f"{a} {ti}"
    q = re.sub(r"\s*\[[^\]]*\]","",q).strip()
    h = shop_links("", q)[0][1]
    return f'<i>&#9679;</i><a href="{h}" target="_blank" rel="sponsored noopener">{html.escape(short(t))}</a>'
TICKER="".join(tick_link(t) for _,_,t,_,_ in vin) or "<i>&#9679;</i>Japanese City Pop on original pressings"

TRACKS=[("A1","Writing","記事","/blog","Essays on the records, the people, and how a 1980s genre found a second life."),
        ("A2","Somehow, City Pop","書籍","/somehow-city-pop-book","The first English-language reference book on the genre."),
        ("A3","About","略歴","/about-van-paugam","A decade of nights, a board seat, and a wall of Japanese pressings."),
        ("B1","Buy vinyl","レコード","/buy-vinyl","Where to find reissues and originals, plus what was pressed this month."),
        ("B2","Mayonaka Hour","真夜中アワー","/podcast","One artist, one era, one record at a time."),
        ("B3","Booking","出演依頼","/contact","Clubs, festivals, private rooms. Tell me the date."),]

def track_row(c,t,jp,href,d):
    return (f'<a class="track" href="{href}"><span class="cue">{c}</span>'
            f'<h3>{html.escape(t)} <em>{jp}</em></h3><p>{html.escape(d)}</p></a>')

def strip_li(l,t,th):
    im=f'<img src="{th}" alt="" loading="lazy">' if th else '<div class="ph"></div>'
    return f'<li><a href="/buy-vinyl">{im}<h4>{html.escape(short(t))}</h4></a></li>'

def lead_card(d,l,t,x,th,big=False):
    im=f'<img src="{th}" alt="" loading="lazy">' if th else ""
    return (f'<a class="lead" href="{l}">{im}<p class="meta">{d}</p><h3>{html.escape(t)}</h3>'
            + (f'<p>{html.escape(x)}</p>' if big else "") + '</a>')

HOME_JS = """
(function(){
  var sl=[].slice.call(document.querySelectorAll('#featured .slide')),
      dt=[].slice.call(document.querySelectorAll('#featured .dot')), i=0, timer;
  if(sl.length>1){
    var rm=matchMedia('(prefers-reduced-motion: reduce)').matches;
    function go(n){ sl[i].classList.remove('on'); dt[i].classList.remove('on');
      i=(n+sl.length)%sl.length; sl[i].classList.add('on'); dt[i].classList.add('on'); }
    function start(){ if(!rm) timer=setInterval(function(){go(i+1)},7000) }
    dt.forEach(function(d){ d.addEventListener('click',function(){ clearInterval(timer); go(+d.dataset.i); start(); }) });
    var box=document.getElementById('featured');
    box.addEventListener('mouseenter',function(){clearInterval(timer)});
    box.addEventListener('mouseleave',start);
    start();
  }
})();
(function(){
  var rm = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if ('IntersectionObserver' in window && !rm){
    var io = new IntersectionObserver(function(es){
      es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('seen'); io.unobserve(e.target); } });
    },{rootMargin:'0px 0px -12% 0px'});
    document.querySelectorAll('.reveal').forEach(function(n){ io.observe(n); });
  } else {
    document.querySelectorAll('.reveal').forEach(function(n){ n.classList.add('seen'); });
  }
  if (!rm){
    var plat=document.querySelector('.platter'), slv=document.querySelector('.sleeve'), tick=false;
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
  var enc=encodeURIComponent;
  fetch('/api/reissues').then(function(r){ if(!r.ok) throw 0; return r.json() }).then(function(d){
    var it=(d.items||[]).slice(0,6); if(!it.length) throw 0;
    var ul=document.getElementById('strip'); ul.innerHTML='';
    it.forEach(function(r){
      var q=((r.artist&&r.artist!=='Various Artists'?r.artist:'')+' '+r.title).trim();
      var li=document.createElement('li');
      var cov=r.cover?'<img src="'+r.cover+'" alt="" loading="lazy" referrerpolicy="no-referrer">':'<div class="ph"></div>';
      var a=document.createElement('a');
      a.href='/buy-vinyl'; a.innerHTML=cov+'<h4></h4><p></p>';
      a.querySelector('h4').textContent=r.title; a.querySelector('p').textContent=r.artist;
      li.appendChild(a); ul.appendChild(li);
    });
    document.getElementById('pressed').hidden=false;
  }).catch(function(){});
})();
"""

home=f"""<section class="sideA"><div class="wrap sideA-in">
<div><p class="kicker">SIDE A — 和製ポップス</p>
<h1><span class="ln"><span>Japanese City Pop:</span></span><span class="ln"><span>records, writing,</span></span><span class="ln"><span>and DJ sets.</span></span></h1>
<p class="lede">Van Paugam is the DJ, writer, and vinyl specialist widely credited with the global revival of Japanese City Pop — over a hundred nights in Chicago, Paris, Berlin, and Tokyo, all of it from original Japanese pressings.</p>
<div class="btn-row"><a class="btn" href="/contact">Book a set</a><a class="btn btn-ghost" href="/buy-vinyl">Buy vinyl</a></div></div>
<div class="turntable"><div class="platter" aria-hidden="true"></div>
<figure class="sleeve"><img src="{HERO}" alt="Van Paugam DJing a set from vinyl" fetchpriority="high"></figure></div>
</div>
<div class="ticker"><div class="ticker-track"><span>{TICKER}</span><span aria-hidden="true">{TICKER}</span></div></div>
</section>

{FEATURED_HTML}

<div class="wrap"><nav class="index" aria-label="Sections">
<p class="side-label">SIDE A</p>
{"".join(track_row(*t) for t in TRACKS[:3])}
<p class="side-label">SIDE B</p>
{"".join(track_row(*t) for t in TRACKS[3:])}
</nav>

<section class="band"><div class="band-head"><h2>Latest writing</h2><span class="jp">記事</span><a class="more" href="/blog">All writing</a></div>
<div class="reveal" style="border-top:2px solid var(--shu);margin-bottom:1.75rem"></div>
<div class="lead-grid"><div>{lead_card(*blog[0],big=True) if blog else ''}</div>
<ul class="entries" style="margin:0">{"".join(entry_li(*b) for b in blog[1:4])}</ul></div></section>

<section class="band" id="pressed" hidden><div class="band-head"><h2>Just pressed</h2><span class="jp">新譜</span><a class="more" href="/buy-vinyl">Buy vinyl</a></div>
<div class="reveal" style="border-top:2px solid var(--shu);margin-bottom:1.75rem"></div>
<ul class="strip" id="strip"></ul>
<p class="meta" id="strip-note" style="padding-top:1rem">Reissued or newly pressed this season.</p></section>

<section class="band"><div class="band-head"><h2>On the turntable</h2><span class="jp">プレイリスト</span><a class="more" href="/new-music">New music</a></div>
<div class="reveal" style="border-top:2px solid var(--shu);margin-bottom:1.75rem"></div>
{PLAYLIST}</section>

<section class="band"><div class="band-head"><h2>Somehow, City Pop</h2><span class="jp">書籍</span></div>
<div class="reveal" style="border-top:2px solid var(--shu);margin-bottom:1.75rem"></div>
<div class="feature">{f'<img src="{book_img}" alt="Cover of Somehow, City Pop">' if book_img else ''}
<div><p>The first comprehensive English-language book on City Pop — a definitive guide to a genre that refused to die, and the decades it took to become a global phenomenon.</p>
<div class="btn-row"><a class="btn" href="/somehow-city-pop-book">About the book</a></div></div></div></section>

<section class="band"><div class="band-head"><h2>Mayonaka Hour</h2><span class="jp">真夜中アワー</span><a class="more" href="/podcast">All episodes</a></div>
<div class="reveal" style="border-top:2px solid var(--shu);margin-bottom:1.75rem"></div>
<ul class="entries">{"".join(entry_li(*p) for p in pod)}</ul></section>

<section class="band" id="newsletter"><div class="band-head"><h2>The mailing list</h2><span class="jp">メール</span></div>
<div class="reveal" style="border-top:2px solid var(--shu);margin-bottom:1.75rem"></div>
<div class="feature" style="grid-template-columns:1fr">
<p style="max-width:40rem">New writing, upcoming dates, and a note when something worth owning gets repressed. A few times a year, never more.</p>
<form class="form signup" name="newsletter" method="POST" data-netlify="true" netlify-honeypot="company" action="/subscribed">
<input type="hidden" name="form-name" value="newsletter">
<p class="hp"><label>Leave this empty <input name="company"></label></p>
<label for="nl-email">Email address</label><input id="nl-email" type="email" name="email" required autocomplete="email" placeholder="you@example.com">
<button class="btn" type="submit">Join the list</button></form></div></section>

<section class="band"><div class="band-head"><h2>News</h2><span class="jp">最新情報</span><a class="more" href="/latest-news">All news</a></div>
<div class="reveal" style="border-top:2px solid var(--shu);margin-bottom:1.75rem"></div>
<ul class="entries">{"".join(entry_li(*n) for n in news)}</ul></section></div>
<script>{HOME_JS}</script>"""
write("/",home,"Van Paugam — Japanese City Pop DJ, Writer & Vinyl Specialist",
      "Van Paugam is the DJ, writer, and vinyl specialist widely credited with the global revival of Japanese City Pop. Booking, writing, podcast, and records.",HERO)
urls.append(("/",""))

# ---------- contact ----------
contact=f"""<div class="wrap narrow"><div class="article-head"><h1>Booking &amp; press</h1><div class="lede-rule"></div></div>
<p class="hero-lede">For club nights, festivals, private events, interviews, and licensing. Tell me the date and the room, and I'll come back to you with availability and a rate.</p>
<form class="form" name="contact" method="POST" data-netlify="true" netlify-honeypot="company" action="/thank-you">
<input type="hidden" name="form-name" value="contact">
<p class="hp"><label>Leave this empty <input name="company"></label></p>
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

# ---------- assets ----------
shutil.copy(CSS,os.path.join(OUT,"style.css"))
open(os.path.join(OUT,"sitemap.xml"),"w").write(
  '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
  +"".join(f"  <url><loc>{SITE}{u}</loc>{f'<lastmod>{d}</lastmod>' if d else ''}</url>\n" for u,d in sorted(set(urls)))
  +"</urlset>\n")
open(os.path.join(OUT,"robots.txt"),"w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
extra=[("/home","/"),("/contact-1","/contact"),("/blog-1","/blog"),("/new","/latest-news"),("/city-pop-blog","/blog"),("/new-page-1","/"),("/member-site-homepage-1","/")]
open(os.path.join(OUT,"_redirects"),"w").write(
  "# /api/reissues is served by netlify/functions/reissues.mjs\n"
  "# Squarespace -> static. 301 keeps Google rankings.\n"
  "https://www.vanpaugam.com/*  https://vanpaugam.com/:splat  301!\n"
  +"".join(f"{a}  {b}  301\n" for a,b in redirects+extra if a!=b))
missing=[u for u in images.values() if not os.path.exists(os.path.join(OUT,u.lstrip("/")))]
print(len(urls),"pages,",len(images),"images referenced,",len(missing),"missing images")
