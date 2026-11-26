// r277 테스트 — 견적 표: 한 칸 복사 → 여러 칸 선택 → 붙여넣기 = 전체 채움
const { chromium } = require('playwright'); const fs=require('fs'), path=require('path');
const file=path.resolve(process.argv[2]||'/home/claude/d277/index.html');
let pass=0, fail=0; function ok(c,m){ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} }
(async()=>{
  const src=fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){','window.__T=function(c){return eval(c);}; function _vacUnlimited(id){');
  const tmp=path.join(path.dirname(file),'_h_r277.html'); fs.writeFileSync(tmp,src);
  const br=await chromium.launch(); const errs=[]; const ctx=await br.newContext({viewport:{width:1700,height:900},permissions:['clipboard-read','clipboard-write']}); const pg=await ctx.newPage(); pg.on('pageerror',e=>errs.push(String(e)));
  await pg.route('**/*', r=>r.request().url().startsWith('file://')?r.continue():r.abort());
  await pg.goto('file://'+tmp); await pg.waitForTimeout(2500); await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  const T=c=>pg.evaluate(c2=>window.__T(c2),c);
  const reset=()=>T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울'}]; myMemberId='m1'; _qLeaveGuard=function(){return false;}; switchPage('estimate'); quoteVendors=[{id:'v1',name:'대국산기'}]; _qCurId='v1'; _qCart=[]; for(var i=0;i<8;i++) _qCart.push({vid:'v1',vname:'대국산기',spec:'A-'+i,name:'품'+i,qty:1,e:1000,buy:800,sell:900,eta:i==0?'재고':''}); _qgReset(); renderQCart(); 'ok'`);
  await reset(); await pg.waitForTimeout(300);
  const cell=(r,c)=>pg.locator('#qCart table.qcart-tbl tbody tr').nth(r).locator('input.qc-in').nth(c);
  const drag=async(r0,c0,r1,c1)=>{ const a=await cell(r0,c0).boundingBox(), b=await cell(r1,c1).boundingBox(); await pg.mouse.move(a.x+a.width/2,a.y+a.height/2); await pg.mouse.down(); await pg.mouse.move(a.x+a.width/2+3,a.y+a.height/2+3,{steps:2}); await pg.mouse.move(b.x+b.width/2,b.y+b.height/2,{steps:6}); await pg.mouse.up(); await pg.waitForTimeout(120); };
  await cell(0,4).click(); await pg.keyboard.press('Control+c'); await pg.waitForTimeout(150);
  await drag(1,4,6,4); await pg.keyboard.press('Control+v'); await pg.waitForTimeout(350);
  ok(await T(`_qCart.map(function(c){return c.eta;}).join('|')`)==='재고|재고|재고|재고|재고|재고|재고|', '납기 한 칸 복사 → 6칸 드래그 → 붙여넣기 = 6칸 모두 (전엔 첫 칸만)');
  await pg.evaluate(()=>navigator.clipboard.writeText('5')); await drag(2,2,5,2); await pg.keyboard.press('Control+v'); await pg.waitForTimeout(350);
  ok(await T(`_qCart.map(function(c){return c.qty;}).join('|')`)==='1|1|5|5|5|5|1|1', '수량 칸도 선택한 4칸만 채움');
  await pg.evaluate(()=>navigator.clipboard.writeText('950')); await drag(0,3,7,3); await pg.keyboard.press('Control+v'); await pg.waitForTimeout(350);
  ok(await T(`_qCart.every(function(c){return c.sell==950;})`), '판매가 8칸 채움');
  await pg.evaluate(()=>navigator.clipboard.writeText('가\n나')); await drag(0,4,3,4); await pg.keyboard.press('Control+v'); await pg.waitForTimeout(350);
  ok(await T(`_qCart.slice(0,5).map(function(c){return c.eta;}).join('|')`)==='가|나|가|나|재고', '2칸 복사 → 4칸 선택 = 반복해서 채움');
  await pg.evaluate(()=>navigator.clipboard.writeText('x\ny\nz')); await drag(0,4,3,4); await pg.keyboard.press('Control+v'); await pg.waitForTimeout(350);
  ok(await T(`_qCart.slice(0,5).map(function(c){return c.eta;}).join('|')`)==='x|y|z|나|재고', '배수가 안 맞으면 전처럼 복사한 만큼만');
  await pg.evaluate(()=>navigator.clipboard.writeText('단독')); await T(`_qgReset(); 'ok'`); await cell(7,4).click(); await pg.keyboard.press('Control+a'); await pg.keyboard.press('Control+v'); await pg.keyboard.press('Tab'); await pg.waitForTimeout(250);
  ok(await T(`_qCart[7].eta`)==='단독' && await T(`_qCart[6].eta`)==='재고', '선택 없이 한 칸에 붙여넣기는 전과 같음');
  await pg.keyboard.press('Control+z'); 
  ok(errs.length===0, '오류 없음 '+errs.slice(0,2).join(' | '));
  console.log(`\n${pass} passed, ${fail} failed`); await br.close(); process.exit(fail?1:0);
})();
