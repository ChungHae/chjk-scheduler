// r235 테스트 — 견적서 메일 보내기 (설정 창 · 초안 자동 채움 · 발송 흐름(가짜 Worker) · 기록 배지)
//  사용:  node test_r235.js <r235 적용된 index.html>
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b235/test/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const STUB = `
  window._xlsxStyleReady=true;
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r235.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  const sent=[]; let cfgStore={};
  await pg.route('**/*', r => { const u=r.request().url();
    if(u.startsWith('file://')) return r.continue();
    if(u.indexOf('sched_mail_cfg.json')>=0){ if(r.request().method()==='PATCH'){ Object.assign(cfgStore, JSON.parse(r.request().postData())); return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify(cfgStore)}); } return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify(cfgStore)}); }
    if(u.indexOf('worker.test/ping')>=0) return r.fulfill({status:200, contentType:'application/json', headers:{'access-control-allow-origin':'*'}, body:JSON.stringify({ok:true,user:'ch***@chjk.co.kr'})});
    if(u.indexOf('worker.test/send')>=0){ const b=JSON.parse(r.request().postData()); b._key=r.request().headers()['x-mail-key']; sent.push(b); if(b.subject.indexOf('FAIL')>=0) return r.fulfill({status:502, contentType:'application/json', headers:{'access-control-allow-origin':'*'}, body:JSON.stringify({ok:false,error:'로그인 (아이디/외부 앱 비밀번호 확인) 실패: 535'})}); return r.fulfill({status:200, contentType:'application/json', headers:{'access-control-allow-origin':'*'}, body:JSON.stringify({ok:true,id:'<x@chjk.co.kr>'})}); }
    r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  await T(`
    _fbDbUrl='https://fb.test'; _authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울',phone:'010-5228-2922'}];
    _fbPutOk=async function(){ return true; }; debouncedFbSave=function(){}; saveAll=function(){ window.__saved=(window.__saved||0)+1; };
    _fbFetch=async function(url,opts){ return fetch(url,opts); };
    _nyLoadAssets=async function(){ return {}; }; _qPriceIdx={};
    clientInfo={ 'HINTER':{ taxEmail:'tax@hinter.co.kr', contacts:[{name:'김 영업',email:'sales@hinter.co.kr'},{name:'조영훈',email:'cho@hinter.co.kr'}] } };
    _ensurePdfMake=async function(){ return { createPdf:function(dd){ return { getBlob:function(cb){ cb(new Blob(['%PDF-1.4 test'],{type:'application/pdf'})); }, download:function(){} }; } }; };
    _qPdfFontLoad=async function(){ return 'NotoSansKR'; }; _qBuildPdfDoc=function(){ return {content:[]}; };
    _qQuoteNo='HINTER-20261014-01'; _qLoadedId='qid1'; quoteSaved=[{id:'qid1',title:'HINTER-20261014-01',vname:'HINTER',count:2,total:100000,savedBy:'김재성',savedAt:Date.now()}];
    _qPersistQuote=async function(){ window.__persisted=(window.__persisted||0)+1; };
    _qCart=[{spec:'MGPM20-25Z',name:'실린더',qty:85,sell:89690,vname:'HINTER',info:{maker:'SMC'}},{spec:'KQ2H06-01AS',name:'피팅',qty:10,sell:990,vname:'HINTER',info:{maker:'SMC'}}]; _qNego=1000; _qCols=[];
    var mg=document.getElementById('qManager'); if(mg){ mg.disabled=false; mg.value='조영훈'; }
    'ok'`);

  console.log('▶ A) 다운로드 메뉴 · 설정 없음');
  await T(`switchPage('quote'); qOpenDownloadMenu(); 'ok'`); await pg.waitForTimeout(300);
  const menu=await T(`document.getElementById('qDlMenuOverlay').innerText`);
  ok(menu.indexOf('메일 보내기')>=0 && menu.indexOf('메일 설정')>=0 && menu.indexOf('HTML 견적서')>=0, '[메일 보내기] + 관리자용 [메일 설정] + 기존 버튼 유지');
  await T(`document.getElementById('qDlMenuOverlay').style.display='none'; window.__info=[]; var _o=showInfoModal; showInfoModal=function(t,m){ window.__info.push(t+'|'+m); }; 'ok'`);
  await T(`qOpenMailSend(); 'ok'`); await pg.waitForTimeout(500);
  ok(await T(`(window.__info[0]||'').indexOf('메일 설정 필요')>=0 && !document.getElementById('mailSendOverlay')`), '설정 전에는 안내만 (발송 창 안 열림)');

  console.log('▶ B) 메일 설정');
  await T(`mailOpenCfg(); 'ok'`); await pg.waitForTimeout(500);
  ok(await T(`getComputedStyle(document.getElementById('mailCfgOverlay')).display==='flex' && !!document.getElementById('mlCfgUrl')`), '설정 창 열림');
  await T(`document.getElementById('mlCfgUrl').value='https://worker.test'; mailCfgPing(); 'ok'`); await pg.waitForTimeout(500);
  ok(await T(`document.getElementById('mlCfgMsg').innerText.indexOf('연결됨')>=0 && document.getElementById('mlCfgMsg').innerText.indexOf('ch***@chjk.co.kr')>=0`), '[연결 확인] → /ping 응답 표시');
  await T(`document.getElementById('mlCfgKey').value='k-123'; document.getElementById('mlCfgCc').value='chjk@chjk.co.kr'; mailCfgSave(); 'ok'`); await pg.waitForTimeout(500);
  ok(cfgStore.url==='https://worker.test' && cfgStore.key==='k-123' && cfgStore.cc==='chjk@chjk.co.kr', 'PATCH sched_mail_cfg 저장 ('+JSON.stringify(cfgStore)+')');
  await T(`document.getElementById('mailCfgOverlay').style.display='none'; 'ok'`);

  console.log('▶ C) 발송 창 초안');
  await T(`qOpenMailSend(); 'ok'`); await pg.waitForTimeout(600);
  const to=await T(`document.getElementById('mlTo').value`), subj=await T(`document.getElementById('mlSubj').value`), body=await T(`document.getElementById('mlBody').value`), cc=await T(`document.getElementById('mlCc').value`);
  ok(to==='cho@hinter.co.kr, sales@hinter.co.kr, tax@hinter.co.kr', '받는 사람: 담당자(조영훈) 메일 맨 앞 + 나머지 담당자 + 계산서 메일 ('+to+')');
  ok(subj==='[충해전기] 견적서 HINTER-20261014-01 — HINTER', '제목');
  ok(body.indexOf('HINTER 조영훈 님, 안녕하세요.')===0 && body.indexOf('충해전기㈜ 김재성입니다')>=0 && body.indexOf('견적번호 HINTER-20261014-01')>=0 && body.indexOf('품목 2건 · 공급가액 7,632,550원')>=0 && body.indexOf('010-5228-2922')>=0 && body.indexOf('airmall24.co.kr')>=0, '본문 기본 문안 (수신·담당·건수·공급가액(NEGO 반영)·서명)');
  ok(cc==='chjk@chjk.co.kr', '기본 참조 채움');
  ok(await T(`document.getElementById('mlAttPdf').checked && document.getElementById('mlAttHtml').checked`), '첨부 PDF·HTML 기본 체크');

  console.log('▶ D) 발송');
  await T(`document.getElementById('mlTo').value='bad-address'; qMailSendNow(); 'ok'`); await pg.waitForTimeout(300);
  ok(await T(`document.getElementById('mlStatus').innerText.indexOf('주소 형식')>=0`) && sent.length===0, '잘못된 주소는 보내기 전에 막음');
  await T(`document.getElementById('mlTo').value='cho@hinter.co.kr'; qMailSendNow(); 'ok'`);
  for(let i=0;i<50 && !(await T(`(window.__info||[]).some(function(x){ return x.indexOf('메일 발송 완료')>=0; })`)); i++) await pg.waitForTimeout(100);
  ok(sent.length===1 && sent[0]._key==='k-123' && sent[0].to==='cho@hinter.co.kr' && sent[0].cc==='chjk@chjk.co.kr' && /^\[충해전기\] 견적서/.test(sent[0].subject), 'Worker /send 호출 (열쇠·받는이·참조·제목)');
  ok(sent.length===1 && sent[0].attachments.length===2 && sent[0].attachments[0].name==='견적서 HINTER-20261014-01.pdf' && sent[0].attachments[0].type==='application/pdf' && Buffer.from(sent[0].attachments[0].b64,'base64').toString().indexOf('%PDF')===0, 'PDF 첨부 (이름·형식·내용)');
  ok(sent.length===1 && sent[0].attachments[1].name==='견적서 HINTER-20261014-01.html' && Buffer.from(sent[0].attachments[1].b64,'base64').toString('utf8').indexOf('<!DOCTYPE html>')===0, 'HTML 첨부 (r233 견적서)');
  ok(sent.length===1 && sent[0].fromName==='충해전기㈜ 김재성' && sent[0].html.indexOf('안녕하세요')>=0 && sent[0].text.indexOf('안녕하세요')>=0, '보낸이 이름 · 본문 text/html');
  ok(await T(`window.__persisted===1`), '보내기 전 견적 자동 저장');
  ok(await T(`quoteSaved[0].mail && quoteSaved[0].mail.length===1 && quoteSaved[0].mail[0].to==='cho@hinter.co.kr' && quoteSaved[0].mail[0].by==='김재성' && quoteSaved[0].mail[0].files.length===2 && window.__saved>=1`), '저장 견적에 발송 기록');
  ok(await T(`getComputedStyle(document.getElementById('mailSendOverlay')).display==='none' && (window.__info||[]).some(function(x){ return x.indexOf('메일 발송 완료')>=0 && x.indexOf('cho@hinter.co.kr')>=0; })`), '완료 안내 + 창 닫힘');

  console.log('▶ E) 발송 실패 처리');
  await T(`qOpenMailSend(); 'ok'`); await pg.waitForTimeout(500);
  await T(`document.getElementById('mlTo').value='cho@hinter.co.kr'; document.getElementById('mlSubj').value='FAIL test'; document.getElementById('mlAttPdf').checked=false; document.getElementById('mlAttHtml').checked=false; qMailSendNow(); 'ok'`);
  for(let i=0;i<50 && !(await T(`document.getElementById('mlStatus').innerText.indexOf('발송 실패')>=0`)); i++) await pg.waitForTimeout(100);
  ok(await T(`document.getElementById('mlStatus').innerText.indexOf('외부 앱 비밀번호')>=0 && !document.getElementById('mlSendBtn').disabled && document.getElementById('mlSendBtn').textContent==='보내기'`), 'Worker 오류 메시지 표시 · 버튼 복구');
  ok(sent.length===2 && sent[1].attachments.length===0 && (await T(`quoteSaved[0].mail.length===1`)), '첨부 해제 반영 · 실패는 기록 안 함');

  console.log('▶ F) 불러오기 목록 배지');
  await T(`document.getElementById('mailSendOverlay').style.display='none'; qOpenLoad(); 'ok'`); await pg.waitForTimeout(600);
  ok(await T(`document.body.innerText.indexOf('✉ 1회')>=0`), '불러오기 목록에 ✉ 1회');

  ok(errs.length===0, '페이지 오류 없음'+(errs.length?(' — '+errs.slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(_e){}
  process.exit(fail?1:0);
})();
