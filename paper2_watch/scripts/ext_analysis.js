// Extended planted-signal analysis for Paper 2 (post hoc, exploratory).
// Uses the shipped AMR-WATCH 0.21.0 functions (extracted from the HTML) and adds:
//  - seasonality and duplicate-isolate options in a COPY of the generator (RNG order for base data unchanged)
//  - extra comparators: count test with BH-FDR / Bonferroni over the 40 series, EARS-C2-style z score
//  - threshold sweeps (sensitivity vs false alerts per dataset)
// Usage: node ext_analysis.js AMR-WATCH-0.21.0.html out.json
const fs=require('fs'), vm=require('vm');
const html=fs.readFileSync(process.argv[2],'utf8');
const cut=(a,b)=>{const i=html.indexOf(a), j=html.indexOf(b,i); if(i<0||j<0) throw new Error('marker '+a); return html.slice(i,j);};
const src=[cut('function mulberry32','\n}\n')+'\n}\n', cut('function baselineStats','function buildComparisonChart'),
 cut('const TR_WARDS','function trWilson'), html.split('\n').find(l=>l.startsWith('function trWilson')), html.split('\n').find(l=>l.startsWith('function trAgg')),
 html.split('\n').find(l=>l.startsWith('function trPct')), html.split('\n').find(l=>l.startsWith('function trBinomTail'))].join('\n');
const ctx={Math,Array,Object,Number}; vm.createContext(ctx); vm.runInContext(src+'\nthis.T={mulberry32,baselineStats,detectMA,detectEWMA,detectCUSUM,TR_DEF,TR_WARDS,TR_WFAC,TR_N,trPois,trBinom,trGen,trWilson,trAgg,trPct,trBinomTail};',ctx);
const T=ctx.T;
// ---- extended generator: base draws identical to trGen when opts are zero ----
function gen(seed,planted,o){
  const g=T.trGen(seed,planted?'planted':'none',o.rise||{});
  if(!o.season&&!o.dup) return g;
  // regenerate with same RNG stream but modified p (season) -- replicate trGen loop
  const r=T.mulberry32((seed>>>0)^0x5bd1e995), data={}; let plant=null,decoy=null;
  if(planted){ plant={org:'kpn',drug:'MEM',ward:'ICU',onset:16,peak:(o.rise&&o.rise.peak)||0.30,ramp:(o.rise&&o.rise.ramp)||4};
    const c=[['ecoli','CIP','Surgical'],['sau','FOX','Paediatrics'],['efm','VAN','ICU']][Math.floor(r()*3)]; decoy={org:c[0],drug:c[1],ward:c[2],month:9+Math.floor(r()*10)}; }
  const rd=T.mulberry32(((seed>>>0)^0x9e3779b9)>>>0);
  for(const org in T.TR_DEF){ data[org]={}; for(const d in T.TR_DEF[org].drugs){ data[org][d]={}; for(const w of T.TR_WARDS){ data[org][d][w]=[]; const base=T.TR_DEF[org].drugs[d][1];
    for(let m=0;m<T.TR_N;m++){ const n=T.trPois(T.TR_DEF[org].vol*T.TR_WFAC[w],r); let p=base*(0.85+0.3*r());
      if(plant&&plant.org===org&&plant.drug===d&&plant.ward===w&&m>=plant.onset){ const f=Math.min(1,(m-plant.onset+1)/plant.ramp); p=base+(plant.peak-base)*f; }
      else if(o.season) p=Math.min(0.95,p*(1+o.season.amp*Math.sin(2*Math.PI*(m-o.season.phase)/12)));
      let nn=n; if(decoy&&decoy.org===org&&decoy.drug===d&&decoy.ward===w&&m===decoy.month){ nn=Math.max(3,Math.min(n,4)); p=0.75; }
      let k=T.trBinom(nn,p,r), N=nn;
      if(o.dup){ let dn=0,dr=0; for(let i=0;i<nn;i++) if(rd()<o.dup){ dn++; if(rd()<(nn?k/nn:0)) dr++; } N+=dn; k+=dr; }
      data[org][d][w].push({n:N,r:k}); } } } }
  return {data,truth:g.truth};
}
const KEYS=['MA','EWMA','CUSUM','two','dashboard','count01','count_BH','count_Bonf','C2'];
function evalSeries(s,opt){ // returns object of booleans + count p-value
  const v=T.trPct(s), b=T.baselineStats(v);
  const det=[T.detectMA(v,b.mean),T.detectEWMA(v,b.mean,b.std),T.detectCUSUM(v,b.mean,(opt&&opt.cusumStd)?b.std:b.std)];
  const l3=s.slice(-3).reduce((t,x)=>({n:t.n+x.n,r:t.r+x.r}),{n:0,r:0}), b6=s.slice(0,6).reduce((t,x)=>({n:t.n+x.n,r:t.r+x.r}),{n:0,r:0});
  const two=det.filter(x=>x.flagged).length>=2, sup=l3.r>=5&&l3.n>0&&T.trWilson(l3.r,l3.n)[0]>(b6.n?100*b6.r/b6.n:0);
  const p0=Math.max(0.01,b6.n?b6.r/b6.n:0.01), pv=l3.r>=3?T.trBinomTail(l3.r,l3.n,p0):1;
  // EARS-C2-style: z>3 in any of last 3 months, baseline = 7 months ending 2 months earlier
  let c2=false; for(let t=s.length-3;t<s.length;t++){ const bs=v.slice(t-9,t-2); const mu=bs.reduce((a,x)=>a+x,0)/7; const sd=Math.max(0.5,Math.sqrt(bs.reduce((a,x)=>a+(x-mu)*(x-mu),0)/7)); if((v[t]-mu)/sd>3) c2=true; }
  return {MA:det[0].flagged,EWMA:det[1].flagged,CUSUM:det[2].flagged,two,dashboard:two&&sup,count01:pv<0.01&&l3.r>=3,pv,C2:c2,v,b,l3,b6};
}
function runSet(seedBase,mul,N,o){
  const rows=[];
  for(const planted of [true,false]) for(let i=0;i<N;i++){
    const seed=seedBase+i*mul+(planted?0:1), g=gen(seed,planted,o);
    const pk=g.truth.filter(t=>t.kind==='planted').map(t=>t.org+'|'+t.drug+'|'+t.ward)[0], dk=g.truth.filter(t=>t.kind==='decoy').map(t=>t.org+'|'+t.drug+'|'+t.ward)[0];
    const ser=[]; for(const og in T.TR_DEF) for(const d in T.TR_DEF[og].drugs) for(const w of T.TR_WARDS){ const key=og+'|'+d+'|'+w; const s=T.trAgg(g.data,og,d,w,T.TR_N); const e=evalSeries(s); e.isP=key===pk; e.isD=key===dk; ser.push(e); }
    // BH and Bonferroni over the 40 series
    const ps=ser.map(e=>e.pv), idx=ps.map((p,i)=>i).sort((a,b)=>ps[a]-ps[b]); let kmax=-1; idx.forEach((ix,rk)=>{ if(ps[ix]<=0.05*(rk+1)/ps.length) kmax=rk; });
    ser.forEach(e=>{e.count_Bonf=e.pv<0.05/ps.length&&e.l3.r>=3; e.count_BH=false;}); for(let rk=0;rk<=kmax;rk++){ const e=ser[idx[rk]]; if(e.l3.r>=3) e.count_BH=true; }
    rows.push({planted,ser:ser.map(e=>{const o2={isP:e.isP,isD:e.isD,pv:e.pv}; KEYS.forEach(k=>o2[k]=!!e[k]); return o2;})});
  }
  return rows;
}
function summ(rows){ const out={}; const nPl=rows.filter(r=>r.planted).length, nDs=rows.length;
  for(const k of KEYS){ let tp=0,fa=0,dec=0,nd=0; const per=[]; rows.forEach(r=>{ let f=0,t=0; r.ser.forEach(e=>{ if(e.isP){ if(e[k]) t=1; } else if(e[k]) f++; }); if(r.planted){ tp+=t; const d=r.ser.find(e=>e.isD); if(d){ nd++; if(d[k]) dec++; } } fa+=f; per.push({t:r.planted?t:null,f}); });
    // bootstrap over datasets
    const R=T_boot(per,2000); out[k]={found:tp,of:nPl,sens:tp/nPl,fa_total:fa,fa_per_ds:fa/nDs,real_share:(tp+fa)?tp/(tp+fa):null,decoy_flagged:dec,decoys:nd,sens_ci:R.s,fa_ci:R.f}; }
  return out; }
let seedState=12345; const rnd=()=>{seedState=(seedState*1664525+1013904223)>>>0; return seedState/4294967296;};
function T_boot(per,B){ const pl=per.filter(x=>x.t!==null), S=[],F=[]; for(let b=0;b<B;b++){ let t=0; for(let i=0;i<pl.length;i++) t+=pl[Math.floor(rnd()*pl.length)].t; S.push(t/pl.length); let f=0; for(let i=0;i<per.length;i++) f+=per[Math.floor(rnd()*per.length)].f; F.push(f/per.length); }
  const q=(a,p)=>{a=a.slice().sort((x,y)=>x-y); return a[Math.floor(p*(a.length-1))];}; return {s:[q(S,.025),q(S,.975)],f:[q(F,.025),q(F,.975)]}; }
// ---- sweeps: sensitivity vs false alerts/dataset across thresholds (end-of-series) ----
function sweep(seedBase,mul,N){
  const sets=[]; for(const planted of [true,false]) for(let i=0;i<N;i++){ const seed=seedBase+i*mul+(planted?0:1), g=gen(seed,planted,{}); const pk=g.truth.filter(t=>t.kind==='planted').map(t=>t.org+'|'+t.drug+'|'+t.ward)[0]; const ser=[];
    for(const og in T.TR_DEF) for(const d in T.TR_DEF[og].drugs) for(const w of T.TR_WARDS){ const s=T.trAgg(g.data,og,d,w,T.TR_N), v=T.trPct(s), b=T.baselineStats(v); ser.push({isP:(og+'|'+d+'|'+w)===pk,s,v,b}); } sets.push({planted,ser}); }
  const methods={
    CUSUM_h:{vals:[2,3,4,5,6,8,10],f:(x,h)=>{ let c=0,fl=false; const sl=0.5*x.b.std; for(const y of x.v){ c=Math.max(0,c+(y-x.b.mean-sl)); if(c>h*x.b.std) fl=true; } return fl; }},
    count_alpha:{vals:[0.1,0.05,0.01,0.001,0.0001],f:(x,a)=>{ const l3=x.s.slice(-3).reduce((t,z)=>({n:t.n+z.n,r:t.r+z.r}),{n:0,r:0}), b6=x.s.slice(0,6).reduce((t,z)=>({n:t.n+z.n,r:t.r+z.r}),{n:0,r:0}); const p0=Math.max(0.01,b6.n?b6.r/b6.n:0.01); return l3.r>=3&&T.trBinomTail(l3.r,l3.n,p0)<a; }},
    dashboard_minr:{vals:[1,2,3,4,5,6,8],f:(x,m)=>{ const det=[T.detectMA(x.v,x.b.mean),T.detectEWMA(x.v,x.b.mean,x.b.std),T.detectCUSUM(x.v,x.b.mean,x.b.std)]; const two=det.filter(z=>z.flagged).length>=2; const l3=x.s.slice(-3).reduce((t,z)=>({n:t.n+z.n,r:t.r+z.r}),{n:0,r:0}), b6=x.s.slice(0,6).reduce((t,z)=>({n:t.n+z.n,r:t.r+z.r}),{n:0,r:0}); return two&&l3.r>=m&&l3.n>0&&T.trWilson(l3.r,l3.n)[0]>(b6.n?100*b6.r/b6.n:0); }}};
  const out={}; for(const [mn,m] of Object.entries(methods)){ out[mn]=m.vals.map(val=>{ let tp=0,fa=0; sets.forEach(S=>{ let t=0,f=0; S.ser.forEach(x=>{ const fl=m.f(x,val); if(x.isP){ if(fl) t=1; } else if(fl) f++; }); if(S.planted) tp+=t; fa+=f; }); return {param:val,found:tp,of:N,fa_per_ds:fa/sets.length}; }); }
  return out; }
const res={};
const cfgs={base:{},season_adverse:{season:{amp:0.3,phase:6}},season_favourable:{season:{amp:0.3,phase:0}},dup15:{dup:0.15},season_adverse_dup15:{season:{amp:0.3,phase:6},dup:0.15}};
// season: p*(1+0.3*sin(2pi(m-phase)/12)), m=0..23; phase 6: baseline months in trough, peaks at m=9 and m=21 (adverse); phase 0: peak inside baseline (favourable)
for(const [nm,o] of Object.entries(cfgs)){ res[nm]={main:summ(runSet(7000,31,60,o)),newseeds:summ(runSet(50000,37,60,o))}; console.error('done',nm); }
res.sweep_main=sweep(7000,31,60); res.sweep_new=sweep(50000,37,60);
res.meta={note:'post hoc exploratory; seeds 7000+31i (+1 unplanted) and 50000+37i (+1); end-of-series measure; bootstrap 2000 resamples of datasets',keys:KEYS,cfgs};
fs.writeFileSync(process.argv[3],JSON.stringify(res,null,1));
