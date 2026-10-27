// r251 테스트 — 견적 메일: 업체별 주소록 칩(넣기/빼기/지우기) · 주소록에 저장 · 처음 값 1개 · 자동 저장 체크
//  사용:  node test_r250.js <r250 적용된 index.html>
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b250/test/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const STUB = `
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r250.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  const sent=[]; const cfgStore={ url:'https://worker.test', key:'k-123', cc:'' };
  await pg.route('**/*', r => { const u=r.request().url();
    if(u.startsWith('file://') || /cdnjs\.cloudflare\.com|cdn\.jsdelivr\.net/.test(u)) return r.continue();
    if(u.indexOf('sched_mail_cfg.json')>=0) return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify(cfgStore)});
    if(u.indexOf('worker.test/send')>=0){ sent.push(JSON.parse(r.request().postData())); return r.fulfill({status:200, contentType:'application/json', headers:{'access-control-allow-origin':'*'}, body:'{"ok":true}'}); }
    r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  await T(`
    _fbDbUrl='https://fb.test'; _authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울',phone:'010-5228-2922'}];
    _fbPutOk=async function(){ return true; }; debouncedFbSave=function(){ window.__fb=(window.__fb||0)+1; }; saveAll=function(){};
    _fbFetch=async function(url,opts){ return fetch(url,opts); }; _nyLoadAssets=async function(){ return {}; }; _qPriceIdx={};
    clientList=[]; clientInfo={ '충해)성기웅|서울':{ email:'office@sk.com', contacts:[{dept:'',rank:'과장',name:'홍길동',phone:'010-0000-0000',phone2:'',email:'hong@sk.com'},{dept:'',rank:'대리',name:'이몽룡',phone:'',phone2:'',email:'lee@sk.com'}] } }; _ciVer++;
    _qQuoteNo='성기웅-20261027-01'; _qLoadedId='qid1'; quoteSaved=[{id:'qid1',title:'성기웅-20261027-01',vname:'충해)성기웅',count:1,total:1,savedBy:'김재성',savedAt:Date.now()}];
    _qPersistQuote=async function(){}; _qMakePdfBlob=async function(){ return new Blob(['%PDF-1.4'],{type:'application/pdf'}); };
    quoteVendors=[{id:'v1',name:'충해)성기웅'}]; _qCurId='v1';
    _qCart=[{vid:'v1',vname:'충해)성기웅',spec:'MGPM20-25Z',name:'실린더',qty:5,sell:89690,info:{maker:'SMC'}}]; _qNego=0; _qCols=[]; _qMgr='이몽룡';
    window.__info=[]; showInfoModal=function(t,m){ window.__info.push(t+'|'+m); }; showPromptModal=function(t,m,d,fn){ fn(window.__promptAns!=null?window.__promptAns:d); }; showConfirmModal=function(t,m,fn){ fn(); }; _mtToast=function(){};
    switchPage('quote'); 'ok'`);

  console.log('▶ 1) 열기: 주소록 칩 + 처음 값은 견적 담당자 1명');
  await T(`qOpenMailSend(); 'ok'`); await pg.waitForTimeout(600);
  ok(await T(`document.querySelectorAll('#mlBook .ml-chip').length===3`), '주소록 칩 3개 (담당자 2 + 대표 메일)');
  ok(await T(`document.getElementById('mlTo').value==='lee@sk.com'`), '받는 사람 처음 값 = 견적 담당자(이몽룡) 메일 1개 — '+(await T(`document.getElementById('mlTo').value`)));
  ok(await T(`document.querySelector('#mlBook .ml-chip.on') && document.querySelector('#mlBook .ml-chip.on').textContent.indexOf('이몽룡')>=0`), '선택된 칩 표시(✓)');
  ok(await T(`document.getElementById('mlBook').innerText.indexOf('대표 메일')>=0 && document.getElementById('mlBook').innerText.indexOf('과장')>=0`), '칩에 이름·직급·구분');

  console.log('▶ 2) 칩으로 넣기/빼기');
  await T(`mlBookToggle(0); 'ok'`);
  ok(await T(`document.getElementById('mlTo').value==='lee@sk.com, hong@sk.com'`), '홍길동 추가');
  await T(`mlBookToggle(1); 'ok'`);
  ok(await T(`document.getElementById('mlTo').value==='hong@sk.com'`), '이몽룡 빼기');

  console.log('▶ 3) 새 주소 → [+ 주소록에 저장] (이름 입력)');
  await T(`document.getElementById('mlTo').value='hong@sk.com, kim@sk.com'; window.__promptAns='김구매'; mlBookSave(); 'ok'`); await pg.waitForTimeout(150);
  ok(await T(`clientInfo['충해)성기웅|서울'].contacts.some(function(c){ return c.name==='김구매' && c.email==='kim@sk.com'; }) && (window.__fb||0)>=1`), '새 연락처(김구매) 저장 + 동기화');
  ok(await T(`document.querySelectorAll('#mlBook .ml-chip').length===4 && document.getElementById('mlTo').value==='hong@sk.com, kim@sk.com'`), '칩 4개 · 받는 사람 유지');
  await T(`mlBookSave(); 'ok'`);
  ok(await T(`clientInfo['충해)성기웅|서울'].contacts.length===3`), '이미 있는 주소는 다시 저장 안 함');

  console.log('▶ 4) 주소록에서 지우기 (연락처 정보 있으면 메일만)');
  await T(`mlBookDel(0); 'ok'`);
  ok(await T(`clientInfo['충해)성기웅|서울'].contacts[0].name==='홍길동' && clientInfo['충해)성기웅|서울'].contacts[0].email==='' && document.getElementById('mlTo').value==='kim@sk.com'`), '홍길동: 연락처는 남기고 메일만 삭제, 받는 사람에서도 빠짐');
  const idxK = await T(`_mailAddrBook('충해)성기웅').findIndex(function(b){ return b.email==='kim@sk.com'; })`);
  await T(`mlBookDel(${idxK}); 'ok'`);
  ok(await T(`!_mailAddrBook('충해)성기웅').some(function(b){ return b.email==='kim@sk.com'; }) && !clientInfo['충해)성기웅|서울'].contacts.some(function(c){ return c.email==='kim@sk.com'; })`), '김구매 메일 주소록에서 삭제');

  console.log('▶ 5) 보내기 — 자동 저장 체크 해제면 저장 안 함');
  await T(`document.getElementById('mlTo').value='new@x.com'; document.getElementById('mlRemember').checked=false; window.__info=[]; qMailSendNow(); 'ok'`);
  for(let i=0;i<80 && !(await T(`(window.__info||[]).some(function(x){ return x.indexOf('메일 발송 완료')>=0 || x.indexOf('실패')>=0; })`)); i++) await pg.waitForTimeout(150);
  ok(sent.length===1 && sent[0].to==='new@x.com', '발송됨');
  ok(await T(`!_mailAddrBook('충해)성기웅').some(function(b){ return b.email==='new@x.com'; })`), '체크 해제 → 주소록에 안 남음');
  await T(`qOpenMailSend(); 'ok'`); await pg.waitForTimeout(500);
  ok(await T(`document.getElementById('mlRemember').checked===true`), '다시 열면 자동 저장 기본 ✓');
  await T(`document.getElementById('mlTo').value='auto@x.com'; window.__info=[]; qMailSendNow(); 'ok'`);
  for(let i=0;i<80 && !(await T(`(window.__info||[]).some(function(x){ return x.indexOf('메일 발송 완료')>=0; })`)); i++) await pg.waitForTimeout(150);
  ok(await T(`_mailAddrBook('충해)성기웅').some(function(b){ return b.email==='auto@x.com'; })`), '체크 상태로 보내면 새 주소 자동 저장 (r245 동작 유지)');

  ok(errs.length===0, '페이지 오류 없음'+(errs.length?(' — '+errs.slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(_e){}
  process.exit(fail?1:0);
})();
