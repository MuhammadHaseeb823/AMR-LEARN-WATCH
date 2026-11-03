const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1300,height:1100}});
const errs=[];p.on('pageerror',e=>errs.push(String(e)));
await p.goto('file://'+process.cwd()+'/w021.html');await p.waitForTimeout(1500);
await p.evaluate(()=>{document.querySelectorAll('[data-page="trends"]').forEach(e=>e.click())});await p.waitForTimeout(800);
const out={};
async function run(n,pk,rp){await p.selectOption('#trValN',n);await p.selectOption('#trValPeak',pk);await p.selectOption('#trValRamp',rp);await p.click('#trValBtn');await p.waitForTimeout(n==='60'?6000:3000);
 return await p.evaluate(()=>({intro:document.querySelector('#trValOut p:nth-of-type(2)').innerText,rows:[...document.querySelectorAll('#trValOut tbody tr')].map(r=>[...r.cells].map(c=>c.innerText))}));}
out['60_0.30_4']=await run('60','0.30','4');
for(const pk of ['0.15','0.30','0.50'])for(const rp of ['1','4','8']){if(pk==='0.30'&&rp==='4')continue;out['60_'+pk+'_'+rp]=await run('60',pk,rp);}
require('fs').writeFileSync('val021.json',JSON.stringify(out,null,1));
await p.locator('#trValOut').scrollIntoViewIfNeeded();await p.screenshot({path:'trends021.png'});
console.log(errs);await b.close()})();
