// r282 테스트 — 감사: 소카테고리 · 저장된 명세표(현재 화면/검색/쪽넘김/내역/삭제) · 미리보기 양식
//  사용:  node test_r282.js <index.html(__T 주입본)> [라벨]
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
    __T("window.__CONF=''; showConfirmModal=function(t,m,f){ window.__CONF=(t||'')+' | '+(m||''); window.__CONFOK=f; };");
    __T("_fbDbUrl='https://stub';");
    __T("_asCfgLoaded=true; _asPos=Object.assign({},_AS_POS0); _asMap={};");
    __T("quoteVendors=[{id:'v1',name:'하나코리아 주식회사',count:412},{id:'v2',name:'하나정밀(주)',count:87}]");
    __T("clientList=[['하나코리아 주식회사','357-87-03525','서울'],['하나정밀(주)','123-45-67890','서울'],['다른회사','999-99-99999','서울']]");
    // 저장된 명세표 46건 — 날짜가 뒤섞여 있고 업체 두 곳
    window.__DOCS = (function(){
      var o={};
      for(var i=0;i<46;i++){
        var mon = (i%12)+1, day = ((i*5)%27)+1;
        mon = (mon<10?'0'+mon:''+mon);
        var id='as'+i;
        o[id]={ id:id, no:(i%29)+1, date:'2026-'+mon+'-'+(day<10?'0'+day:day), ship:'2026'+mon+'01',
          vid:(i%2)?'v1':'v2', vname:(i%2)?'하나코리아 주식회사':'하나정밀(주)',
          biz:'357-87-03525', ceo:'윤석봉', addr:'서울', memo:(i===0?'메모시험':''),
          rows:[{spec:'P-'+i, name:(i%3?'CYLINDER':'VALVE'), qty:2, price:1000+i, supply:2*(1000+i), tax:Math.round(2*(1000+i)*0.1)}],
          supply:2*(1000+i), tax:Math.round(2*(1000+i)*0.1), total:Math.round(2*(1000+i)*1.1),
          by:'김재성', at:1700000000000+i, upd:1700000000000+i };
      }
      return o;
    })();
    window.__DEL = [];
    __T("_fbFetch=async function(u,o){ if(o&&o.method==='DELETE'){ window.__DEL.push(String(u)); return {ok:true,status:200,json:async function(){return null;}}; } if(/_audit_stmt\\.json/.test(String(u))) return {ok:true,status:200,json:async function(){ return window.__DOCS; }}; return {ok:true,status:200,json:async function(){ return null; }}; };");
    __T("_fbPutOk=async function(){ return true; };");
    __T("switchPage('audit')");
  });
  await pg.waitForTimeout(700);

  const has = await pg.evaluate(()=>typeof window.asTab==='function');
  if(!has){
    ['소카테고리','엑셀 올리기 위치','현재 화면 목록','정렬','쪽넘김','업체 검색','기간 검색','품목 검색 잠금','내역','삭제','미리보기 양식']
      .forEach(n => ok('r282 기능 없음 — ' + n, false));
    ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
    await b.close(); return out();
  }

  // ── ① 소카테고리 ──
  const sub = await pg.evaluate(()=>{
    var t=Array.prototype.map.call(document.querySelectorAll('#pageAudit .as-subtab'), e=>e.textContent.trim());
    var bar=document.querySelector('#pageAudit .inv-toolbar');
    return { tabs:t, on:(document.querySelector('#pageAudit .as-subtab.on')||{}).textContent,
             label:!!document.querySelector('#pageAudit .inv-flat-label'),
             barTxt:bar?bar.textContent.replace(/\s+/g,' ').trim():'' };
  });
  ok('소카테고리 두 개가 있다', sub.tabs.length===2 && sub.tabs[0]==='명세표 만들기' && sub.tabs[1]==='저장된 명세표', JSON.stringify(sub.tabs));
  ok('처음에는 [명세표 만들기] 가 켜져 있다', (sub.on||'').trim()==='명세표 만들기', sub.on);
  ok("툴바의 '감사' 글자를 없앴다", !sub.label && !/^감사/.test(sub.barTxt), sub.barTxt.slice(0,40));
  ok('[저장된 명세표] 단추는 사라졌다', !/저장된 명세표/.test(sub.barTxt.replace('저장된 명세표','',1).replace('명세표 만들기','')) , sub.barTxt.slice(0,60));

  // ── ② 엑셀 올리기가 드래그 칸 안 ──
  const drop = await pg.evaluate(()=>{
    var d=document.getElementById('asDrop'); if(!d) return null;
    var btns=Array.prototype.filter.call(d.querySelectorAll('button,a,.btn'), e=>/엑셀 올리기/.test(e.textContent));
    var out=Array.prototype.filter.call(document.querySelectorAll('#pageAudit .inv-toolbar button, #pageAudit .inv-toolbar a'), e=>/엑셀 올리기/.test(e.textContent));
    return { inside:btns.length, outside:out.length };
  });
  ok('[엑셀 올리기] 가 드래그 칸 안에 있다', drop && drop.inside===1, drop?JSON.stringify(drop):'(asDrop 없음)');
  ok('툴바에는 [엑셀 올리기] 가 없다', drop && drop.outside===0, drop?drop.outside:'');

  // ── ③ 저장된 명세표: 현재 화면 ──
  await pg.evaluate(()=>__T("asTab('list')")); await pg.waitForTimeout(900);
  ok('팝업창을 띄우지 않는다', await pg.evaluate(()=>{
    var ov=document.getElementById('asListOv'); return !ov || getComputedStyle(ov).display==='none'; }));
  const L = () => pg.evaluate(()=>{
    var rows=Array.prototype.slice.call(document.querySelectorAll('#pageAudit .as-lrow'));
    return { n:rows.length, dates:rows.map(r=>(r.innerText.match(/\d{4}-\d{2}-\d{2}/)||[''])[0]),   // r283 ▸ 표시 · r285 체크칸
             total:(document.getElementById('pageAudit').innerText.match(/모두 (\d+)건/)||[])[1],
             cur:((document.querySelector('#pageAudit b[style*="background:#1B3A6B"]')||{}).textContent||''),   // r290: 지금 쪽 강조
             nums:[].slice.call(document.querySelectorAll('#pageAudit button')).map(function(e){return e.textContent.trim();}).filter(function(t){return /^\d+$/.test(t);}) };
  });
  let l1 = await L();
  ok('목록이 현재 화면에 그려진다', l1.n>0 && l1.total==='46', JSON.stringify({n:l1.n,total:l1.total}));
  ok('한 쪽에 15건까지', l1.n===15, l1.n);   // r289: 20 → 15
  const minD = await pg.evaluate(()=>Object.keys(window.__DOCS).map(k=>window.__DOCS[k].date).sort()[0]);
  ok('과거 → 현재 순으로 나온다',
     l1.dates.slice().sort().join(',')===l1.dates.join(',') && l1.dates[0]===minD,
     l1.dates.slice(0,4).join(' / ')+'  (가장 과거 '+minD+')');
  ok('첫 쪽이 1 로 강조된다', l1.cur==='1' && l1.nums.length>0, JSON.stringify({cur:l1.cur,nums:l1.nums}));   // r289·r290

  await pg.evaluate(()=>__T("asLGo(1)")); await pg.waitForTimeout(400);
  let l2 = await L();
  ok('[다음] 으로 둘째 쪽', l2.n===15 && l2.cur==='2' && l2.dates[0]>=l1.dates[14], l2.cur+' / '+l2.dates[0]+' >= '+l1.dates[14]);
  await pg.evaluate(()=>__T("asLGo(3)")); await pg.waitForTimeout(400);
  ok('마지막 쪽은 1건', (await L()).n===1);
  await pg.evaluate(()=>__T("asLGo(0)")); await pg.waitForTimeout(400);

  // ── ④ 업체 검색 ──
  ok('업체 검색칸이 견적과 같은 q-flat',
     await pg.evaluate(()=>{ var i=document.getElementById('asLV'); return !!i && i.classList.contains('q-flat'); }));
  await pg.fill('#asLV','하나정밀'); await pg.waitForTimeout(350);
  const dd = await pg.evaluate(()=>{ var d=document.getElementById('asLVdd');
    return { shown:getComputedStyle(d).display!=='none', n:d.querySelectorAll('.asvd-item').length, html:d.innerHTML }; });
  ok('업체 검색 목록이 뜬다', dd.shown && dd.n===1 && /하나정밀/.test(dd.html), 'n='+dd.n);
  await pg.evaluate(()=>document.querySelectorAll('#asLVdd .asvd-item')[0].click());
  await pg.waitForTimeout(500);
  let l3 = await L();
  ok('업체를 고르면 그 업체만 걸러진다', l3.total==='23', l3.total);

  // ── ⑤ 기간 검색 ──
  await pg.evaluate(()=>{ __T("asLSet('from','2026-07-01')"); });
  await pg.waitForTimeout(350);
  await pg.evaluate(()=>{ __T("asLSet('to','2026-07-31')"); });
  await pg.waitForTimeout(400);
  let l4 = await L();
  ok('기간으로 걸러진다', +l4.total>0 && +l4.total<23 && l4.dates.every(d=>d>='2026-07-01'&&d<='2026-07-31'),   // 7월만
     JSON.stringify({t:l4.total,d:l4.dates.slice(0,3)}));

  // ── ⑥ 품목·규격 검색은 업체+기간 뒤에 열린다 ──
  ok('지금은 품목 검색칸이 열려 있다', await pg.evaluate(()=>{
    var e=document.getElementById('asLQ'); return !!e && !e.disabled; }));
  await pg.evaluate(()=>__T("asLSet('vname','')")); await pg.waitForTimeout(400);
  ok('업체를 비우면 품목 검색칸이 잠긴다', await pg.evaluate(()=>{
    var e=document.getElementById('asLQ'); return !!e && e.disabled; }));
  ok('잠겼을 때 안내글이 보인다', await pg.evaluate(()=>
    /업체와 기간을 먼저 정하세요/.test((document.getElementById('asLQ')||{}).placeholder||'')));
  await pg.evaluate(()=>{ __T("asLSet('vname','하나정밀(주)')"); }); await pg.waitForTimeout(400);
  const spec = await pg.evaluate(()=>{
    var r=document.querySelector('#pageAudit .as-lrow'); return r?r.children[0].textContent.trim():''; });
  const pick = await pg.evaluate(()=>{
    var ids=Object.keys(window.__DOCS).map(k=>window.__DOCS[k]).filter(v=>v.vname==='하나정밀(주)' && v.date>='2026-07-01' && v.date<='2026-07-31');
    return ids.length?ids[0].rows[0].spec:''; });
  await pg.evaluate(s=>__T("asLSet('q','"+s+"')"), pick); await pg.waitForTimeout(450);
  let l5 = await L();
  ok('품번으로 검색된다', l5.total==='1' && pick, JSON.stringify({q:pick,t:l5.total}));
  await pg.evaluate(()=>__T("asLSet('q','없는품번ZZZ')")); await pg.waitForTimeout(400);
  ok('없는 품번이면 0건', /조건에 맞는 거래명세표가 없습니다/.test(await pg.evaluate(()=>document.getElementById('pageAudit').innerText)));
  await pg.evaluate(()=>__T("asLClear()")); await pg.waitForTimeout(450);
  ok('[지우기] 로 조건이 풀린다', (await L()).total==='46');

  // ── ⑦ 내역 확인 (r283: 줄 아무 곳이나 눌러 펼친다) ──
  await pg.evaluate(()=>{ document.querySelector('#pageAudit .as-lrow').children[2].click(); });
  await pg.waitForTimeout(450);
  const det = await pg.evaluate(()=>{
    var t=document.querySelectorAll('#pageAudit table').length;
    var inner=document.querySelectorAll('#pageAudit table table, #pageAudit .as-lrow + tr table').length;
    var txt=document.getElementById('pageAudit').innerText;
    return { tables:t, inner:inner, head:/규격/.test(txt),
             mark:/▾/.test(document.querySelector('#pageAudit .as-lrow').innerText) };
  });
  ok('줄을 누르면 품목이 펼쳐진다', det.head && det.mark && det.inner>0, JSON.stringify(det));
  await pg.evaluate(()=>{ document.querySelector('#pageAudit .as-lrow').children[2].click(); });
  await pg.waitForTimeout(400);
  ok('다시 누르면 닫힌다', await pg.evaluate(()=>!document.querySelector('#pageAudit table table')));

  // ── ⑧ 삭제 ──
  await pg.evaluate(()=>{ var r=document.querySelector('#pageAudit .as-lrow');
    Array.prototype.filter.call(r.querySelectorAll('button'), e=>/삭제/.test(e.textContent))[0].click(); });
  await pg.waitForTimeout(300);
  ok('삭제는 먼저 물어본다(native confirm 아님)',
     await pg.evaluate(()=>/거래명세표 삭제/.test(window.__CONF||'') && /되돌릴 수 없습니다/.test(window.__CONF||'')),
     await pg.evaluate(()=>String(window.__CONF).slice(0,80)));
  await pg.evaluate(async ()=>{ await window.__CONFOK(); }); await pg.waitForTimeout(600);
  const del = await pg.evaluate(()=>({ n:window.__DEL.length, u:window.__DEL[0]||'',
    total:(document.getElementById('pageAudit').innerText.match(/모두 (\d+)건/)||[])[1] }));
  ok('확인하면 DELETE 로 지운다', del.n===1 && /_audit_stmt\/as\w+\.json/.test(del.u), JSON.stringify(del));
  ok('지운 뒤 목록에서 빠진다', del.total==='45', del.total);

  // ── ⑨ 다시 인쇄 ──
  await pg.evaluate(()=>{ window.__PRN=''; __T("_asPrintHtml=function(h){ window.__PRN=h; };"); });
  await pg.evaluate(()=>{ var r=document.querySelector('#pageAudit .as-lrow');
    Array.prototype.filter.call(r.querySelectorAll('button'), e=>/인쇄/.test(e.textContent))[0].click(); });
  await pg.waitForTimeout(400);
  const prn = await pg.evaluate(()=>({ len:(window.__PRN||'').length, slip:/as-slip/.test(window.__PRN||''),
    form:/<svg/.test(window.__PRN||''), grid:/class="as-slip as-grid"/.test(window.__PRN||'') }));
  ok('[인쇄] 은 글자만 — 양식을 그리지 않는다', prn.len>500 && prn.slip && !prn.form && !prn.grid, JSON.stringify(prn));

  // ── ⑩ 미리보기에는 양식까지 ──
  const prev = await pg.evaluate(()=>{
    function mk(n){ var r=[]; for(var i=1;i<=n;i++) r.push({spec:'P-'+i,name:'CYLINDER',qty:1,price:1000,supply:1000,tax:100}); return r; }
    var dr={ vid:'v1', vname:'하나코리아 주식회사', biz:'357-87-03525', ceo:'윤석봉', addr:'서울',
             docs:[{ship:'20261106',date:'2026-11-10',warn:'',no:9,rows:mk(13),memo:''}] };
    window.__PV = __T("_asDocHtml")(dr, dr.docs, 'form');
    window.__PR = __T("_asDocHtml")(dr, dr.docs, false);
    window.__CA = __T("_asDocHtml")(dr, dr.docs, true);
    return { pvForm:/class="as-form"/.test(window.__PV), pvSvg:(window.__PV.match(/<svg/g)||[]).length,
             pvTitle:/거 래 명 세 서/.test(window.__PV), pvSeal:/인감|㊞ *소/.test(''),
             prForm:/class="as-form"/.test(window.__PR), prSvg:/<svg/.test(window.__PR),
             caGrid:/class="as-slip as-grid"/.test(window.__CA), caForm:/<svg/.test(window.__CA) };
  });
  ok('미리보기에 양식이 그려진다', prev.pvForm && prev.pvTitle && prev.pvSvg===2, JSON.stringify(prev));
  ok('인쇄본에는 양식이 없다', !prev.prForm && !prev.prSvg);
  ok('[인쇄 보정] 시험 인쇄는 옛 점선만 — 양식 없음', prev.caGrid && !prev.caForm, JSON.stringify({g:prev.caGrid,f:prev.caForm}));

  // ── ⑪ 긴 한글 금액이 (₩…) 와 겹치지 않는다 ──
  const amt = await pg.evaluate(()=>{
    function slip(total){
      var rows=[{spec:'X',name:'Y',qty:1,price:total/1.1,supply:Math.round(total/1.1),tax:total-Math.round(total/1.1)}];
      var dr={ vid:'v1', vname:'가', biz:'1', ceo:'나', addr:'다' };
      var h=__T("_asDocHtml")(dr, [{ship:'20261101',date:'2026-11-03',no:3,rows:rows,memo:''}], false);
      var d=document.createElement('div'); d.innerHTML=h.replace(/^[\s\S]*<body>/,'').replace('</body></html>','');
      var fs=Array.prototype.slice.call(d.querySelectorAll('.as-f'));
      var ko=fs.filter(e=>/整$/.test(e.textContent))[0], nm=fs.filter(e=>/^\(₩/.test(e.textContent))[0];
      if(!ko||!nm) return null;
      var kx=parseFloat((ko.style.left||'0').replace('mm',''));
      var nx=parseFloat((nm.style.left||'0').replace('mm',''));
      var fsz=parseFloat(ko.style.fontSize);
      return { ko:ko.textContent, kx:kx, nx:nx, fs:fsz, end:kx+ko.textContent.length*fsz*0.3528 };
    }
    return { short:slip(1811007), long:slip(1237537), huge:slip(987654321) };
  });
  // r293: 총금액 한글+숫자가 한 칸(cTot)의 한 세트가 됐다 — (₩…) 는 한글 뒤를 따라 움직인다
  const tp = await pg.evaluate(()=>{ var p=__T("_AS_POS0");
    return { s:(p.sclX||1), o:(p.offX||0), tk:(p.cTot||p.cTotKo)[0] }; });
  ok('짧은 금액은 양식 자리 그대로', amt && Math.abs(amt.short.kx-(tp.tk*tp.s+tp.o))<0.02,
     amt?JSON.stringify(amt.short)+' 기대 '+(tp.tk*tp.s+tp.o).toFixed(3):'');
  ok('긴 금액도 (₩…) 와 겹치지 않는다',
     amt && amt.long.end <= amt.long.nx+0.2 && amt.huge.end <= amt.huge.nx+0.2,
     amt?JSON.stringify({l:amt.long,h:amt.huge}):'');
  ok('한글이 길수록 (₩…) 가 오른쪽으로 밀린다', amt && amt.huge.nx > amt.short.nx,
     amt?JSON.stringify([amt.short.nx, amt.huge.nx]):'');

  // ── 재고가 업무 소카테고리로 ──
  const inv = await pg.evaluate(()=>{
    var top=Array.prototype.map.call(document.querySelectorAll('.page-nav .page-tab'), e=>e.textContent.trim());
    var sub=Array.prototype.map.call(document.querySelectorAll('#etcSubNav .sub-tab'), e=>e.textContent.trim());
    __T("switchPage('inventory')");
    return { top:top, sub:sub,
      etcOn:document.getElementById('tabEtc').classList.contains('active'),
      navShown:getComputedStyle(document.getElementById('etcSubNav')).display!=='none',
      pageOn:document.getElementById('pageInventory').classList.contains('active'),
      subOn:(document.querySelector('#etcSubNav .sub-tab.active')||{}).textContent };
  });
  ok('상단 탭에서 [재고] 가 빠졌다', inv.top.indexOf('재고')<0, inv.top.join(' '));
  ok('업무 소카테고리가 사이트·매입처·재고·감사 순',
     inv.sub.join(',')==='사이트,매입처,재고,감사', inv.sub.join(','));
  ok('재고를 열면 업무 탭이 켜지고 소카테고리가 보인다', inv.etcOn && inv.navShown && inv.pageOn,
     JSON.stringify({e:inv.etcOn,n:inv.navShown,p:inv.pageOn}));
  ok('소카테고리에서 [재고] 가 켜진다', (inv.subOn||'').trim()==='재고', inv.subOn);
  await pg.evaluate(()=>__T("switchPage('audit')")); await pg.waitForTimeout(500);

  // ── ⑫ 탭 왕복 ──
  await pg.evaluate(()=>__T("asTab('new')")); await pg.waitForTimeout(400);
  ok('[명세표 만들기] 로 돌아오면 드래그 칸이 보인다',
     await pg.evaluate(()=>!!document.getElementById('asDrop') && !document.getElementById('asLV')));
  ok('옛 asOpenList() 는 소카테고리로 넘어간다', await (async()=>{
     await pg.evaluate(()=>__T("asOpenList()")); await pg.waitForTimeout(500);
     return await pg.evaluate(()=>!!document.getElementById('asLV')); })());

  ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
  await b.close(); return out();

  function out(){
    let p=0; P.forEach(x=>{ if(x[1]) p++; console.log((x[1]?'  OK  ':'  FAIL')+'  '+x[0]+(x[1]?'':'   → '+x[2])); });
    console.log('\n['+LABEL+'] '+p+'/'+P.length);
    process.exit(p===P.length?0:1);
  }
})();
