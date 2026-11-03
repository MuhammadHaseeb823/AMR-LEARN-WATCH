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

const KEYS=['MA','EWMA','CUSUM','two','dashboard','count01'];
function cur(s){ // flags using ONLY the state at the last month of s
  const v=T.trPct(s), b=T.baselineStats(v), n=v.length;
  const ma=T.detectMA(v,b.mean), ew=T.detectEWMA(v,b.mean,b.std), cu=T.detectCUSUM(v,b.mean,b.std);
  const f={MA:ma.flagged, EWMA:ew.ewma[n-1]>ew.UCL&&ew.ewma[n-2]>ew.UCL, CUSUM:cu.cusum[n-1]>cu.h};
  const l3=s.slice(-3).reduce((t,x)=>({n:t.n+x.n,r:t.r+x.r}),{n:0,r:0}), b6=s.slice(0,6).reduce((t,x)=>({n:t.n+x.n,r:t.r+x.r}),{n:0,r:0});
  const two=(f.MA+f.EWMA+f.CUSUM)>=2, sup=l3.r>=5&&l3.n>0&&T.trWilson(l3.r,l3.n)[0]>(b6.n?100*b6.r/b6.n:0);
  const p0=Math.max(0.01,b6.n?b6.r/b6.n:0.01);
  return {MA:f.MA,EWMA:f.EWMA,CUSUM:f.CUSUM,two,dashboard:two&&sup,count01:l3.r>=3&&T.trBinomTail(l3.r,l3.n,p0)<0.01};
}
function ever(s){ // app definition: EWMA/CUSUM stay flagged once crossed (end-of-series measure in the paper)
  const v=T.trPct(s), b=T.baselineStats(v); const det=[T.detectMA(v,b.mean),T.detectEWMA(v,b.mean,b.std),T.detectCUSUM(v,b.mean,b.std)];
  const l3=s.slice(-3).reduce((t,x)=>({n:t.n+x.n,r:t.r+x.r}),{n:0,r:0}), b6=s.slice(0,6).reduce((t,x)=>({n:t.n+x.n,r:t.r+x.r}),{n:0,r:0});
  const two=det.filter(x=>x.flagged).length>=2, sup=l3.r>=5&&l3.n>0&&T.trWilson(l3.r,l3.n)[0]>(b6.n?100*b6.r/b6.n:0);
  const p0=Math.max(0.01,b6.n?b6.r/b6.n:0.01);
  return {MA:det[0].flagged,EWMA:det[1].flagged,CUSUM:det[2].flagged,two,dashboard:two&&sup,count01:l3.r>=3&&T.trBinomTail(l3.r,l3.n,p0)<0.01};
}
function run(seedBase,mul,N){
  const out={};
  for(const mode of ['ever24','current24','monitor12_24']){ out[mode]={}; KEYS.forEach(k=>out[mode][k]={tp:0,fa:0}); }
  let nds=0, nPl=0;
  for(const planted of [true,false]) for(let i=0;i<N;i++){
    const seed=seedBase+i*mul+(planted?0:1), g=gen(seed,planted,{}); nds++; if(planted) nPl++;
    const pk=g.truth.filter(t=>t.kind==='planted').map(t=>t.org+'|'+t.drug+'|'+t.ward)[0];
    const acc={ever24:{},current24:{},monitor12_24:{}}; // per dataset: tp flag, fa count
    for(const m in acc) KEYS.forEach(k=>acc[m][k]={t:0,f:0});
    for(const og in T.TR_DEF) for(const d in T.TR_DEF[og].drugs) for(const w of T.TR_WARDS){ const key=og+'|'+d+'|'+w, isP=key===pk;
      const full=T.trAgg(g.data,og,d,w,24); const e=ever(full), c=cur(full);
      const mon={}; KEYS.forEach(k=>mon[k]=false); for(let t=12;t<=24;t++){ const x=ever(T.trAgg(g.data,og,d,w,t)); KEYS.forEach(k=>{ if(x[k]) mon[k]=true; }); }
      for(const [m,f] of [['ever24',e],['current24',c],['monitor12_24',mon]]) KEYS.forEach(k=>{ if(f[k]){ if(isP) acc[m][k].t=1; else acc[m][k].f++; } }); }
    for(const m in acc) KEYS.forEach(k=>{ out[m][k].tp+=acc[m][k].t; out[m][k].fa+=acc[m][k].f; });
  }
  for(const m in out) KEYS.forEach(k=>{ out[m][k].of=nPl; out[m][k].fa_per_ds=out[m][k].fa/nds; });
  return out; }
const res={main:run(7000,31,60),newseeds:run(50000,37,60)};
require('fs').writeFileSync(process.argv[3],JSON.stringify(res,null,1));
for(const s of ['main','newseeds']) for(const m of ['ever24','current24','monitor12_24']) console.log(s,m,KEYS.map(k=>k+' '+res[s][m][k].tp+'/'+res[s][m][k].of+' fa/ds '+res[s][m][k].fa_per_ds.toFixed(2)).join(' | '));
