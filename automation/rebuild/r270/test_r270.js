// r270 테스트 — 발주 탭(E가·구매가·DC·삭제·아이디만 연결): 업체명 → 견적 불러오기 → 대성 발주 (Worker 는 가짜)
const { chromium } = require('playwright');
const fs=require('fs'), path=require('path');
const file=path.resolve(process.argv[2]||'/home/claude/d270/test/index.html');
let pass=0, fail=0; function ok(c,m){ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} }
(async()=>{
  const src=fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){','window.__T=function(c){return eval(c);}; function _vacUnlimited(id){');
  const tmp=path.join(path.dirname(file),'_h_r270.html'); fs.writeFileSync(tmp,src);
  const br=await chromium.launch(); const pg=await br.newPage({viewport:{width:1400,height:1000}}); const errs=[]; pg.on('pageerror',e=>errs.push(String(e)));
  const calls=[]; let fbPut=null;
  await pg.route('**/*', async r=>{ const u=r.request().url(); if(u.startsWith('file://')) return r.continue();
    if(u.startsWith('https://ds.test/')){ const p=new URL(u).pathname.replace(/^\/wmis/,''); const b=r.request().postData(); calls.push({p, key:r.request().headers()['x-mail-key'], b:b?JSON.parse(b):null});
      if(p==='/lookup') return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true,deliv:{deliType:'충해전기',deliCmpy:'구로정기배송',deliPlace:'서울특별시 구로구 (대성기본)',deliTel:'010-5228-2922'},items:JSON.parse(b).items.map(it=>{
        if(it.pn==='SY5120-5LZD-01') return {pn:it.pn,found:true,code:'SMC000216197',name:'SMC',price:38810,stock:{'서울':3,'BDC':0,'부산':1,'대구':0}};
        if(it.pn==='KQ2H06-01AS') return {pn:it.pn,found:true,code:'SMC000000777',name:'SMC',price:1200,stock:{'서울':100}};
        if(it.pn==='VP342R-5DZ1-01A-F') return {pn:it.pn,found:true,code:'SMC000000888',name:'SMC',price:90000,stock:{}};
        return {pn:it.pn,found:false,cands:[{code:'SMC1',pn:it.pn+'-M9BW',price:50000,stock:{'서울':1}}]}; })})});
      if(p==='/order') return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true,orderNo:'SO2611120001'})});
      if(p==='/ping') return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true,user:'S0***',cust:'충해전기(주)'})});
    }
    if(/fb\.test.*_qsaved\/qs1\.json/.test(u)) return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify([
      {vname:'대국산기',spec:'SY5120-5LZD-01',qty:'2',e:38810,buy:25230,sell:30000},{vname:'대국산기',spec:'CDQ2B32-20DZ',qty:1},{vname:'대국산기',spec:'VP342R-5DZ1-01B',qty:1,altOff:true},{vname:'대국산기',spec:'VP342R-5DZ1-01A-F',qty:1,altOf:'VP342R-5DZ1-01B'},{vname:'대국산기',spec:'KQ2H06-01AS',qty:10,e:1200,buy:900,sell:1100,small:true},{vname:'대국산기',spec:'',qty:1}])});
    if(/sched_ds_cfg\.json/.test(u) && r.request().method()==='PATCH'){ fbPut=JSON.parse(r.request().postData()); return r.fulfill({status:200,contentType:'application/json',body:'{}'}); }
    return r.abort(); });
  await pg.goto('file://'+tmp); await pg.waitForTimeout(2500);
  await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  const T=c=>pg.evaluate(c2=>window.__T(c2),c);
  ok(await pg.evaluate(()=>!document.getElementById('qDsBtn')), '견적 화면에서 [대성 발주] 버튼 빠짐');
  ok(await pg.evaluate(()=>{ const t=[...document.querySelectorAll('.page-nav .page-tab')].map(b=>b.textContent.trim()); return t.indexOf('발주')===t.indexOf('견적')+1; }), '상단 탭: 견적 다음에 [발주]');
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'화성',phone:'010-5228-2922'}]; saveAll=function(){ window.__saved=(window.__saved||0)+1; }; showInfoModal=function(t,m){ window.__info=m; };
    _fbDbUrl='https://fb.test'; _fbFetch=function(u,o){ return fetch(u,o); };
    _dsLoadCfg=async function(){ return {id:'S0757',pw:'pw'}; }; _mailLoadCfg=async function(){ return {url:'https://ds.test',key:'kk'}; }; window.__conf=[]; confirm=function(m){ window.__conf.push(m); return true; };
    quoteSaved=[{id:'qs1',title:'Q-20261112-01',vname:'대국산기',count:6,total:150000,savedBy:'김재성',savedAt:Date.now()-3600e3},{id:'qs2',title:'Q-20261110-03',vname:'솔브레인',count:2,total:9000,savedBy:'이영희',savedAt:Date.now()-86400e3*2},{id:'qs3',title:'Q-20261101-02',vname:'대국산기',count:1,total:100,savedAt:Date.now()-86400e3*10}]; 'ok'`);
  await pg.evaluate(()=>[...document.querySelectorAll('.page-nav .page-tab')].find(b=>b.textContent.trim()==='발주').click()); await pg.waitForTimeout(300);
  ok(await pg.evaluate(()=>document.getElementById('pageOrder').classList.contains('active')), '[발주] 탭 → 발주 페이지');
  let txt=await pg.evaluate(()=>document.getElementById('pageOrder').innerText);
  ok(/최근 견적 15건/.test(txt) && /Q-20261110-03/.test(txt), '업체명 비우면 최근 견적 목록');
  ok(await pg.evaluate(()=>[...document.querySelectorAll('#poVendorList option')].map(o=>o.value).join(','))==='대국산기,솔브레인', '업체명 자동완성 = 견적 저장 업체 (최근 순)');
  await pg.fill('#poVendor','대국'); await pg.waitForTimeout(400);
  txt=await pg.evaluate(()=>document.getElementById('pageOrder').innerText);
  ok(/견적 2건/.test(txt) && /Q-20261112-01/.test(txt) && /Q-20261101-02/.test(txt) && !/Q-20261110-03/.test(txt), '업체명 입력 → 그 업체 견적만');
  ok(await pg.evaluate(()=>document.activeElement&&document.activeElement.id==='poVendor'), '입력 중 커서 유지');
  await T(`poLoadQuote('qs1')`); await pg.waitForTimeout(700);
  const c0=calls.find(c=>c.p==='/lookup');
  ok(c0 && c0.key==='kk' && c0.b.cred.id==='S0757' && c0.b.items.map(x=>x.pn).join(',')==='SY5120-5LZD-01,CDQ2B32-20DZ,VP342R-5DZ1-01A-F,KQ2H06-01AS', '불러오기: 빈 줄·재고없음 원래 줄 빼고, 변경 제안 포함 · 메일 서버 /wmis + 아이디 전달');
  txt=await pg.evaluate(()=>document.getElementById('pageOrder').innerText);
  ok(/SMC000216197/.test(txt) && /38,810/.test(txt) && /서울 3/.test(txt) && /변경 제안/.test(txt), '대성 코드·대리점가·재고 + 변경 제안 표시');
  ok(/대성에 없음/.test(txt) && /CDQ2B32-20DZ-M9BW/.test(txt), '못 찾은 품번 + 비슷한 품번');
  ok(/발주 3품목/.test(txt.replace(/\s+/g,' ')) && /179,620/.test(txt), '대리점가 합계 = 77,620 + 90,000 + 12,000');
  ok(/116,754/.test(txt), '대성가 합계 (×0.65) = 25,227×2 + 58,500 + 780×10');
  ok(/35%/.test(txt) && /25%/.test(txt) && /25,230/.test(txt) && /30,000/.test(txt), '견적 E가·구매가·판매가·견적 DC 표시 (35% · 25%)');
  ok(await pg.evaluate(()=>{ const i=[...document.querySelectorAll('#pageOrder tbody input[type=number]')].map(x=>x.value); return i[0]==='2'&&i[3]==='10'; }), '수량 = 견적 그대로 (문자열 "2" 포함)');
  ok(await pg.evaluate(()=>document.getElementById('dsRemk').value)==='', '기타요청사항 비어 있음');
  await T(`poSelectThr()`); ok(await T(`_ds.lines.map(function(l){return l.on?1:0}).join('')`)==='1000', '견적 DC 35% 이상만 선택 → SY5120 만');
  await T(`poSetThr(20); poSelectThr()`); ok(await T(`_ds.lines.map(function(l){return l.on?1:0}).join('')`)==='1001', '기준 20% → KQ2H06 도');
  await T(`poSelectAll(true); poSetThr(35)`);
  await T(`dsDel(2)`); ok(await T(`_ds.lines.length===3 && _ds.lines.map(function(l){return l.pn}).indexOf('VP342R-5DZ1-01A-F')<0`), '× 로 줄 삭제');
  ok(await pg.evaluate(()=>document.getElementById('dsType').value)==='충해전기 화성영업소' && await pg.evaluate(()=>document.getElementById('dsTel').value)==='031-352-4475', '화성 직원 → 화성 배송지');
  await T(`dsBranch('서울')`); ok(await pg.evaluate(()=>document.getElementById('dsAddr').value)==='서울특별시 구로구 (대성기본)', '서울 → 대성 기본 배송지');
    await T(`dsPickCand(1,'SMC1'); dsQty(0,'3')`);
  await T(`dsSubmit()`); await pg.waitForTimeout(500);
  const o=calls.find(c=>c.p==='/order');
  ok(o && o.b.items.map(x=>x.code+'×'+x.qty).join(',')==='SMC000216197×3,SMC1×1,SMC000000777×10' && o.b.items[1].pn==='CDQ2B32-20DZ-M9BW', '발주 품목: 수량·후보 반영, 체크 해제 제외');
  ok(o && o.b.deli.cmpy==='구로정기배송' && o.b.deli.type==='충해전기', '배송지 전달');
  ok(await T(`window.__conf.length===1 && /바로 대성에 접수/.test(window.__conf[0])`), '발주 전 확인창');
  txt=await pg.evaluate(()=>document.getElementById('pageOrder').innerText);
  ok(/주문번호 SO2611120001/.test(txt), '완료 → 주문번호');
  ok(await T(`quoteSaved[0].dsOrders && quoteSaved[0].dsOrders[0].no==='SO2611120001' && quoteSaved[0].dsOrders[0].n===3 && _qsPend['qs1']>0`), '그 견적에 대성 발주 기록 (병합 보호)');
  ok(/최근 대성 발주/.test(txt) && /SO2611120001/.test(txt.split('최근 대성 발주')[1]) && /대성 발주 1/.test(txt), '최근 대성 발주 목록 + 견적 목록 배지');
  await T(`dsSubmit()`); await pg.waitForTimeout(200); ok(calls.filter(c=>c.p==='/order').length===1, '두 번 발주 안 됨');
  await T(`poReset()`); ok(!/② 발주 품목 Q-/.test(await pg.evaluate(()=>document.getElementById('pageOrder').innerText)) && await pg.evaluate(()=>document.getElementById('poVendor').value)==='대국', '[새 발주] → 품목 비우고 업체명 유지');
  // 설정: 아이디·비밀번호만
  await T(`_dsLoadCfg=async function(){ return {}; }; _dsCfg={}; dsOpenCfg()`); await pg.waitForTimeout(200);
  ok(await pg.evaluate(()=>!!document.getElementById('dsCfgId') && !!document.getElementById('dsCfgPw')), '설정 창: 대성 아이디·비밀번호 칸');
  await pg.fill('#dsCfgId','S0757'); await pg.fill('#dsCfgPw','pw'); await T(`dsCfgPing()`); await pg.waitForTimeout(300);
  ok(/연결됨/.test(await pg.evaluate(()=>document.getElementById('dsCfgMsg').innerText)), '연결 확인 = 메일 서버 주소로 /wmis/ping');
  await T(`dsCfgSave()`); await pg.waitForTimeout(300); ok(fbPut && fbPut.id==='S0757' && fbPut.pw==='pw' && fbPut.url==='' , '설정 저장 = 아이디·비밀번호 (서버 주소 비움 → 메일 설정 사용)');
  await T(`_dsLoadCfg=async function(){ return {}; }; _ds.lines=[{pn:'A',qty:1,st:'wait',on:true}]; _dsLookup()`); await pg.waitForTimeout(200);
  ok(/아이디·비밀번호 설정 필요/.test(await pg.evaluate(()=>document.getElementById('pageOrder').innerText)), '아이디 없으면 대성 미확인 + 안내');
  await T(`document.getElementById('dsCfgOverlay').style.display='none'; _authUser={id:'x',name:'테스트직원',role:'user'}; renderOrderPage()`);
  ok(await pg.evaluate(()=>![...document.querySelectorAll('#pageOrder button')].some(b=>b.textContent==='대성 설정')), '직원 화면엔 [대성 설정] 없음');
  const re=errs.filter(e=>!/net::|Failed to fetch|firebase|XLSX|cdnjs/.test(e)); ok(re.length===0,'페이지 오류 없음'+(re.length?' — '+re[0]:''));
  console.log(`\n결과: ${pass} 통과 / ${fail} 실패`); await br.close(); try{fs.unlinkSync(tmp);}catch(e){} process.exit(fail?1:0);
})();
