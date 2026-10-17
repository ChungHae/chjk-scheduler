// r238 테스트 — 견적서 메일 보내기 (설정 창 · 초안 자동 채움 · 발송 흐름(가짜 Worker) · 기록 배지)
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
  const tmp = path.join(path.dirname(file), '_h_r238.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  const sent=[]; let cfgStore={};
  await pg.route('**/*', r => { const u=r.request().url();
    if(u.startsWith('file://')) return r.continue();
    if(u.indexOf('sched_mail_cfg.json')>=0){ if(r.request().method()==='PATCH'){ Object.assign(cfgStore, JSON.parse(r.request().postData())); return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify(cfgStore)}); } return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify(cfgStore)}); }
    if(u.indexOf('worker.test/ping')>=0) return r.fulfill({status:200, contentType:'application/json', headers:{'access-control-allow-origin':'*'}, body:JSON.stringify({ok:true,user:'ch***@chjk.co.kr',accounts:{seoul:'ch***@chjk.co.kr',hs:(global.__hsOn?'hs***@chjk.co.kr':null)}})});
    if(u.indexOf('worker.test/send')>=0){ const b=JSON.parse(r.request().postData()); b._key=r.request().headers()['x-mail-key']; sent.push(b); if(b.subject.indexOf('FAIL')>=0) return r.fulfill({status:502, contentType:'application/json', headers:{'access-control-allow-origin':'*'}, body:JSON.stringify({ok:false,error:'로그인 (아이디/외부 앱 비밀번호 확인) 실패: 535'})}); return r.fulfill({status:200, contentType:'application/json', headers:{'access-control-allow-origin':'*'}, body:JSON.stringify({ok:true,id:'<x@chjk.co.kr>'})}); }
    r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  await T(`
    _fbDbUrl='https://fb.test'; _authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울',phone:'010-5228-2922'},{id:'m2',name:'함현식',group:'화성',phone:'010-0000-0000'}];
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


  console.log('▶ A) 설정 창 연결 확인 — 두 계정 표시');
  await T(`window.__info=[]; showInfoModal=function(t,m){ window.__info.push(t+'|'+m); }; mailOpenCfg(); 'ok'`); await pg.waitForTimeout(500);
  await T(`document.getElementById('mlCfgUrl').value='https://worker.test'; mailCfgPing(); 'ok'`); await pg.waitForTimeout(500);
  let msg=await T(`document.getElementById('mlCfgMsg').innerText`);
  ok(msg.indexOf('연결됨')>=0 && msg.indexOf('서울 ch***@chjk.co.kr')>=0 && msg.indexOf('화성')>=0 && msg.indexOf('미설정')>=0 && msg.indexOf('SMTP_USER_HS')>=0, '화성 계정 미설정이면 안내 ('+msg+')');
  global.__hsOn=true; await T(`mailCfgPing(); 'ok'`); await pg.waitForTimeout(500); msg=await T(`document.getElementById('mlCfgMsg').innerText`);
  ok(msg.indexOf('화성 hs***@chjk.co.kr')>=0, '화성 계정 설정되면 표시 ('+msg+')');
  ok(await T(`document.getElementById('mailCfgOverlay').innerText.indexOf('hs-chjk@chjk.co.kr')>=0`), '설정 안내문에 두 계정');
  await T(`document.getElementById('mlCfgKey').value='k-123'; document.getElementById('mlCfgCc').value='chjk@chjk.co.kr'; mailCfgSave(); 'ok'`); await pg.waitForTimeout(500);
  await T(`document.getElementById('mailCfgOverlay').style.display='none'; 'ok'`);

  console.log('▶ B) 서울 직원(김재성) — 기본 서울 계정');
  await T(`switchPage('quote'); qOpenMailSend(); 'ok'`); await pg.waitForTimeout(600);
  ok(await T(`!!document.getElementById('mlAcct') && document.getElementById('mlAcct').value==='seoul'`), '보내는 계정 선택칸 기본 = 서울');
  ok(await T(`document.getElementById('mlAcct').innerText.indexOf('hs-chjk@chjk.co.kr')>=0 && document.getElementById('mlAcct').innerText.indexOf('chjk@chjk.co.kr')>=0`), '선택지: 서울 chjk@ / 화성 hs-chjk@');
  ok(await T(`document.getElementById('mlFromName').innerText==='충해전기㈜ 김재성' && document.getElementById('mlBody').value.indexOf('chjk@chjk.co.kr')>=0 && document.getElementById('mlBody').value.indexOf('02-2671-4474')>=0`), '서울 서명(법인명·전화·메일)');
  await T(`document.getElementById('mlTo').value='cho@hinter.co.kr'; qMailSendNow(); 'ok'`);
  for(let i=0;i<50 && !(await T(`(window.__info||[]).some(function(x){ return x.indexOf('메일 발송 완료')>=0; })`)); i++) await pg.waitForTimeout(100);
  ok(sent.length===1 && sent[0].account==='seoul' && sent[0].fromName==='충해전기㈜ 김재성', '요청에 account=seoul ('+JSON.stringify({account:sent[0]&&sent[0].account, fromName:sent[0]&&sent[0].fromName})+')');

  console.log('▶ C) 화성 직원(함현식) — 기본 화성 계정 + 화성 서명');
  await T(`_authUser={id:'hhs',name:'함현식',role:'user'}; window.__info=[]; qOpenMailSend(); 'ok'`); await pg.waitForTimeout(600);
  ok(await T(`document.getElementById('mlAcct').value==='hs'`), '소속이 화성이면 기본 = 화성');
  const hb=await T(`document.getElementById('mlBody').value`);
  ok(hb.indexOf('충해전기㈜ 화성영업소 함현식입니다')>=0 && hb.indexOf('hs-chjk@chjk.co.kr')>=0 && hb.indexOf('031-352-4475')>=0 && !/[^-]chjk@chjk\.co\.kr/.test(hb), '화성 서명(화성영업소·031·hs-chjk@)');
  ok(await T(`document.getElementById('mlFromName').innerText==='충해전기㈜ 화성영업소 함현식'`), '보낸이 이름 = 화성영업소');
  await T(`document.getElementById('mlTo').value='cho@hinter.co.kr'; qMailSendNow(); 'ok'`);
  for(let i=0;i<50 && !(await T(`(window.__info||[]).some(function(x){ return x.indexOf('메일 발송 완료')>=0; })`)); i++) await pg.waitForTimeout(100);
  ok(sent.length===2 && sent[1].account==='hs' && sent[1].fromName==='충해전기㈜ 화성영업소 함현식', '요청에 account=hs');

  console.log('▶ D) 보내기 창에서 계정을 바꾸면 서명도 바뀜 (본문을 손대지 않았을 때만)');
  await T(`window.__info=[]; qOpenMailSend(); 'ok'`); await pg.waitForTimeout(600);
  await T(`document.getElementById('mlAcct').value='seoul'; mlAcctChanged(); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`document.getElementById('mlBody').value.indexOf('충해전기㈜ 함현식입니다')>=0 && document.getElementById('mlBody').value.indexOf('02-2671-4474')>=0 && document.getElementById('mlFromName').innerText==='충해전기㈜ 함현식'`), '화성→서울로 바꾸면 서울 서명·보낸이로');
  await T(`document.getElementById('mlBody').value='직접 쓴 본문'; document.getElementById('mlAcct').value='hs'; mlAcctChanged(); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`document.getElementById('mlBody').value==='직접 쓴 본문' && document.getElementById('mlFromName').innerText==='충해전기㈜ 화성영업소 함현식'`), '본문을 고쳤으면 본문은 두고 보낸이만 바뀜');
  await T(`document.getElementById('mlTo').value='cho@hinter.co.kr'; qMailSendNow(); 'ok'`);
  for(let i=0;i<50 && !(await T(`(window.__info||[]).some(function(x){ return x.indexOf('메일 발송 완료')>=0; })`)); i++) await pg.waitForTimeout(100);
  ok(sent.length===3 && sent[2].account==='hs' && sent[2].text==='직접 쓴 본문' && sent[2].fromName==='충해전기㈜ 화성영업소 함현식', '바꾼 계정으로 발송');

  ok(errs.length===0, '페이지 오류 없음'+(errs.length?(' — '+errs.slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(_e){}
  process.exit(fail?1:0);
})();
