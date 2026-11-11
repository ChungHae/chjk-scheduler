// r265 테스트 — 매입처 문의 메일 간단 디자인
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs=require('fs'), path=require('path');
const file=path.resolve(process.argv[2]||'d265/test/index.html');
let pass=0, fail=0; function ok(c,m){ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} }
(async()=>{
  const src=fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){','window.__T=function(c){return eval(c);}; function _vacUnlimited(id){');
  const tmp=path.join(path.dirname(file),'_h_r265.html'); fs.writeFileSync(tmp,src);
  const br=await chromium.launch(); const pg=await br.newPage({viewport:{width:1400,height:900}}); const errs=[]; pg.on('pageerror',e=>errs.push(String(e)));
  const sent=[];
  await pg.route('**/*', async r=>{ const u=r.request().url(); if(u.startsWith('file://')) return r.continue(); if(u.startsWith('https://w.test/send')){ sent.push(JSON.parse(r.request().postData())); return r.fulfill({status:200,contentType:'application/json',body:'{"ok":true}'}); } return r.abort(); });
  await pg.goto('file://'+tmp); await pg.waitForTimeout(2500);
  await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  const T=c=>pg.evaluate(c2=>window.__T(c2),c);
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울',phone:'010-5228-2922',email:'kjs@chjk.co.kr'}]; saveAll=function(){}; showInfoModal=function(){};
    _mailLoadCfg=async function(){ return {url:'https://w.test',key:'k'}; };
    purchaseVendors=[{id:'v1',brand:'SMC',distributor:'대성산업(주) 에이앤에이사업부',contacts:[{role:'과장',name:'홍길동',email:'hong@ds.test'},{name:'김영희',email:'kim@ds.test'}]},{id:'v2',brand:'SMC',distributor:'다른대리점',contacts:[]}]; pvInq=[];
    document.querySelectorAll('.page-section').forEach(function(p){p.classList.remove('active')}); document.getElementById('pagePurchase').classList.add('active'); renderPurchasePage(); 'ok'`);
  await pg.evaluate(()=>{ [...document.querySelectorAll('#purchaseList .pv-card')].find(c=>/대성산업/.test(c.innerText)).click(); });
  await pg.waitForTimeout(300);
  ok(await pg.evaluate(()=>document.getElementById('pvInqOverlay').style.display==='flex'), '매입처 카드 클릭 → 문의 메일 창');
  const fields=await pg.evaluate(()=>[...document.querySelectorAll('#pvInqOverlay input:not([type=hidden]), #pvInqOverlay textarea, #pvInqOverlay select')].map(e=>e.id).join(','));
  ok(fields==='pvqTo,pvqCc,pvqSubj,pvqBody,pvqMy', '입력칸은 받는 사람·참조·제목·본문·답장 메일 뿐 (품번 표·브랜드·문의종류 없음): '+fields);
  ok(await pg.evaluate(()=>document.getElementById('pvqTo').value)==='hong@ds.test' && await pg.evaluate(()=>document.querySelectorAll('#pvInqOverlay .ml-chip').length)===2, '받는 사람 = 첫 담당자 · 담당자 칩 2');
  ok(await pg.evaluate(()=>document.getElementById('pvqCc').value)==='kjs@chjk.co.kr' && await pg.evaluate(()=>document.getElementById('pvqMy').value)==='kjs@chjk.co.kr', '참조·답장 = 내 메일');
  const body=await pg.evaluate(()=>document.getElementById('pvqBody').value);
  ok(body.indexOf('대성산업(주) 에이앤에이사업부 홍길동 님, 안녕하세요.')===0 && /아래 품목 견적 및 납기 문의드립니다\./.test(body) && /김재성 · 010-5228-2922/.test(body), '본문 기본 문구(인사·서명), 품번은 직접');
  ok(await pg.evaluate(()=>{ const t=document.getElementById('pvqBody'); return document.activeElement===t && t.value.slice(0,t.selectionStart).endsWith('문의드립니다.\n\n'); }), '커서가 품번 적을 자리에');
  await T(`pvq2Chip(1); 'ok'`);
  ok(await pg.evaluate(()=>document.getElementById('pvqTo').value)==='hong@ds.test, kim@ds.test', '칩으로 받는 사람 추가');
  await pg.evaluate(()=>{ const t=document.getElementById('pvqBody'); t.value=t.value.replace('문의드립니다.\n\n','문의드립니다.\n\nSY5120-5LZD-01 10개\nCDQ2B32-20DZ 5개, 납기 확인 부탁드립니다\n'); t.dispatchEvent(new Event('input')); });
  await T(`pvInqSend()`); await pg.waitForTimeout(400);
  const m=sent[0]||{};
  ok(sent.length===1 && m.to==='hong@ds.test, kim@ds.test' && m.cc==='kjs@chjk.co.kr' && m.replyTo==='kjs@chjk.co.kr' && /SY5120-5LZD-01 10개/.test(m.text) && m.subject==='[충해전기] 견적 문의드립니다', '발송: '+JSON.stringify([m.to,m.cc,m.replyTo,m.subject]));
  ok(await T(`pvInq.length===1 && pvInq[0].vendors[0]==='대성산업(주) 에이앤에이사업부' && /SY5120/.test(pvInq[0].body)`), '문의함 기록');
  // 담당자 없는 대리점 → 직접 입력한 주소 기억
  await T(`pvInqOpen({vendorId:'v2'}); 'ok'`); await pg.waitForTimeout(100);
  ok(/저장된 담당자 메일이 없습니다/.test(await pg.evaluate(()=>document.getElementById('pvInqOverlay').innerText)), '담당자 없으면 안내');
  await pg.evaluate(()=>{ const i=document.getElementById('pvqTo'); i.value='new@other.test'; i.dispatchEvent(new Event('change')); });
  await T(`pvInqSend()`); await pg.waitForTimeout(300);
  ok(await T(`purchaseVendors[1].contacts.some(function(c){ return c.email==='new@other.test'; })`), '보낸 주소를 그 대리점 담당자로 기억');
  const re=errs.filter(e=>!/net::|Failed to fetch|firebase|XLSX|cdnjs/.test(e)); ok(re.length===0,'페이지 오류 없음'+(re.length?' — '+re[0]:''));
  console.log(`\n결과: ${pass} 통과 / ${fail} 실패`); await br.close(); try{fs.unlinkSync(tmp);}catch(e){} process.exit(fail?1:0);
})();
