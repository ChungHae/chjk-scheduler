// r263 테스트 — 구매 링크가 견적 ℹ️ 와 원장관리에서 같게 보이는지
//  사용:  node test_r263.js <index.html(__T 주입본)> [라벨]
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
  const T = c => pg.evaluate(c2 => window.__T(c2), c);

  await pg.evaluate(() => {
    var g=document.getElementById('authGate'); if(g) g.style.display='none';
    __T("_authUser={id:'chjk',name:'김재성',role:'master'}");
    __T("_fbDbUrl='https://stub'");
    __T("window.__INFO=''; showInfoModal=function(t,m){ window.__INFO=(t||'')+' | '+(m||''); };");
    __T("showConfirmModal=function(t,m,okf){ okf&&okf(); };");
    __T("debouncedFbSave=function(){}; doFbSave=function(){}; saveAll=function(){};");
    __T("window.__STORE={};");
    __T("_qBlobPut=async function(id,rows){ window.__STORE[id]=JSON.parse(JSON.stringify(rows)); _qBlobCache[id]=JSON.parse(JSON.stringify(rows)); };");
    __T("_qBlobGet=async function(id){ return window.__STORE[id]?JSON.parse(JSON.stringify(window.__STORE[id])):null; };");
    __T("_ensurePriceSyncMap=async function(){}; _priceSyncMap=null;");
  });

  const has = await T("typeof _qInfoUrl==='function'");
  if(!has){
    ['헬퍼 있음','makerUrl 읽음','srcUrl 읽음','link 우선','원장 표 버튼 켜짐','원장 표 title',
     '링크 창 현재값','링크 창 안내','규격 수정 창 링크 칸','링크 비우기','검색에 링크','견적 ℹ️ 와 동일']
      .forEach(n => ok('r263 기능 없음 — ' + n, false));
    ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
    await b.close(); return out();
  }

  // ── 헬퍼 규칙 ──
  ok('헬퍼 있음', true);
  ok('link 가 있으면 link', await pg.evaluate(()=>__T("_qInfoUrl")({link:'https://a/1',makerUrl:'https://b/2',srcUrl:'https://c/3'})==='https://a/1'));
  ok('link 없으면 makerUrl', await pg.evaluate(()=>__T("_qInfoUrl")({makerUrl:'https://b/2',srcUrl:'https://c/3'})==='https://b/2'));
  ok('makerUrl 도 없으면 srcUrl', await pg.evaluate(()=>__T("_qInfoUrl")({srcUrl:'https://c/3'})==='https://c/3'));
  ok('아무것도 없으면 빈 문자열', await pg.evaluate(()=>__T("_qInfoUrl")({maker:'MISUMI'})===''));
  ok('안내문 — 메이커 칸', await pg.evaluate(()=>/메이커/.test(__T("_qInfoUrlFrom")({makerUrl:'https://b/2'}))));
  ok('안내문 — 구매처 칸', await pg.evaluate(()=>/구매처/.test(__T("_qInfoUrlFrom")({srcUrl:'https://c/3'}))));
  ok('직접 넣은 link 면 안내문 없음', await pg.evaluate(()=>__T("_qInfoUrlFrom")({link:'https://a/1',srcUrl:'https://c/3'})===''));

  // ── 사용자 보고 그대로: maker/src 는 있고 makerUrl 만 있는 행 ──
  await pg.evaluate(async () => {
    __T("quoteVendors=[{id:'v1',name:'솔브레인엘티케이 주식회사',count:2}]");
    __T("window.__STORE['v1']=[" +
        "{spec:'SGNAA-500-500-2',name:'ETC',e:186522,buy:186530,sell:211970,eta:'2~3주 예상',info:{maker:'MISUMI',src:'MISUMI',makerUrl:'https://kr.misumi-ec.com/aaa'}}," +
        "{spec:'SRC-ONLY-1',name:'테스트',e:100,buy:80,sell:100,info:{src:'한국상사',srcUrl:'https://shop.example/bbb'}}," +
        "{spec:'NOLINK-1',name:'링크없음',e:10,buy:8,sell:10,info:{maker:'SMC'}}]");
    __T("_qCurId='v1'");
    __T("_qRows=JSON.parse(JSON.stringify(window.__STORE['v1']))");
    __T("_qRows.forEach(function(r){ r._rid='q'+Math.random().toString(36).slice(2,8); })");
    __T("qOpenLedger()");
    await new Promise(r=>setTimeout(r,300));
    __T("qLedgerOpenVendor('v1')");
    await new Promise(r=>setTimeout(r,700));
  });

  const tbl = await pg.evaluate(()=>{
    return [].slice.call(document.querySelectorAll('#qlmTable tbody tr')).map(tr=>{
      var ins=[].slice.call(tr.querySelectorAll('input.qlm-in')).map(i=>i.value);
      var lk=tr.querySelector('button.b');
      return {spec:ins[0], maker:ins[9], src:ins[10], cls:lk?lk.className:'', title:lk?lk.getAttribute('title'):''};
    });
  });
  const rowA = tbl.find(r=>r.spec==='SGNAA-500-500-2')||{};
  const rowB = tbl.find(r=>r.spec==='SRC-ONLY-1')||{};
  const rowC = tbl.find(r=>r.spec==='NOLINK-1')||{};
  ok('원장 표 — 메이커 링크 행 버튼 켜짐', /\bon\b/.test(rowA.cls||''), JSON.stringify(rowA));
  ok('원장 표 — 메이커 링크가 title 에', (rowA.title||'').indexOf('misumi')>=0, rowA.title);
  ok('원장 표 — 구매처 링크 행도 켜짐', /\bon\b/.test(rowB.cls||''), JSON.stringify(rowB));
  ok('원장 표 — 링크 없는 행은 꺼짐', !/\bon\b/.test(rowC.cls||'') && (rowC.title||'')==='링크 입력', JSON.stringify(rowC));
  ok('원장 표 — 메이커·구매처 글자는 그대로', rowA.maker==='MISUMI' && rowA.src==='MISUMI', JSON.stringify([rowA.maker,rowA.src]));

  // ── 링크 창 ──
  const dlg = await pg.evaluate(async ()=>{
    var i = __T("_lmRows.findIndex(function(r){return r.spec==='SGNAA-500-500-2';})");
    __T("qLedgerLink("+i+")");
    await new Promise(r=>setTimeout(r,250));
    var ov=document.getElementById('qlmLinkOv');
    return { val:(document.getElementById('qlmLinkIn')||{}).value||'', txt: ov?ov.innerText:'' , idx:i };
  });
  ok('링크 창 — 현재값이 채워짐', dlg.val.indexOf('misumi')>=0, dlg.val);
  ok('링크 창 — 어디서 온 링크인지 안내', /메이커 칸/.test(dlg.txt), dlg.txt.slice(0,160));
  ok('링크 창 — 비우면 지운다는 안내', /비우고 저장하면/.test(dlg.txt));
  ok('링크 창 — [열기] 버튼 보임', /열기/.test(dlg.txt));

  // ── 저장하면 info.link 로 옮겨 적는다 ──
  const saved = await pg.evaluate(async ()=>{
    document.getElementById('qlmLinkIn').value='https://kr.misumi-ec.com/aaa';
    __T("qLedgerLinkSave("+__T("_lmRows.findIndex(function(r){return r.spec==='SGNAA-500-500-2';})")+")");
    await new Promise(r=>setTimeout(r,250));
    return __T("JSON.parse(JSON.stringify(_lmRows.find(function(r){return r.spec==='SGNAA-500-500-2';}).info))");
  });
  ok('저장하면 info.link 에 적힌다', saved.link==='https://kr.misumi-ec.com/aaa', JSON.stringify(saved));

  // ── 비우고 저장하면 엑셀 칸 링크까지 지운다 ──
  const cleared = await pg.evaluate(async ()=>{
    var i = __T("_lmRows.findIndex(function(r){return r.spec==='SRC-ONLY-1';})");
    __T("qLedgerLink("+i+")");
    await new Promise(r=>setTimeout(r,200));
    document.getElementById('qlmLinkIn').value='';
    __T("qLedgerLinkSave("+i+")");
    await new Promise(r=>setTimeout(r,250));
    var inf = __T("_lmRows.find(function(r){return r.spec==='SRC-ONLY-1';}).info");
    var tr = [].slice.call(document.querySelectorAll('#qlmTable tbody tr')).map(function(t){
      var ins=[].slice.call(t.querySelectorAll('input.qlm-in')).map(x=>x.value);
      var lk=t.querySelector('button.b'); return {spec:ins[0], cls:lk?lk.className:''};
    }).find(function(x){ return x.spec==='SRC-ONLY-1'; });
    return { info: inf?JSON.parse(JSON.stringify(inf)):null, cls: tr?tr.cls:'' };
  });
  ok('비우면 srcUrl 까지 지워진다', !cleared.info || (!cleared.info.link && !cleared.info.srcUrl && !cleared.info.makerUrl), JSON.stringify(cleared.info));
  ok('비우면 구매처 글자는 남는다', !!(cleared.info && cleared.info.src==='한국상사'), JSON.stringify(cleared.info));
  ok('비우면 표 버튼도 꺼진다', !/\bon\b/.test(cleared.cls||''), cleared.cls);

  // ── 원장 검색: 링크 주소로도 찾기 ──
  const found = await pg.evaluate(async ()=>{
    document.getElementById('qlmSearch').value='misumi-ec';
    __T("_lmTable()");
    await new Promise(r=>setTimeout(r,200));
    return [].slice.call(document.querySelectorAll('#qlmTable tbody tr')).map(function(t){
      var ins=[].slice.call(t.querySelectorAll('input.qlm-in')).map(x=>x.value); return ins[0];
    });
  });
  ok('검색 — 링크 주소로 찾힌다', found.indexOf('SGNAA-500-500-2')>=0, JSON.stringify(found));
  await pg.evaluate(async ()=>{ document.getElementById('qlmSearch').value=''; __T("_lmTable()"); await new Promise(r=>setTimeout(r,150)); });

  // ── 규격 수정 창의 링크 칸 ──
  const spec = await pg.evaluate(async ()=>{
    __T("window.__STORE['v2']=[{spec:'ONLY-MK',name:'x',e:1,buy:1,sell:1,info:{maker:'MISUMI',makerUrl:'https://kr.misumi-ec.com/zzz'}}]");
    __T("quoteVendors=[{id:'v2',name:'두번째',count:1}]");
    __T("_qCurId='v2'");
    __T("_qRows=[{_rid:'rid1',spec:'ONLY-MK',name:'x',e:1,buy:1,sell:1,info:{maker:'MISUMI',makerUrl:'https://kr.misumi-ec.com/zzz'}}]");
    __T("_qOpenSpecModal('edit','rid1')");
    await new Promise(r=>setTimeout(r,250));
    return (document.getElementById('qsLink')||{}).value||'';
  });
  ok('규격 수정 창 — 링크 칸에 메이커 링크가 채워진다', spec.indexOf('misumi-ec')>=0, spec);

  const specCleared = await pg.evaluate(async ()=>{
    document.getElementById('qsLink').value='';
    __T("qsSave()");
    await new Promise(r=>setTimeout(r,500));
    var r=(window.__STORE['v2']||[])[0]||{};
    return r.info?JSON.parse(JSON.stringify(r.info)):null;
  });
  ok('규격 수정 — 링크를 비우면 makerUrl 도 안 남는다', !specCleared || (!specCleared.link && !specCleared.makerUrl && !specCleared.srcUrl), JSON.stringify(specCleared));
  ok('규격 수정 — 메이커 글자는 남는다', !!(specCleared && specCleared.maker==='MISUMI'), JSON.stringify(specCleared));

  // ── 견적 ℹ️ 창과 원장이 같은 값을 쓴다 ──
  const popup = await pg.evaluate(async ()=>{
    __T("_qInfoPopup({maker:'MISUMI',src:'MISUMI',makerUrl:'https://kr.misumi-ec.com/aaa'}, 'SGNAA-500-500-2')");
    await new Promise(r=>setTimeout(r,200));
    var ov=document.getElementById('qInfoOverlay');
    var a=ov?ov.querySelector('a[target="_blank"]'):null;
    return { href: a?a.getAttribute('href'):'', txt: ov?ov.innerText:'' };
  });
  ok('견적 ℹ️ — 바로가기 주소가 같다', popup.href==='https://kr.misumi-ec.com/aaa', popup.href);
  ok('견적 ℹ️ — 브랜드·구매처 표시 그대로', /MISUMI/.test(popup.txt));

  ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
  await b.close(); return out();

  function out(){
    let p=0; P.forEach(x=>{ if(x[1]) p++; console.log((x[1]?'  OK  ':'  FAIL')+'  '+x[0]+(x[1]?'':'   → '+x[2])); });
    console.log('\n['+LABEL+'] '+p+'/'+P.length);
    process.exit(p===P.length?0:1);
  }
})();
