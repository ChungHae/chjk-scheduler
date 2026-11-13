// r269 테스트 — SMC 확인 '타사' 칸
const { chromium } = require('playwright'); const fs=require('fs'), path=require('path');
const file=path.resolve(process.argv[2]||'/home/claude/d269/test/index.html');
let pass=0, fail=0; function ok(c,m){ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} }
(async()=>{
  const src=fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){','window.__T=function(c){return eval(c);}; function _vacUnlimited(id){');
  const tmp=path.join(path.dirname(file),'_h_r269.html'); fs.writeFileSync(tmp,src);
  const br=await chromium.launch(); const pg=await br.newPage({viewport:{width:1280,height:900}}); const errs=[]; pg.on('pageerror',e=>errs.push(String(e)));
  const puts={};
  await pg.route('**/*', async r=>{ const u=r.request().url(); if(u.startsWith('file://')) return r.continue();
    const m=u.match(/fb\.test.*_price\/(\w+)\.json/); if(m){ if(r.request().method()==='PUT'){ puts[m[1]]=JSON.parse(r.request().postData()); return r.fulfill({status:200,contentType:'application/json',body:'{}'}); } return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify(m[1]==='pmC'?[{spec:'X1',buy:1}]:[])}); }
    return r.abort(); });
  await pg.goto('file://'+tmp); await pg.waitForTimeout(2500); await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  const T=c=>pg.evaluate(c2=>window.__T(c2),c);
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; saveAll=function(){}; window.__info=''; showInfoModal=function(t,m){ window.__info=m; }; confirm=function(){ return true; }; _fbDbUrl='https://fb.test'; _fbFetch=function(u,o){ return fetch(u,o); }; _fbPutOk=async function(u,rows){ await fetch(u,{method:'PUT',body:JSON.stringify(rows)}); };
    priceMakers=[{id:'pmS',name:'SMC',count:0},{id:'pmC',name:'CKD',count:1}];
    smcQueue=[{id:'a',spec:'KQ2H06-01AS',e:920,status:'wait',at:5},{id:'b',spec:'4GB119-00-C2-3',e:30000,buy:21000,name:'CKD 밸브',status:'wait',at:4,vname:'우진전자'},{id:'c',spec:'ABC-999',e:100,status:'wait',at:3},{id:'d',spec:'OLD',e:1,status:'skip',at:1}];
    try{ localStorage.removeItem('smc_bulk_last'); }catch(e){}
    switchPage('estimate'); qSetSubTab('smc'); 'ok'`);
  await pg.waitForTimeout(300);
  ok(await pg.evaluate(()=>{ const b=document.getElementById('smcOtherTab'); return b && b.textContent==='타사 0' && b.previousElementSibling.textContent.indexOf('제외')===0; }), '필터에 [타사 0] (제외 다음)');
  ok(await pg.evaluate(()=>document.querySelectorAll('#smcResult .smc-oth').length)===3, '대기 줄마다 [타사] 버튼');
  await T(`smcToOther('b')`); await pg.waitForTimeout(100);
  ok(await pg.evaluate(()=>document.getElementById('smcOtherTab').textContent)==='타사 1' && await pg.evaluate(()=>document.querySelectorAll('#smcResult tr[data-id]').length)===2, '[타사] → 대기에서 빠지고 타사 1');
  // 일괄 결과 → 타사로
  await T(`smcBulkOpen()`); await pg.fill('#smcBkText', "KQ2H06-01AS\t920\t정품번\nABC-999\t\t공급불가\n"); await T(`smcBulkParse()`);
  ok(/SMC 에 없음 1건 → 타사로/.test(await pg.evaluate(()=>document.getElementById('smcBkOverlay').innerText)), '일괄 결과: [SMC 에 없음 → 타사로] 버튼');
  await T(`smcBulkSkipNone()`); await pg.waitForTimeout(100);
  ok(await T(`smcQueue.find(function(q){return q.id==='c'}).status==='other' && /공급불가/.test(smcQueue.find(function(q){return q.id==='c'}).smcNote)`), '공급불가 → 타사 (사유 기록)');
  ok(await T(`localStorage.getItem('smc_bulk_last')`)!==null, '마지막 결과 기억');
  await T(`document.getElementById('smcBkOverlay').style.display='none'; _smcBk.text=''; _smcBk.res=null; smcBulkOpen()`); await pg.waitForTimeout(100);
  ok(/E가 일치 1건/.test(await pg.evaluate(()=>document.getElementById('smcBkOverlay').innerText)), '창 다시 열면 지난 결과 자동으로 채워 확인');
  await T(`document.getElementById('smcBkOverlay').style.display='none'; smcSetFilter('other')`); await pg.waitForTimeout(100);
  const tt=await pg.evaluate(()=>document.getElementById('smcResult').innerText);
  ok(/4GB119-00-C2-3/.test(tt) && /ABC-999/.test(tt) && /메이커/.test(tt) && /가격표 등록/.test(tt), '타사 화면: 목록·메이커 칸·[가격표 등록]');
  ok(await pg.evaluate(()=>[...document.querySelectorAll('#smcMakerList option')].map(o=>o.value).join())==='CKD', '메이커 자동완성 = SMC 외 가격표 메이커');
  await T(`smcOtherRegister('b')`); ok(/메이커를 적어/.test(await T('window.__info')), '메이커 없으면 안내');
  await pg.fill('#smcResult tr[data-id="b"] input[data-f="mk"]','CKD'); await T(`smcOtherRegister('b')`); await pg.waitForTimeout(400);
  ok(puts.pmC && puts.pmC.length===2 && puts.pmC[1].spec==='4GB119-00-C2-3' && puts.pmC[1].ega===30000 && puts.pmC[1].buy===21000, 'CKD 가격표에 E가·매입가로 추가');
  ok(/등록 · CKD/.test(await pg.evaluate(()=>document.getElementById('smcResult').innerText)), '등록 표시');
  await pg.fill('#smcResult tr[data-id="c"] input[data-f="mk"]','신규메이커'); await T(`smcOtherRegister('c')`); await pg.waitForTimeout(400);
  ok(await T(`priceMakers.some(function(m){ return m.name==='신규메이커' && m.count===1; })`), '없는 메이커면 새 가격표 만들어 등록');
  await T(`smcOtherBack('c')`); ok(await T(`smcQueue.find(function(q){return q.id==='c'}).status==='wait'`), '[대기로] 복귀');
  const re=errs.filter(e=>!/net::|Failed to fetch|firebase|XLSX|cdnjs/.test(e)); ok(re.length===0,'페이지 오류 없음'+(re.length?' — '+re[0]:''));
  console.log(`\n결과: ${pass} 통과 / ${fail} 실패`); await br.close(); try{fs.unlinkSync(tmp);}catch(e){} process.exit(fail?1:0);
})();
