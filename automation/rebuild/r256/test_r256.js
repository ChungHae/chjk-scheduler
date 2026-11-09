// r256 테스트 — ① 원장 엑셀 합치기가 추가정보를 지우지 않는다
//                ② 규격추가 덮어쓰기도 마찬가지
//                ③ 업체명 변경이 견적 거래처·원장·담당업체·기준가·등록대기·저장견적까지 따라간다
//  사용:  node test_r256.js <index.html(__T 주입본)> [라벨]
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const FILE = process.argv[2], LABEL = process.argv[3] || '?';
const P = [];
const ok = (n, c, e) => P.push([n, !!c, e === undefined ? '' : String(e)]);

(async () => {
  const b = await chromium.launch({});
  const pg = await (await b.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:950} })).newPage();
  await pg.route(/^https?:\/\//, r => r.abort());
  const errs = []; pg.on('pageerror', e => errs.push(String(e).slice(0,200)));
  await pg.goto('file://' + FILE); await pg.waitForTimeout(3200);
  const T = c => pg.evaluate(c2 => window.__T(c2), c);

  await pg.evaluate(() => {
    var g=document.getElementById('authGate'); if(g) g.style.display='none';
    __T("_authUser={id:'chjk',name:'김재성',role:'master'}");
    __T("_fbDbUrl='https://stub'");
    __T("window.__INFO=''; showInfoModal=function(t,m){ window.__INFO=(t||'')+' | '+(m||''); };");
    __T("showConfirmModal=function(t,m,okf){ window.__CONF=(t||'')+' | '+(m||''); okf&&okf(); };");
    __T("debouncedFbSave=function(){}; doFbSave=function(){}; saveAll=function(){};");
    __T("window.__STORE={};");
    __T("_qBlobPut=async function(id,rows){ window.__STORE[id]=JSON.parse(JSON.stringify(rows)); _qBlobCache[id]=JSON.parse(JSON.stringify(rows)); };");
    __T("_qBlobGet=async function(id){ return window.__STORE[id]?JSON.parse(JSON.stringify(window.__STORE[id])):null; };");
    __T("_ensurePriceSyncMap=async function(){}; _priceSyncMap=null;");
  });

  const has = await T("typeof _qMergeLedgerRow==='function' && typeof _qRenameClientEverywhere==='function'");
  if(!has){
    ['업로드: 메이커 유지','업로드: 구매처 유지','업로드: 비고 유지','업로드: 링크 유지','업로드: 새 메이커로 교체',
     '업로드: 가격은 교체','업로드: 품목 교체','업로드: 납기 교체','업로드: pl·small 유지','업로드: 단종 해제',
     '업로드: 새 규격 추가','업로드: 리포트가 추가정보 변경도 센다',
     '규격추가 덮어쓰기: 기존 메이커 유지','규격추가 덮어쓰기: 새 구매처 반영','규격추가 덮어쓰기: 가격 교체',
     '업체명 변경: quoteVendors','업체명 변경: 원장 id 그대로','업체명 변경: 저장 견적 vname','업체명 변경: 담당 업체 키',
     '업체명 변경: 업체 기준가 키','업체명 변경: 등록 대기 이름','업체명 변경: 장바구니 vname',
     '업체명 변경: 다른 업체는 안 건드림','사업자번호만 바꾸면 이름 유지','안내문에 견적 쪽 변경 표시']
      .forEach(n => ok('r256 기능 없음 — ' + n, false));
    ok('pageerror 없음', errs.length === 0, errs.slice(0,2).join(' | '));
    await b.close(); return out();
  }

  // ───────── ① 원장 엑셀 업로드 합치기 ─────────
  const m1 = await pg.evaluate(() => {
    var old = { spec:'AAA-1', name:'옛품목', e:1000, buy:800, sell:1000, eta:'3일',
                pl:true, small:700,
                info:{ maker:'SMC', src:'한국상사', remark:'비고메모', link:'https://old/x' } };
    var up  = { spec:'AAA-1', name:'새품목', e:2000, buy:1600, sell:2000, eta:'7일' };   // 엑셀에 추가정보 열이 없음
    return __T("_qMergeLedgerRow")(old, up);
  });
  ok('업로드: 메이커 유지', m1.info && m1.info.maker==='SMC', JSON.stringify(m1.info));
  ok('업로드: 구매처 유지', m1.info && m1.info.src==='한국상사');
  ok('업로드: 비고 유지', m1.info && m1.info.remark==='비고메모');
  ok('업로드: 링크 유지', m1.info && m1.info.link==='https://old/x');
  ok('업로드: 가격은 교체', m1.e===2000 && m1.buy===1600 && m1.sell===2000, JSON.stringify([m1.e,m1.buy,m1.sell]));
  ok('업로드: 품목 교체', m1.name==='새품목');
  ok('업로드: 납기 교체', m1.eta==='7일');
  ok('업로드: pl·small 유지', m1.pl===true && m1.small===700, JSON.stringify([m1.pl,m1.small]));

  const m2 = await pg.evaluate(() => {
    var old = { spec:'B', name:'x', e:1, buy:1, sell:1, disc:'단종', info:{ maker:'SMC', src:'가' } };
    var up  = { spec:'B', name:'x', e:1, buy:1, sell:5, info:{ maker:'CONVUM' } };
    return __T("_qMergeLedgerRow")(old, up);
  });
  ok('업로드: 새 메이커로 교체', m2.info && m2.info.maker==='CONVUM', JSON.stringify(m2.info));
  ok('업로드: 안 올라온 구매처는 유지', m2.info && m2.info.src==='가');
  ok('업로드: 단종 해제', m2.disc===undefined, JSON.stringify(m2.disc));

  ok('업로드: 리포트가 추가정보 변경도 센다',
     await pg.evaluate(() => __T("_qRowDiffers")({spec:'A',e:1,buy:1,sell:1,info:{maker:'SMC'}}, {spec:'A',e:1,buy:1,sell:1,info:{maker:'CONVUM'}})));
  ok('업로드: 값이 같으면 동일로 센다',
     await pg.evaluate(() => !__T("_qRowDiffers")({spec:'A',e:1,buy:1,sell:1,info:{maker:'SMC'}}, {spec:'A',e:1,buy:1,sell:1,info:{maker:'SMC'}})));

  // 실제 qxDoUpload 병합 경로 (엑셀 파싱은 건너뛰고 _qParseLedgerFile 만 바꿔 끼운다)
  const up1 = await pg.evaluate(async () => {
    __T("quoteVendors=[{id:'v1',name:'테스트상사',count:2}]");
    __T("window.__STORE['v1']=[{spec:'AAA-1',name:'옛',e:1000,buy:800,sell:1000,eta:'3일',info:{maker:'SMC',src:'한국상사',remark:'메모',link:'https://old/x'}},{spec:'ZZZ-9',name:'그대로',e:5,buy:4,sell:5,info:{maker:'NITTA'}}]");
    __T("_qParseLedgerFile=async function(){ return [{spec:'AAA-1',name:'새',e:2000,buy:1600,sell:2000,eta:'7일'},{spec:'NEW-1',name:'신규',e:10,buy:8,sell:10}]; }");
    __T("_qxVendor='테스트상사'; _qxFile={name:'x.xlsx'};");
    __T("allClients=function(){ return [['테스트상사','']]; }");
    __T("_qShowUploadReport=function(){}");
    __T("renderEstimatePage=function(){}");
    await __T("qxDoUpload()");
    await new Promise(r=>setTimeout(r,500));
    return { rows: window.__STORE['v1'], rep: window.__T("window._qUpReport") };
  });
  const r1 = (up1.rows||[]).find(r=>r.spec==='AAA-1') || {};
  const r2 = (up1.rows||[]).find(r=>r.spec==='ZZZ-9') || {};
  const r3 = (up1.rows||[]).find(r=>r.spec==='NEW-1');
  ok('업로드(실경로): 기존 규격의 추가정보 유지', !!(r1.info && r1.info.maker==='SMC' && r1.info.src==='한국상사' && r1.info.link==='https://old/x'), JSON.stringify(r1.info));
  ok('업로드(실경로): 기존 규격의 가격 교체', r1.e===2000 && r1.sell===2000, JSON.stringify([r1.e,r1.sell]));
  ok('업로드(실경로): 안 올라온 규격은 그대로', !!(r2.info && r2.info.maker==='NITTA'));
  ok('업로드(실경로): 새 규격 추가', !!r3, JSON.stringify((up1.rows||[]).map(r=>r.spec)));

  // ───────── ② 규격추가 덮어쓰기 ─────────
  const ov = await pg.evaluate(async () => {
    __T("window.__STORE['v2']=[{spec:'CCC-3',name:'옛',e:100,buy:80,sell:100,info:{maker:'SMC',src:'한국상사',remark:'메모'}}]");
    __T("quoteVendors=[{id:'v2',name:'두번째상사',count:1}]");
    __T("_qCurId='v2'");
    __T("_qRows=[{spec:'CCC-3',name:'옛',e:100,buy:80,sell:100,info:{maker:'SMC',src:'한국상사',remark:'메모'}}]");
    __T("_qOpenSpecModal('add',null)");
    document.getElementById('qsSpec').value='CCC-3';
    document.getElementById('qsName').value='새이름';
    document.getElementById('qsE').value='500';
    document.getElementById('qsBuy').value='400';
    document.getElementById('qsSell').value='500';
    document.getElementById('qsSrc').value='새구매처';     // 구매처만 새로 입력
    await __T("qsSave()");
    await new Promise(r=>setTimeout(r,500));
    return { store: window.__STORE['v2'], conf: window.__CONF||'' };
  });
  const o1 = (ov.store||[])[0] || {};
  ok('규격추가 덮어쓰기: 기존 메이커 유지', o1.info && o1.info.maker==='SMC', JSON.stringify(o1.info));
  ok('규격추가 덮어쓰기: 기존 비고 유지', o1.info && o1.info.remark==='메모');
  ok('규격추가 덮어쓰기: 새 구매처 반영', o1.info && o1.info.src==='새구매처');
  ok('규격추가 덮어쓰기: 가격 교체', o1.e===500 && o1.sell===500, JSON.stringify([o1.e,o1.sell]));
  ok('규격추가 덮어쓰기: 안내문에 설명 추가', /기존 값이 그대로/.test(ov.conf), ov.conf);

  // ───────── ③ 업체명 변경 연동 ─────────
  const rn = await pg.evaluate(() => {
    __T("quoteVendors=[{id:'v9',name:'옛상사',count:3},{id:'v8',name:'다른상사',count:1}]");
    __T("quoteSaved=[{id:'s1',vname:'옛상사',vid:'v9'},{id:'s2',vname:'다른상사',vid:'v8'}]");
    __T("_qCart=[{vid:'v9',vname:'옛상사',spec:'A',qty:1}]");
    __T("_qCartSave=function(){}");
    __T("clientOwner={m:{'옛상사':{who:'김'}},a:{'옛상사':{who:'박'},'다른상사':{who:'최'}}}");
    __T("clientPBase={'옛상사':{base:'hp'},'다른상사':{base:'sm'}}");
    __T("clientPend=[{id:'p1',name:'옛상사',status:'wait'},{id:'p2',name:'다른상사',status:'wait'}]");
    __T("renderEstimatePage=function(){}");
    var r=__T("_qRenameClientEverywhere('옛상사','새상사')");
    return {
      r:r,
      vendors: __T("JSON.parse(JSON.stringify(quoteVendors))"),
      saved: __T("JSON.parse(JSON.stringify(quoteSaved))"),
      cart: __T("JSON.parse(JSON.stringify(_qCart))"),
      owner: __T("JSON.parse(JSON.stringify(clientOwner))"),
      pbase: __T("JSON.parse(JSON.stringify(clientPBase))"),
      pend: __T("JSON.parse(JSON.stringify(clientPend))")
    };
  });
  ok('업체명 변경: quoteVendors 이름', rn.vendors[0].name==='새상사', JSON.stringify(rn.vendors));
  ok('업체명 변경: 원장 id 는 그대로', rn.vendors[0].id==='v9');
  ok('업체명 변경: 규격 개수 유지', rn.vendors[0].count===3);
  ok('업체명 변경: 저장 견적 vname', rn.saved[0].vname==='새상사');
  ok('업체명 변경: 장바구니 vname', rn.cart[0].vname==='새상사');
  ok('업체명 변경: 담당 업체(수동) 키', rn.owner.m['새상사'] && rn.owner.m['새상사'].who==='김' && rn.owner.m['옛상사']===undefined, JSON.stringify(rn.owner.m));
  ok('업체명 변경: 담당 업체(자동) 키', rn.owner.a['새상사'] && rn.owner.a['새상사'].who==='박');
  ok('업체명 변경: 업체 기준가 키', rn.pbase['새상사'] && rn.pbase['새상사'].base==='hp' && rn.pbase['옛상사']===undefined, JSON.stringify(rn.pbase));
  ok('업체명 변경: 등록 대기 이름', rn.pend[0].name==='새상사');
  ok('업체명 변경: 다른 업체는 안 건드림',
     rn.vendors[1].name==='다른상사' && rn.saved[1].vname==='다른상사' && !!rn.owner.a['다른상사'] && !!rn.pbase['다른상사'] && rn.pend[1].name==='다른상사');

  const noop = await pg.evaluate(() => {
    __T("quoteVendors=[{id:'v7',name:'그대로상사',count:1}]");
    var r=__T("_qRenameClientEverywhere('그대로상사','그대로상사')");
    return { r:r, name: __T("quoteVendors[0].name") };
  });
  ok('사업자번호만 바꾸면(이름 동일) 아무것도 안 바뀐다', noop.r.vendor===0 && noop.name==='그대로상사', JSON.stringify(noop.r));

  const note = await pg.evaluate(() => {
    __T("_qRenameNote('옛','새',{vendor:1,cart:0,saved:2,owner:1,pbase:1,pend:1})");
    __T("window.__INFO=''");
    __T("_qRenameFlush()");
    return __T("window.__INFO");
  });
  ok('안내문에 견적 쪽 변경 표시',
     /견적 거래처·원장/.test(note) && /저장 견적 2건/.test(note) && /담당 업체/.test(note) && /업체 기준가/.test(note) && /업체 등록 대기/.test(note),
     note);

  ok('pageerror 없음', errs.length === 0, errs.slice(0,2).join(' | '));
  await b.close(); return out();

  function out(){
    let p = 0;
    P.forEach(x => { if (x[1]) p++; console.log((x[1] ? '  OK  ' : '  FAIL') + '  ' + x[0] + (x[1] ? '' : '   → ' + x[2])); });
    console.log('\n[' + LABEL + '] ' + p + '/' + P.length);
    process.exit(p === P.length ? 0 : 1);
  }
})();
