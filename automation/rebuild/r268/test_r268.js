// r268 테스트 — SMC 확인 처리 칸 잘림 + 일괄 확인
const { chromium } = require('playwright'); const fs=require('fs'), path=require('path');
const file=path.resolve(process.argv[2]||'/home/claude/d268/test/index.html');
let pass=0, fail=0; function ok(c,m){ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} }
(async()=>{
  const src=fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){','window.__T=function(c){return eval(c);}; function _vacUnlimited(id){');
  const tmp=path.join(path.dirname(file),'_h_r268.html'); fs.writeFileSync(tmp,src);
  const br=await chromium.launch(); const pg=await br.newPage({viewport:{width:1280,height:900}}); const errs=[]; pg.on('pageerror',e=>errs.push(String(e)));
  let put=null, puts=0;
  await pg.route('**/*', async r=>{ const u=r.request().url(); if(u.startsWith('file://')) return r.continue();
    if(/fb\.test.*_price\/pmS\.json/.test(u)){ if(r.request().method()==='PUT'){ puts++; put=JSON.parse(r.request().postData()); return r.fulfill({status:200,contentType:'application/json',body:'{}'}); } return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify([{spec:'KQ2H06-01AS',ega:900,name:'피팅'},{spec:'OLD-1',ega:1}])}); }
    return r.abort(); });
  await pg.goto('file://'+tmp); await pg.waitForTimeout(2500); await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  const T=c=>pg.evaluate(c2=>window.__T(c2),c);
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; saveAll=function(){}; showInfoModal=function(){}; confirm=function(){ return true; }; _fbDbUrl='https://fb.test'; _fbFetch=function(u,o){ return fetch(u,o); }; _fbPutOk=async function(u,rows){ var r=await fetch(u,{method:'PUT',body:JSON.stringify(rows)}); if(!r.ok) throw new Error('x'); };
    priceMakers=[{id:'pmS',name:'SMC',count:2}];
    smcQueue=[{id:'a',spec:'KQ2H06-01AS',e:920,status:'wait',at:5,vname:'우진전자'},{id:'b',spec:'SY5120-5LZD-01',e:38810,status:'wait',at:4},{id:'c',spec:'CDQ2B32-20DZ',e:50000,status:'wait',at:3},{id:'d',spec:'ABC-999',e:100,status:'wait',at:2},{id:'e',spec:'면장갑',e:1000,status:'wait',at:1},{id:'f',spec:'VQ1000',e:500,status:'wait',at:0}];
    for(var i=0;i<30;i++) smcQueue.push({id:'z'+i,spec:'ZZZ-LONG-PART-NUMBER-'+i,name:'아주 긴 품목명 솔레노이드 밸브 파일럿식',e:1,status:'wait',at:-i,vname:'(주)에이아이이 긴거래처이름',quoteNo:'(주)에이아이이-20261112-01'});
    switchPage('estimate'); qSetSubTab('smc'); 'ok'`);
  await pg.waitForTimeout(300);
  ok(await pg.evaluate(()=>{ const b=document.querySelector('#smcResult tbody tr td:last-child'); const r=b.getBoundingClientRect(); return r.right<=innerWidth && r.left>0; }), '1280px 에서 처리(등록·제외) 칸이 화면 안에');
  ok(await pg.evaluate(()=>{ const h=document.querySelector('#smcResult thead tr th:last-child').getBoundingClientRect(); return h.right<=innerWidth; }), '처리 머리글도 화면 안에');
  await T(`smcBulkOpen()`); await pg.waitForTimeout(200);
  const t=await pg.evaluate(()=>document.getElementById('smcBkOverlay').innerText);
  ok(/대기 36건 · SMC 품번 35건/.test(t) && /1~35번 복사/.test(t), '일괄 창: 한글 품목 빼고 200개씩 복사 버튼');
  // SMC 화면에서 끌어 복사한 모양 (No, 품번, E가, …)
  const manual="1\tKQ2H06-01AS\t920\tS(5,600)\t7,276\t\t0\tCN\t●\t\n상세\n2\tSY5120-5LZD-01\t39,000\tA(140)\t0\t1\t0\tCN\t●\t\n상세\n3\tCDQ2B32-20DZ\t\t\t\t\t0\t\t●\t\n사양\nVQ1000\t500\t문의요망\n";
  await pg.fill('#smcBkText', manual); await T(`smcBulkParse()`); await pg.waitForTimeout(100);
  const t2=(await pg.evaluate(()=>document.getElementById('smcBkOverlay').innerText)).replace(/\s+/g,' ');
  ok(/E가 일치 1건/.test(t2) && /E가 다름·문의요망 2건/.test(t2) && /SMC 가격 없음·품번 아님 1건/.test(t2), '결과 해석: 일치 1 · 다름/문의 2 · 없음 1 — '+(t2.match(/E가 일치 \d+건|다름·문의요망 \d+건|품번 아님 \d+건/g)||[]).join(','));
  ok(/1건 일괄 등록/.test(t2), '등록 버튼 = 일치분만');
  await T(`smcBulkUseSmc(true)`); ok(/2건 일괄 등록/.test((await pg.evaluate(()=>document.getElementById('smcBkOverlay').innerText))), '다른 것도 SMC 값으로 → 문의요망 빼고 2건');
  await T(`smcBulkUseSmc(false)`); await T(`smcBulkRegister()`); await pg.waitForTimeout(400);
  ok(puts===1 && put.find(x=>x.spec==='KQ2H06-01AS').ega===920 && put.length===2, '가격표에 한 번에 저장 (기존 행 E가 갱신)');
  ok(await T(`smcQueue.find(function(q){return q.id==='a'}).status==='ok' && smcQueue.find(function(q){return q.id==='b'}).status==='wait'`), '일치분만 등록됨, 다른 건 대기 유지');
  await T(`smcBulkSkipNone()`); ok(await T(`smcQueue.find(function(q){return q.id==='c'}).status==='skip'`), '없는 품번 → 제외로');
  const re=errs.filter(e=>!/net::|Failed to fetch|firebase|XLSX|cdnjs/.test(e)); ok(re.length===0,'페이지 오류 없음'+(re.length?' — '+re[0]:''));
  console.log(`\n결과: ${pass} 통과 / ${fail} 실패`); await br.close(); try{fs.unlinkSync(tmp);}catch(e){} process.exit(fail?1:0);
})();
