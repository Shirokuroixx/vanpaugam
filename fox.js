/* Hidden foxes and konbini details, sitewide. */
(function(){
  var d=document, rm=matchMedia('(prefers-reduced-motion: reduce)').matches;
  var C={K:'#0E1626',O:'#E8772E',W:'#F3F2ED',R:'#C2422B',P:'#F2A08C',E:'#0E1626',S:'#B9C0CC',B:'#2F5DA8',G:'#3A3F4B',N:'#1B2A1F'};
  function px(rows,keys){var o='';rows.forEach(function(r,y){for(var x=0;x<r.length;){var c=r[x];if(c!=='.'&&(!keys||keys.indexOf(c)>-1)){var e=x;while(r[e]===c)e++;o+='<rect x="'+x+'" y="'+y+'" width="'+(e-x)+'" height="1" fill="'+C[c]+'"/>';x=e}else x++}});return o}
  function svg(rows,w,h,inner){return '<svg viewBox="0 0 '+w+' '+h+'" shape-rendering="crispEdges" aria-hidden="true">'+(inner||px(rows))+'</svg>'}
  var FOX=['.K..........K.','.KK........KK.','.KOK......KOK.','.KOOKKKKKKOOK.','.KOOOOOOOOOOK.','.KOEEOOOOEEOK.','.KWWOOOOOOWWK.','..KWWWKKWWWK..','...KWWWWWWK...'];
  var DJ=FOX.map(function(r,i){return i>2&&i<6?'R'+r.slice(1,13)+'R':r});
  var ITEMS={
    onigiri:{w:10,h:8,rows:['....KK....','...KWWK...','..KWWWWK..','.KWWWWWWK.','.KWWWWWWK.','KWWKKKKWWK','KWWKNNKWWK','KKKKKKKKKK'],say:['おにぎり!','Tuna mayo, of course']},
    ramen:{w:10,h:8,rows:['KKKKKKKKKK','KRRRRRRRRK','.KWWWWWWK.','.KRRRRRRK.','.KWWWWWWK.','..KWWWWK..','..KWWWWK..','..KKKKKK..'],say:['3 minutes…','ずるずる'],steam:1},
    coffee:{w:6,h:9,rows:['.KKKK.','KSSSSK','KBBBBK','KBWWBK','KBWWBK','KBBBBK','KBBBBK','KSSSSK','.KKKK.'],say:['缶コーヒー','Hot from the shelf']},
    gacha:{w:8,h:7,rows:['..KKKK..','.KRRRRK.','KRRWRRRK','KKKKKKKK','KWWWWWWK','.KWWWWK.','..KKKK..'],say:['ガチャ!','Rare pull ✦']}
  };
  function seed(s){var h=2166136261;for(var i=0;i<s.length;i++){h^=s.charCodeAt(i);h=Math.imul(h,16777619)}return function(){h=Math.imul(h^h>>>15,2246822507);h=Math.imul(h^h>>>13,3266489909);return((h^=h>>>16)>>>0)/4294967296}}
  var rnd=seed(location.pathname);
  function found(){try{return JSON.parse(localStorage.getItem('vp-foxes')||'[]')}catch(e){return[]}}
  var toastEl;
  function toast(t){if(!toastEl){toastEl=d.createElement('div');toastEl.className='fx-toast';toastEl.setAttribute('role','status');d.body.appendChild(toastEl)}
    toastEl.textContent=t;toastEl.classList.remove('on');void toastEl.offsetWidth;toastEl.classList.add('on')}
  function hop(b,say){b.classList.remove('fx-hop');void b.offsetWidth;b.classList.add('fx-hop');if(say){var s=b.querySelector('.fx-say');s.textContent=say}}
  function foxBtn(id,cls){var b=d.createElement('button');b.type='button';b.className='fx-fox '+(cls||'');b.setAttribute('aria-label','A hidden fox');
    b.innerHTML='<span class="fx-say" aria-hidden="true">コン!</span>'+svg(FOX,14,9,px(FOX,'KOW')+'<g class="fx-eyes">'+px(FOX,'E')+'</g>');
    b.addEventListener('click',function(){var f=found(),n=f.indexOf(id)<0;if(n){f.push(id);try{localStorage.setItem('vp-foxes',JSON.stringify(f))}catch(e){}}
      hop(b,n?'コン!':'またね');toast(n?'狐 You found a fox! '+f.length+' found so far.':'You already found this one. '+f.length+' found.')});return b}
  function itemBtn(k){var it=ITEMS[k],b=d.createElement('button');b.type='button';b.className='fx-item fx-'+k;b.setAttribute('aria-label','A little konbini snack');
    b.innerHTML='<span class="fx-say" aria-hidden="true"></span>'+(it.steam?'<i class="fx-steam"></i><i class="fx-steam s2"></i>':'')+svg(it.rows,it.w,it.h);
    var i=0;b.addEventListener('click',function(){hop(b,it.say[i++%it.say.length])});return b}
  // tuck foxes and snacks at the end of headings in the page body
  var hs=Array.from(d.querySelectorAll('main h2, main h3')).filter(function(h){return !h.closest('.slide,.hm-tile,dialog,.fx-skip')&&h.offsetParent!==null});
  for(var i=hs.length-1;i>0;i--){var j=Math.floor(rnd()*(i+1)),t=hs[i];hs[i]=hs[j];hs[j]=t}
  var keys=Object.keys(ITEMS);
  hs.slice(0,2).forEach(function(h,n){h.appendChild(foxBtn(location.pathname+'#'+n))});
  hs.slice(2,4).forEach(function(h){h.appendChild(itemBtn(keys[Math.floor(rnd()*keys.length)]))});
  // a neon sign in the footer, and a DJ fox by the footer signup
  var col=d.querySelector('.colophon');
  if(col){var ne=d.createElement('span');ne.className='fx-neon';ne.setAttribute('aria-hidden','true');ne.textContent='営業中 24H';col.appendChild(ne)}
  var fs=d.querySelector('.foot-sub');
  if(fs){var dj=d.createElement('button');dj.type='button';dj.className='fx-dj';dj.setAttribute('aria-label','The DJ fox');
    dj.innerHTML='<span class="fx-say" aria-hidden="true">Now spinning ♪</span><span class="fx-note" aria-hidden="true">♪</span><span class="fx-note n2" aria-hidden="true">♫</span>'
      +'<span class="fx-dj-fox">'+svg(DJ,14,9)+'</span><span class="fx-deck"><span class="fx-rec"></span><span class="fx-arm"></span></span>';
    var tunes=['Now spinning ♪','Plastic Love','真夜中のドア','Request? ✦','Ride on Time'],k=0;
    dj.addEventListener('click',function(){dj.classList.toggle('fx-scratch');hop(dj,tunes[k++%tunes.length]);if(!dj.dataset.f){dj.dataset.f=1;var f=found();if(f.indexOf('dj')<0){f.push('dj');try{localStorage.setItem('vp-foxes',JSON.stringify(f))}catch(e){}toast('狐 You found the DJ fox! '+f.length+' found so far.')}}});
    fs.appendChild(dj)}
  // now and then a fox peeks in from the edge of the screen
  if(!rm){var shown=false,edge=foxBtn('edge:'+location.pathname,'fx-edge');d.body.appendChild(edge);
    addEventListener('scroll',function(){if(shown)return;var m=d.documentElement.scrollHeight-innerHeight;if(m>0&&scrollY/m>.45){shown=true;edge.classList.add('peek');setTimeout(function(){edge.classList.remove('peek')},9000)}},{passive:true})}
})();
