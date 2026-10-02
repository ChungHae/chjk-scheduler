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
    __T("showInfoModal=function(t,m){window.__i={t:t,m:m};}; showConfirmModal=function(t,m,ok){ok&&ok();};");
    __T("fxSalesInv=[]; fxPurchInv=[]; fxDeposits=[]; fxAdjusts=[]; fxOpenings={}; fxTerms={}; fxExcluded=[]; fxAlias={};");
  });

  // ① 입출금 탭이 사라졌다
  const nav=await pg.evaluate(()=>{
    __T("switchPage('fxsum')");
    return [].slice.call(document.querySelectorAll('#acctSubNav .sub-tab')).map(function(b){ return {t:(b.innerText||'').trim(), p:b.dataset.page}; });
  });
  ok('회계 하위 탭이 집계·미수현황·카드매출·자료 업로드 (입출금 없음)',
     JSON.stringify(nav.map(x=>x.t))===JSON.stringify(['집계','미수현황','카드매출','자료 업로드']), JSON.stringify(nav.map(x=>x.t)));
  ok('data-page 에 armatch 가 없다', nav.every(x=>x.p!=='armatch'), JSON.stringify(nav.map(x=>x.p)));

  // ② 마크업·함수·링크 잔재
  const left=await pg.evaluate(()=>({
    page: !!document.getElementById('pageArmatch'),
    grid: !!document.getElementById('misuSummaryGrid'),
    chart: !!document.getElementById('armChartGrid'),
    link: !!document.querySelector('a[href*="chjk-manage"]'),
    load: typeof window.loadMisuSummary,
    html: document.documentElement.innerHTML.indexOf('streamlit')
  }));
  ok('#pageArmatch 마크업이 없다', !left.page, String(left.page));
  ok('미수 요약 칸·차트 칸이 없다', !left.grid && !left.chart, JSON.stringify(left));
  ok('Streamlit 앱 링크가 없다', !left.link && left.html<0, JSON.stringify({link:left.link, idx:left.html}));
  ok('loadMisuSummary 전역이 없다', left.load==='undefined', String(left.load));

  // ③ 상단 회계 탭 → 집계
  const def=await pg.evaluate(async()=>{
    __T("switchPage('memo')");
    document.getElementById('tabAccounting').click();
    await new Promise(r=>setTimeout(r,400));
    var vis=[].slice.call(document.querySelectorAll('.page-section')).filter(function(s){ return getComputedStyle(s).display!=='none'; }).map(function(s){ return s.id; });
    var act=[].slice.call(document.querySelectorAll('#acctSubNav .sub-tab')).filter(function(b){ return b.classList.contains('active'); }).map(function(b){ return (b.innerText||'').trim(); });
    return { vis:vis, act:act, tab:__T("_fxTab") };
  });
  ok('회계 탭을 누르면 집계가 열린다', def.vis.indexOf('pageFx')>=0 && def.act[0]==='집계', JSON.stringify(def));
  ok('_fxTab 이 sum 이다', def.tab==='sum', String(def.tab));

  // ④ 나머지 회계 탭이 멀쩡히 돈다
  for(const [p,t] of [['fx','ar'],['fxup','up'],['fxsum','sum']]){
    const r=await pg.evaluate((a)=>{ __T("switchPage('"+a+"')"); return __T("_fxTab"); }, p);
    ok(p+' → _fxTab='+t, r===t, String(r));
  }
  const cs=await pg.evaluate(async()=>{ __T("switchPage('cardsales')"); await new Promise(r=>setTimeout(r,300));
    return [].slice.call(document.querySelectorAll('.page-section')).filter(function(s){ return getComputedStyle(s).display!=='none'; }).map(function(s){ return s.id; }); });
  ok('카드매출도 그대로 열린다 (_misuNote 유지)', cs.indexOf('pageCardSales')>=0, JSON.stringify(cs));
  ok('_misuNote 는 남아 있다 (카드매출이 씀)', await pg.evaluate(()=>{ try{ return typeof __T("_misuNote")==='function'; }catch(e){ return false; } }), '');

  ok('pageerror 없음', errs.length===0, errs.join(' | '));

  await b.close();
  let p=0; P.forEach(x=>{ if(x[1])p++; console.log((x[1]?'  OK  ':'  FAIL')+'  '+x[0]+(x[1]?'':'   → '+x[2])); });
  console.log('['+LABEL+'] '+p+'/'+P.length);
})();
