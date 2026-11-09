// r260 테스트 — 타 거래처 원장 판매가 미적용 · 내 원장은 유지 · 마진/DC 일괄(소물 포함/제외, 빈 칸만/전체)
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs=require('fs'), path=require('path');
const file=path.resolve(process.argv[2]||'d260/test/index.html');
let pass=0, fail=0; function ok(c,m){ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} }
(async()=>{
  const src=fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){','window.__T=function(c){return eval(c);}; function _vacUnlimited(id){');
  const tmp=path.join(path.dirname(file),'_h_r260.html'); fs.writeFileSync(tmp,src);
  const br=await chromium.launch(); const pg=await br.newPage({viewport:{width:1400,height:900}}); const errs=[]; pg.on('pageerror',e=>errs.push(String(e)));
  await pg.route('**/*',r=>r.request().url().startsWith('file://')?r.continue():r.abort());
  await pg.goto('file://'+tmp); await pg.waitForTimeout(2500);
  await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  const T=c=>pg.evaluate(c2=>window.__T(c2),c);
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; saveAll=function(){}; _qCartSave=function(){};
    window.other={spec:'AW30-03BG-A',name:'FRL',e:44360,buy:25730,sell:28590,eta:'재고 있음 (3일 예상)'};
    window.mine={spec:'AN30-03',name:'소음기',e:3420,buy:2050,sell:2600,eta:'당일'};
    _qAllIdx={}; _qAllIdx[_qNorm(other.spec)]=[{vid:'vOther',vname:'다른업체',r:other}]; _qAllIdx[_qNorm(mine.spec)]=[{vid:'vNew',vname:'대국산기',r:mine}]; _qAllReady=true;
    _qPriceIdx={}; _qCurId='vNew'; _qRows=[mine]; _qgObk=null;
    _qCart=[{vid:'vNew',vname:'대국산기',spec:'AW30-03BG-A',qty:12,manual:true},{vid:'vNew',vname:'대국산기',spec:'AN30-03',qty:50,manual:true}];
    _qIsSmc=function(){ return false; };
    _qgFillFromLedger(0); _qgFillFromLedger(1); 'ok'`);
  ok(await T(`_qCart[0].buy===25730 && _qCart[0].e===44360`), '타 거래처 원장: E가·구매가는 참고로 가져옴');
  ok(await T(`_qCart[0].sell===null && _qCart[0].eta===''`), '타 거래처 원장: 판매가·예상납기는 비움 (AW30-03BG-A 재현 수정)');
  ok(await T(`_qCart[1].sell===2600 && _qCart[1].eta==='당일'`), '내 원장(이 거래처 이력): 판매가·예상납기 유지');
  await T(`_qCart.push({}); _qcsCur=[{r:other}]; qCartSpecPick(2,0,false); 'ok'`);
  ok(await T(`_qCart[2].spec==='AW30-03BG-A' && _qCart[2].sell===null`), '자동완성으로 타업체 행 골라도 판매가 없음');
  await T(`_qCart=[]; _qPushCartNew(other); _qPushCartNew(mine); 'ok'`);
  ok(await T(`_qCart[0].sell===null && _qCart[1].sell===2600`), '검색 결과 담기: 타업체 판매가 없음 · 내 원장 유지');

  console.log('▶ 일괄 적용');
  await T(`_qCart=[
      {spec:'A',e:10000,buy:6000,sell:null},
      {spec:'B',e:20000,buy:12000,sell:15000},
      {spec:'C',e:3000,buy:1800,small:1700,sell:null},
      {spec:'D',e:5000,buy:null,sell:null},
      {spec:'E',e:8000,buy:4000,sell:null,disc:'단종'},
      {spec:'F',e:44360,buy:25730,pl:true,sell:null}];
    renderQCart=function(){}; qBulkRateOpen(); 'ok'`);
  ok(await pg.evaluate(()=>document.getElementById('qBulkOverlay').style.display==='flex'), '일괄 적용 창 열림');
  await pg.evaluate(()=>{ document.getElementById('qbRate').value='20'; _qbPrev(); });
  const pv=await pg.evaluate(()=>document.getElementById('qbPrev').innerText);
  ok(/2줄/.test(pv) && /이미 값 있음 1/.test(pv) && /소물류 1/.test(pv) && /구매가 없음 1/.test(pv) && /단종\/변경 1/.test(pv), '미리보기(마진·빈 칸만·소물 제외): '+pv.replace(/\n/g,' '));
  await T(`qBulkRateApply(); 'ok'`);
  ok(await T(`_qCart[0].sell===_qCalcSell(6000,0.2) && _qCart[1].sell===15000 && _qCart[2].sell===null && _qCart[3].sell===null && _qCart[4].sell===null && _qCart[5].sell===_qCalcSell(25730,0.2)`), '마진 20%: 빈 칸·비소물만 판매가, 기존 값·소물·단종 그대로');
  ok(await T(`_qCart[0].sell`)===7500, '판매가 = 6000 ÷ 0.8 = 7,500');
  await T(`qBulkRateOpen(); 'ok'`);
  await pg.evaluate(()=>{ document.querySelector('input[name=qbScope][value=all]').click(); document.querySelector('input[name=qbSmall][value=include]').click(); document.getElementById('qbRate').value='10'; _qbPrev(); });
  await T(`qBulkRateApply(); 'ok'`);
  ok(await T(`_qCart[1].sell===_qCalcSell(12000,0.1) && _qCart[2].sell===_qCalcSell(1800,0.1)`), '전체 덮어쓰기 + 소물 포함');
  await T(`qBulkRateOpen(); 'ok'`);
  await pg.evaluate(()=>{ document.querySelector('input[name=qbMode][value=dc]').click(); document.querySelector('input[name=qbScope][value=all]').click(); document.querySelector('input[name=qbSmall][value=exclude]').click(); document.getElementById('qbRate').value='40'; _qbPrev(); });
  await T(`qBulkRateApply(); 'ok'`);
  ok(await T(`_qCart[0].buy===_qCalcBuy(10000,0.4) && _qCart[3].buy===_qCalcBuy(5000,0.4) && _qCart[2].buy===1800 && _qCart[5].buy===25730`), 'DC 40%: 구매가 계산 · 소물 제외 · 확판 잠금 줄은 그대로');
  ok(await T(`_qUndo.length`)>=3, '되돌리기 기록');
  ok(await pg.evaluate(()=>!!document.getElementById('qBulkBtn')), '견적 툴바에 일괄 적용 버튼');
  const re=errs.filter(e=>!/net::|Failed to fetch|firebase|XLSX|cdnjs/.test(e)); ok(re.length===0,'페이지 오류 없음'+(re.length?' — '+re[0]:''));
  console.log(`\n결과: ${pass} 통과 / ${fail} 실패`); await br.close(); try{fs.unlinkSync(tmp);}catch(e){} process.exit(fail?1:0);
})();
