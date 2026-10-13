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
    if p not in ("img",".git"): shutil.rmtree(os.path.join(OUT,p),ignore_errors=True) if os.path.isdir(os.path.join(OUT,p)) else os.remove(os.path.join(OUT,p))

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
    return IMG_RE.sub(lambda m: local_img(m.group(0)),body)

NAV=[("/about-van-paugam","About"),("/somehow-city-pop-book","The Book"),("/blog","Writing"),
     ("/podcast","Podcast"),("/buy-vinyl","Buy Vinyl"),("/latest-news","News"),("/contact","Contact")]

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
<link rel="stylesheet" href="/style.css">{ld}</head><body>
<header class="site-head"><div class="wrap"><a class="mark" href="/">VAN PAUGAM</a><nav class="site-nav">{nav}</nav></div></header>
<main id="main">"""

FOOT=f"""</main>
<footer class="site-foot"><div class="wrap"><div class="foot-grid">
<div><h4>VAN PAUGAM</h4><p style="margin:0;max-width:22rem">Japanese City Pop on original pressings — writing, radio, and records from Chicago.</p></div>
<div><h4>Read</h4><ul><li><a href="/blog">Writing</a></li><li><a href="/what-is-city-pop">What is City Pop?</a></li><li><a href="/somehow-city-pop-book">The book</a></li><li><a href="/latest-news">News</a></li></ul></div>
<div><h4>Listen</h4><ul><li><a href="/podcast">Mayonaka Hour</a></li><li><a href="/buy-vinyl">Buy vinyl</a></li><li><a href="/vinyl">My picks</a></li><li><a href="/new-music">New music</a></li><li><a href="{SP}" rel="noopener">Spotify</a></li></ul></div>
<div><h4>Contact</h4><ul><li><a href="/contact">Booking &amp; press</a></li><li><a href="mailto:info@vanpaugam.com">info@vanpaugam.com</a></li><li><a href="{IG}" rel="me noopener">Instagram</a></li><li><a href="{FB}" rel="me noopener">Facebook</a></li></ul></div>
</div><p class="colophon">© Van Paugam {2026}. Chicago.</p></div></footer></body></html>"""

def write(path,body,title,desc,img=None,date=None):
    d=os.path.join(OUT,path.strip("/")); os.makedirs(d,exist_ok=True)
    open(os.path.join(d,"index.html"),"w",encoding="utf-8").write(head(path,title,desc,img,date)+body+FOOT)

def plain(s,n=165):
    s=re.sub(r"<figcaption.*?</figcaption>"," ",s or "",flags=re.S)
    s=re.sub(r"\[/?caption[^\]]*\]"," ",s)
    t=re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",s))).strip()
    return (t[:n].rsplit(" ",1)[0]+"…") if len(t)>n else t

# ---------- parse ----------
root=ET.parse(SRC).getroot(); items=root.find("channel").findall("item")
attach={it.findtext("wp:post_id",namespaces=NS):it.findtext("wp:attachment_url",namespaces=NS)
        for it in items if it.findtext("wp:post_type",namespaces=NS)=="attachment"}
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
    if typ=="post":
        col="/"+link.strip("/").split("/")[0]
        cover=f'<figure class="cover"><img src="{thumb}" alt="" loading="lazy"></figure>' if thumb and thumb not in body else ""
        art=(f'<div class="wrap narrow"><div class="article-head"><p class="meta">{date}</p>'
             f'<h1>{html.escape(title)}</h1><div class="lede-rule"></div></div>{cover}'
             f'<div class="prose">{body}</div>'
             f'<p style="padding-bottom:2rem"><a href="{col}">← All {dict(NAV).get(col,"posts").lower()}</a></p></div>')
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

for link,(title,desc,body,thumb) in pages.items():
    if not re.search(r"<h1",body): body=f"<h1>{html.escape(title)}</h1>"+body
    body=re.sub(r"<h1[^>]*>(.*?)</h1>",lambda m:f'<div class="article-head"><h1>{m.group(1)}</h1><div class="lede-rule"></div></div>',body,count=1,flags=re.S)
    write(link,f'<div class="wrap narrow"><div class="prose" style="padding-top:2rem">{body}</div></div>',title,desc,thumb)
    urls.append((link,""))

# ---------- home ----------
def strip_from(col,n):
    return sorted(cols.get(col,[]),reverse=True)[:n]
blog=strip_from("/blog",4); news=strip_from("/latest-news",4); pod=strip_from("/podcast",4); vin=strip_from("/vinyl",4)
book_img=None
if "/somehow-city-pop-book" in pages:
    m=re.search(r'src="(/img/[^"]+)"',pages["/somehow-city-pop-book"][2]); book_img=m.group(1) if m else None
home=f"""<section class="hero-dark"><div class="disc" aria-hidden="true"></div><div class="wrap hero-inner">
<div class="obi">シティ・ポップ</div>
<div><h1>Japanese City Pop, played from the records it was pressed on.</h1>
<p class="hero-lede">Van Paugam is the DJ, writer, and vinyl specialist widely credited with the global revival of Japanese City Pop. Over a hundred nights in Chicago, Paris, Berlin, and Tokyo — all of it from original Japanese pressings.</p>
<div class="btn-row"><a class="btn" href="/contact">Book a set</a><a class="btn btn-ghost" href="/buy-vinyl">Buy vinyl</a></div></div>
<figure class="hero-fig"><img src="{HERO}" alt="Van Paugam DJing a set from vinyl" fetchpriority="high">
<figcaption>A night of original Japanese pressings, Chicago.</figcaption></figure>
</div></section>

<div class="wrap"><section class="band"><div class="band-head"><h2>Writing</h2><span class="jp">記事</span><a class="more" href="/blog">All writing</a></div>
<ul class="entries">{"".join(entry_li(d,l,t,x,th) for d,l,t,x,th in blog)}</ul></section>

<section class="band"><div class="band-head"><h2>Somehow, City Pop</h2><span class="jp">書籍</span></div>
<div class="feature">{f'<img src="{book_img}" alt="Cover of Somehow, City Pop">' if book_img else ''}
<div><p>The first comprehensive English-language book on City Pop — a definitive guide to a genre that refused to die, and the decades it took to become a global phenomenon.</p>
<div class="btn-row"><a class="btn" href="/somehow-city-pop-book">About the book</a></div></div></div></section>

<section class="band"><div class="band-head"><h2>Mayonaka Hour</h2><span class="jp">真夜中アワー</span><a class="more" href="/podcast">All episodes</a></div>
<ul class="entries">{"".join(entry_li(d,l,t,x,th) for d,l,t,x,th in pod)}</ul></section>

<section class="band"><div class="band-head"><h2>Vinyl</h2><span class="jp">レコード</span><a class="more" href="/vinyl">All pressings</a></div>
<ul class="grid">{"".join(card(l,t,th,d) for d,l,t,x,th in vin)}</ul></section>

<section class="band"><div class="band-head"><h2>News</h2><span class="jp">最新情報</span><a class="more" href="/latest-news">All news</a></div>
<ul class="entries">{"".join(entry_li(d,l,t,x,th) for d,l,t,x,th in news)}</ul></section></div>"""
write("/",home,"Van Paugam — Japanese City Pop DJ, Writer & Vinyl Specialist",
      "Van Paugam is the DJ, writer, and vinyl specialist widely credited with the global revival of Japanese City Pop. Booking, writing, podcast, and vinyl.",HERO)
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
      '<a href="'+r.discogs+'" target="_blank" rel="noopener" style="color:var(--mute)">Discogs</a></p></div>';
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
  "# Live reissue feed, proxied so the browser sees it as same-origin.\n"
  "/api/reissues  https://citypopwiki.org/api/reissues  200\n\n"
  "# Squarespace -> static. 301 keeps Google rankings.\n"
  "https://www.vanpaugam.com/*  https://vanpaugam.com/:splat  301!\n"
  +"".join(f"{a}  {b}  301\n" for a,b in redirects+extra if a!=b))
missing=[u for u in images.values() if not os.path.exists(os.path.join(OUT,u.lstrip("/")))]
print(len(urls),"pages,",len(images),"images referenced,",len(missing),"missing images")
