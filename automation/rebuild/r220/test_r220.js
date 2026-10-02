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
    __T("fxDeposits=[]; fxAdjusts=[]; fxOpenings={}; fxTerms={}; fxExcluded=[]; fxAlias={};");
    // 2024: 매출 1000/매입 800 (마진 20%), 2025: 매출 500/매입 500 (0%), 2026: 매출 2000/매입 1600 (20%)
    var S=[],Pu=[];
    function mk(y,mm,v,vn){ return {biz:'화성', date:y+'-'+mm+'-10', vendor:vn, vbiz:'111-81-11111', supply:v, tax:Math.round(v/10), total:v+Math.round(v/10)}; }
    S.push(mk('2024','03',1000000,'가업체')); Pu.push(mk('2024','03',800000,'나업체'));
    S.push(mk('2025','05',500000,'가업체'));  Pu.push(mk('2025','05',500000,'나업체'));
    S.push(mk('2026','01',1200000,'가업체')); Pu.push(mk('2026','01',1000000,'나업체'));
    S.push(mk('2026','02',800000,'가업체'));  Pu.push(mk('2026','02',600000,'나업체'));
    window.__S=S; window.__P=Pu;
    __T("fxSalesInv=window.__S; fxPurchInv=window.__P;");
    __T("_fxRegion='화성'; _fxSumYear='2026'; _fxSumMode='month';");
  });

  // ① 툴바에 연도별 버튼
  const tb=await pg.evaluate(()=>{
    __T("switchPage('fxsum')");
    var h=document.getElementById('fxSumBody');
    if(!h){ h=document.createElement('div'); h.id='fxSumBody'; document.body.appendChild(h); }
    return [].slice.call(document.querySelectorAll('#fxSumModeBtns .pf-btn')).map(function(b){ return {t:(b.innerText||'').trim(), m:b.dataset.m}; });
  });
  ok('모드 버튼이 월별 · 연도별 · 거래처별 (r220)',
     JSON.stringify(tb.map(x=>x.t))===JSON.stringify(['월별','연도별','거래처별']), JSON.stringify(tb.map(x=>x.t)));
  ok('data-m 도 month · year · vendor',
     JSON.stringify(tb.map(x=>x.m))===JSON.stringify(['month','year','vendor']), JSON.stringify(tb.map(x=>x.m)));

  // ② 월별에 마진율 열
  const mon=await pg.evaluate(()=>{
    __T("_fxSumMode='month'; _fxSumYear='2026'; _fxRenderSumBody();");
    var t=document.querySelector('#fxSumBody table');
    var ths=[].slice.call(t.querySelectorAll('thead th')).map(function(x){ return (x.innerText||'').trim(); });
    var rows=[].slice.call(t.querySelectorAll('tbody tr'));
    var jan=[].slice.call(rows[0].querySelectorAll('td')).map(function(x){ return (x.innerText||'').trim(); });
    var sum=[].slice.call(rows[rows.length-1].querySelectorAll('td')).map(function(x){ return (x.innerText||'').trim(); });
    return { ths:ths, jan:jan, sum:sum, note:(document.getElementById('fxSumBody').innerText||'') };
  });
  ok('월별 머리글에 마진율이 있다', mon.ths.indexOf('마진율')>=0, JSON.stringify(mon.ths));
  ok('1월 마진율 16.7% ((1,200,000-1,000,000)/1,200,000)', mon.jan[mon.jan.length-1]==='16.7%', JSON.stringify(mon.jan));
  ok('월별 합계 마진율 20.0% ((2,000,000-1,600,000)/2,000,000)', mon.sum[mon.sum.length-1]==='20.0%', JSON.stringify(mon.sum));
  ok('마진율 산식 안내가 있다', /마진율 = \(매출 공급가액 − 매입 공급가액\)/.test(mon.note), '');

  // ③ 연도별 모드
  const yr=await pg.evaluate(()=>{
    __T("_fxSumMode='year'; _fxRenderSumBody();");
    var host=document.getElementById('fxSumBody');
    var t=host.querySelector('table');
    var ths=[].slice.call(t.querySelectorAll('thead th')).map(function(x){ return (x.innerText||'').trim(); });
    var rows=[].slice.call(t.querySelectorAll('tbody tr')).map(function(r){ return [].slice.call(r.querySelectorAll('td')).map(function(x){ return (x.innerText||'').trim(); }); });
    var ysel=document.getElementById('fxSumYearSel');
    var bars=host.querySelectorAll('div[title^="매출 "], div[title^="매입 "]');
    return { ths:ths, rows:rows, hidden:ysel?ysel.style.display:'?', nbar:bars.length, txt:(host.innerText||'') };
  });
  ok('연도별 머리글에 매출총이익·마진율이 있다', yr.ths.indexOf('매출총이익')>=0 && yr.ths.indexOf('마진율')>=0, JSON.stringify(yr.ths));
  ok('연도가 최신순 (2026 → 2025 → 2024)',
     yr.rows.length>=3 && (yr.rows[0]||[])[0]==='2026년' && (yr.rows[1]||[])[0]==='2025년' && (yr.rows[2]||[])[0]==='2024년',
     JSON.stringify(yr.rows.map(r=>r[0])));
  ok('2026년 매출총이익 400,000 · 마진율 20.0%',
     (yr.rows[0]||[])[7]==='400,000' && (yr.rows[0]||[])[8]==='20.0%', JSON.stringify(yr.rows[0]));
  ok('2025년은 이익 0 · 마진율 0.0%', (yr.rows[1]||[])[7]==='0' && (yr.rows[1]||[])[8]==='0.0%', JSON.stringify(yr.rows[1]));
  ok('2024년 매출총이익 200,000 · 마진율 20.0%', (yr.rows[2]||[])[7]==='200,000' && (yr.rows[2]||[])[8]==='20.0%', JSON.stringify(yr.rows[2]));
  ok('합계 줄 이익 600,000 · 마진율 17.1%',
     yr.rows[3] && (yr.rows[3]||[])[0]==='합계' && (yr.rows[3]||[])[7]==='600,000' && (yr.rows[3]||[])[8]==='17.1%', JSON.stringify(yr.rows[3]));
  ok('연도별에서는 연도 선택이 숨겨진다', yr.hidden==='none', yr.hidden);
  ok('추이 막대가 연도 수 × 2 (3년 → 6개)', yr.nbar===6, String(yr.nbar));
  ok('추이 제목·범례가 있다', /연도별 매출·매입 추이/.test(yr.txt) && /공급가액 기준/.test(yr.txt), '');

  // ④ 모드 전환 후 연도 선택이 다시 보인다
  const back=await pg.evaluate(()=>{
    __T("_fxSumMode='month'; _fxRenderSumBody();");
    var y1=document.getElementById('fxSumYearSel').style.display;
    __T("_fxSumMode='vendor'; _fxRenderSumBody();");
    var y2=document.getElementById('fxSumYearSel').style.display;
    var rk=/매출 순위/.test(document.getElementById('fxSumBody').innerText||'');
    return { y1:y1, y2:y2, rk:rk };
  });
  ok('월별로 돌아오면 연도 선택이 다시 보인다', back.y1==='', back.y1);
  ok('거래처별(r219 순위표)도 그대로 동작', back.y2==='' && back.rk, JSON.stringify(back));

  // ⑤ 엑셀 — 연도별 시트
  const xls=await pg.evaluate(async()=>{
    window.__wb=null;
    __T("_ensureXlsxLib=async function(){ window.XLSX={ utils:{ book_new:function(){return {SheetNames:[],Sheets:{}};}, aoa_to_sheet:function(a){return {__aoa:a, '!ref':'A1:A1'};}, book_append_sheet:function(wb,ws,nm){wb.SheetNames.push(nm); wb.Sheets[nm]=ws;}, decode_range:function(){return {s:{r:0,c:0},e:{r:0,c:0}};}, encode_cell:function(){return 'A1';} }, writeFile:function(wb,fn){ window.__wb={wb:wb, fn:fn}; } }; };");
    __T("_fxXlsStyle=function(){};");
    __T("_fxSumMode='year';");
    await __T("fxSumXls()"); await new Promise(r=>setTimeout(r,250));
    var a=window.__wb;
    window.__wb=null;
    __T("_fxSumMode='month';");
    await __T("fxSumXls()"); await new Promise(r=>setTimeout(r,250));
    var b=window.__wb;
    return { yName:a&&a.wb.SheetNames, yFn:a&&a.fn, yHead:a&&a.wb.Sheets[a.wb.SheetNames[0]].__aoa[0], yRow:a&&a.wb.Sheets[a.wb.SheetNames[0]].__aoa[1],
             mHead:b&&b.wb.Sheets[b.wb.SheetNames[0]].__aoa[0], mRow:b&&b.wb.Sheets[b.wb.SheetNames[0]].__aoa[1] };
  });
  ok('엑셀 연도별 시트가 만들어진다', JSON.stringify(xls.yName)===JSON.stringify(['연도별']) && /연도별/.test(String(xls.yFn)), JSON.stringify(xls.yName)+' '+xls.yFn);
  ok('연도별 시트 머리글에 매출총이익·마진율(%)',
     Array.isArray(xls.yHead) && xls.yHead.indexOf('매출총이익')>=0 && xls.yHead.indexOf('마진율(%)')>=0, JSON.stringify(xls.yHead));
  ok('연도별 1행 2026년 이익 400000 · 마진 20',
     Array.isArray(xls.yRow) && xls.yRow[0]==='2026년' && xls.yRow[7]===400000 && xls.yRow[8]===20, JSON.stringify(xls.yRow));
  ok('월별 시트에도 마진율(%) 열', Array.isArray(xls.mHead) && xls.mHead[10]==='마진율(%)', JSON.stringify(xls.mHead));
  ok('월별 1월 마진율 16.7', Array.isArray(xls.mRow) && xls.mRow[10]===16.7, JSON.stringify(xls.mRow));

  ok('pageerror 없음', errs.length===0, errs.join(' | '));

  await b.close();
  let p=0; P.forEach(x=>{ if(x[1])p++; console.log((x[1]?'  OK  ':'  FAIL')+'  '+x[0]+(x[1]?'':'   → '+x[2])); });
  console.log('['+LABEL+'] '+p+'/'+P.length);
})();
