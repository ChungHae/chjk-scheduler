// r247 테스트 — 사내 내규 페이지(일정 옆 탭): 관리자 작성·수정·순서·삭제, 직원 열람, Firebase sched_rules 저장, 본문 표기
//  사용:  node test_r247.js <r247 적용된 index.html>
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b247/test/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const STUB = `
  window._xlsxStyleReady=true;
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r247.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1400,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  let store=null; const puts=[];
  await pg.route('**/*', r => { const u=r.request().url(); const m=r.request().method();
    if(u.startsWith('file://')) return r.continue();
    if(u.indexOf('/sched_rules.json')>=0){
      if(m==='GET') return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify(store)});
      if(m==='PUT'){ store=JSON.parse(r.request().postData()); puts.push(1); return r.fulfill({status:200, contentType:'application/json', body:'{}'}); }
    }
    r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  await T(`_fbDbUrl='https://fb.test'; _fbFetch=async function(u,o){ return fetch(u,o); }; _authUser={id:'kjs',name:'김재성',role:'admin'}; members=defaultMembers(); debouncedFbSave=function(){}; saveAll=function(){}; 'ok'`);

  console.log('▶ 1) 탭 · 빈 상태(관리자)');
  ok(await T(`!!document.querySelector('.page-tab[data-page="rules"]') && document.querySelector('.page-tab[data-page="rules"]').previousElementSibling.id==='tabSchedule'`), '일정 바로 옆에 [내규] 탭');
  await T(`document.querySelector('.page-tab[data-page="rules"]').click(); 'ok'`); await pg.waitForTimeout(500);
  ok(await T(`document.getElementById('pageRules').classList.contains('active') && document.querySelector('.page-tab[data-page="rules"]').classList.contains('active')`), '탭 클릭 → 내규 페이지');
  ok(await T(`document.getElementById('rlBody').innerText.indexOf('기본 항목 4개로 시작하기')>=0 && document.getElementById('rlAddBtn').style.display!=='none'`), '비어 있으면 기본 항목 제안 + [항목 추가]');

  console.log('▶ 2) 기본 항목 만들기 → 저장(PUT) → 렌더');
  await T(`rlSeed(); 'ok'`); await pg.waitForTimeout(500);
  ok(puts.length===1 && store && store.secs.length===4 && store.secs[1].title==='2. 법인카드', 'Firebase sched_rules 에 4항목 저장');
  ok(await T(`document.querySelectorAll('#rlBody .rl-sec').length===4 && document.querySelectorAll('#rlBody .rl-toc a').length===4`), '4항목 + 목차');
  ok(await T(`document.querySelectorAll('#rlBody .rl-sec')[0].querySelector('h3').textContent==='근무' && document.querySelectorAll('#rlBody .rl-sec')[1].querySelector('ul li b').textContent==='미리 한 줄 신청'`), '본문 표기: ## 소제목 · - 글머리 · **굵게**');
  ok(await T(`document.querySelectorAll('#rlBody .rl-sec')[1].innerText.indexOf('정산이 빨라집니다')>=0 && document.getElementById('rlBody').innerText.indexOf('허가')<0`), '법인카드 문구는 안내 톤(“허가” 없음)');

  console.log('▶ 3) 수정 · 순서 · 삭제');
  const id0 = store.secs[0].id;
  await T(`rlEditSec('${id0}'); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`!!document.getElementById('rlB_${id0}') && document.activeElement && document.activeElement.id==='rlB_${id0}'`), '[수정] → 제목·본문 입력칸(포커스)');
  await T(`document.getElementById('rlT_${id0}').value='1. 근무 시간'; document.getElementById('rlB_${id0}').value='- 09:00~18:00\\n- 점심 12~13시'; rlSaveSec('${id0}'); 'ok'`); await pg.waitForTimeout(400);
  ok(store.secs[0].title==='1. 근무 시간' && store.secs[0].body.indexOf('점심 12~13시')>0 && store.secs[0].by==='김재성' && store.secs[0].upd>0, '저장 → 제목·본문·수정자·수정일');
  ok(await T(`document.querySelectorAll('#rlBody .rl-sec')[0].querySelector('h2').textContent.indexOf('1. 근무 시간')===0 && document.querySelectorAll('#rlBody .rl-sec')[0].querySelector('.rl-foot').textContent.indexOf('김재성')>0`), '화면에 반영 + 수정 정보');
  await T(`rlMove('${id0}', 1); 'ok'`); await pg.waitForTimeout(300);
  ok(store.secs[1].id==='${id0}'.replace('${id0}','')+'' || store.secs[1].id===id0, '아래로 이동');
  await T(`showConfirmModal=function(t,m,fn){ fn(); }; rlDel('${id0}'); 'ok'`); await pg.waitForTimeout(300);
  ok(store.secs.length===3 && !store.secs.some(s=>s.id===id0), '삭제');
  await T(`rlAdd(); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`document.querySelectorAll('#rlBody .rl-sec input.rl-title').length===1`), '[항목 추가] → 빈 입력칸');
  await T(`rlCancel(); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`document.querySelectorAll('#rlBody .rl-sec').length===3`) && store.secs.length===3, '취소하면 빈 항목은 버림');

  console.log('▶ 4) 일반 직원 = 열람만');
  await T(`_authUser={id:'hhs',name:'함현식',role:'user'}; _rlDoc=null; renderRulesPage(); 'ok'`); await pg.waitForTimeout(400);
  ok(await T(`document.querySelectorAll('#rlBody .rl-sec').length===3 && !document.querySelector('#rlBody .rl-tools') && document.getElementById('rlAddBtn').style.display==='none'`), '3항목 보이고 수정 도구 없음');
  ok(await T(`document.getElementById('rlMeta').textContent.indexOf('항목 3')===0`), '상단 메타(항목 수·최근 수정)');

  ok(errs.length===0, '페이지 오류 없음'+(errs.length?(' — '+errs.slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(_e){}
  process.exit(fail?1:0);
})();
