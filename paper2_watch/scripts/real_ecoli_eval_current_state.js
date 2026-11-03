// AMR-WATCH detectors on real monthly series (e.g. ARMD E. coli urine) + semi-synthetic planted-rise test.
// Usage: node real_ecoli_eval.js AMR-WATCH-0.21.0.html monthly_ecoli_urine.csv out.json
const fs=require('fs'), vm=require('vm');
const html=fs.readFileSync(process.argv[2],'utf8');
const cut=(a,b)=>{const i=html.indexOf(a), j=html.indexOf(b,i); if(i<0||j<0) throw new Error('marker '+a); return html.slice(i,j);};
const src=[cut('function mulberry32','\n}\n')+'\n}\n', cut('function baselineStats','function buildComparisonChart'),
 html.split('\n').find(l=>l.startsWith('function trWilson')), html.split('\n').find(l=>l.startsWith('function trBinomTail'))].join('\n');
const ctx={Math,Array,Object,Number}; vm.createContext(ctx);
vm.runInContext(src+'\nthis.T={mulberry32,baselineStats,detectMA,detectEWMA,detectCUSUM,trWilson,trBinomTail};',ctx); const T=ctx.T;
const rows=fs.readFileSync(process.argv[3],'utf8').trim().split('\n').map(l=>l.split(',')); const H=rows.shift();
const ix=n=>H.indexOf(n); const S={};
for(const r of rows){ const k=r[ix('version')]+'|'+r[ix('antibiotic')]; (S[k]=S[k]||{})[r[ix('month')]]={n:+r[ix('n')],r:+r[ix('r')]}; }
function months(a,b){ const out=[]; let [y,m]=a.split('-').map(Number); const [yb,mb]=b.split('-').map(Number); while(y<yb||(y===yb&&m<=mb)){ out.push(y+'-'+String(m).padStart(2,'0')); m++; if(m>12){m=1;y++;} } return out; }
const M=months('2008-02','2023-12');
function flags(s){ // CURRENT-STATE measure: only the state at the window end counts
  const v=s.map(x=>x.n?100*x.r/x.n:0), b=T.baselineStats(v), n=v.length; const ma=T.detectMA(v,b.mean), ew=T.detectEWMA(v,b.mean,b.std), cu=T.detectCUSUM(v,b.mean,b.std);
  const f=[ma.flagged, ew.ewma[n-1]>ew.UCL&&ew.ewma[n-2]>ew.UCL, cu.cusum[n-1]>cu.h];
  const l3=s.slice(-3).reduce((t,x)=>({n:t.n+x.n,r:t.r+x.r}),{n:0,r:0}), b6=s.slice(0,6).reduce((t,x)=>({n:t.n+x.n,r:t.r+x.r}),{n:0,r:0});
  const two=f.filter(Boolean).length>=2, sup=l3.r>=5&&l3.n>0&&T.trWilson(l3.r,l3.n)[0]>(b6.n?100*b6.r/b6.n:0);
  const p0=Math.max(0.01,b6.n?b6.r/b6.n:0.01), cnt=l3.r>=3&&T.trBinomTail(l3.r,l3.n,p0)<0.01;
  return {MA:f[0],EWMA:f[1],CUSUM:f[2],two,dashboard:two&&sup,count01:cnt}; }
const KEYS=['MA','EWMA','CUSUM','two','dashboard','count01']; const res={series:{},meta:{windows:'24 months, step 1 (real); step 6 (planted test)'}};
const rng=T.mulberry32(20261101);
function binom(n,p){ let k=0; for(let i=0;i<n;i++) if(rng()<p) k++; return k; }
for(const [key,mo] of Object.entries(S)){
  const ser=M.map(m=>mo[m]||{n:0,r:0}); const out={months_missing:M.filter(m=>!mo[m]).length,real:{},planted:{}};
  // (A) real windows: fraction of windows flagged, and which window-end months flag
  const win=[]; for(let e=24;e<=ser.length;e++){ const f=flags(ser.slice(e-24,e)); win.push({end:M[e-1],...f}); }
  out.real={windows:win.length,alert_share:Object.fromEntries(KEYS.map(k=>[k,win.filter(w=>w[k]).length/win.length])),flagged_ends:Object.fromEntries(KEYS.map(k=>[k,win.filter(w=>w[k]).map(w=>w.end)]))};
  // (B) semi-synthetic: plant a rise (absolute +delta pp over a 4-month ramp from window month 17) into REAL windows, keeping real counts and noise
  for(const delta of [5,10,20]){ let nw=0; const hit=Object.fromEntries(KEYS.map(k=>[k,0])), base=Object.fromEntries(KEYS.map(k=>[k,0]));
    for(let e=24;e<=ser.length;e+=6){ const w=ser.slice(e-24,e); const p6=(()=>{const t=w.slice(0,6).reduce((a,x)=>({n:a.n+x.n,r:a.r+x.r}),{n:0,r:0}); return t.n?t.r/t.n:0;})();
      const f0=flags(w); const w2=w.map((x,i)=>{ if(i<16) return x; const ramp=Math.min(1,(i-15)/4), target=Math.min(0.95,p6+delta/100*ramp), p=x.n?x.r/x.n:0; if(target<=p) return x; const q=(target-p)/(1-p); return {n:x.n,r:x.r+binom(x.n-x.r,q)}; });
      const f1=flags(w2); nw++; KEYS.forEach(k=>{ if(f1[k]) hit[k]++; if(f0[k]) base[k]++; }); }
    out.planted['+'+delta+'pp']={windows:nw,sensitivity:Object.fromEntries(KEYS.map(k=>[k,hit[k]/nw])),alert_share_unmodified:Object.fromEntries(KEYS.map(k=>[k,base[k]/nw]))}; }
  res.series[key]=out; }
fs.writeFileSync(process.argv[4],JSON.stringify(res,null,1));
for(const [k,o] of Object.entries(res.series)) console.log(k,'missing months',o.months_missing,'real alert share',JSON.stringify(o.real.alert_share));
