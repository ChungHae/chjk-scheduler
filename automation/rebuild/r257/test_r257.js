// r257 테스트 — 업체 ✉ · 매입처 메일 링크 → 빠른 메일 창 · 전산 발송(replyTo/cc) · 웍스 링크 · 주소 기억
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'd256/test/index.html');
let pass=0, fail=0; function ok(c,m){ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} }
(async()=>{
  const src=fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){','window._xlsxStyleReady=true; window.__T=function(c){return eval(c);}; function _vacUnlimited(id){');
  const tmp=path.join(path.dirname(file),'_h_r257.html'); fs.writeFileSync(tmp,src);
  const br=await chromium.launch(); const pg=await br.newPage({viewport:{width:1400,height:900}}); const errs=[]; pg.on('pageerror',e=>errs.push(String(e)));
  const sent=[];
  await pg.route('**/*', async r=>{ const u=r.request().url(); if(u.startsWith('file://')) return r.continue();
    if(u.startsWith('https://w.test/send')){ sent.push(JSON.parse(r.request().postData())); return r.fulfill({status:200,contentType:'application/json',body:'{"ok":true}'}); }
    return r.abort(); });
  await pg.goto('file://'+tmp); await pg.waitForTimeout(3000);
  await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  const T=c=>pg.evaluate(c2=>window.__T(c2),c);
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울',phone:'010-0000-0000',email:'kjs@chjk.co.kr'}]; debouncedFbSave=function(){}; saveAll=function(){}; window.__info=[]; showInfoModal=function(t,m){ window.__info.push(t+'|'+m); };
    _mailLoadCfg=async function(){ return {url:'https://w.test', key:'k1'}; };
    clientList=[['㈜테스트','123-45-67890'],['㈜빈업체','111-11-11111']]; clientInfo={}; clientInfo[_clxInfoKey('㈜테스트')]={contacts:[{name:'홍길동',rank:'과장',email:'hong@test.co.kr'},{name:'김영희',email:'kim@test.co.kr'}],taxEmail:'tax@test.co.kr'};
    purchaseVendors=[{id:'v1',brand:'CKD',distributor:'이나코퍼레이션',contacts:[{role:'과장',name:'김동형',phone:'',email:'kim@ina.test'}]}];
    window.__opened=[]; window.open=function(u){ window.__opened.push(u); return {}; }; 'ok'`);

  console.log('▶ 1) 업체 목록 ✉');
  await T(`_clxExp=null; _clxRender(); 'ok'`); await pg.waitForTimeout(300);
  const btns=await pg.evaluate(()=>[...document.querySelectorAll('#clxBox tr[data-nm] .clx-mail-btn, tr[data-nm] .clx-mail-btn')].map(b=>b.closest('tr').dataset.nm+':'+(b.style.color||'on')));
  ok(btns.length===2, '업체 2줄에 ✉ (' + btns.join(', ') + ')');
  ok(btns.some(b=>b.startsWith('㈜테스트:on')) && btns.some(b=>b.startsWith('㈜빈업체:') && /rgb\(209, 213, 219\)|d1d5db/.test(b)), '주소 있는 업체는 진하게, 없는 업체는 흐리게');
  await pg.evaluate(()=>{ const b=[...document.querySelectorAll('tr[data-nm="㈜테스트"] .clx-mail-btn')][0]; b.click(); }); await pg.waitForTimeout(200);
  ok(await pg.evaluate(()=>document.getElementById('mailQuickOverlay').style.display==='flex'), '빠른 메일 창 열림');
  ok(await pg.evaluate(()=>!document.querySelector('tr[data-nm="㈜테스트"] + tr td[colspan]')), '줄은 펼쳐지지 않음(클릭 전파 차단)');
  ok(await pg.evaluate(()=>document.querySelectorAll('#mailQuickOverlay .ml-chip').length)===3, '담당자 칩 3개(담당자 2 + 계산서)');
  ok(await T(`window._mq.to.length`)===0, '주소가 여럿이면 받는 사람은 비워 둠');
  ok(await pg.evaluate(()=>document.getElementById('mqMy').value)==='kjs@chjk.co.kr' && await pg.evaluate(()=>document.getElementById('mqCc').value)==='kjs@chjk.co.kr', '내 메일(팀원 정보) → Reply-To·참조 자동');
  await T(`mqChip(0); 'ok'`);
  ok(await pg.evaluate(()=>document.getElementById('mqTo').value)==='hong@test.co.kr', '칩 눌러 받는 사람');
  const body=await pg.evaluate(()=>document.getElementById('mqBody').value);
  ok(body.indexOf('㈜테스트 홍길동 님, 안녕하세요.')===0 && body.indexOf('김재성 · 010-0000-0000 · kjs@chjk.co.kr')>0, '본문 인사(담당자 이름)·서명');

  console.log('▶ 2) 웍스에서 쓰기');
  await pg.evaluate(()=>{ document.getElementById('mqSubj').value='[충해전기] 견적 문의 회신'; document.getElementById('mqSubj').dispatchEvent(new Event('input')); });
  await T(`mqOpenWorks(); 'ok'`);
  const u=await T(`window.__opened[0]||''`);
  ok(u.indexOf('https://mail.worksmobile.com/w/write?to=hong%40test.co.kr&subject=')===0 && decodeURIComponent(u.split('subject=')[1])==='[충해전기] 견적 문의 회신', '웍스 작성 URL(받는 사람·제목): '+u);

  console.log('▶ 3) 전산 발송');
  await pg.evaluate(()=>{ document.getElementById('mqTo').value='hong@test.co.kr, new@test.co.kr'; document.getElementById('mqTo').dispatchEvent(new Event('change')); });
  await pg.evaluate(()=>{ document.getElementById('mqBody').value='테스트 본문'; document.getElementById('mqBody').dispatchEvent(new Event('input')); });
  await T(`mailQuickSend()`); await pg.waitForTimeout(400);
  ok(sent.length===1, 'Worker /send 1회');
  const m=sent[0]||{};
  ok(m.to==='hong@test.co.kr, new@test.co.kr' && m.cc==='kjs@chjk.co.kr' && m.replyTo==='kjs@chjk.co.kr' && m.account==='seoul' && m.text==='테스트 본문', 'to/cc/replyTo/계정/본문: '+JSON.stringify([m.to,m.cc,m.replyTo,m.account]));
  ok(await T(`_mailClientEmails('㈜테스트').indexOf('new@test.co.kr')>=0`), '새 주소를 업체 담당자로 기억');
  ok(await pg.evaluate(()=>document.getElementById('mailQuickOverlay').style.display==='none') && /메일 발송 완료/.test(await T(`window.__info[window.__info.length-1]`)), '창 닫힘 + 완료 안내');

  console.log('▶ 4) 매입처 카드 메일 링크');
  await T(`document.querySelectorAll('.page-section').forEach(function(p){p.classList.remove('active')}); document.getElementById('pagePurchase').classList.add('active'); renderPurchasePage(); 'ok'`); await pg.waitForTimeout(200);
  const href=await pg.evaluate(()=>{ const a=document.querySelector('#purchaseList a[href^="mailto:"]'); return a?a.getAttribute('onclick'):''; });
  ok(/pvMailOpen\(event,'v1','kim@ina.test'\)/.test(href), '담당자 메일 링크에 바로 쓰기 연결');
  await pg.evaluate(()=>{ document.querySelector('#purchaseList a[href^="mailto:"]').click(); }); await pg.waitForTimeout(200);
  ok(await pg.evaluate(()=>document.getElementById('mailQuickOverlay').style.display==='flex') && await pg.evaluate(()=>document.getElementById('mqTo').value)==='kim@ina.test' && await T(`window._mq.vname`)==='이나코퍼레이션', '매입처 담당자로 창 열림(받는 사람·대리점명)');
  ok(await pg.evaluate(()=>location.href.indexOf('mailto')<0), 'mailto 로 이동하지 않음');

  const realErrs=errs.filter(e=>!/net::|Failed to fetch|NetworkError|fb\.test|firebase|XLSX|cdnjs/.test(e));
  ok(realErrs.length===0, '페이지 오류 없음'+(realErrs.length?(' — '+realErrs.slice(0,3).join(' | ')):''));
  console.log(`\n결과: ${pass} 통과 / ${fail} 실패`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(e){}
  process.exit(fail?1:0);
})();
