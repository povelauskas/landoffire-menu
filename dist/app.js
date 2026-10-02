(()=>{const UI=JSON.parse(document.getElementById("ui").textContent),d=document,root=d.documentElement,KEY="lof-lang";
const pick=()=>{try{const s=localStorage.getItem(KEY);if(s&&UI[s])return s}catch(e){}
 const n=(navigator.languages||[navigator.language||"lt"]).map(x=>x.slice(0,2));
 for(const l of n){if(l==="lt"||l==="ru")return l;if(l==="en")return"en"}return n.length&&n[0]!=="lt"?"en":"lt"};
function setLang(l){root.dataset.lang=l;root.lang=l;
 d.querySelectorAll(".langs button").forEach(b=>b.setAttribute("aria-pressed",b.dataset.l===l));
 d.querySelectorAll("[data-ui]").forEach(el=>el.textContent=UI[l][el.dataset.ui]);
 d.querySelectorAll("[data-ph]").forEach(el=>el.placeholder=UI[l][el.dataset.ph]);
 d.querySelectorAll("[data-al]").forEach(el=>el.setAttribute("aria-label",UI[l][el.dataset.al]));
 try{localStorage.setItem(KEY,l)}catch(e){}}
setLang(pick());
d.querySelector(".langs").addEventListener("click",e=>{const b=e.target.closest("button");if(b)setLang(b.dataset.l)});
const bar=d.querySelector(".selbar");
if(bar){
/* selection: guests mark what they want, then show the list to the waiter (not an order) */
const SK="lof-pick",TTL=6*3600e3,ctls=[...d.querySelectorAll(".ctl")],cat=new Map();
ctls.forEach(c=>cat.set(c.dataset.k,{n:c.dataset.n,p:+c.dataset.p,z:JSON.parse(c.dataset.z)}));
let sel={};try{const s=JSON.parse(localStorage.getItem(SK));if(s&&Date.now()-s.t<TTL)sel=s.q}catch(e){}
for(const k in sel)if(!cat.has(k)||!(sel[k]>0))delete sel[k];
const L=()=>UI[root.dataset.lang],eur=c=>(c/100).toFixed(2).replace(".",",")+"\u00a0€",
 zl=z=>z?(typeof z==="string"?z:z[root.dataset.lang]||z.lt):"",
 esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"})[c]),
 step=(k,q,n)=>`<span class="step"><button type="button" data-d="-1" data-k="${esc(k)}" aria-label="${esc(L().less+": "+n)}">−</button><output>${q}</output><button type="button" data-d="1" data-k="${esc(k)}" aria-label="${esc(L().more+": "+n)}">+</button></span>`;
const dlg=d.getElementById("sel"),wv=d.querySelector(".wv"),live=d.getElementById("live");
function paint(){const keys=Object.keys(sel);let n=0,sum=0;
 keys.forEach(k=>{n+=sel[k];sum+=sel[k]*cat.get(k).p});
 ctls.forEach(c=>{const q=sel[c.dataset.k]||0;
  c.innerHTML=q?step(c.dataset.k,q,c.dataset.n):`<button type="button" class="add" data-d="1" data-k="${esc(c.dataset.k)}" aria-label="${esc(L().add+": "+c.dataset.n)}">${esc(L().add)}</button>`});
 d.querySelectorAll("[data-s]").forEach(a=>a.classList.toggle("on",!!a.querySelector(".step")));
 bar.classList.toggle("show",n>0);d.body.classList.toggle("has-sel",n>0);
 bar.querySelector(".cnt").textContent=n;d.querySelectorAll(".sum").forEach(s=>s.textContent=eur(sum));
 const rows=keys.map(k=>{const it=cat.get(k);return{k,it,q:sel[k],z:zl(it.z)}});
 dlg.querySelector(".sl").innerHTML=rows.map(r=>`<li><span class="nm"><b>${esc(r.it.n)}</b>${r.z?`<small>${esc(r.z)}</small>`:""}</span>${step(r.k,r.q,r.it.n)}<span class="lt">${eur(r.q*r.it.p)}</span></li>`).join("");
 dlg.querySelector(".nosel").hidden=n>0;dlg.querySelector(".tot").hidden=!n;dlg.querySelector(".wvb").disabled=!n;
 wv.querySelector("ul").innerHTML=rows.map(r=>{const z=r.it.z&&typeof r.it.z==="object"?r.it.z.lt:r.z; /* staff read Lithuanian */
  return`<li><span class="q">${r.q}×</span><span>${esc(r.it.n)}${z?`<small>${esc(z)}</small>`:""}</span></li>`}).join("");
 try{localStorage.setItem(SK,JSON.stringify({t:Date.now(),q:sel}))}catch(e){}
 return n}
function change(k,dl){const q=Math.max(0,(sel[k]||0)+dl);if(q)sel[k]=q;else delete sel[k];
 const n=paint();live.textContent=L().mine+": "+n}
d.addEventListener("click",e=>{const b=e.target.closest("button[data-d]");if(b)change(b.dataset.k,+b.dataset.d)});
bar.addEventListener("click",()=>dlg.showModal());
dlg.querySelector(".x").addEventListener("click",()=>dlg.close());
dlg.addEventListener("click",e=>{if(e.target===dlg)dlg.close()});
dlg.querySelector(".clr").addEventListener("click",()=>{if(confirm(L().clearq)){sel={};paint();dlg.close()}});
let lock=null;
dlg.querySelector(".wvb").addEventListener("click",async()=>{dlg.close();wv.hidden=false;d.body.style.overflow="hidden";
 try{lock=await navigator.wakeLock?.request("screen")}catch(e){}});
wv.querySelector(".back").addEventListener("click",()=>{wv.hidden=true;d.body.style.overflow="";lock?.release();lock=null;dlg.showModal()});
paint();
d.querySelector(".langs").addEventListener("click",()=>paint());
/* search */
const q=d.getElementById("q"),items=[...d.querySelectorAll("[data-s]")],secs=[...d.querySelectorAll(".sec")],empty=d.querySelector(".empty");
const fold=s=>s.toLowerCase().replace(/ə/g,"e").replace(/ı/g,"i").normalize("NFD").replace(/[\u0300-\u036f]/g,"");
q.addEventListener("input",()=>{const v=fold(q.value.trim());let any=0;
 items.forEach(it=>{const ok=!v||it.dataset.s.includes(v);it.hidden=!ok;any+=ok});
 secs.forEach(s=>s.hidden=!s.querySelector("[data-s]:not([hidden])"));empty.style.display=any?"none":"block"});
/* active section chip */
const links=new Map([...d.querySelectorAll("nav.cats a")].map(a=>[a.dataset.sec,a]));let cur;
const io=new IntersectionObserver(es=>{es.forEach(en=>{if(en.isIntersecting){const a=links.get(en.target.id);
 if(a&&a!==cur){cur&&cur.classList.remove("on");a.classList.add("on");cur=a;
 a.parentNode.scrollTo({left:a.offsetLeft-16,behavior:"smooth"})}}})},{rootMargin:"-30% 0px -65% 0px"});
secs.forEach(s=>io.observe(s));
/* back to top */
}
const tt=d.querySelector(".totop");if(tt){addEventListener("scroll",()=>tt.classList.toggle("show",scrollY>900),{passive:true});
tt.addEventListener("click",()=>scrollTo({top:0}))}
})();
