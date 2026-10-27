// r245 테스트 — ① 메일 받는 사람 주소를 업체 상세에 저장(다음부터 자동 채움) + 자동 채움 키 수정 ② 견적서 엑셀 첨부
//  사용:  node test_r245.js <r245 적용된 index.html>   (cdnjs·jsdelivr 네트워크 필요)
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b245/test/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const STUB = `
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r245.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  const sent=[]; let cfgStore={ url:'https://worker.test', key:'k-123', cc:'' };
  await pg.route('**/*', r => { const u=r.request().url();
    if(u.startsWith('file://') || /cdnjs\.cloudflare\.com|cdn\.jsdelivr\.net/.test(u)) return r.continue();
    if(u.indexOf('sched_mail_cfg.json')>=0) return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify(cfgStore)});
    if(u.indexOf('worker.test/send')>=0){ const b=JSON.parse(r.request().postData()); sent.push(b); return r.fulfill({status:200, contentType:'application/json', headers:{'access-control-allow-origin':'*'}, body:JSON.stringify({ok:true,id:'<x@chjk.co.kr>'})}); }
    r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  await T(`
    _fbDbUrl='https://fb.test'; _authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울',phone:'010-5228-2922'}];
    _fbPutOk=async function(){ return true; }; debouncedFbSave=function(){ window.__fb=(window.__fb||0)+1; }; saveAll=function(){};
    _fbFetch=async function(url,opts){ return fetch(url,opts); }; _nyLoadAssets=async function(){ return {}; }; _qPriceIdx={};
    clientList=[]; clientInfo={ '충해)성기웅|서울':{ email:'', contacts:[{dept:'',rank:'',name:'홍길동',phone:'010-0000-0000',phone2:'',email:'hong@x.com'}] } }; _ciVer++;
    _qQuoteNo='성기웅-20261020-01'; _qLoadedId='qid1'; quoteSaved=[{id:'qid1',title:'성기웅-20261020-01',vname:'충해)성기웅',count:1,total:448450,savedBy:'김재성',savedAt:Date.now()}];
    _qPersistQuote=async function(){};
    quoteVendors=[{id:'v1',name:'충해)성기웅'}]; _qCurId='v1';
    _qCart=[{vid:'v1',vname:'충해)성기웅',spec:'MGPM20-25Z',name:'실린더',qty:5,sell:89690,info:{maker:'SMC'}}]; _qNego=0; _qCols=[];
    _qMgr='홍길동'; window._qPdfOrient='p';
    window.__info=[]; showInfoModal=function(t,m){ window.__info.push(t+'|'+m); };
    switchPage('quote'); 'ok'`);

  console.log('▶ 1) 받는 사람 자동 채움 — 업체명|지점 키의 담당자 메일');
  await T(`qOpenMailSend(); 'ok'`); await pg.waitForTimeout(700);
  ok(await T(`document.getElementById('mlTo').value==='hong@x.com'`), '담당자 홍길동 메일 자동 채움 (키 수정) — '+(await T(`document.getElementById('mlTo').value`)));
  ok(await T(`!!document.getElementById('mlAttXlsx') && !document.getElementById('mlAttXlsx').checked`), '첨부에 [견적서 엑셀] 체크박스 (기본 해제)');

  console.log('▶ 2) 새 주소 추가 + 엑셀 첨부 체크 → 발송');
  await T(`document.getElementById('mlTo').value='hong@x.com, new@y.com'; document.getElementById('mlAttXlsx').checked=true; window.__info=[]; qMailSendNow(); 'ok'`);
  for(let i=0;i<200 && !(await T(`(window.__info||[]).some(function(x){ return x.indexOf('메일 발송 완료')>=0 || x.indexOf('실패')>=0; })`)); i++) await pg.waitForTimeout(150);
  console.log('   info:', JSON.stringify(await T(`window.__info`)).slice(0,200));
  ok(sent.length===1 && sent[0].attachments.length===2 && /\.pdf$/.test(sent[0].attachments[0].name) && /\.xlsx$/.test(sent[0].attachments[1].name), '첨부 = PDF + 엑셀 ('+(sent[0]&&sent[0].attachments.map(a=>a.name).join(', '))+')');
  const x = sent[0] && sent[0].attachments[1];
  ok(x && x.type.indexOf('spreadsheetml')>=0 && Buffer.from(x.b64,'base64').slice(0,2).toString()==='PK' && Buffer.from(x.b64,'base64').length>3000, '엑셀 첨부가 실제 xlsx(zip) 바이트 ('+(x?Buffer.from(x.b64,'base64').length:0)+' bytes)');
  fs.writeFileSync('/tmp/r245_mail.xlsx', Buffer.from(x.b64,'base64'));
  ok(await T(`clientInfo['충해)성기웅|서울'].email==='new@y.com'`), '새 주소 → 업체 상세 대표 메일로 저장 (담당자는 이미 메일 있음)');
  ok(await T(`(window.__info||[]).some(function(s){ return s.indexOf('주소 1건을 업체 상세에 저장')>=0; })`), '완료 안내에 저장 건수');
  ok(await T(`(window.__fb||0)>=1`), '팀 동기화 저장 호출');
  await T(`qOpenMailSend(); 'ok'`); await pg.waitForTimeout(500);
  ok(await T(`document.getElementById('mlTo').value==='hong@x.com' && (!document.getElementById('mlBook') || document.getElementById('mlBook').innerText.indexOf('new@y.com')>=0)`) || await T(`document.getElementById('mlTo').value==='hong@x.com, new@y.com'`), '다시 열면 저장된 주소 사용 (r250 부터: 담당자 1명 + 나머지는 주소록 칩)');

  console.log('▶ 3) 담당자 메일이 비어 있으면 담당자 연락처에 · 담당자 없고 업체도 없으면 새로 등록');
  await T(`clientInfo['충해)성기웅|서울'].contacts[0].email=''; clientInfo['충해)성기웅|서울'].email=''; 'ok'`);
  ok(await T(`_mailRemember('충해)성기웅','홍길동','h2@x.com')===1 && clientInfo['충해)성기웅|서울'].contacts[0].email==='h2@x.com'`), '담당자 연락처 메일 채움');
  ok(await T(`_mailRemember('충해)성기웅','김철수','kim@x.com')===1 && clientInfo['충해)성기웅|서울'].contacts.some(function(c){ return c.name==='김철수' && c.email==='kim@x.com'; })`), '없는 담당자 → 연락처 새로 추가');
  ok(await T(`_mailRemember('새업체','', 'a@b.com')===1 && clientInfo['새업체|서울'].email==='a@b.com' && clientList.some(function(c){ return c[0]==='새업체'; })`), '업체 상세 없는 업체 → 새로 만들고 대표 메일 저장');
  ok(await T(`_mailRemember('새업체','', 'a@b.com')===0 && _mailRemember('새업체','', 'bad-address')===0`), '이미 있는 주소·잘못된 주소는 무시');

  ok(errs.length===0, '페이지 오류 없음'+(errs.length?(' — '+errs.slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(_e){}
  process.exit(fail?1:0);
})();
