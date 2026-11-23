// r274 테스트 — 수량별 가격(MOQ): 같은 규격 줄마다 가격을 따로
const { chromium } = require('playwright'); const fs=require('fs'), path=require('path');
const file=path.resolve(process.argv[2]||'/home/claude/d274/index.html');
let pass=0, fail=0; function ok(c,m){ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} }
(async()=>{
  const src=fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){','window.__T=function(c){return eval(c);}; function _vacUnlimited(id){');
  const tmp=path.join(path.dirname(file),'_h_r274.html'); fs.writeFileSync(tmp,src);
  const br=await chromium.launch(); const errs=[];
  const pg=await br.newPage({viewport:{width:1500,height:900}}); pg.on('pageerror',e=>errs.push(String(e)));
  await pg.route('**/*', r=>r.request().url().startsWith('file://')?r.continue():r.abort());
  await pg.goto('file://'+tmp); await pg.waitForTimeout(2500); await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  const T=c=>pg.evaluate(c2=>window.__T(c2),c);
  const setup=`_authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울'}]; myMemberId='m1'; _qLeaveGuard=function(){return false;}; switchPage('estimate'); quoteVendors=[{id:'v1',name:'대국산기'}]; _qCurId='v1';`;
  const cart=`_qCart=[{vid:'v1',vname:'대국산기',spec:'PAG-15B-FE-RA',name:'게이지',qty:10,e:10000,buy:8000,sell:9000},{vid:'v1',vname:'대국산기',spec:'PAG-15B-FE-RA',name:'게이지',qty:50,e:10000,buy:8000,sell:9000},{vid:'v1',vname:'대국산기',spec:'PAG-15B-FE-RA',name:'게이지',qty:100,e:10000,buy:8000,sell:9000}]; renderQCart(); 'ok'`;
  await T(setup+cart); await pg.waitForTimeout(300);
  // 기존 동작: 가격 바꾸면 같은 규격 맞출지 묻는다 + 새 선택지
  await T(`qCartField(1,'buy','7000'); 'ok'`); await pg.waitForTimeout(700);
  const mtxt=await pg.evaluate(()=>{ const o=document.getElementById('confirmOverlay'); return o&&o.style.display==='flex'?o.innerText:''; });
  ok(/같게 할까요/.test(mtxt) && /수량\(MOQ\)에 따라 가격이 다릅니다/.test(mtxt), '가격 수정 → 확인창에 "수량에 따라 가격이 다릅니다" 선택지');
  await pg.click('#confirmOverlay a'); await pg.waitForTimeout(300);
  ok(await T('_qCart.every(function(c){return c.qp&&c.once;})') && await T('_qCart[0].buy')==8000 && await T('_qCart[1].buy')==7000, '선택 → 3줄 모두 수량별(일회성), 가격은 각자 유지');
  ok(await pg.evaluate(()=>document.querySelectorAll('#qCart .q-qp').length)===3, '줄마다 [수량별] 표시');
  await pg.waitForTimeout(600); await T(`qCartField(2,'buy','6000'); qCartField(2,'sell','7500'); 'ok'`); await pg.waitForTimeout(700);
  ok(await pg.evaluate(()=>{ const o=document.getElementById('confirmOverlay'); return !o||o.style.display!=='flex'; }), '이후 가격을 바꿔도 다시 묻지 않음');
  ok(await T('_qCart[0].buy')==8000 && await T('_qCart[1].buy')==7000 && await T('_qCart[2].buy')==6000 && await T('_qCart[0].sell')==9000 && await T('_qCart[2].sell')==7500, '10개 8,000 / 50개 7,000 / 100개 6,000 따로 유지');
  ok(await T('_qCartSyncSameSpec()')===0, '같은 규격 자동 맞춤 대상에서 제외');
  // 같은 규격 새 줄 → 수량별, E가만
  await T(`_qCart.push({vid:'v1',vname:'대국산기',spec:'PAG-15B-FE-RA',qty:200}); _qCartCopyAbove(3); 'ok'`);
  ok(await T('_qCart[3].qp')===true && await T('_qCart[3].e')==10000 && await T('_qCart[3].buy==null') , '같은 규격 새 줄: 수량별 + E가만 채우고 구매가는 비움');
  // 해제
  await T(`qCartQpToggle(0); 'ok'`); ok(await T('_qCart.every(function(c){return !c.qp;})'), '[수량별] 누르면 그 규격 전체 해제');
  // 우클릭 메뉴
  await T(cart); await pg.waitForTimeout(200);
  await pg.click('#qCart tbody tr:nth-child(1) td:nth-child(1)', {button:'right'}); await pg.waitForTimeout(200);
  ok(/수량별 가격/.test(await pg.evaluate(()=>(document.getElementById('qCartCtxMenu')||{}).innerText||'')), '우클릭 메뉴에 [수량별 가격]');
  await T(`qCartQpToggle(0); 'ok'`); ok(await T('_qCart.every(function(c){return c.qp;})'), '메뉴로 켜기 → 같은 규격 전체');
  // 다른 규격은 기존대로
  await T(`_qCart=[{vid:'v1',vname:'대국산기',spec:'A-1',qty:1,e:100,buy:80,sell:90},{vid:'v1',vname:'대국산기',spec:'A-1',qty:2}]; _qCartSyncSameSpec(); 'ok'`);
  ok(await T('_qCart[1].buy')==80, '수량별이 아닌 규격은 전처럼 같은 가격으로 채움');
  ok(errs.length===0, '오류 없음 '+errs.slice(0,2).join(' | '));
  console.log(`\n${pass} passed, ${fail} failed`); await br.close(); process.exit(fail?1:0);
})();
