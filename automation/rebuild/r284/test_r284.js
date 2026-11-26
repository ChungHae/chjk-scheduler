// r284 테스트 — 같은 발행일·물류출하일·업체·품목·수량이면 중복이라고 알려 준다
//  사용:  node test_r284.js <index.html(__T 주입본)> [라벨]
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const FILE = process.argv[2], LABEL = process.argv[3] || '?';
const P = [];
const ok = (n, c, e) => P.push([n, !!c, e === undefined ? '' : String(e)]);

(async () => {
  const b = await chromium.launch({});
  const pg = await (await b.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:950} })).newPage();
  await pg.route(/^https?:\/\//, r => r.abort());
  const errs=[]; pg.on('pageerror', e=>errs.push(String(e).slice(0,200)));
  await pg.goto('file://'+FILE); await pg.waitForTimeout(3200);

  await pg.evaluate(() => {
    var g=document.getElementById('authGate'); if(g) g.style.display='none';
    __T("_authUser={id:'chjk',name:'김재성',role:'master'}");
    __T("debouncedFbSave=function(){}; doFbSave=function(){}; saveAll=function(){};");
    __T("window.__INFO=''; showInfoModal=function(t,m){ window.__INFO=(t||'')+' | '+(m||''); };");
    __T("window.__CONF=null; showConfirmModal=function(t,m,f,lab,col){ window.__CONF={t:t,m:m,lab:lab,col:col}; window.__CONFOK=f; };");
    __T("_fbDbUrl='https://stub';");
    __T("_asCfgLoaded=true; _asPos=Object.assign({},_AS_POS0); _asMap={};");
    __T("quoteVendors=[{id:'v1',name:'하나코리아 주식회사',count:9}]");
    __T("clientList=[['하나코리아 주식회사','357-87-03525','서울']]");
    // 이미 저장된 거래명세표 1건
    window.__DOCS = { asX:{ id:'asX', no:7, date:'2026-11-10', ship:'20261106',
      vid:'v1', vname:'하나코리아 주식회사', biz:'357-87-03525', ceo:'윤석봉', addr:'서울', memo:'',
      rows:[{spec:'P-1',name:'CYLINDER',qty:2,price:1000,supply:2000,tax:200},
            {spec:'P-2',name:'VALVE',qty:1,price:3000,supply:3000,tax:300}],
      supply:5000, tax:500, total:5500, by:'김재성', at:1, upd:1 } };
    window.__PUT=[];
    __T("_fbFetch=async function(u,o){ if(/_audit_stmt\\.json/.test(String(u))) return {ok:true,status:200,json:async function(){ return window.__DOCS; }}; return {ok:true,status:200,json:async function(){ return null; }}; };");
    __T("_fbPutOk=async function(u,body){ window.__PUT.push(String(u)); return true; };");
    __T("_qBlobGet=async function(){ return []; }; _qBlobPut=async function(){ return true; };");
    __T("switchPage('audit')");
  });
  await pg.waitForTimeout(700);

  const has = await pg.evaluate(()=>typeof __T("_asDupOf")==='function');
  if(!has){
    ['중복 찾기','올린 뒤 표시','묶음 머리 안내','저장할 때 확인','취소','그대로 저장','다른 날짜','다른 수량','다른 업체']
      .forEach(n => ok('r284 기능 없음 — ' + n, false));
    ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
    await b.close(); return out();
  }

  // 같은 내용 1건 + 다른 내용 1건
  const mkDraft = (rows2, date2) => pg.evaluate(([rows2,date2])=>{
    window.__DR = { key:'H0T|하나코리아', ucode:'H0T', uname:'하나코리아', list:[],
      vid:'v1', vname:'하나코리아 주식회사', biz:'357-87-03525', ceo:'윤석봉', addr:'서울',
      docs:[{ ship:'20261106', date:'2026-11-10', warn:'', no:12,
              rows:[{spec:'P-1',name:'CYLINDER',qty:2,price:1000,supply:2000,tax:200},
                    {spec:'P-2',name:'VALVE',qty:1,price:3000,supply:3000,tax:300}], memo:'' },
            { ship:'20261117', date:date2, warn:'', no:5, rows:rows2, memo:'' }] };
    __T("_asFileName='x.xls'"); __T("_asRaw=new Array(3)");
    __T("_asDrafts=[window.__DR]"); __T("_asLRows=null"); __T("_asRender()");
    return __T("_asMarkDupAll()");
  }, [rows2, date2]);

  await mkDraft([{spec:'P-9',name:'X',qty:1,price:100,supply:100,tax:10}], '2026-11-19');
  await pg.waitForTimeout(600);

  const m1 = await pg.evaluate(()=>{
    var dr=__T("_asDrafts")[0];
    return { d0:!!dr.docs[0].dup, d1:!!dr.docs[1].dup,
             no:(dr.docs[0].dup||{}).no,
             txt:document.getElementById('pageAudit').innerText };
  });
  ok('같은 내용인 전표를 중복으로 잡는다', m1.d0 && m1.no===7, JSON.stringify({d0:m1.d0,no:m1.no}));
  ok('다른 전표는 중복이 아니다', m1.d1===false);
  ok('묶음 머리에 중복 건수 안내', /같은 내용이 1건/.test(m1.txt), (m1.txt.match(/같은 내용이[^\n]*/)||[''])[0]);
  ok('전표 줄에도 어떤 것과 겹치는지 보인다',
     /이미 저장된 거래명세표와 같은 내용입니다 — 2026-11-10 · 번호 7/.test(m1.txt),
     (m1.txt.match(/이미 저장된 거래명세표[^\n]*/)||[''])[0]);

  // ── 저장할 때 묻는다 ──
  await pg.evaluate(()=>{ window.__PRN=''; __T("_asPrintHtml=function(h){ window.__PRN=h; };"); });
  await pg.evaluate(()=>__T("asSavePrint(0)")); await pg.waitForTimeout(600);
  const c1 = await pg.evaluate(()=>window.__CONF);
  ok('저장할 때 중복이라고 알려 준다', c1 && /중복 확인/.test(c1.t) && /중복 내역 1건/.test(c1.m), c1?JSON.stringify(c1).slice(0,160):'(없음)');
  ok('어느 것과 겹치는지 적어 준다', c1 && /2026-11-10 번호 7 \(2품목\)/.test(c1.m), c1?c1.m.slice(0,200):'');
  ok('단추가 [중복이지만 그대로 저장]', c1 && c1.lab==='중복이지만 그대로 저장', c1?c1.lab:'');

  // 취소 = 아무것도 안 한다
  await pg.evaluate(()=>{ window.__CONF=null; });
  await pg.waitForTimeout(100);
  ok('취소하면 저장되지 않는다', await pg.evaluate(()=>window.__PUT.length===0 && __T("_asDrafts").length===1));

  // 그대로 저장
  await pg.evaluate(async ()=>{ await window.__CONFOK(); }); await pg.waitForTimeout(800);
  ok('[그대로 저장] 을 고르면 저장된다', await pg.evaluate(()=>window.__PUT.length===2 && (window.__PRN||'').length>500),
     await pg.evaluate(()=>window.__PUT.length));

  // ── 중복이 아닌 경우 ──
  const cases = [
    ['발행일이 다르면 중복이 아니다', ()=>{ __T("_asDrafts")[0].docs[0].date='2026-11-11'; }],
    ['물류출하일이 다르면 중복이 아니다', ()=>{ __T("_asDrafts")[0].docs[0].ship='20261107'; }],
    ['수량이 다르면 중복이 아니다', ()=>{ __T("_asDrafts")[0].docs[0].rows[0].qty=3; }],
    ['품번이 다르면 중복이 아니다', ()=>{ __T("_asDrafts")[0].docs[0].rows[0].spec='P-7'; }],
    ['업체가 다르면 중복이 아니다', ()=>{ var d=__T("_asDrafts")[0]; d.vid='v9'; d.vname='다른회사'; }],
    ['품목 수가 다르면 중복이 아니다', ()=>{ __T("_asDrafts")[0].docs[0].rows.pop(); }],
  ];
  for(const [name, fn] of cases){
    await mkDraft([{spec:'P-9',name:'X',qty:1,price:100,supply:100,tax:10}], '2026-11-19');
    await pg.waitForTimeout(350);
    await pg.evaluate(fn);
    await pg.evaluate(()=>__T("_asMarkDupAll()")); await pg.waitForTimeout(350);
    ok(name, await pg.evaluate(()=>!__T("_asDrafts")[0].docs[0].dup));
  }
  // 줄 차례가 바뀌어도 같은 것으로 본다
  await mkDraft([{spec:'P-9',name:'X',qty:1,price:100,supply:100,tax:10}], '2026-11-19');
  await pg.waitForTimeout(350);
  await pg.evaluate(()=>{ __T("_asDrafts")[0].docs[0].rows.reverse(); __T("_asMarkDupAll()"); });
  await pg.waitForTimeout(400);
  ok('품목 차례만 다른 것은 같은 것으로 본다', await pg.evaluate(()=>!!__T("_asDrafts")[0].docs[0].dup));

  // 중복이 없으면 평소 문구
  await pg.evaluate(()=>{ window.__DOCS={}; __T("_asLRows=null"); });
  await mkDraft([{spec:'P-9',name:'X',qty:1,price:100,supply:100,tax:10}], '2026-11-19');
  await pg.waitForTimeout(400);
  await pg.evaluate(()=>{ window.__CONF=null; __T("asSavePrint(0)"); }); await pg.waitForTimeout(600);
  const c2 = await pg.evaluate(()=>window.__CONF);
  ok('중복이 없으면 평소처럼 묻는다', c2 && c2.t==='거래명세표 저장·인쇄' && c2.lab==='저장하고 인쇄' && !/중복/.test(c2.m),
     c2?JSON.stringify(c2).slice(0,140):'(없음)');

  ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
  await b.close(); return out();

  function out(){
    let p=0; P.forEach(x=>{ if(x[1]) p++; console.log((x[1]?'  OK  ':'  FAIL')+'  '+x[0]+(x[1]?'':'   → '+x[2])); });
    console.log('\n['+LABEL+'] '+p+'/'+P.length);
    process.exit(p===P.length?0:1);
  }
})();
