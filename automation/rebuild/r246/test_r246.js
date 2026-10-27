// r246 테스트 — 목표 세부 항목 → 담당자 일정 줄(날짜) · 완료 양방향 동기화 · 삭제 시 줄 제거 · [목표] 배지
//  사용:  node test_r246.js <r246 적용된 index.html>
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b246/test/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const STUB = `
  window._xlsxStyleReady=true;
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r246.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1400,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  await pg.route('**/*', r => { if(r.request().url().startsWith('file://')) return r.continue(); r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  const today=await T(`_mmToday()`);
  await T(`
    _fbDbUrl='https://fb.test'; _authUser={id:'hhs',name:'함현식',role:'user'}; members=[{id:'m1',name:'김재성',group:'서울'},{id:'m2',name:'함현식',group:'화성'}];
    debouncedFbSave=function(){}; saveAll=function(){}; _mtSave=function(){ window.__mt=(window.__mt||0)+1; }; _mmSave=function(){ window.__mm=(window.__mm||0)+1; };
    memoLines=[]; _mtDelMap={};
    meetings=[{id:'mtg1',date:'${today}',title:'10월 회의',author:'김재성',attendees:['김재성','함현식'],agenda:[],reports:[],goals:[{name:'함현식',items:[{id:'g1',title:'신규 거래처 3곳 발굴',detail:'',subs:[],at:1,upd:1}]}],updatedAt:1,createdAt:1}];
    switchPage('meeting'); mtOpen('mtg1'); 'ok'`); await pg.waitForTimeout(300);

  console.log('▶ 1) 세부 항목 추가(날짜 지정) → 내 일정에 줄');
  ok(await T(`!!document.querySelector('#mtBody .mt-goal[data-gid="g1"] .mt-goal-add input[type=date]')`), '추가칸에 날짜 입력');
  await T(`var add=document.querySelector('#mtBody .mt-goal[data-gid="g1"] .mt-goal-add'); add.querySelector('input[type=date]').value='2026-10-30'; var ip=add.querySelector('input:not([type=date])'); ip.value='A사 방문 미팅'; mtGoalSubAdd('mtg1','g1',ip); 'ok'`); await pg.waitForTimeout(200);
  const sub = await T(`JSON.stringify(meetings[0].goals[0].items[0].subs[0])`);
  ok(JSON.parse(sub).due==='2026-10-30' && !!JSON.parse(sub).memoId, '세부 항목에 날짜·연결 id — '+sub);
  ok(await T(`memoLines.length===1 && memoLines[0].owner==='함현식' && memoLines[0].text==='목표 · 신규 거래처 3곳 발굴 — A사 방문 미팅' && memoLines[0].when.date==='2026-10-30' && memoLines[0].goalRef.sid===meetings[0].goals[0].items[0].subs[0].id && !memoLines[0].done`), '담당자 일정 줄 생성 (글·날짜·연결)');
  ok(await T(`!!document.querySelector('#mtBody .mt-goal[data-gid="g1"] .mt-goal-sub input.mt-goal-date') && document.querySelector('#mtBody .mt-goal[data-gid="g1"] .mt-goal-sub input.mt-goal-date').value==='2026-10-30'`), '세부 항목 줄에 날짜 표시');

  console.log('▶ 2) 일정에서 완료 → 이수율 · 회의록 체크 해제 → 일정도 취소');
  await T(`switchPage('memo'); renderMemoPage(true); 'ok'`); await pg.waitForTimeout(300);
  ok(await T(`!!document.querySelector('#mmList .mm-chip.mm-mt') && document.querySelector('#mmList .mm-chip.mm-mt').textContent==='목표'`), '일정 줄에 [목표] 배지');
  await T(`_mmMarkDone(memoLines[0]); 'ok'`);
  ok(await T(`meetings[0].goals[0].items[0].subs[0].done===true && _mtGoalProg(meetings[0].goals[0].items[0]).pct===100`), '일정 완료 → 세부 항목 완료 → 이수율 100%');
  await T(`mtGoalSubToggle('mtg1','g1',meetings[0].goals[0].items[0].subs[0].id,false); 'ok'`);
  ok(await T(`memoLines[0].done===false && memoLines[0].doneAt===0`), '목표에서 체크 해제 → 일정 줄도 미완료');
  await T(`mtGoalSubToggle('mtg1','g1',meetings[0].goals[0].items[0].subs[0].id,true); 'ok'`);
  ok(await T(`memoLines[0].done===true`), '목표에서 체크 → 일정 줄 완료');

  console.log('▶ 3) 날짜 변경 · 날짜 없이 추가 · 삭제');
  await T(`mtGoalSubDue('mtg1','g1',meetings[0].goals[0].items[0].subs[0].id,'2026-11-03'); 'ok'`);
  ok(await T(`memoLines[0].when.date==='2026-11-03' && meetings[0].goals[0].items[0].subs[0].due==='2026-11-03'`), '날짜 바꾸면 일정 줄 날짜도');
  await T(`switchPage('meeting'); mtOpen('mtg1'); 'ok'`); await pg.waitForTimeout(200);
  await T(`var add=document.querySelector('#mtBody .mt-goal[data-gid="g1"] .mt-goal-add'); var ip=add.querySelector('input:not([type=date])'); ip.value='B사 제안서 발송'; mtGoalSubAdd('mtg1','g1',ip); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`memoLines.length===2 && memoLines[1].when.date==='' && memoLines[1].text.indexOf('B사 제안서 발송')>0`), '날짜 없이 추가 → 날짜 없는 일정 줄');
  const sid2 = await T(`meetings[0].goals[0].items[0].subs[1].id`);
  await T(`mtGoalSubDel('mtg1','g1','${sid2}'); 'ok'`);
  ok(await T(`memoLines.length===1 && meetings[0].goals[0].items[0].subs.length===1`), '세부 항목 삭제 → 일정 줄 제거');
  ok(await T(`_mtGoalCan('김재성')===false`), '다른 사람 목표는 수정 불가(일반 직원)');
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; window.__cf=null; showConfirmModal=function(t,m,fn){ fn(); }; mtGoalDel('mtg1','g1'); 'ok'`); await pg.waitForTimeout(100);
  ok(await T(`memoLines.length===0 && meetings[0].goals[0].items.length===0`), '목표 삭제 → 세부 항목 일정 줄 전부 제거');

  console.log('▶ 4) 메모장 내 목표 카드에서도 동일');
  await T(`_authUser={id:'hhs',name:'함현식',role:'user'}; meetings[0].goals[0].items=[{id:'g2',title:'SMC 신제품 소개',detail:'',subs:[],at:2,upd:2}]; switchPage('memo'); renderMemoPage(true); 'ok'`); await pg.waitForTimeout(300);
  await T(`var add=document.querySelector('#mmList .mt-goal[data-gid="g2"] .mt-goal-add'); add.querySelector('input[type=date]').value='${today}'; var ip=add.querySelector('input:not([type=date])'); ip.value='C사 카탈로그 전달'; mtGoalSubAdd('mtg1','g2',ip); 'ok'`); await pg.waitForTimeout(300);
  ok(await T(`memoLines.length===1 && memoLines[0].when.date==='${today}' && memoLines[0].goalRef.gid==='g2'`), '카드에서 추가 → 오늘 일정 줄');
  ok(await T(`document.getElementById('mmList').innerText.indexOf('C사 카탈로그 전달')>=0`), '메모 목록에 보임');

  ok(errs.length===0, '페이지 오류 없음'+(errs.length?(' — '+errs.slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(_e){}
  process.exit(fail?1:0);
})();
