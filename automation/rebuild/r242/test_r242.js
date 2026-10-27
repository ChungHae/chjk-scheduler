// r242 테스트 — 일정 페이지 1회성 공지 팝업(유튜브 임베드), 계정별 확인 기록(Firebase sched_notice_seen)
//  사용:  node test_r242.js <r242 적용된 index.html>
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b242/test/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const STUB = `
  window._xlsxStyleReady=true;
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r242.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1400,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  const store = {};   // 가짜 Firebase: sched_notice_seen/<nid>/<uid> → ts
  const puts = [];
  await pg.route('**/*', r => { const u=r.request().url(); const m=r.request().method();
    if(u.startsWith('file://')) return r.continue();
    const mm = u.match(/\/sched_notice_seen\/([^/]+)\/([^/.]+)\.json/);
    if(mm){ const k=mm[1]+'/'+mm[2];
      if(m==='GET') return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify(store[k]==null?null:store[k])});
      if(m==='PUT'){ store[k]=JSON.parse(r.request().postData()); puts.push(k); return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify(store[k])}); }
    }
    if(u.indexOf('youtube.com/embed')>=0) return r.fulfill({status:200, contentType:'text/html', body:'<html><body>yt</body></html>'});
    r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  await T(`
    _fbDbUrl='https://fb.test'; _fbFetch=async function(url,opts){ return fetch(url,opts); };
    _authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울'},{id:'m2',name:'함현식',group:'서울'}];
    debouncedFbSave=function(){}; saveAll=function(){}; memoLines=[]; meetings=[];
    'ok'`);

  console.log('▶ 1) 일정 페이지 진입 → 공지 팝업 (유튜브 임베드)');
  await T(`switchPage('memo'); 'ok'`); await pg.waitForTimeout(900);
  ok(await T(`!!document.getElementById('ntOverlay')`), '팝업 표시됨');
  ok(await T(`(document.getElementById('ntFrame')||{}).src==='https://www.youtube.com/embed/mx2bnXbRZq0?rel=0&playsinline=1'`), '쇼츠 임베드 iframe src');
  ok(await T(`!!document.querySelector('#ntOverlay a[href="https://www.youtube.com/shorts/mx2bnXbRZq0"][target="_blank"]')`), '[유튜브에서 열기] 링크');
  ok(await T(`document.getElementById('ntOverlay').innerText.indexOf('다시 표시되지 않습니다')>=0`), '안내 문구');

  console.log('▶ 2) × 로 닫기만 하면 기록 안 남고 다음 진입에 다시 뜸');
  await T(`document.getElementById('ntClose').click(); 'ok'`); await pg.waitForTimeout(100);
  ok(await T(`!document.getElementById('ntOverlay')`), '닫힘');
  ok(puts.length===0 && !(await T(`localStorage.getItem('sched_notice_seen_nt20261020_kjs')`)), '기록 없음');
  await T(`_ntShown={}; switchPage('weekly'); switchPage('memo'); 'ok'`); await pg.waitForTimeout(900);
  ok(await T(`!!document.getElementById('ntOverlay')`), '다시 표시됨');

  console.log('▶ 3) [확인] → Firebase 기록 + 로컬 캐시, 이후 안 뜸');
  await T(`document.getElementById('ntOk').click(); 'ok'`); await pg.waitForTimeout(400);
  ok(await T(`!document.getElementById('ntOverlay')`), '팝업 닫힘');
  ok(puts.length===1 && puts[0]==='nt20261020/kjs' && typeof store['nt20261020/kjs']==='number', 'PUT sched_notice_seen/nt20261020/kjs = 시각 ('+JSON.stringify(puts)+')');
  ok(!!(await T(`localStorage.getItem('sched_notice_seen_nt20261020_kjs')`)), '로컬 캐시 저장');
  await T(`_ntShown={}; switchPage('weekly'); switchPage('memo'); 'ok'`); await pg.waitForTimeout(900);
  ok(await T(`!document.getElementById('ntOverlay')`), '같은 계정 재진입 — 안 뜸');

  console.log('▶ 4) 다른 계정은 다시 1회 · 서버에 이미 기록된 계정(다른 PC 에서 확인)은 안 뜸');
  await T(`_authUser={id:'hhs',name:'함현식',role:'user'}; _ntShown={}; switchPage('weekly'); switchPage('memo'); 'ok'`); await pg.waitForTimeout(900);
  ok(await T(`!!document.getElementById('ntOverlay')`), '다른 계정 → 표시');
  await T(`document.getElementById('ntClose').click(); 'ok'`);
  store['nt20261020/pjh']=1760000000000;
  await T(`_authUser={id:'pjh',name:'박지현',role:'user'}; _ntShown={}; switchPage('weekly'); switchPage('memo'); 'ok'`); await pg.waitForTimeout(900);
  ok(await T(`!document.getElementById('ntOverlay')`), '서버 기록 있는 계정 → 안 뜸');
  ok(!!(await T(`localStorage.getItem('sched_notice_seen_nt20261020_pjh')`)), '서버 기록을 로컬 캐시로 복사');

  console.log('▶ 5) 로그인 전·동기화 전에는 띄우지 않음');
  await T(`_authUser=null; _ntShown={}; switchPage('weekly'); switchPage('memo'); 'ok'`); await pg.waitForTimeout(900);
  ok(await T(`!document.getElementById('ntOverlay')`), '로그인 전 — 안 뜸');
  await T(`_authUser={id:'new1',name:'신입',role:'user'}; _fbDbUrl=''; _ntShown={}; switchPage('weekly'); switchPage('memo'); 'ok'`); await pg.waitForTimeout(900);
  ok(await T(`!document.getElementById('ntOverlay')`), '동기화 전 — 안 뜸');

  ok(errs.length===0, '페이지 오류 없음'+(errs.length?(' — '+errs.slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(_e){}
  process.exit(fail?1:0);
})();
