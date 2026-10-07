const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b219/testpage/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', '  window.__T=function(c){return eval(c);};\n  function _vacUnlimited(id){');
  const tmp = path.join(path.dirname(file), '_h_r222.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  await pg.route('**/*', r => { const u=r.request().url(); if(u.startsWith('file://')) r.continue(); else r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  const show = (id) => pg.evaluate((id)=>{ document.querySelectorAll('.page-section').forEach(p=>{ if(p.id===id) p.style.display='block'; }); }, id);

  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울'},{id:'m2',name:'함현식',group:'서울'},{id:'m3',name:'김은석',group:'서울'}]; myMemberId='m1'; memoLines=[]; meetings=[]; 'ok'`);

  console.log('▶ ① 회의 안건 저장 → 참석자 각자의 일정에');
  await T(`meetings.push({ id:'mt1', date:'2026-10-08', time:'09:30 ~ 10:30', place:'서울', room:'회의실', title:'주간 회의', author:'김재성', attendees:['김재성','함현식','외부손님'], agenda:[], reports:[{name:'김재성',items:[]},{name:'함현식',items:[]}], createdAt:Date.now(), createdBy:'김재성', updatedAt:Date.now(), status:'draft' }); _mtOpen='mt1'; switchPage('meeting'); renderMeetingPage(true); 'ok'`);
  await pg.waitForTimeout(300); await show('pageMeeting');
  ok(await T(`!!document.getElementById('mtAgIn')`), '안건 작성란 있음');
  await pg.locator('#mtAgIn').fill('신규 거래처 발굴: 업종별 방문 영업\n재고 정리');
  await T(`mtSaveAgenda('mt1'); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`meetings[0].agenda.length===2 && meetings[0].agenda[0].memoIds.length===2 && meetings[0].agenda[1].memoIds.length===2`), '안건 2건 · 각각 참석자(멤버) 2명의 일정 줄 연결 (외부손님 제외)');
  ok(await T(`memoLines.length===4 && memoLines.filter(function(l){return l.owner==='함현식';}).length===2 && memoLines.filter(function(l){return l.owner==='김재성';}).length===2`), '메모 4줄: 김재성 2 · 함현식 2');
  ok(await T(`memoLines[0].text==='회의 안건(주간 회의) · 신규 거래처 발굴: 업종별 방문 영업' && memoLines[0].kind==='meeting' && memoLines[0].when.date==='2026-10-08' && memoLines[0].mtRef.mid==='mt1' && memoLines[0].mtRef.iid===meetings[0].agenda[0].id`), '줄 내용·종류(미팅)·회의 날짜·회의록 연결');
  ok(await T(`memoLines[2].text==='회의 안건(주간 회의) · 재고 정리'`), '제목 없는 안건 줄');
  ok(await T(`document.getElementById('mtToast').textContent.indexOf('참석자 일정에 4건 등록')>=0`), '토스트: 참석자 일정에 4건 등록');
  ok(await T(`document.getElementById('mtBody').innerHTML.indexOf('일정 2</span>')>=0`), '회의록 안건 줄에 "일정 2" 표시');

  console.log('▶ 완료 동기화 (안건 ↔ 참석자 줄 전부)');
  await T(`mtToggle('mt1', meetings[0].agenda[0].id); 'ok'`); await pg.waitForTimeout(100);
  ok(await T(`meetings[0].agenda[0].done && memoLines.filter(function(l){ return l.mtRef.iid===meetings[0].agenda[0].id; }).every(function(l){ return l.done; })`), '안건 완료 → 두 사람 일정 줄 모두 완료');
  await T(`mtToggle('mt1', meetings[0].agenda[0].id); 'ok'`); await pg.waitForTimeout(100);
  ok(await T(`!meetings[0].agenda[0].done && memoLines.filter(function(l){ return l.mtRef.iid===meetings[0].agenda[0].id; }).every(function(l){ return !l.done; })`), '완료 취소 → 모두 취소');
  await T(`var _l=memoLines.find(function(l){ return l.owner==='함현식' && l.mtRef.iid===meetings[0].agenda[1].id; }); _l.done=true; _l.doneAt=Date.now(); _mtSyncFromMemo(_l, true); 'ok'`); await pg.waitForTimeout(100);
  ok(await T(`meetings[0].agenda[1].done && memoLines.find(function(l){ return l.owner==='김재성' && l.mtRef.iid===meetings[0].agenda[1].id; }).done`), '함현식 일정에서 완료 → 안건 완료 + 김재성 줄도 완료');

  console.log('▶ 메모장 표시 + 삭제 시 연결 해제');
  await T(`switchPage('memo'); 'ok'`); await pg.waitForTimeout(300);
  ok(await T(`document.querySelectorAll('#pageMemo .mm-chip.mm-mt').length>=1 && document.getElementById('pageMemo').innerText.indexOf('회의 안건(주간 회의)')>=0`), '메모장(개인 일정)에 안건 줄 + [회의] 칩');
  await T(`mtDelItem('mt1', meetings[0].agenda[0].id); 'ok'`); await pg.waitForTimeout(100);
  ok(await T(`meetings[0].agenda.length===1 && memoLines.length===4 && memoLines.filter(function(l){ return !l.mtRef; }).length===2`), '안건 삭제 → 일정 줄은 남고 연결(mtRef)만 해제');

  console.log('▶ 참석자 중 멤버가 없으면 작성자 본인');
  await T(`meetings.push({ id:'mt2', date:'2026-10-09', title:'외부 미팅', author:'김재성', attendees:['외부손님'], agenda:[], reports:[], createdAt:Date.now(), createdBy:'김재성', updatedAt:Date.now(), status:'draft' }); _mtOpen='mt2'; switchPage('meeting'); renderMeetingPage(true); 'ok'`);
  await pg.waitForTimeout(200); await show('pageMeeting');
  await pg.locator('#mtAgIn').fill('샘플 전달'); await T(`mtSaveAgenda('mt2'); 'ok'`); await pg.waitForTimeout(100);
  ok(await T(`meetings[1].agenda[0].memoIds.length===1 && memoLines[memoLines.length-1].owner==='김재성'`), '작성자 일정에 1건');

  console.log('▶ ② 견적서 저장 → 작성자 일정에 완료된 업무');
  await T(`memoLines=[]; _fbDbUrl='https://x.test'; _fbPutOk=async function(){ return true; }; _fbFetch=async function(){ return {ok:true, json:async function(){ return {}; }}; }; debouncedFbSave=function(){}; doFbSave=function(){};
    quoteVendors=[{id:'qv1',name:'주식회사 케이에스',count:1}]; _qCurId='qv1'; quoteSaved=[];
    _qCart=[{vid:'qv1',vname:'주식회사 케이에스',spec:'LVMK205-5K',name:'VALVE',e:28390,buy:17320,sell:18830,qty:2},{vid:'qv1',vname:'주식회사 케이에스',spec:'KPH04-01',name:'FITTING',e:2800,buy:2100,sell:2420,qty:1}];
    _qQuoteNo='주식회사 케이에스-20261007-01'; _qLoadedId='q_t1'; 'ok'`);
  await pg.evaluate(async()=>{ await window.__T('_qPersistQuote()'); });
  await pg.waitForTimeout(100);
  ok(await T(`memoLines.length===1 && memoLines[0].done===true && memoLines[0].owner==='김재성'`), '완료된 메모 1줄 (작성자)');
  ok(await T(`memoLines[0].text==='견적서 작성 · 주식회사 케이에스 · 주식회사 케이에스-20261007-01 (2품목 · 40,080원)' && memoLines[0].qRef.id==='q_t1' && memoLines[0].vendor==='주식회사 케이에스'`), '줄 내용: 거래처·견적번호·품목수·합계 + 견적 연결');
  await T(`_qCart.push({vid:'qv1',vname:'주식회사 케이에스',spec:'AS2201F-01-06S',name:'SPEED',e:5000,buy:3500,sell:4000,qty:1}); 'ok'`);
  await pg.evaluate(async()=>{ await window.__T('_qPersistQuote()'); });
  ok(await T(`memoLines.length===1 && memoLines[0].text.indexOf('(3품목 · 44,080원)')>0`), '같은 견적 다시 저장 → 새 줄 없이 갱신');
  await T(`switchPage('done'); 'ok'`); await pg.waitForTimeout(300);
  ok(await T(`document.getElementById('dnList').innerText.indexOf('견적서 작성 · 주식회사 케이에스')>=0`), '완료한 업무 탭에 보임');
  await T(`switchPage('memo'); 'ok'`); await pg.waitForTimeout(300);
  ok(await T(`!!document.querySelector('#pageMemo .mm-chip.mm-qt')`), '메모장에 [견적] 칩');
  await T(`window.__loaded=null; window.qLoadSaved=function(id){ window.__loaded=id; }; mmGoQuote('q_t1'); 'ok'`);
  ok(await T(`window.__loaded==='q_t1'`), '[견적] 칩 → 그 견적 불러오기');
  await T(`memoLines=[]; _authUser={id:'x',name:'외부인',role:'admin'}; 'ok'`);
  await pg.evaluate(async()=>{ await window.__T('_qPersistQuote()'); });
  ok(await T(`memoLines.length===0`), '멤버가 아닌 사용자면 기록하지 않음');

  ok(errs.length===0, 'pageerror 0'+(errs.length?(' — '+errs.join(' | ')):''));
  console.log(`\n결과: ${pass}/${pass+fail}`);
  fs.unlinkSync(tmp); await br.close(); process.exit(fail?1:0);
})();
