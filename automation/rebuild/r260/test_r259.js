// r259 테스트 — 매입처 카드 클릭 → 문의 작성 · 링크/버튼은 그대로 · 견적 메뉴·툴바에 문의 없음
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs=require('fs'), path=require('path');
const file=path.resolve(process.argv[2]||'d259/test/index.html');
let pass=0, fail=0; function ok(c,m){ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} }
(async()=>{
  const src=fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){','window.__T=function(c){return eval(c);}; function _vacUnlimited(id){');
  const tmp=path.join(path.dirname(file),'_h_r259.html'); fs.writeFileSync(tmp,src);
  const br=await chromium.launch(); const pg=await br.newPage({viewport:{width:1400,height:900}}); const errs=[]; pg.on('pageerror',e=>errs.push(String(e)));
  await pg.route('**/*',r=>r.request().url().startsWith('file://')?r.continue():r.abort());
  await pg.goto('file://'+tmp); await pg.waitForTimeout(2500);
  await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  const T=c=>pg.evaluate(c2=>window.__T(c2),c);
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울',email:'kjs@chjk.co.kr'}]; saveAll=function(){};
    purchaseVendors=[{id:'v1',brand:'CKD',distributor:'이나코퍼레이션',contacts:[{role:'과장',name:'김동형',phone:'010-1111-2222',email:'kim@ina.test'}]},{id:'v2',brand:'FESTO',distributor:'다스코리아',contacts:[{name:'박태준',email:'tj@das.test'}]}]; pvInq=[];
    document.querySelectorAll('.page-section').forEach(function(p){p.classList.remove('active')}); document.getElementById('pagePurchase').classList.add('active'); renderPurchasePage(); 'ok'`);
  ok(await pg.evaluate(()=>document.querySelectorAll('#purchaseList .pv-card').length)===2, '대리점 카드 2개 클릭 가능');
  ok(await pg.evaluate(()=>!document.getElementById('pvInqNewBtn') && !!document.getElementById('pvInqBoxBtn')), '툴바 [품번 문의] 없음 · 문의함은 있음');
  ok((await pg.evaluate(()=>document.body.innerHTML)).indexOf('pvInqOpen({fromCart:true})')<0, '견적 다운로드 메뉴에 매입처 문의 없음');
  // 카드 빈 곳 클릭
  await pg.evaluate(()=>{ const c=[...document.querySelectorAll('#purchaseList .pv-card')].find(e=>/다스코리아/.test(e.innerText)); c.click(); });
  await pg.waitForTimeout(200);
  ok(await pg.evaluate(()=>document.getElementById('pvInqOverlay')&&document.getElementById('pvInqOverlay').style.display==='flex'), '카드 클릭 → 문의 창');
  ok(await T(`window._pvq.brand`)==='FESTO' && await T(`window._pvq.to.join()`)==='tj@das.test', '그 대리점 브랜드·담당자 채워짐');
  await T(`document.getElementById('pvInqOverlay').style.display='none'; 'ok'`);
  // 수정 버튼 클릭은 문의 창 안 뜸
  await T(`openPurchaseModal=function(){ window.__edit=1; }; renderPurchasePage(); 'ok'`);
  await pg.evaluate(()=>{ const b=document.querySelector('#purchaseList .pv-card button[title="수정"]'); b.click(); });
  ok(await T(`window.__edit===1`) && await pg.evaluate(()=>document.getElementById('pvInqOverlay').style.display==='none'), '수정 버튼은 수정만');
  // 전화 링크 클릭도 문의 창 안 뜸
  await pg.evaluate(()=>{ const a=document.querySelector('#purchaseList .pv-card a[href^="tel:"]'); a.addEventListener('click',e=>e.preventDefault()); a.click(); });
  ok(await pg.evaluate(()=>document.getElementById('pvInqOverlay').style.display==='none'), '전화 링크는 전화만');
  // 메일 링크 → 빠른 메일 창(r257) 그대로
  await pg.evaluate(()=>{ document.querySelector('#purchaseList .pv-card a[href^="mailto:"]').click(); });
  ok(await pg.evaluate(()=>document.getElementById('mailQuickOverlay')&&document.getElementById('mailQuickOverlay').style.display==='flex') && await pg.evaluate(()=>document.getElementById('pvInqOverlay').style.display==='none'), '메일 주소 클릭은 빠른 메일 창(r257)');
  const re=errs.filter(e=>!/net::|Failed to fetch|firebase|XLSX|cdnjs/.test(e)); ok(re.length===0,'페이지 오류 없음'+(re.length?' — '+re[0]:''));
  console.log(`\n결과: ${pass} 통과 / ${fail} 실패`); await br.close(); try{fs.unlinkSync(tmp);}catch(e){} process.exit(fail?1:0);
})();
