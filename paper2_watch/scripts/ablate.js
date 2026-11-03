const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage();const errs=[];p.on('pageerror',e=>errs.push(String(e)));
await p.goto('file://'+process.cwd()+'/probe021.html');await p.waitForTimeout(1500);
const scen=JSON.parse(process.argv[2]||'{}');
const out=await p.evaluate((opt)=>{const T=window.__T;const N=60;const rows=[];
const V=['MA','EWMA','CUSUM','two','two+min5','two+wilson','dashboard','count'];
const wil=(l3,b6)=>T.trWilson(l3.r,l3.n)[0]>(b6.n?100*b6.r/b6.n:0);
for(const sc of ['planted','none']) for(let i=0;i<N;i++){const g=T.trGen(7000+i*31+(sc==='none'?1:0),sc,opt);
 const pk=g.truth.filter(t=>t.kind==='planted').map(t=>t.org+'|'+t.drug+'|'+t.ward)[0];
 const dk=g.truth.filter(t=>t.kind==='decoy').map(t=>t.org+'|'+t.drug+'|'+t.ward)[0];
 const ds={sc,i,fa:Object.fromEntries(V.map(v=>[v,0])),faAny:Object.fromEntries(V.map(v=>[v,0])),decoy:null,hit:null,hitDelay:null,hitAny:null};
 for(const o in T.TR_DEF) for(const d in T.TR_DEF[o].drugs) for(const w of T.TR_WARDS){
  const s=T.trAgg(g.data,o,d,w,T.TR_N), v=T.trPct(s), b=T.baselineStats(v);
  const key=o+'|'+d+'|'+w, isP=key===pk, isD=key===dk;
  const flags=(m)=>{const sv=v.slice(0,m), ss=s.slice(0,m);
   const det=[T.detectMA(sv,b.mean),T.detectEWMA(sv,b.mean,b.std),T.detectCUSUM(sv,b.mean,b.std)];
   const l3=ss.slice(-3).reduce((t,x)=>({n:t.n+x.n,r:t.r+x.r}),{n:0,r:0}), b6=ss.slice(0,6).reduce((t,x)=>({n:t.n+x.n,r:t.r+x.r}),{n:0,r:0});
   const two=det.filter(x=>x.flagged).length>=2, min5=l3.r>=5, w_=l3.n>0&&wil(l3,b6);
   const p0c=Math.max(0.01,b6.n?b6.r/b6.n:0.01), cnt=l3.r>=3&&T.trBinomTail(l3.r,l3.n,p0c)<0.01;
   return [det[0].flagged,det[1].flagged,det[2].flagged,two,two&&min5,two&&w_,two&&min5&&w_,cnt];};
  const fe=flags(24); const any=Array(8).fill(false); for(let m=12;m<=24;m++){const f=flags(m); f.forEach((x,k)=>{if(x)any[k]=true;});}
  if(isP){ds.hit=fe;ds.hitAny=any;const sv=v,dd=[T.detectMA(sv,b.mean),T.detectEWMA(sv,b.mean,b.std),T.detectCUSUM(sv,b.mean,b.std)];ds.detIdx=dd.map(x=>x.detected);ds.nTarget=s.map(x=>x.n);ds.pct=v;}
  else{V.forEach((vn,k)=>{if(fe[k])ds.fa[vn]++; if(any[k])ds.faAny[vn]++;}); if(isD) ds.decoy=fe;}
 }
 rows.push(ds);}
return {V,rows};},scen);
require('fs').writeFileSync(process.argv[3]||'abl.json',JSON.stringify(out));console.log(out.rows.length,errs);await b.close()})();
