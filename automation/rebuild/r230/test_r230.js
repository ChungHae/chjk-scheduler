const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const FILE=process.argv[2], LABEL=process.argv[3]||'?';
(async()=>{
  const b=await chromium.launch({});
  const pg=await (await b.newContext({timezoneId:'Asia/Seoul', viewport:{width:1500,height:950}})).newPage();
  await pg.route(/^https?:\/\//, r=>r.abort());
  const errs=[]; pg.on('pageerror',e=>errs.push(String(e).slice(0,200)));
  await pg.goto('file://'+FILE); await pg.waitForTimeout(3200);
  const P=[]; const ok=(n,c,e)=>P.push([n,!!c,e===undefined?'':String(e)]);

  await pg.evaluate(()=>{
    var g=document.getElementById('authGate'); if(g) g.style.display='none';
    __T("_authUser={id:'chjk',name:'김재성',role:'master'}"); __T("_fbDbUrl='https://stub'");
    __T("_fxLoaded=true"); __T("debouncedFbSave=function(){}"); __T("_fxSave=function(){}");
    __T("_fxSaveBig=async function(){}"); __T("_fxEnsureData=async function(){}");
    __T("showInfoModal=function(t,m){}; showConfirmModal=function(t,m,ok){ok&&ok();};");
    __T("fxAdjusts=[]; fxOpenings={}; fxTerms={}; fxExcluded=[]; fxAlias={};");
    var S=[],Pu=[],D=[];
    // 매출: 서울 ~2026-09-30 (2건), 화성 ~2026-10-10 (1건)
    S.push({biz:'서울', date:'2026-09-30', vendor:'가', vbiz:'1', supply:100, tax:10, total:110});
    S.push({biz:'서울', date:'2026-08-01', vendor:'가', vbiz:'1', supply:100, tax:10, total:110});
    S.push({biz:'화성', date:'2026-10-10', vendor:'나', vbiz:'2', supply:100, tax:10, total:110});
    // 매입: 서울만
    Pu.push({biz:'서울', date:'2026-09-15', vendor:'다', vbiz:'3', supply:50, tax:5, total:55});
    // 은행: 신한 서울 2026-08-21 / 신한 화성 2026-10-01 / 국민 서울 2026-10-13
    D.push({biz:'서울', date:'2026-08-21', kind:'bank', bank:'신한', amount:1, payer:'x'});
    D.push({biz:'서울', date:'2026-07-01', kind:'bank', bank:'신한', amount:1, payer:'x'});
    D.push({biz:'화성', date:'2026-10-01', kind:'bank', bank:'신한', amount:1, payer:'x'});
    D.push({biz:'서울', date:'2026-10-13', kind:'bank', bank:'국민', amount:1, payer:'x'});
    // 어음: 신한어음 화성 2026-09-20
    D.push({biz:'화성', date:'2026-09-20', kind:'note', bank:'신한어음', amount:1, payer:'y'});
    window.__S=S; window.__P=Pu; window.__D=D;
    __T("fxSalesInv=window.__S; fxPurchInv=window.__P; fxDeposits=window.__D;");
    __T("_fxRenderUnasg=function(){};");
  });

  // 자료 업로드 탭 열기
  const t=await pg.evaluate(async()=>{
    __T("switchPage('fxup')");
    await new Promise(r=>setTimeout(r,600));
    var h=document.getElementById('fxUpStat');
    if(!h) return {no:true};
    var tbl=h.querySelector('table');
    var rows=[].slice.call(tbl?tbl.querySelectorAll('tbody tr'):[]).map(function(tr){
      var td=[].slice.call(tr.querySelectorAll('td'));
      if(td.length===1) return {grp:(td[0].innerText||'').trim()};
      return {k:(td[0].innerText||'').trim(), s:(td[1].innerText||'').replace(/\n/g,' ').trim(), hw:(td[2].innerText||'').replace(/\n/g,' ').trim()};
    });
    var ths=[].slice.call(tbl?tbl.querySelectorAll('thead th'):[]).map(function(x){return (x.innerText||'').trim();});
    return { ths:ths, rows:rows, txt:(h.innerText||''), first:(document.getElementById('fxBody').firstElementChild||{}).id };
  });
  ok('자료 업로드 탭에 #fxUpStat 이 있다', !t.no, JSON.stringify(t).slice(0,80));
  ok('업로드 카드들보다 위(맨 처음)에 있다', t.first==='fxUpStat', String(t.first));
  ok('표 머리글이 구분 · 서울 · 화성', JSON.stringify(t.ths)===JSON.stringify(['구분','서울','화성']), JSON.stringify(t.ths));
  ok('"마지막 거래일" 안내 문구', /마지막 거래일/.test(t.txt)&&/중복은 자동으로 걸러집니다/.test(t.txt), '');

  const g = (t.rows||[]).filter(r=>r.grp).map(r=>r.grp);
  const order = (t.rows||[]).map(r=>r.k||('['+r.grp+']'));
  ok('계산서는 매출 → 매입 순서',
     order.indexOf('매출 계산서')>=0 && order.indexOf('매출 계산서') < order.indexOf('매입 계산서'), JSON.stringify(order));
  ok('은행은 이름순 (국민 → 신한)', order.indexOf('국민') < order.indexOf('신한'), JSON.stringify(order));
  ok('묶음이 계산서 · 은행 입금 · 어음', JSON.stringify(g)===JSON.stringify(['계산서','은행 입금','어음']), JSON.stringify(g));

  const find = k => ((t.rows||[]).find(r=>r.k===k)||{});
  ok('매출 계산서 — 서울 2026-09-30(2건) · 화성 2026-10-10(1건)',
     /2026-09-30/.test(find('매출 계산서').s||'') && /2건/.test(find('매출 계산서').s||'')
     && /2026-10-10/.test(find('매출 계산서').hw||'') && /1건/.test(find('매출 계산서').hw||''),
     JSON.stringify(find('매출 계산서')));
  ok('매입 계산서 — 화성은 자료 없음(—)', (find('매입 계산서').hw||'')==='—', JSON.stringify(find('매입 계산서')));
  ok('신한 — 서울 2026-08-21(2건) · 화성 2026-10-01(1건)',
     /2026-08-21/.test(find('신한').s||'') && /2건/.test(find('신한').s||'') && /2026-10-01/.test(find('신한').hw||''),
     JSON.stringify(find('신한')));
  ok('국민 — 서울만 2026-10-13', /2026-10-13/.test(find('국민').s||'') && (find('국민').hw||'')==='—', JSON.stringify(find('국민')));
  ok('어음 묶음에 신한어음 — 화성 2026-09-20', /2026-09-20/.test(find('신한어음').hw||'') && (find('신한어음').s||'')==='—', JSON.stringify(find('신한어음')));
  ok('자료 없는 은행은 줄이 안 생긴다 (우리·하나 없음)', !(t.rows||[]).some(r=>r.k==='우리'||r.k==='하나'), JSON.stringify((t.rows||[]).map(r=>r.k||r.grp)));
  ok('"N일 전" 이 같이 보인다', /일 전/.test(t.txt), '');

  // 업로드 뒤 갱신: _fxMetaRefresh 가 표도 다시 그린다
  const up=await pg.evaluate(async()=>{
    window.__D.push({biz:'서울', date:'2026-10-14', kind:'bank', bank:'신한', amount:1, payer:'z'});
    __T("_fxMetaRefresh()");
    await new Promise(r=>setTimeout(r,200));
    var rows=[].slice.call(document.querySelectorAll('#fxUpStat tbody tr'));
    var tr=rows.find(function(x){ var td=x.querySelectorAll('td'); return td.length===3 && (td[0].innerText||'').trim()==='신한'; });
    return tr?(tr.querySelectorAll('td')[1].innerText||'').replace(/\n/g,' ').trim():'none';
  });
  ok('업로드 후 _fxMetaRefresh() 로 표가 갱신된다 (신한 서울 → 2026-10-14 · 3건)', /2026-10-14/.test(up)&&/3건/.test(up), up);

  // 다른 탭에서는 아무 일도 안 일어난다
  const safe=await pg.evaluate(async()=>{
    __T("switchPage('fxsum')"); await new Promise(r=>setTimeout(r,300));
    try{ __T("_fxMetaRefresh()"); return 'ok'; }catch(e){ return 'ERR '+e.message; }
  });
  ok('다른 탭에서 _fxMetaRefresh() 를 불러도 오류 없음', safe==='ok', safe);

  ok('pageerror 없음', errs.length===0, errs.join(' | '));
  await b.close();
  let p=0; P.forEach(x=>{ if(x[1])p++; console.log((x[1]?'  OK  ':'  FAIL')+'  '+x[0]+(x[1]?'':'   → '+x[2])); });
  console.log('['+LABEL+'] '+p+'/'+P.length);
})();
