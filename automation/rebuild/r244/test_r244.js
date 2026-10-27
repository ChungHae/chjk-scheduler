// r244 테스트 — ① 견적 담당자 저장·복원(새로고침·불러오기) ② 저장된 그대로면 재접속·이동 때 '작성 중인 견적' 안 묻기
//  사용:  node test_r244.js <r244 적용된 index.html>
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b244/test/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const STUB = `
  window._xlsxStyleReady=true;
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r244.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  await pg.route('**/*', r => { if(r.request().url().startsWith('file://')) return r.continue(); r.abort(); });
  const SETUP = `
    _fbDbUrl='https://fb.test'; _authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울',phone:'010-5228-2922'}];
    debouncedFbSave=function(){}; saveAll=function(){};
    quoteVendors=[{id:'v1',name:'충해)성기웅'}]; _qBlobGet=async function(){ return []; }; _ensurePriceSyncMap=async function(){}; _qEnsureAllIdx=async function(){};
    _qsBlobPut=async function(id,items){ window.__put=(window.__put||0)+1; window.__items=items; }; _qsBlobGet=async function(id){ return window.__items; };
    _qFlushLedgerFromCart=async function(){}; _smcCollectFromCart=async function(){}; _pendTouchFromCart=function(){}; _qLogDoneMemo=function(){}; _coAfterQuote=function(){};
    'ok'`;
  async function boot(){
    await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
    await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
    await T(SETUP);
  }
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  await boot();

  console.log('▶ 1) 담당자 입력 → 새로고침 뒤에도 남음');
  await T(`switchPage('estimate'); qSetSubTab('quote'); 'ok'`); await pg.waitForTimeout(200);
  await T(`(async function(){ await _qSelectVendorNow('v1', true); })(); 'ok'`); await pg.waitForTimeout(400);
  await T(`_qCart=[{vid:'v1',vname:'충해)성기웅',spec:'MGPM20-25Z',name:'실린더',qty:5,sell:89690,buy:70000,e:100000}]; renderQCart(); 'ok'`);
  ok(await T(`!document.getElementById('qManager').disabled`), '거래처 선택 후 담당자 칸 활성');
  await T(`var m=document.getElementById('qManager'); m.value='홍길동'; m.dispatchEvent(new Event('input')); _qCartSaveFlush(); 'ok'`);
  ok(await T(`_qMgr==='홍길동' && localStorage.getItem(_qCartKey()+'_mgr')==='홍길동'`), '_qMgr + localStorage 저장');
  await T(`renderQCart(); 'ok'`);
  ok(await T(`document.getElementById('qManager').value==='홍길동'`), '다시 그려도 값 유지');
  // 새로고침(재접속) — 저장 안 한 초안이므로 '작성 중인 견적' 창이 떠야 함
  await boot(); await T(`_qDraftBootCheck(); 'ok'`); await pg.waitForTimeout(300);
  ok(await T(`document.getElementById('qLeaveOverlay') && document.getElementById('qLeaveOverlay').style.display==='flex'`), '저장 안 한 초안 → 재접속 때 묻는다 (기존 동작)');
  await T(`document.getElementById('qLeaveOverlay').style.display='none'; switchPage('estimate'); qSetSubTab('quote'); (async function(){ await _qSelectVendorNow('v1', false); })(); 'ok'`); await pg.waitForTimeout(400);
  ok(await T(`_qMgr==='홍길동' && document.getElementById('qManager').value==='홍길동'`), '재접속 후 담당자 복원');

  console.log('▶ 2) 저장(자동 저장 = PDF 등 내보내기와 같은 _qPersistQuote) → 재접속·이동 때 안 묻는다');
  await T(`(async function(){ await _qPersistQuote(); window.__persisted=true; })(); 'ok'`);
  for(let i=0;i<40 && !(await T(`!!window.__persisted`)); i++) await pg.waitForTimeout(100);
  const qid = await T(`_qLoadedId`);
  ok(await T(`quoteSaved[0] && quoteSaved[0].mgr==='홍길동' && quoteSaved[0].id===_qLoadedId`), '저장 견적 meta.mgr = 담당자');
  ok(await T(`_qDraftIsClean() && !!localStorage.getItem(_qCartKey()+'_sig')`), '저장 서명 기록 → clean');
  ok(await T(`_qLeaveGuard('memo')===false && _qCart.length===1`), '카테고리 이동 가드: 묻지 않고 목록 유지');
  const savedQS = await T(`JSON.stringify(quoteSaved)`); const savedItems = await T(`JSON.stringify(window.__items)`);
  await boot(); await T(`quoteSaved=${JSON.stringify(savedQS)}; quoteSaved=JSON.parse(quoteSaved); window.__items=JSON.parse(${JSON.stringify(savedItems)}); _qBootChecked=false; _qDraftBootCheck(); 'ok'`); await pg.waitForTimeout(300);
  ok(await T(`!(document.getElementById('qLeaveOverlay') && document.getElementById('qLeaveOverlay').style.display==='flex')`), '재접속: 저장된 그대로 → 묻지 않음');
  ok(await T(`_qCart.length===1 && _qLoadedId==='${qid}'`), '견적 목록은 그대로 남아 있음');

  console.log('▶ 3) 내용을 고치면 다시 묻는다 · 불러오기 직후는 clean · 담당자 복원');
  await T(`switchPage('estimate'); qSetSubTab('quote'); _qCart[0].qty=7; _qCartSave(); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`!_qDraftIsClean()`), '수량 변경 → dirty');
  ok(await T(`_qLeaveGuard('memo')===true`), '이동 가드가 다시 묻는다');
  await T(`document.getElementById('qLeaveOverlay').style.display='none'; _qDraftClear(); 'ok'`);
  ok(await T(`_qMgr==='' && !_qCartHasContent()`), '비우기 → 담당자도 비움');
  await T(`switchPage('estimate'); qSetSubTab('quote'); _qCart=[]; qLoadSaved('${qid}'); 'ok'`); await pg.waitForTimeout(600);
  ok(await T(`_qMgr==='홍길동' && _qCart.length===1 && _qDraftIsClean()`), '불러오기 → 담당자 복원 + clean');
  await pg.waitForTimeout(300);
  ok(await T(`document.getElementById('qManager').value==='홍길동'`), '담당자 칸에 표시');
  await T(`var m=document.getElementById('qManager'); m.value='김철수'; m.dispatchEvent(new Event('input')); _qCartSaveFlush(); 'ok'`);
  ok(await T(`!_qDraftIsClean()`), '담당자만 바꿔도 dirty (저장 대상)');

  ok(errs.length===0, '페이지 오류 없음'+(errs.length?(' — '+errs.slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(_e){}
  process.exit(fail?1:0);
})();
