// r266 테스트 — 견적 → 대성 발주 창 (Worker 는 가짜)
const { chromium } = require('playwright');
const fs=require('fs'), path=require('path');
const file=path.resolve(process.argv[2]||'/home/claude/d266/test/index.html');
let pass=0, fail=0; function ok(c,m){ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} }
(async()=>{
  const src=fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){','window.__T=function(c){return eval(c);}; function _vacUnlimited(id){');
  const tmp=path.join(path.dirname(file),'_h_r266.html'); fs.writeFileSync(tmp,src);
  const br=await chromium.launch(); const pg=await br.newPage({viewport:{width:1400,height:900}}); const errs=[]; pg.on('pageerror',e=>errs.push(String(e)));
  const calls=[]; let fbPut=null;
  await pg.route('**/*', async r=>{ const u=r.request().url(); if(u.startsWith('file://')) return r.continue();
    if(u.startsWith('https://ds.test/')){ const p=new URL(u).pathname; const b=r.request().postData(); calls.push({p, key:r.request().headers()['x-wmis-key'], b:b?JSON.parse(b):null});
      if(p==='/lookup') return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true,deliv:{deliType:'충해전기',deliCmpy:'구로정기배송',deliPlace:'서울특별시 구로구 (대성기본)',deliTel:'010-5228-2922'},items:[
        {pn:'SY5120-5LZD-01',found:true,code:'SMC000216197',name:'SMC',price:38810,stock:{'서울':3,'BDC':0,'부산':1,'대구':0}},
        {pn:'CDQ2B32-20DZ',found:false,cands:[{code:'SMC1',pn:'CDQ2B32-20DZ-M9BW',price:50000,stock:{'서울':1}}]},
        {pn:'KQ2H06-01AS',found:true,code:'SMC000000777',name:'SMC',price:1200,stock:{'서울':100}}]})});
      if(p==='/order') return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true,orderNo:'SO2611120001'})});
      if(p==='/ping') return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true,user:'S0***',cust:'충해전기(주)'})});
    }
    if(/sched_ds_cfg\.json/.test(u) && r.request().method()==='PATCH'){ fbPut=JSON.parse(r.request().postData()); return r.fulfill({status:200,contentType:'application/json',body:'{}'}); }
    return r.abort(); });
  await pg.goto('file://'+tmp); await pg.waitForTimeout(2500);
  await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  const T=c=>pg.evaluate(c2=>window.__T(c2),c);
  ok(await pg.evaluate(()=>!!document.getElementById('qDsBtn')), '견적 툴바에 [대성 발주] 버튼');
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'화성',phone:'010-5228-2922'}]; saveAll=function(){}; showInfoModal=function(t,m){ window.__info=m; };
    _dsLoadCfg=async function(){ return {url:'https://ds.test',key:'kk'}; }; window.__conf=[]; confirm=function(m){ window.__conf.push(m); return true; };
    _qQuoteNo='Q-20261112-01'; _qLoadedId='qs1'; quoteSaved=[{id:'qs1',title:'Q-20261112-01'}]; _qPersistQuote=async function(){ window.__persist=(window.__persist||0)+1; };
    _qCart=[{vname:'대국산기',spec:'SY5120-5LZD-01',qty:2},{vname:'대국산기',spec:'CDQ2B32-20DZ',qty:1},{vname:'대국산기',spec:'VP342R-5DZ1-01B',qty:1,altOff:true},{vname:'대국산기',spec:'KQ2H06-01AS',qty:10},{vname:'대국산기',spec:'',qty:1}]; 'ok'`);
  await pg.click('#qDsBtn').catch(()=>T('qDsOpen()')); await pg.waitForTimeout(600);
  ok(await pg.evaluate(()=>document.getElementById('dsOverlay').style.display==='flex'), '버튼 → 대성 발주 창');
  const c0=calls.find(c=>c.p==='/lookup');
  ok(c0 && c0.key==='kk' && c0.b.items.map(x=>x.pn).join(',')==='SY5120-5LZD-01,CDQ2B32-20DZ,KQ2H06-01AS', '조회: 빈 줄·변경제안 원래 줄 빼고 품번 3개, 열쇠 헤더');
  const txt=await pg.evaluate(()=>document.getElementById('dsOverlay').innerText);
  ok(/SMC000216197/.test(txt) && /38,810/.test(txt) && /서울 3/.test(txt), '대성 코드·대리점가·재고');
  ok(/대성에 없음/.test(txt) && /CDQ2B32-20DZ-M9BW/.test(txt), '못 찾은 품번 + 비슷한 품번');
  ok(/발주 2품목/.test(txt.replace(/\s+/g,' ')) && /89,620/.test(txt), '합계 = 38,810×2 + 1,200×10 = 89,620');
  ok(await pg.evaluate(()=>document.getElementById('dsType').value)==='충해전기 화성영업소' && await pg.evaluate(()=>/화성시 팔탄면/.test(document.getElementById('dsAddr').value)) && await pg.evaluate(()=>document.getElementById('dsTel').value)==='031-352-4475', '화성 직원 → 화성 배송지 자동');
  await T(`dsBranch('서울')`); await pg.waitForTimeout(100);
  ok(await pg.evaluate(()=>document.getElementById('dsAddr').value)==='서울특별시 구로구 (대성기본)' && await pg.evaluate(()=>document.getElementById('dsCmpy').value)==='구로정기배송', '서울 → 대성 기본 배송지');
  await T(`dsBranch('화성')`);
  await T(`dsPickCand(1,'SMC1')`); await pg.waitForTimeout(100);
  ok(/발주 3품목/.test((await pg.evaluate(()=>document.getElementById('dsOverlay').innerText)).replace(/\s+/g,' ')), '후보 선택 → 발주 품목에 포함');
  await T(`dsToggle(1,false); dsQty(0,'3')`);
  ok(await pg.evaluate(()=>document.getElementById('dsDate').value)>=new Date().toISOString().slice(0,10), '납품요청일 기본값');
  await T(`dsSubmit()`); await pg.waitForTimeout(500);
  const o=calls.find(c=>c.p==='/order');
  ok(o && o.b.items.length===2 && o.b.items[0].code==='SMC000216197' && o.b.items[0].qty===3 && o.b.items[1].qty===10, '발주: 체크한 2품목·수량 반영');
  ok(o && o.b.deli.type==='충해전기 화성영업소' && o.b.deli.cmpy==='택배' && o.b.deli.tel==='031-352-4475' && /Q-20261112-01/.test(o.b.remk) && /대국산기/.test(o.b.remk), '배송지·비고(견적번호/거래처)');
  ok(await T(`window.__conf.length===1 && /바로 대성에 접수/.test(window.__conf[0])`), '저장 전 확인창 (바로 접수 안내)');
  ok(/주문번호 SO2611120001/.test(await pg.evaluate(()=>document.getElementById('dsOverlay').innerText)), '완료 → 주문번호 표시');
  ok(await T(`quoteSaved[0].dsOrders && quoteSaved[0].dsOrders[0].no==='SO2611120001' && quoteSaved[0].dsOrders[0].n===2`), '저장 견적에 대성 발주 기록');
  await T(`dsSubmit()`); await pg.waitForTimeout(200);
  ok(calls.filter(c=>c.p==='/order').length===1, '완료 뒤 다시 눌러도 두 번 발주 안 됨');
  // 설정 창
  await T(`_dsLoadCfg=async function(){ return {}; }; _fbFetch=function(u,o){ return fetch(u,o); }; _fbDbUrl='https://fb.test'; dsOpenCfg()`); await pg.waitForTimeout(200);
  await pg.fill('#dsCfgUrl','https://ds.test'); await pg.fill('#dsCfgKey','kk'); await T(`dsCfgPing()`); await pg.waitForTimeout(300);
  ok(/연결됨/.test(await pg.evaluate(()=>document.getElementById('dsCfgMsg').innerText)), '설정: 연결 확인');
  await T(`dsCfgSave()`); await pg.waitForTimeout(300);
  ok(fbPut && fbPut.url==='https://ds.test' && fbPut.key==='kk' && Object.keys(fbPut).length===2, '설정 저장 = 주소·열쇠만 (비밀번호 없음)');
  await T(`_authUser={id:'x',name:'테스트직원',role:'user'}; qDsOpen()`); await pg.waitForTimeout(300);
  ok(await pg.evaluate(()=>![...document.querySelectorAll('#dsOverlay button')].some(b=>b.textContent==='대성 설정')), '직원 화면엔 [대성 설정] 버튼 없음');
  await T(`_qCart=[{spec:'',qty:1}]; window.__info=''; qDsOpen()`); ok(/품번이 없습니다/.test(await T('window.__info')), '빈 견적 안내');
  const re=errs.filter(e=>!/net::|Failed to fetch|firebase|XLSX|cdnjs/.test(e)); ok(re.length===0,'페이지 오류 없음'+(re.length?' — '+re[0]:''));
  console.log(`\n결과: ${pass} 통과 / ${fail} 실패`); await br.close(); try{fs.unlinkSync(tmp);}catch(e){} process.exit(fail?1:0);
})();
