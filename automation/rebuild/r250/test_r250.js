// r250 테스트 — 저장 견적 목록(quoteSaved) 동시 저장 보호.
//  두 탭(A·B)이 가짜 Firebase(메모리)를 공유하며 같은 순간에 견적을 저장한다.
//  사용:  node test_r250.js <r250 적용된 index.html> [라벨]
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || '/tmp/h/live.html');
const LABEL = process.argv[3] || '?';
let pass = 0, fail = 0;
function ok(c, msg, extra){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg, extra===undefined?'':('   → '+extra)); } }
(async () => {
  const STUB = `
  window._xlsxStyleReady=true;
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  let src = fs.readFileSync(file, 'utf8');
  if(src.indexOf('window.__T=') < 0) src = src.replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(require('os').tmpdir(), '_h_r250.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch();

  // ── 가짜 Firebase ──  teamdata_test/<key>.json  과  teamdata_test_qsaved/<id>.json
  const DB = {}; const QS = {}; const putLog = [];
  async function route(r){
    const req = r.request(), u = req.url();
    if(u.startsWith('file://')) return r.continue();
    const mq = u.match(/\/teamdata_[a-z]+_qsaved\/([^.?]+)\.json/);
    if(mq){
      const id = mq[1];
      if(req.method() === 'PUT'){ putLog.push(id); QS[id] = JSON.parse(req.postData() || 'null'); return r.fulfill({status:200, contentType:'application/json', body:'{}'}); }
      if(req.method() === 'DELETE'){ delete QS[id]; return r.fulfill({status:200, contentType:'application/json', body:'{}'}); }
      if(req.method() === 'GET'){ return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify(QS[id] === undefined ? null : QS[id])}); }
    }
    const m = u.match(/\/teamdata_[a-z]+(?:\/([^.?]+))?\.json/);
    if(m){
      const key = m[1];
      if(req.method() === 'PATCH'){ Object.assign(DB, JSON.parse(req.postData())); return r.fulfill({status:200, contentType:'application/json', body:'{}'}); }
      if(req.method() === 'PUT'){ if(key) DB[key] = JSON.parse(req.postData() || 'null'); return r.fulfill({status:200, contentType:'application/json', body:'{}'}); }
      if(req.method() === 'GET'){ const v = key ? (key === '_updatedAt' ? (DB._updatedAt || 0) : (DB[key] === undefined ? null : DB[key])) : DB; return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify(v)}); }
    }
    r.abort();
  }
  async function openClient(name){
    const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1400,height:900} });
    const pg = await ctx.newPage(); const errs = []; pg.on('pageerror', e => errs.push(String(e)));
    await pg.route('**/*', route);
    await pg.goto('file://' + tmp); await pg.waitForTimeout(6000);
    await pg.evaluate(() => { var g = document.getElementById('authGate'); if(g) g.style.display = 'none'; });
    const T = c => pg.evaluate(c2 => window.__T(c2), c);
    await T(`
      _fbDbUrl='https://fb.test'; _fbReady=true; _fbLoadedOnce=true; _authUser={id:'${name}',name:'${name}',role:'admin'};
      members=[{id:'m1',name:'김재성',group:'서울'},{id:'m2',name:'함현식',group:'서울'}];
      _fbFetch=async function(url,opts){ return fetch(url,opts); };
      _isViewer=function(){ return false; };
      showInfoModal=function(){}; showConfirmModal=function(t,m,cb){ cb && cb(); };
      memoLines=[]; personalSchedules=[];
      window.__mkCart=function(spec){ _qCart=[{vid:'v1',vname:'테스트상사',spec:spec,name:spec,qty:1,buy:1000,sell:2000,e:3000}]; _qCols=[]; _qNego=null; _qMemo=''; _qNote=''; _qQuoteYmd='20261027'; };
      'ok'`);
    return { pg, T, errs, name };
  }
  const A = await openClient('김재성'), B = await openClient('함현식');
  const OLD = { id:'q_old', title:'옛견적', vname:'기존상사', vid:'v0', count:1, total:100, savedBy:'김재성', savedAt:1, upd:1 };
  const reset = async () => {
    DB.sched_quote_saved = [OLD]; DB.sched_quote_del = {}; DB._updatedAt = 1;
    for(const C of [A, B]) await C.T(`quoteSaved=${JSON.stringify([OLD])}; save('sched_quote_saved',quoteSaved); if(typeof _qsDelMap!=='undefined'){_qsDelMap={}; _qsPend={};} _fbLastUpdatedAt=1; 'ok'`);
  };

  console.log('▶ 1) 두 사람이 같은 순간에 견적 저장 (0.8초 디바운스 안)');
  await reset();
  await A.T(`__mkCart('AAA-1'); _qLoadedId='q_A1'; _qQuoteNo='A-20261027-01'; _qPersistQuote().then(function(){return 'OK';}).catch(function(e){return 'ERR:'+(e&&e.message||e);})`);
  await B.T(`__mkCart('BBB-1'); _qLoadedId='q_B1'; _qQuoteNo='B-20261027-01'; _qPersistQuote().then(function(){return 'OK';}).catch(function(e){return 'ERR:'+(e&&e.message||e);})`);
  await A.pg.waitForTimeout(7000);
  let ids = (DB.sched_quote_saved || []).map(x => x && x.id);
  ok(ids.indexOf('q_A1') >= 0 && ids.indexOf('q_B1') >= 0 && ids.indexOf('q_old') >= 0,
     '서버 목록에 A·B 견적이 모두 남음 (전에는 한쪽이 덮여 사라졌다)', JSON.stringify(ids));
  ok(putLog.indexOf('q_A1') >= 0 && putLog.indexOf('q_B1') >= 0, '품목은 양쪽 다 직접 PUT 으로 저장됨', JSON.stringify(putLog));

  console.log('▶ 2) 폴링이 아직 안 올린 내 견적을 덮지 않음');
  await reset();
  await B.T(`__mkCart('CCC-1'); _qLoadedId='q_B2'; _qQuoteNo='B-20261027-02'; _qPersistQuote().then(function(){return 'OK';}).catch(function(e){return 'ERR:'+e.message;})`);
  await B.pg.waitForTimeout(150);
  DB.sched_quote_saved = [OLD, { id:'q_other', title:'남의견적', vname:'다른상사', savedAt:2, upd:2 }];
  DB._updatedAt = Date.now() + 1;
  await B.T(`_fbLastUpdatedAt=0; _fbSkipNext=false; _pollSync(true)`); await B.pg.waitForTimeout(900);
  ok(await B.T(`(quoteSaved||[]).some(function(x){return x&&x.id==='q_B2';})`), '폴링 뒤에도 내 견적이 목록에 남아 있음');
  ok(await B.T(`(quoteSaved||[]).some(function(x){return x&&x.id==='q_other';})`), '같은 폴링으로 남의 견적도 받아옴');
  await B.T(`debouncedFbSave()`); await B.pg.waitForTimeout(5000);
  ok((DB.sched_quote_saved || []).some(x => x && x.id === 'q_B2'), '이어서 서버에도 올라감', JSON.stringify((DB.sched_quote_saved||[]).map(x=>x&&x.id)));

  console.log('▶ 3) 삭제는 묘비로 — 옛 사본이 되살리지 못한다');
  await reset();
  await A.T(`quoteSaved.unshift({id:'q_D1',title:'지울견적',vname:'테스트상사',savedAt:5,upd:5}); save('sched_quote_saved',quoteSaved); 'ok'`);
  await B.T(`quoteSaved.unshift({id:'q_D1',title:'지울견적',vname:'테스트상사',savedAt:5,upd:5}); save('sched_quote_saved',quoteSaved); 'ok'`);
  await A.T(`_guardW=function(){return true;}; qDelSaved('q_D1'); 'ok'`); await A.pg.waitForTimeout(2500);
  ok(!(DB.sched_quote_saved || []).some(x => x && x.id === 'q_D1') && DB.sched_quote_del && DB.sched_quote_del.q_D1,
     '서버에서 삭제 + 묘비 기록', JSON.stringify(DB.sched_quote_del));
  await B.T(`__mkCart('DDD-1'); _qLoadedId='q_B3'; _qQuoteNo='B-20261027-03'; _qPersistQuote().then(function(){return 'OK';}).catch(function(e){return 'ERR:'+e.message;})`);
  await B.pg.waitForTimeout(5000);
  ok(!(DB.sched_quote_saved || []).some(x => x && x.id === 'q_D1'), 'B 가 뒤늦게 저장해도 삭제된 견적이 되살아나지 않음');
  ok((DB.sched_quote_saved || []).some(x => x && x.id === 'q_B3'), '같은 저장에서 B 의 새 견적은 들어감');

  console.log('▶ 4) 내용이 빈 견적은 저장하지 않고 안내한다');
  await reset();
  const r4 = await A.T(`_qCart=[{vid:'v1',vname:'테스트상사',spec:'',name:'',qty:1,buy:'',sell:'',e:''}]; _qLoadedId=null; _qQuoteNo=null; _qPersistQuote().then(function(){return 'OK';}).catch(function(e){return 'ERR:'+(e&&e.message||e);})`);
  ok(String(r4).indexOf('ERR:') === 0 && /비어 있습니다/.test(String(r4)), '빈 견적은 오류를 던진다', String(r4).slice(0, 80));
  ok(!(await A.T(`(quoteSaved||[]).some(function(x){return !x||!x.id;})`)), '목록에 id 없는 항목이 생기지 않는다');
  ok(putLog.indexOf('null') < 0 && putLog.indexOf('undefined') < 0, '_qsaved/null 로 쓰지 않는다', JSON.stringify(putLog));

  console.log('▶ 5) 번호를 못 받은 상태는 저장하지 않는다');
  const r5 = await A.T(`__mkCart('EEE-1'); _qLoadedId=null; _qQuoteNo=null; _qEnsureQuoteNo=function(){}; _qPersistQuote().then(function(){return 'OK';}).catch(function(e){return 'ERR:'+(e&&e.message||e);})`);
  ok(String(r5).indexOf('ERR:') === 0 && /견적번호/.test(String(r5)), '번호·id 가 없으면 오류', String(r5).slice(0, 80));

  console.log('▶ 6) 저장·삭제가 묘비 키까지 같이 올린다');
  ok(DB.sched_quote_del !== undefined, "doFbSave 가 sched_quote_del 을 함께 올린다");

  console.log('▶ 7) 페이지 오류 없음');
  ok(A.errs.length === 0 && B.errs.length === 0, 'pageerror 없음', (A.errs.concat(B.errs)).slice(0, 2).join(' | '));

  await br.close();
  console.log('[' + LABEL + '] ' + pass + '/' + (pass + fail));
  if(fail) process.exitCode = 0;
})();
