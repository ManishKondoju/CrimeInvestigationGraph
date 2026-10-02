"""film.html — cinematic cut. render(f) is a pure function of the frame."""
import json, pathlib

HERE = pathlib.Path(__file__).parent
geo = json.loads((HERE / "geo.json").read_text())
sev = json.loads((HERE / "sev.json").read_text())
net = json.loads((HERE / "network.json").read_text())

DATA = json.dumps({
    "geo": geo, "net": net, "sev": sev,
    "question": "which crimes share the same modus operandi?",
    "cypher": [
        "MATCH (c1:Crime)-[:MATCHES_MO]->(m:ModusOperandi)",
        "      <-[:MATCHES_MO]-(c2:Crime)",
        "WHERE c1.id < c2.id",
        "RETURN m.description, m.signature_element",
    ],
    "moDesc": "Breaking through rear windows at night",
    "moSig": "leaves door unlocked",
})

TEMPLATE = r"""<!doctype html>
<html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
 :root{--sub:#0a0a0a;--rai:#121212;--ph:#eaeaea;--dm:#8a8a8a;--fa:#4a4a4a;
       --hz:#e61919;--tm:#4af626;--ru:#2a2a2a}
 *{margin:0;padding:0;box-sizing:border-box}
 html,body{width:1920px;height:1080px;overflow:hidden;background:#000;color:var(--ph);
   font-family:'JetBrains Mono',monospace}
 #stage{position:relative;width:1920px;height:1080px;background:var(--sub);overflow:hidden}
 #cam{position:absolute;inset:0;transform-origin:50% 50%}
 .L{position:absolute;inset:0}
 .grid{background-image:linear-gradient(to right,rgba(234,234,234,.03) 1px,transparent 1px),
   linear-gradient(to bottom,rgba(234,234,234,.03) 1px,transparent 1px);background-size:72px 72px}
 /* 2.39:1 bars, present from frame 0 */
 .bar{position:absolute;left:0;right:0;height:114px;background:#000;z-index:95}
 #barT{top:0} #barB{bottom:0}
 .scan{background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.20) 2px,rgba(0,0,0,.20) 4px);z-index:92}
 .vig{z-index:91}
 #flash{position:absolute;inset:0;background:#fff;z-index:94;opacity:0}
 #wipe{position:absolute;top:0;bottom:0;width:46%;background:var(--hz);z-index:93;left:-50%}
 .tel{font-size:20px;letter-spacing:.17em;text-transform:uppercase;color:var(--dm)}
 .disp{font-family:'Archivo Black',sans-serif;text-transform:uppercase;letter-spacing:-.035em;line-height:.88}
 .hz{color:var(--hz)}
 /* masked line reveal: the mask moves, the type does not fade */
 .mask{overflow:hidden;display:block}
 .mask>span{display:block}
 #hud{position:absolute;left:84px;right:84px;top:142px;display:flex;justify-content:space-between;z-index:60}
 #hudB{position:absolute;left:84px;right:84px;bottom:142px;display:flex;justify-content:space-between;z-index:60}
 #cap{position:absolute;left:84px;top:430px;width:1500px;z-index:55}
 #cap .l1{font-size:126px} #cap .l2{font-size:126px}
 #kick{position:absolute;left:84px;top:380px;z-index:55}
 #mast{position:absolute;left:84px;top:330px;z-index:55}
 #mast .disp{font-size:216px}
 #mrule{position:absolute;left:84px;top:742px;height:7px;background:var(--hz);z-index:55}
 #msub{position:absolute;left:84px;top:782px;font-size:27px;letter-spacing:.09em;color:var(--dm);z-index:55}
 #map{position:absolute;inset:0}
 #netw{position:absolute;inset:0}
 #term{position:absolute;left:84px;top:392px;width:1752px;border:1px solid var(--ru);background:rgba(18,18,18,.92);z-index:55}
 #th{border-bottom:1px solid var(--ru);padding:15px 26px;display:flex;justify-content:space-between}
 #tb{padding:38px 40px;min-height:150px}
 #q{font-size:44px;color:var(--ph)}
 #cyp{position:absolute;left:84px;top:628px;width:1010px;border:1px solid var(--ru);background:rgba(18,18,18,.95);z-index:55}
 #ch{border-bottom:1px solid var(--hz);padding:13px 24px;background:var(--hz);color:var(--sub);
   letter-spacing:.17em;font-size:18px;font-weight:700}
 #cb{padding:26px 26px;font-size:20px;line-height:1.8;white-space:pre;color:var(--dm)}
 #ans{position:absolute;left:1140px;top:628px;width:696px;border:1px solid var(--ru);background:rgba(18,18,18,.95);z-index:55}
 #ah{border-bottom:1px solid var(--ru);padding:13px 24px;letter-spacing:.17em;font-size:18px;color:var(--dm)}
 #ab{padding:26px 26px;font-size:26px;line-height:1.6;color:var(--dm)}
 #mo{margin-top:22px;border-left:3px solid var(--hz);padding-left:18px;font-size:22px;color:var(--ph)}
 #stats{position:absolute;left:84px;top:470px;display:flex;gap:104px;z-index:55}
 .st .n{font-family:'Archivo Black',sans-serif;font-size:92px;letter-spacing:-.03em;color:var(--ph)}
 #out{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:55}
 #out .disp{font-size:150px}
 #otag{margin-top:40px;font-size:29px;letter-spacing:.05em;color:var(--dm);text-align:center;max-width:1240px;line-height:1.55}
 #ourl{margin-top:34px;font-size:30px;letter-spacing:.22em;color:var(--hz)}
 #fx{z-index:50;pointer-events:none}
 #meters{position:absolute;right:84px;top:300px;width:330px;z-index:56}
 .mt{margin-bottom:17px}
 .mt .lab{display:flex;justify-content:space-between;font-size:16px;letter-spacing:.15em;
   text-transform:uppercase;color:var(--fa);margin-bottom:6px}
 .mt .trk{height:9px;background:rgba(234,234,234,.07);position:relative}
 .mt .fil{position:absolute;inset:0 auto 0 0;background:var(--dm)}
 .mt.hot .fil{background:var(--hz)}
 #slats{position:absolute;inset:0;z-index:93;display:flex;pointer-events:none}
 #slats i{flex:1;background:var(--hz);transform:scaleY(0);transform-origin:bottom}
 #qm{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;z-index:58}
 #qmc{font-family:'Archivo Black',sans-serif;color:var(--hz);line-height:1;display:block}
 #pipe{position:absolute;inset:0;z-index:57}
 .hide{display:none!important}
</style></head><body><div id="stage">
 <div id="cam">
  <div class="L grid" id="gl"></div>
  <div class="L" id="ml"><svg id="map" viewBox="0 0 1920 1080"></svg></div>
  <div class="L" id="nl"><svg id="netw" viewBox="0 0 1920 1080"></svg></div>
  <div class="L" id="fx"><svg id="fxs" viewBox="0 0 1920 1080"></svg></div>
  <div id="meters" class="hide"></div>
  <div id="slats"></div>

  <div id="kick" class="tel hide"></div>
  <div id="cap" class="hide">
    <span class="mask"><span class="disp l1" id="c1"></span></span>
    <span class="mask"><span class="disp l2" id="c2"></span></span>
  </div>

  <div id="mast" class="hide">
    <span class="mask"><span class="disp" id="m1">CRIME</span></span>
    <span class="mask"><span class="disp" id="m2">GRAPH<span class="hz">RAG</span></span></span>
  </div>
  <div id="mrule" class="hide"></div><div id="msub" class="hide"></div>

  <div id="term" class="hide"><div id="th"><span class="tel">QUERY INPUT</span><span class="tel" id="thint"></span></div>
    <div id="tb"><span class="hz" style="font-size:44px">&gt;&nbsp;</span><span id="q"></span><span id="car" class="hz" style="font-size:44px">_</span></div></div>
  <div id="cyp" class="hide"><div id="ch">AGENT-WRITTEN CYPHER</div><div id="cb"></div></div>
  <div id="ans" class="hide"><div id="ah">ANSWER</div><div id="ab"><span id="at"></span><div id="mo" class="hide"></div></div></div>

  <div id="qm" class="hide"><span id="qmc">?</span></div>
  <div id="pipe" class="hide"><svg id="pipes" viewBox="0 0 1920 1080"></svg></div>
  <div id="stats" class="hide"></div>
  <div id="out" class="hide"><div class="disp" id="o1">CRIME<span class="hz">GRAPH</span>RAG</div>
    <div id="otag"></div><div id="ourl"></div></div>
 </div>
 <div class="L vig" id="vg"></div><div class="L scan"></div>
 <div id="wipe"></div><div id="flash"></div>
 <div class="bar" id="barT"></div><div class="bar" id="barB"></div>
 <div id="hud"><span class="tel" id="h1"></span><span class="tel" id="h2"></span></div>
 <div id="hudB"><span class="tel" id="h3"></span><span class="tel" id="h4"></span></div>
</div>
<script>
const D=__DATA__, FPS=30, TOTAL=720;
const S={open:[0,70],prob:[70,150],turn:[150,250],title:[250,330],ask:[330,410],
         hand:[410,460],pay:[460,600],out:[600,720]};
const cl=(v,a,b)=>Math.max(a,Math.min(b,v)), pr=(f,s)=>cl((f-S[s][0])/(S[s][1]-S[s][0]),0,1);
const inS=(f,s)=>f>=S[s][0]&&f<S[s][1];
const eo=t=>1-Math.pow(1-t,3), eio=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
const eoq=t=>1-Math.pow(1-t,5);
const $=i=>document.getElementById(i), sh=(e,o)=>e.classList.toggle('hide',!o);
const NS='http://www.w3.org/2000/svg';

// ---- map from REAL coordinates, sized to full frame ----
const la=D.geo.map(g=>g.lat), lo=D.geo.map(g=>g.lon);
const a0=Math.min(...la),a1=Math.max(...la),o0=Math.min(...lo),o1=Math.max(...lo);
const mp=D.geo.map(g=>({x:660+((g.lon-o0)/(o1-o0))*1120,y:120+((a1-g.lat)/(a1-a0))*840,
  hot:['high','critical','severe'].includes(g.sev)}));
const msvg=$('map');
const mc=mp.map(p=>{const c=document.createElementNS(NS,'circle');
  c.setAttribute('cx',p.x);c.setAttribute('cy',p.y);c.setAttribute('r',p.hot?4:2.8);
  c.setAttribute('fill',p.hot?'#e61919':'#8a8a8a');msvg.appendChild(c);return c;});
// proximity links - the "connections" that appear in the turn
const links=[];
for(let i=0;i<mp.length;i+=3){
  let best=-1,bd=1e9;
  for(let j=0;j<mp.length;j+=3){ if(i===j)continue;
    const d=(mp[i].x-mp[j].x)**2+(mp[i].y-mp[j].y)**2;
    if(d<bd){bd=d;best=j;} }
  if(best>=0&&bd<9000){const l=document.createElementNS(NS,'line');
    l.setAttribute('x1',mp[i].x);l.setAttribute('y1',mp[i].y);
    l.setAttribute('x2',mp[best].x);l.setAttribute('y2',mp[best].y);
    l.setAttribute('stroke','#e61919');l.setAttribute('stroke-width','1');
    l.setAttribute('opacity','0');msvg.appendChild(l);links.push(l);}
}
// ---- network from REAL /api/network ----
const nsvg=$('netw'), ids=[...new Set(D.net.nodes.map(n=>n.id))], ps={};
ids.forEach((id,i)=>{const a=(i/ids.length)*Math.PI*2,r=(i%3===0)?330:235;
  ps[id]={x:1300+r*Math.cos(a),y:560+r*Math.sin(a)*.8};});
const nl=D.net.edges.map(e=>{const a=ps[e.source],b=ps[e.target];if(!a||!b)return null;
  const l=document.createElementNS(NS,'line');l.setAttribute('x1',a.x);l.setAttribute('y1',a.y);
  l.setAttribute('x2',b.x);l.setAttribute('y2',b.y);l.setAttribute('stroke','#8a8a8a');
  l.setAttribute('stroke-width','1.2');nsvg.appendChild(l);return l;}).filter(Boolean);
const nc=D.net.nodes.map(n=>{const q=ps[n.id],c=document.createElementNS(NS,'circle');
  c.setAttribute('cx',q.x);c.setAttribute('cy',q.y);const org=n.type==='Organization';
  c.setAttribute('r',org?15:8);c.setAttribute('fill',org?'#e61919':'#8a8a8a');nsvg.appendChild(c);return c;});

// ---------- motion-graphics engine ----------
const fxs=$('fxs');
const mk=(t,a)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);fxs.appendChild(e);return e;};

// corner brackets - frame furniture that breathes with the camera
const CB=[];
[[150,190,1,1],[1770,190,-1,1],[150,890,1,-1],[1770,890,-1,-1]].forEach(([x,y,sx,sy])=>{
  CB.push(mk('path',{d:`M${x} ${y+38*sy} L${x} ${y} L${x+38*sx} ${y}`,
    fill:'none',stroke:'#e61919','stroke-width':2,opacity:0}));});

// radar sweep over the incident field
const sweepG=mk('g',{opacity:0});
const sweepLine=document.createElementNS(NS,'line');
Object.entries({x1:1220,y1:540,x2:1220,y2:120,stroke:'#e61919','stroke-width':2.5,opacity:.55})
  .forEach(([k,v])=>sweepLine.setAttribute(k,v));
sweepG.appendChild(sweepLine);
[130,240,350].forEach(r=>{const c=document.createElementNS(NS,'circle');
  Object.entries({cx:1220,cy:540,r:r,fill:'none',stroke:'#e61919','stroke-width':.8,opacity:.18})
    .forEach(([k,v])=>c.setAttribute(k,v));sweepG.appendChild(c);});

// tracking reticles that lock onto real hot incidents
const hotPts=mp.filter(p=>p.hot).filter((_,i)=>i%37===0).slice(0,4);
const RET=hotPts.map(p=>{
  const g=document.createElementNS(NS,'g');g.setAttribute('opacity','0');
  const S=30;
  [[-1,-1],[1,-1],[-1,1],[1,1]].forEach(([sx,sy])=>{
    const b=document.createElementNS(NS,'path');
    b.setAttribute('d',`M${p.x+sx*S} ${p.y+sy*S-sy*12} L${p.x+sx*S} ${p.y+sy*S} L${p.x+sx*S-sx*12} ${p.y+sy*S}`);
    b.setAttribute('fill','none');b.setAttribute('stroke','#e61919');b.setAttribute('stroke-width','2');
    g.appendChild(b);});
  const r=document.createElementNS(NS,'circle');
  Object.entries({cx:p.x,cy:p.y,r:7,fill:'none',stroke:'#e61919','stroke-width':1.4})
    .forEach(([k,v])=>r.setAttribute(k,v));
  g.appendChild(r); fxs.appendChild(g);
  return {g,x:p.x,y:p.y};});

// scan line that passes down the frame
const scanL=mk('rect',{x:0,y:0,width:1920,height:3,fill:'#eaeaea',opacity:0});

// pulse rings fired from graph nodes
const RINGS=[0,1,2].map(()=>mk('circle',{cx:0,cy:0,r:10,fill:'none',stroke:'#e61919','stroke-width':2,opacity:0}));

// deterministic scramble: no Math.random, so frames stay reproducible
const GL='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/\\#*';
function scramble(txt,prog,f){
  const n=Math.floor(prog*txt.length);
  let o='';
  for(let i=0;i<txt.length;i++){
    if(i<n||txt[i]===' ') o+=txt[i];
    else if(i<n+6) o+=GL[(f*31+i*17+i*i)%GL.length];
    else o+=' ';
  }
  return o;
}
// rolling-digit odometer
function roll(el,target,prog){
  // Counts up only. No digit randomisation: it produced values above the
  // target, and a paused frame must never state a figure the graph does
  // not actually hold.
  el.textContent = Math.round(eo(prog)*target).toLocaleString();
}
// severity meters from REAL distribution
const SEV=Object.entries(D.sev).sort((a,b)=>b[1]-a[1]);
const SMAX=Math.max(...SEV.map(s=>s[1]));
$('meters').innerHTML=SEV.map(([k,v])=>
  `<div class="mt ${['high','critical'].includes(k)?'hot':''}"><div class="lab"><span>${k}</span><span data-v="${v}">0</span></div>`+
  `<div class="trk"><div class="fil" data-w="${(v/SMAX*100).toFixed(1)}" style="width:0%"></div></div></div>`).join('');
const mFil=[...document.querySelectorAll('#meters .fil')], mVal=[...document.querySelectorAll('#meters .lab span[data-v]')];
// slat wipe
$('slats').innerHTML=Array.from({length:18},()=>'<i></i>').join('');
const SL=[...document.querySelectorAll('#slats i')];

// ---------- agent pipeline, revealed out of the question mark ----------
const pipes=$('pipes');
const PN=[['EXTRACT',430],['GENERATE',700],['EXECUTE',960],['VALIDATE',1220],['ANSWER',1490]];
const PY_=600;
const pNode=[], pLab=[], pEdge=[];
PN.forEach(([lab,x],i)=>{
  const r=document.createElementNS(NS,'rect');
  Object.entries({x:x-96,y:PY_-30,width:192,height:60,fill:'#121212',
    stroke:(i===3?'#e61919':'#2a2a2a'),'stroke-width':2}).forEach(([k,v])=>r.setAttribute(k,v));
  pipes.appendChild(r); pNode.push(r);
  const tx=document.createElementNS(NS,'text');
  Object.entries({x:x,y:PY_+6,'text-anchor':'middle',fill:(i===3?'#e61919':'#8a8a8a'),
    'font-size':19,'letter-spacing':'0.14em','font-family':"'JetBrains Mono',monospace"})
    .forEach(([k,v])=>tx.setAttribute(k,v));
  tx.textContent=lab; pipes.appendChild(tx); pLab.push(tx);
  if(i<PN.length-1){
    const l=document.createElementNS(NS,'path');
    Object.entries({d:`M${x+96} ${PY_} L${PN[i+1][1]-96} ${PY_}`,fill:'none',
      stroke:'#8a8a8a','stroke-width':2}).forEach(([k,v])=>l.setAttribute(k,v));
    pipes.appendChild(l); pEdge.push(l);
  }
});
// the retry arc - the behaviour that makes this an agent and not a translator
const retry=document.createElementNS(NS,'path');
Object.entries({d:`M1220 ${PY_+32} C1220 ${PY_+150} 700 ${PY_+150} 700 ${PY_+32}`,
  fill:'none',stroke:'#e61919','stroke-width':2.5,'stroke-dasharray':'8 7'})
  .forEach(([k,v])=>retry.setAttribute(k,v));
pipes.appendChild(retry);
const retryLab=document.createElementNS(NS,'text');
Object.entries({x:960,y:PY_+176,'text-anchor':'middle',fill:'#e61919','font-size':20,
  'letter-spacing':'0.2em','font-family':"'JetBrains Mono',monospace"})
  .forEach(([k,v])=>retryLab.setAttribute(k,v));
retryLab.textContent='RETRY ON FAILURE'; pipes.appendChild(retryLab);
const pipeAll=[...pNode,...pLab,...pEdge,retry,retryLab];

const STATS=[['NODES',1868],['RELATIONSHIPS',2738],['CRIMES',670],['DISTRICTS',41]];
$('stats').innerHTML=STATS.map(s=>`<div class="st"><div class="tel" style="color:var(--fa)">${s[0]}</div><div class="n" data-t="${s[1]}">0</div></div>`).join('');
const sEl=[...document.querySelectorAll('#stats .n')];

// masked line reveal: translateY under overflow:hidden
function line(el,t,delay=0){
  const p=eoq(cl((t-delay)/.42,0,1));
  el.style.transform=`translateY(${(1-p)*110}%)`;
  el.parentElement.style.opacity=p>0?1:0;
}
function render(f){
  const E={gl:$('gl'),ml:$('ml'),nl:$('nl'),kick:$('kick'),cap:$('cap'),mast:$('mast'),mtr:$('meters'),qm:$('qm'),pipe:$('pipe'),
    mrule:$('mrule'),msub:$('msub'),term:$('term'),cyp:$('cyp'),ans:$('ans'),stats:$('stats'),out:$('out')};
  Object.values(E).forEach(e=>sh(e,false));
  sh(E.gl,true);
  $('h1').textContent='CRIMEGRAPHRAG®'; $('h2').textContent='CHICAGO / 2026';
  $('h3').textContent='NEO4J AURA'; $('h4').textContent='LANGGRAPH AGENT';
  [$('h1'),$('h2'),$('h3'),$('h4')].forEach(e=>e.style.opacity=f<40?0:.55);

  // ---- camera: continuous push, per scene. Never a static frame. ----
  let sc=1, tx=0, ty=0;
  for(const k of Object.keys(S)){ if(inS(f,k)){ const t=pr(f,k);
    sc=1.015+t*0.045; tx=(k==='prob'||k==='turn')?-t*26:t*8; ty=-t*10; } }
  $('cam').style.transform=`scale(${sc}) translate(${tx}px,${ty}px)`;
  // parallax: background drifts against the camera
  E.gl.style.transform=`translate(${-tx*1.8}px,${-ty*1.4}px)`;

  // ---- vignette breathes, heavier in the dark beats ----
  const vg=f<250?.72:.5;
  $('vg').style.background=`radial-gradient(ellipse at 50% 50%,transparent ${44+Math.sin(f/30)*3}%,rgba(0,0,0,${vg}) 100%)`;

  // ---- MG layer ----
  // corner brackets: in after the cold open, pulsing subtly
  const cbOn=f>45&&f<700?.75+Math.sin(f/18)*.18:0;
  CB.forEach(b=>b.setAttribute('opacity',cbOn));
  // scan line descends on a slow loop
  scanL.setAttribute('y',(f*9)%1200-60);
  scanL.setAttribute('opacity', f>40&&f<580 ? .05 : 0);
  // radar sweep during the problem beat
  if(inS(f,'prob')||inS(f,'open')){
    const a=(f*4.2)%360;
    sweepG.setAttribute('opacity',inS(f,'prob')?.8:.25);
    sweepLine.setAttribute('transform',`rotate(${a} 1220 540)`);
  } else sweepG.setAttribute('opacity',0);
  // reticles lock on, one after another, during the problem
  RET.forEach((r,i)=>{
    const on=inS(f,'prob')&&pr(f,'prob')>(.18+i*.16);
    const g=cl((f-(S.prob[0]+(.18+i*.16)*80))/9,0,1);
    r.g.setAttribute('opacity',on?.95:0);
    r.g.setAttribute('transform',on?`translate(${r.x} ${r.y}) scale(${1.6-g*.6}) translate(${-r.x} ${-r.y})`:'');
  });
  // pulse rings off the graph during the turn
  RINGS.forEach((ring,i)=>{
    if(!inS(f,'turn')){ring.setAttribute('opacity',0);return;}
    const ph=((f-S.turn[0])/26+i*.33)%1;
    const src=mp[(i*131)%mp.length];
    ring.setAttribute('cx',src.x);ring.setAttribute('cy',src.y);
    ring.setAttribute('r',10+ph*120);
    ring.setAttribute('opacity',(1-ph)*.5);
  });
  // data flowing along the network edges
  nl.forEach((l,i)=>{l.setAttribute('stroke-dasharray','5 11');
    l.setAttribute('stroke-dashoffset',String(-(f*1.6+i*4)%16));});
  // slat wipe on act breaks - geometric, not a crossfade
  SL.forEach((el,i)=>{
    let v=0;
    [250].forEach(wf=>{ const d=f-(wf-14+i*0.5);
      if(d>=0&&d<9) v=Math.max(v,d/9); else if(d>=9&&d<18) v=Math.max(v,1-(d-9)/9); });
    el.style.transform=`scaleY(${v})`;
    el.style.transformOrigin=(i%2?'top':'bottom');
  });

  // ---- act wipes + impact flashes ----
  let wl=-50;
  [[250,'in']].forEach(([wf])=>{ if(f>=wf-9&&f<wf+9) wl=-50+((f-(wf-9))/18)*150; });
  $('wipe').style.left=wl+'%';
  // flash on the title, and on the instant the pipeline resolves
  $('flash').style.opacity = (f===250||f===251) ? .85 : (f===446 ? .5 : 0);

  // ================= 1 COLD OPEN =================
  if(inS(f,'open')){
    const t=pr(f,'open'); sh(E.kick,true); sh(E.cap,true);
    E.kick.style.opacity=eo(cl(t*4,0,1)); E.kick.textContent='CITY OF CHICAGO / CRIME RECORD';
    $('c1').textContent=scramble('670',cl((t-.14)/.3,0,1),f);
    $('c2').textContent=scramble('RECORDED CRIMES',cl((t-.30)/.34,0,1),f);
    line($('c1'),t,.14); line($('c2'),t,.30);
    sh(E.ml,true); E.ml.style.opacity=cl((t-.55)*1.6,0,1)*.5;
    mc.forEach((c,i)=>c.style.opacity=(i/mc.length)<cl((t-.55)*2,0,1)?1:0);
  }
  // ================= 2 THE PROBLEM =================
  if(inS(f,'prob')){
    const t=pr(f,'prob'); sh(E.ml,true); sh(E.cap,true); sh(E.kick,true);
    E.kick.style.opacity=.55; E.kick.textContent='THE PROBLEM';
    E.ml.style.opacity=.85; mc.forEach(c=>c.style.opacity=1);
    sh(E.mtr,true); E.mtr.style.opacity=1;
    const mg=cl((t-.3)/.5,0,1);
    mFil.forEach((el,i)=>el.style.width=`${eo(cl(mg*1.4-i*.12,0,1))*(+el.dataset.w)}%`);
    mVal.forEach((el,i)=>el.textContent=Math.round(eo(cl(mg*1.4-i*.12,0,1))*(+el.dataset.v)));
    $('c1').textContent=scramble('EVERY CONNECTION',cl((t-.05)/.3,0,1),f);
    $('c2').textContent=scramble('IS INVISIBLE',cl((t-.20)/.3,0,1),f);
    line($('c1'),t,.05); line($('c2'),t,.20);
  }
  // ================= 3 THE TURN =================
  if(inS(f,'turn')){
    const t=pr(f,'turn'); sh(E.ml,true); sh(E.cap,true); sh(E.kick,true);
    sh(E.mtr,true); E.mtr.style.opacity=1-cl((t-.55)/.3,0,1);
    E.kick.style.opacity=.55; E.kick.textContent='UNLESS';
    E.ml.style.opacity=.95; mc.forEach(c=>c.style.opacity=1);
    // edges draw in, staggered - the structure emerging is the whole point
    links.forEach((l,i)=>l.style.opacity=(i/links.length)<cl((t-.08)*1.7,0,1)?.55:0);
    $('c1').textContent=scramble('YOU MAKE IT',cl((t-.30)/.26,0,1),f);
    $('c2').innerHTML=(t>.52)?'A <span class="hz">GRAPH</span>':scramble('A GRAPH',cl((t-.44)/.1,0,1),f);
    line($('c1'),t,.30); line($('c2'),t,.44);
  }
  // ================= 4 TITLE =================
  if(inS(f,'title')){
    const t=pr(f,'title'); sh(E.ml,true); sh(E.mast,true); sh(E.mrule,true); sh(E.msub,true);
    E.ml.style.opacity=.3; mc.forEach(c=>c.style.opacity=1);
    links.forEach(l=>l.style.opacity=.2);
    E.mast.style.opacity=1; line($('m1'),t,.04); line($('m2'),t,.16);
    E.mrule.style.width=`${eio(cl((t-.34)*2.2,0,1))*820}px`;
    E.msub.style.opacity=cl((t-.52)*3,0,1);
    E.msub.textContent='A CRIME KNOWLEDGE GRAPH YOU CAN INTERROGATE';
  }
  // ================= 5 ASK =================
  if(inS(f,'ask')){
    const t=pr(f,'ask'); sh(E.term,true); sh(E.ml,true); sh(E.kick,true);
    E.kick.style.opacity=.55; E.kick.textContent='NO QUERY LANGUAGE REQUIRED';
    E.ml.style.opacity=.14; mc.forEach(c=>c.style.opacity=1); links.forEach(l=>l.style.opacity=.1);
    const a=eoq(cl(t*3.2,0,1));
    E.term.style.opacity=a; E.term.style.transform=`translateY(${(1-a)*54}px)`;
    const n=Math.floor(cl((t-.16)/.52,0,1)*D.question.length);
    $('q').textContent=D.question.slice(0,n);
    $('car').style.opacity=(f%20<10)?1:0;
    $('thint').textContent=t>.84?'TRANSMITTING':'';
    sh(E.qm,false);
  }
  // ============ 5.5 HANDOFF: the question mark becomes the agent ============
  // The '?' is the moment of asking. Pushing into it and resolving the
  // pipeline out of it puts the agent loop on screen - the one thing the
  // film otherwise only asserts.
  if(inS(f,'hand')){
    const t=pr(f,'hand');
    sh(E.term,true); sh(E.qm,true);
    // phase 1 (0-.34): terminal recedes, the mark is isolated and lit
    // phase 2 (.34-.62): hard push into the mark
    // phase 3 (.62-1): mark dissolves, pipeline resolves out of it
    const dim=(1-cl(t/.3,0,1)*0.88) * (1-cl((t-.52)/.16,0,1));
    E.term.style.opacity=dim;
    $('q').textContent=D.question.slice(0,-1);   // mark lifted out, shown below
    $('car').style.opacity=0; $('thint').textContent='';
    E.term.style.transform=`scale(${1-cl(t/.5,0,1)*0.16})`;

    const grow=eoq(cl(t/.62,0,1));
    const size=70+grow*620;
    const qc=$('qmc');
    qc.style.fontSize=size+'px';
    qc.style.opacity = t<.62 ? 1 : 1-cl((t-.62)/.2,0,1);
    // glow builds, then blows out as it dissolves
    const gl=12+grow*70;
    qc.style.textShadow=`0 0 ${gl}px rgba(230,25,25,${.35+grow*.5})`;
    qc.style.transform=`scale(${1+Math.sin(t*22)*0.012*(1-grow)})`;

    if(t>.56){
      sh(E.pipe,true);
      const pp=cl((t-.56)/.44,0,1);
      // nodes resolve outward from where the mark was
      pNode.forEach((n,i)=>{
        const a=eoq(cl(pp*1.5-i*0.1,0,1));
        n.setAttribute('opacity',a);
        const cx=PN[i][1];
        n.setAttribute('transform',`translate(${(960-cx)*(1-a)} ${(1-a)*10}) scale(1)`);
      });
      pLab.forEach((l,i)=>{const a=eoq(cl(pp*1.5-i*0.1-0.06,0,1));
        l.setAttribute('opacity',a);
        l.setAttribute('transform',`translate(${(960-PN[i][1])*(1-a)} ${(1-a)*10})`);});
      pEdge.forEach((e,i)=>e.setAttribute('opacity',eoq(cl(pp*1.6-0.3-i*0.08,0,1))*.8));
      retry.setAttribute('opacity',eoq(cl((pp-.52)/.4,0,1)));
      retry.setAttribute('stroke-dashoffset',String(-(f*2)%15));
      retryLab.setAttribute('opacity',eoq(cl((pp-.62)/.3,0,1)));
    }
  }

  // ================= 6 THE PAYOFF =================
  if(inS(f,'pay')){
    const t=pr(f,'pay'); sh(E.term,true); sh(E.cyp,true); sh(E.kick,true);
    if(t<.3){ sh(E.pipe,true);
      const fade=1-cl(t/.3,0,1);
      pipeAll.forEach(el=>el.setAttribute('opacity',(+el.getAttribute('opacity')||1)*fade));
      E.pipe.style.transform=`translateY(${-cl(t/.3,0,1)*90}px)`;
    }
    E.kick.style.opacity=.55; E.kick.textContent='IT SHOWS ITS WORKING';
    E.term.style.opacity=1; E.term.style.transform='none';
    $('q').textContent=D.question; $('car').style.opacity=0; $('thint').textContent='RESOLVED';
    const ca=eoq(cl(t*5,0,1)); E.cyp.style.opacity=ca;
    E.cyp.style.transform=`translateY(${(1-ca)*30}px)`;
    const full=D.cypher.join('\n'), n=Math.floor(cl((t-.04)/.40,0,1)*full.length);
    $('cb').innerHTML=full.slice(0,n).replace(/MATCHES_MO|ModusOperandi/g,m=>`<span class="hz">${m}</span>`)
      +(t<.46&&f%16<8?'<span class="hz">_</span>':'');
    if(t>.44){ sh(E.ans,true);
      const aa=eoq(cl((t-.44)/.26,0,1));
      E.ans.style.opacity=aa; E.ans.style.transform=`translateX(${(1-aa)*60}px)`;
      $('at').innerHTML='<span style="color:var(--ph);font-weight:700">50</span> crimes share one <span style="color:var(--ph);font-weight:700">modus operandi</span>.';
      if(t>.62){ sh($('mo'),true); $('mo').style.opacity=eo(cl((t-.62)/.18,0,1));
        $('mo').innerHTML=`&ldquo;${D.moDesc}&rdquo;<br><span style="color:var(--dm);font-size:19px">SIGNATURE // ${D.moSig}</span>`;
      } else sh($('mo'),false);
    }
  }
  // ================= 7 OUTRO =================
  if(inS(f,'out')){
    const t=pr(f,'out');
    if(t<.52){ sh(E.stats,true); sh(E.nl,true); sh(E.kick,true);
      E.kick.style.opacity=.55; E.kick.textContent='WHAT IS UNDERNEATH';
      const na=eo(cl(t*3,0,1)); E.nl.style.opacity=na*.9;
      nl.forEach((l,i)=>l.style.opacity=(i/nl.length)<cl(t*3.4,0,1)?.5:0);
      nc.forEach((c,i)=>c.style.opacity=(i/nc.length)<cl(t*3.6,0,1)?1:0);
      E.stats.style.opacity=cl(t*5,0,1)*(1-cl((t-.42)/.1,0,1));
      const sa=cl(t/.34,0,1);
      sEl.forEach(e=>roll(e,+e.dataset.t,sa));
    } else { sh(E.out,true);
      const u=cl((t-.52)/.48,0,1), a=eoq(cl(u*2.4,0,1));
      $('o1').style.opacity=a; $('o1').style.transform=`scale(${.955+a*.045})`;
      $('otag').style.opacity=cl((u-.26)*3,0,1);
      $('otag').textContent='Ask it anything in plain English. It writes the query, checks the result, and shows you exactly how it got there.';
      $('ourl').style.opacity=cl((u-.5)*3,0,1);
      $('ourl').textContent='CRIME-INVESTIGATION-GRAPH.VERCEL.APP';
    }
  }
}
window.render=render; window.TOTAL=TOTAL; render(0);
</script></body></html>
"""
(HERE / "film.html").write_text(TEMPLATE.replace("__DATA__", DATA))
print("film.html v2:", (HERE / "film.html").stat().st_size, "bytes")
