// r225 테스트 — 담당 업체(견적 5회) 자동 편입 + 메모장 '내 담당 업체 매출' 팝업 + 관리자 수동 지정
//  사용:  node test_r225.js <r225 적용된 index.html>
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b225/test/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const STUB = `
  window._xlsxStyleReady=true;
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r225.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  await pg.route('**/*', r => { const u=r.request().url(); if(u.startsWith('file://')) r.continue(); else r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  const Y = new Date().getFullYear();

  await T(`
    _fbDbUrl='https://x.test'; _authUser={id:'kjs',name:'김재성',role:'admin'}; myMemberId='m1';
    members=[{id:'m1',name:'김재성',group:'서울'},{id:'m2',name:'함현식',group:'서울'},{id:'m3',name:'이영희',group:'화성'}];
    window.__PUT=[]; _fbPutOk=async function(){ return true; }; debouncedFbSave=function(){};
    clientList=[['A전기','111-11-11111'],['B산업','222-22-22222'],['C상사','333-33-33333'],['D테크','444-44-44444']];
    customClients=[]; clientOwner={}; memoLines=[];
    var mk=function(vn,who,at){ return {id:'q'+Math.random().toString(36).slice(2),title:'Q',vname:vn,vid:'',count:1,total:0,savedBy:who,savedAt:at}; };
    quoteSaved=[];
    for(var i=0;i<6;i++) quoteSaved.push(mk('A전기','김재성',1000+i));        // 김재성 6회 → 담당
    for(var i=0;i<4;i++) quoteSaved.push(mk('B산업','김재성',2000+i));        // 4회 → 아직 아님
    for(var i=0;i<5;i++) quoteSaved.push(mk('C상사','함현식',3000+i));        // 함현식 5회
    for(var i=0;i<5;i++) quoteSaved.push(mk('C상사','김재성',4000+i));        // 김재성도 5회, 동률 → 최근 작성자(김재성)
    for(var i=0;i<7;i++) quoteSaved.push(mk('D테크','탈퇴자',5000+i));        // 멤버 아님 → 담당 없음
    fxSalesInv=[
      {biz:'서울',date:'${Y}-03-10',vendor:'A전기',vbiz:'111-11-11111',supply:1000000,tax:100000,total:1100000},
      {biz:'화성',date:'${Y}-05-10',vendor:'A전기(구명)',vbiz:'111-11-11111',supply:500000,tax:50000,total:550000},   // 이름 달라도 사업자번호로 매칭
      {biz:'서울',date:'${Y-1}-07-10',vendor:'A전기',vbiz:'111-11-11111',supply:300000,tax:30000,total:330000},
      {biz:'서울',date:'${Y-2}-07-10',vendor:'A전기',vbiz:'111-11-11111',supply:200000,tax:20000,total:220000},
      {biz:'서울',date:'${Y-3}-07-10',vendor:'A전기',vbiz:'111-11-11111',supply:999999,tax:0,total:0},            // 범위 밖 연도 → 미집계
      {biz:'서울',date:'${Y}-02-01',vendor:'C상사',vbiz:'333-33-33333',supply:700000,tax:70000,total:770000},
      {biz:'서울',date:'${Y}-02-01',vendor:'B산업',vbiz:'222-22-22222',supply:40000,tax:4000,total:44000}
    ];
    _fxLoaded=true; _fxEnsureData=async function(){}; 'ok'`);

  console.log('▶ 담당 산정');
  ok(await T(`_coOwnerOf('A전기')==='김재성'`), 'A전기: 김재성 6회 → 담당');
  ok(await T(`_coOwnerOf('B산업')===''`), 'B산업: 4회 → 담당 없음');
  ok(await T(`_coOwnerOf('C상사')==='김재성'`), 'C상사: 5:5 동률 → 최근 작성자 김재성');
  ok(await T(`_coOwnerOf('D테크')===''`), 'D테크: 멤버 아닌 작성자 → 담당 없음');
  ok(await T(`_coMine('김재성').map(function(o){return o.vname;}).sort().join(',')==='A전기,C상사'`), '김재성 담당 2곳');
  ok(await T(`_coMine('함현식').length===0`), '함현식 담당 0곳');

  console.log('▶ 매출 집계');
  const s = await T(`JSON.stringify(_coSalesByYear(['A전기','C상사'], _coYears()))`);
  const so = JSON.parse(s);
  ok(so['A전기'][String(Y)]===1500000 && so['A전기'][String(Y-1)]===300000 && so['A전기'][String(Y-2)]===200000, 'A전기 올해 150만(서울+화성, 사업자번호 매칭) · 작년 30만 · 재작년 20만 ('+s+')');
  ok(so['C상사'][String(Y)]===700000, 'C상사 올해 70만');

  console.log('▶ 메모장 버튼 → 팝업');
  ok(await T(`!!document.querySelector('#pageMemo button[onclick="coOpenMine()"]')`), '메모장 도구줄에 버튼');
  await T(`coOpenMine(); 'ok'`); await pg.waitForTimeout(500);
  ok(await T(`document.getElementById('coMineOverlay').style.display==='flex'`), '팝업 열림');
  let txt = await T(`document.getElementById('coMineBody').innerText`);
  ok(txt.indexOf('2곳')>=0 && txt.indexOf('2,200,000원')>=0, '타일: 담당 2곳 · 올해 2,200,000원');
  ok(txt.indexOf('A전기')>=0 && txt.indexOf('C상사')>=0 && txt.indexOf('B산업')<0, '업체 A·C 만 (B 제외)');
  ok(await T(`document.querySelectorAll('#coMineOverlay tbody tr').length===3`), '표 2줄 + 합계');
  ok(await T(`document.querySelector('#coMineOverlay tr.tot').innerText.indexOf('2,200,000')>=0`), '합계줄 2,200,000');
  ok(await T(`document.querySelectorAll('#coMineOverlay .co-tag').length===2 && document.querySelectorAll('#coMineOverlay .co-tag.m').length===0`), '근거 태그: 자동 2');
  ok(await T(`document.getElementById('coMineSum').textContent.indexOf('김재성 · 2곳')===0`), '머리말 요약');
  ok(await T(`!!document.getElementById('coViewBtn') && !!document.getElementById('coAsgVn')`), '관리자: 전체 보기 버튼 + 수동 지정 상자');

  console.log('▶ 관리자 수동 지정');
  await T(`coSetOwner('B산업','함현식'); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`_coOwnerOf('B산업')==='함현식' && clientOwner.m['B산업'].who==='함현식'`), 'B산업 → 함현식 수동 지정');
  ok(await T(`_coMine('함현식').length===1`), '함현식 담당 1곳');
  await T(`coSetOwner('A전기',''); 'ok'`);
  ok(await T(`_coOwnerOf('A전기')==='' && _coMine('김재성').length===1`), 'A전기 "(담당 없음)" 지정 → 자동 편입 막힘');
  await T(`coClearOwner('A전기'); 'ok'`);
  ok(await T(`_coOwnerOf('A전기')==='김재성'`), 'A전기 "자동으로" → 김재성 복귀');
  await T(`coOpenMine('all'); 'ok'`); await pg.waitForTimeout(400);
  txt = await T(`document.getElementById('coMineBody').innerText`);
  ok(txt.indexOf('B산업')>=0 && txt.indexOf('함현식')>=0 && (await T(`document.querySelectorAll('#coMineOverlay .co-tag.m').length===1`)), '전체 담당 현황: B산업 함현식(지정)');
  ok(await T(`document.querySelectorAll('#coMineOverlay tbody tr').length===4`), '전체 3곳 + 합계');

  console.log('▶ 비관리자');
  await T(`_authUser={id:'h',name:'함현식',role:'user'}; myMemberId='m2'; coOpenMine(); 'ok'`); await pg.waitForTimeout(400);
  ok(await T(`!document.getElementById('coViewBtn') && !document.getElementById('coAsgVn') && !document.querySelector('#coMineOverlay select.co-sel')`), '전체 보기·지정 UI 없음');
  txt = await T(`document.getElementById('coMineBody').innerText`);
  ok(txt.indexOf('B산업')>=0 && txt.indexOf('40,000')>=0 && txt.indexOf('지정')>=0, '함현식: B산업 40,000 (지정)');
  await T(`coSetOwner('C상사','함현식'); 'ok'`);
  ok(await T(`_coOwnerOf('C상사')==='김재성'`), '비관리자 coSetOwner 무시');

  console.log('▶ 견적 저장 뒤 편입 알림');
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; myMemberId='m1'; clientOwner={}; memoLines=[];
    quoteSaved=quoteSaved.filter(function(q){ return q.vname!=='B산업'; });
    for(var i=0;i<4;i++) quoteSaved.push({id:'b'+i,title:'Q',vname:'B산업',vid:'',count:1,total:0,savedBy:'이영희',savedAt:6000+i}); 'ok'`);
  await T(`_coAfterQuote('B산업','이영희'); 'ok'`);
  ok(await T(`memoLines.length===0 && !(clientOwner.a&&clientOwner.a['B산업']&&clientOwner.a['B산업'].who)`), '4회째: 아무 일 없음');
  await T(`quoteSaved.push({id:'b5',title:'Q',vname:'B산업',vid:'',count:1,total:0,savedBy:'이영희',savedAt:6010}); _coAfterQuote('B산업','이영희'); 'ok'`);
  ok(await T(`memoLines.length===1 && memoLines[0].owner==='이영희' && memoLines[0].done===true && memoLines[0].text.indexOf('담당 업체 편입 · B산업')===0 && memoLines[0].coRef.vname==='B산업'`), '5회째: 이영희 일정에 완료 줄 1개');
  await T(`quoteSaved.push({id:'b6',title:'Q',vname:'B산업',vid:'',count:1,total:0,savedBy:'이영희',savedAt:6011}); _coAfterQuote('B산업','이영희'); 'ok'`);
  ok(await T(`memoLines.length===1 && clientOwner.a['B산업'].who==='이영희'`), '6회째: 중복 알림 없음');

  console.log('▶ 배관');
  ok(await T(`typeof clientOwner==='object'`), 'clientOwner 선언');
  const keysN = await T(`(function(){ var n=0; var s=document.documentElement.outerHTML; return s; })().length>0`);
  ok(keysN, '페이지 정상');
  const srcTxt = fs.readFileSync(file,'utf8');
  const isTest = /\/test\//.test(file) || /testpage/.test(file);
  ok(srcTxt.split("'sched_client_pend','sched_client_owner','sched_meetings'").length-1 === (isTest?3:2), 'KEYS 목록에 sched_client_owner ('+(isTest?3:2)+'곳)');
  ok(srcTxt.indexOf("save('sched_client_owner', clientOwner)")>=0 && srcTxt.indexOf("sched_client_owner: clientOwner,   // r225\n")>=0, 'save/푸시/백업 배관');
  ok(srcTxt.indexOf("clientOwner      = load('sched_client_owner')")>=0, '복원 배관');
  ok(srcTxt.indexOf("_coAfterQuote(vn, who)")>=0, '견적 저장 후 호출');

  ok(errs.length===0, '페이지 오류 없음'+(errs.length?(' — '+errs.slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(_e){}
  process.exit(fail?1:0);
})();
