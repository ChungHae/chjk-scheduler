const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b217/testpage/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', '  window.__T=function(c){return eval(c);};\n  function _vacUnlimited(id){');
  const tmp = path.join(path.dirname(file), '_h_r217.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  await pg.route('**/*', r => { const u=r.request().url(); if(u.startsWith('file://')) r.continue(); else r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  const show = (id) => pg.evaluate((id)=>{ document.querySelectorAll('.page-section').forEach(p=>{ if(p.id===id) p.style.display='block'; }); }, id);
  const confirmText = () => T(`(function(){ var o=document.getElementById('confirmOverlay'); return o && o.style.display!=='none' ? o.innerText : ''; })()`);

  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; quoteVendors=[{id:'qv1',name:'주식회사 케이에스',count:1}]; _qCurId=null; _qCart=[]; clientPend=[]; switchPage('quote'); 'ok'`);
  await pg.waitForTimeout(300); await show('pageEstimate');

  console.log('▶ 없는 거래처 이름 + Enter → 확인창 → 임시 등록 → 견적 작성 가능');
  const inp = pg.locator('#qVendorSearch');
  await inp.fill('새싹테크'); await T(`renderQVendorDropdown(); 'ok'`);
  ok(await T(`document.getElementById('qVendorDropdown').innerText.indexOf('임시 등록하고 바로 작성')>=0`), '드롭다운에 "임시 등록하고 바로 작성" 줄');
  await inp.press('Enter'); await pg.waitForTimeout(200);
  const ct = await confirmText();
  ok(ct.indexOf('등록되지 않은 거래처')>=0 && ct.indexOf('새싹테크')>=0, '확인창: 등록되지 않은 거래처');
  await pg.evaluate(()=>{ const b=[...document.querySelectorAll('#confirmOverlay button')].find(x=>/임시 등록/.test(x.textContent)); b.click(); });
  await pg.waitForTimeout(400);
  ok(await T(`!!quoteVendors.find(function(v){ return v.name==='새싹테크'; })`), 'quoteVendors 에 등록');
  ok(await T(`_qCurId===quoteVendors.find(function(v){ return v.name==='새싹테크'; }).id`), '그 거래처가 선택됨 (견적 작성 가능)');
  ok(await T(`allClients().some(function(c){ return c[0]==='새싹테크' && !c[1]; })`), '업체 목록에 이름만으로 등록 (사업자번호 없음)');
  ok(await T(`clientPend.length===1 && clientPend[0].name==='새싹테크' && clientPend[0].status==='wait' && clientPend[0].by==='김재성'`), '등록 대기열에 1건');
  ok(await T(`document.getElementById('mtToast') && document.getElementById('mtToast').textContent.indexOf('임시 등록')>=0`), '안내 토스트');

  console.log('▶ 같은 이름을 또 임시 등록해도 중복 없음');
  await T(`qQuickVendor('새싹테크'); 'ok'`); await pg.waitForTimeout(100);
  ok(await T(`clientPend.length===1 && allClients().filter(function(c){ return c[0]==='새싹테크'; }).length===1 && quoteVendors.filter(function(v){ return v.name==='새싹테크'; }).length===1`), '대기열·업체·원장 모두 1건 유지');

  console.log('▶ 기존 거래처 Enter 는 그대로 선택 (확인창 없음)');
  await T(`_qCart=[]; 'ok'`);
  await inp.fill('주식회사 케이에스'); await inp.press('Enter'); await pg.waitForTimeout(200);
  ok((await confirmText())==='' && await T(`_qCurId==='qv1'`), '정확히 같은 이름 → 바로 선택');

  console.log('▶ 메모장·업체 관리 배너 + 대기 창');
  ok(await T(`_pendBanner().indexOf('업체 정보 등록 대기 1건')>=0`), '배너 문구 (1건)');
  await T(`switchPage('memo'); 'ok'`); await pg.waitForTimeout(300);
  ok(await T(`!!document.querySelector('#pageMemo .mm-smc.pend')`), '메모장에 파란 배너');
  await T(`switchPage('clients'); 'ok'`); await pg.waitForTimeout(300);
  ok(await T(`document.getElementById('clxPendBar').innerText.indexOf('등록 대기 1건')>=0`), '업체 관리 상단 배너');
  await T(`pendOpen(); 'ok'`); await pg.waitForTimeout(100);
  ok(await T(`document.getElementById('pendOverlay').style.display==='flex' && document.getElementById('pendOverlay').innerText.indexOf('새싹테크')>=0`), '대기 창에 새싹테크');

  console.log('▶ [정보 등록] → 업체 관리에서 그 업체가 펼쳐짐');
  await T(`pendGo(clientPend[0].id); 'ok'`); await pg.waitForTimeout(300); await show('pageClients');
  ok(await T(`document.getElementById('pendOverlay').style.display==='none'`), '대기 창 닫힘');
  ok(await T(`_clxExp==='새싹테크|서울' && !!document.querySelector('#clxForm')`), '업체 관리에서 새싹테크 폼 펼침');
  ok(await T(`document.getElementById('clxSearch').value==='새싹테크'`), '검색칸에 이름');

  console.log('▶ 사업자번호 저장하면 자동으로 "등록됨"');
  await T(`(function(){ var i=clientList.findIndex(function(c){ return c[0]==='새싹테크'; }); clientList[i]=_cliMake('새싹테크','123-45-67890'); _saveClients(); })(); 'ok'`);
  ok(await T(`_pendWaitCount()===0 && clientPend[0].status==='ok' && clientPend[0].okBy==='자동'`), '대기 0건 · 상태 ok(자동)');
  ok(await T(`_pendBanner()===''`), '배너 사라짐');

  console.log('▶ 제외 / 대기로');
  await T(`clientPend.push({id:'cpX',name:'다른업체',by:'김재성',at:Date.now(),quoteNo:'',status:'wait'}); pendSkip('cpX'); 'ok'`); await pg.waitForTimeout(100);
  ok(await T(`clientPend.find(function(p){return p.id==='cpX';}).status==='skip'`), '제외');
  await T(`pendRestore('cpX'); 'ok'`); await pg.waitForTimeout(100);
  ok(await T(`clientPend.find(function(p){return p.id==='cpX';}).status==='wait'`), '대기로 복귀');
  await T(`_pendClose(); 'ok'`);

  console.log('▶ 저장 키');
  ok(await T(`JSON.parse(localStorage.getItem('sched_client_pend')||'[]').length===2`), 'localStorage sched_client_pend 저장');
  ok(errs.length===0, 'pageerror 0'+(errs.length?(' — '+errs.join(' | ')):''));
  console.log(`\n결과: ${pass}/${pass+fail}`);
  fs.unlinkSync(tmp); await br.close(); process.exit(fail?1:0);
})();
