const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const FILE=process.argv[2], LABEL=process.argv[3]||'?';
(async()=>{
  const b=await chromium.launch({});
  const pg=await (await b.newContext({timezoneId:'Asia/Seoul', viewport:{width:1500,height:950}})).newPage();
  await pg.route(/^https?:\/\//, r=>r.abort());
  const errs=[]; pg.on('pageerror',e=>errs.push(String(e).slice(0,200)));
  await pg.goto('file://'+FILE); await pg.waitForTimeout(3200);
  const P=[]; const ok=(n,c,e)=>P.push([n,!!c,e===undefined?'':String(e)]);

  // ── 공통 스텁 + 가짜 계산서 자료 ────────────────────────────
  await pg.evaluate(()=>{
    var g=document.getElementById('authGate'); if(g) g.style.display='none';
    __T("_authUser={id:'chjk',name:'김재성',role:'master'}"); __T("_fbDbUrl='https://stub'");
    __T("_fxLoaded=true"); __T("debouncedFbSave=function(){}"); __T("_fxSave=function(){}");
    __T("_fxSaveBig=async function(){}"); __T("_fxEnsureData=async function(){}");
    __T("showInfoModal=function(t,m){window.__i={t:t,m:m};}; showConfirmModal=function(t,m,ok){ok&&ok();};");
    __T("fxDeposits=[]; fxAdjusts=[]; fxOpenings={}; fxTerms={}; fxExcluded=[]; fxAlias={};");
    // 매출: 26곳 (금액 내림차순이 되도록), 매입: 4곳. 전년(2025)도 일부.
    var S=[], Pu=[];
    for(var i=1;i<=26;i++){
      var amt=(27-i)*3000000;             // 1위 78,000,000 … 26위 3,000,000
      var nc=(i===1?3:1), one=amt/nc;
      for(var c=0;c<nc;c++) S.push({biz:'화성', date:'2026-03-0'+((c%9)+1), vendor:'매출업체'+i, vbiz:'1'+String(100+i)+'-81-'+String(10000+i), supply:one, tax:0, total:one});
    }
    // 전년: 1위는 절반(=▲100%), 2위는 2배(=▼50%), 3위는 없음(=신규)
    Pu.push({biz:'화성', date:'2026-05-01', vendor:'매입업체A', vbiz:'201-81-00001', supply:0, tax:0, total:7000000});
    Pu.push({biz:'화성', date:'2026-05-02', vendor:'매입업체B', vbiz:'202-81-00002', supply:0, tax:0, total:3000000});
    S.push({biz:'화성', date:'2025-03-01', vendor:'매출업체1', vbiz:'1101-81-10001', supply:0, tax:0, total:39000000});
    S.push({biz:'화성', date:'2025-03-01', vendor:'매출업체2', vbiz:'1102-81-10002', supply:0, tax:0, total:150000000});
    window.__S=S; window.__P=Pu;
    __T("fxSalesInv=window.__S; fxPurchInv=window.__P;");
    __T("_fxRegion='화성'; _fxSumYear='2026'; _fxSumMode='vendor'; _fxSumQ='';");
  });

  // ① 모드 전환 함수 존재
  const fns=await pg.evaluate(()=>({ more:typeof window.fxSumRankMore, mode:typeof window.fxSumMode }));
  ok('fxSumRankMore 전역 함수가 있다 (r219)', fns.more==='function', fns.more);
  ok('fxSumMode 는 그대로 있다', fns.mode==='function', fns.mode);

  // 집계 탭을 그려서 거래처별 모드 렌더
  const view=await pg.evaluate(()=>{
    __T("switchPage('fxsum')");
    var h=document.getElementById('fxSumBody');
    if(!h){ h=document.createElement('div'); h.id='fxSumBody'; document.body.appendChild(h); }
    __T("_fxSumMode='vendor'; _fxRkTopS=20; _fxRkTopP=20; _fxRenderSumBody();");
    var host=document.getElementById('fxSumBody');
    var txt=host.innerText||'';
    var tables=host.querySelectorAll('table');
    var ths=[].slice.call(tables[0]?tables[0].querySelectorAll('thead th'):[]).map(function(t){return (t.innerText||'').trim();});
    var r1=[].slice.call(tables[0]?tables[0].querySelectorAll('tbody tr'):[]);
    var firstRow=r1[0]?[].slice.call(r1[0].querySelectorAll('td')).map(function(t){return (t.innerText||'').trim();}):[];
    var secondRow=r1[1]?[].slice.call(r1[1].querySelectorAll('td')).map(function(t){return (t.innerText||'').trim();}):[];
    var grid=host.firstElementChild;
    var gcs=grid?getComputedStyle(grid):null;
    return { txt:txt, nTables:tables.length, ths:ths, firstRow:firstRow, secondRow:secondRow,
             nRows:r1.length, display:gcs?gcs.display:'', cols:gcs?gcs.gridTemplateColumns:'',
             bars:host.querySelectorAll('div[style*="height:3px"]').length,
             btns:[].slice.call(host.querySelectorAll('button')).map(function(x){return (x.innerText||'').trim();}) };
  });
  ok('매출 순위 / 매입 순위 두 표가 나온다', view.nTables===2 && /매출 순위/.test(view.txt) && /매입 순위/.test(view.txt), view.nTables+' '+view.txt.slice(0,40).replace(/\n/g,'|'));
  ok('좌우 2열 그리드로 배치된다', view.display==='grid' && view.cols.split(' ').filter(function(w){ return parseFloat(w)>0; }).length===2, view.display+' / '+view.cols);
  ok('표 머리글이 순위·거래처·건·합계·비중·전년', JSON.stringify(view.ths)===JSON.stringify(['순위','거래처','건','합계','비중','전년']), JSON.stringify(view.ths));
  ok('1위가 금액 1등(78,000,000)이고 순위 숫자가 1', view.firstRow[0]==='1' && view.firstRow[3]==='78,000,000', JSON.stringify(view.firstRow));
  ok('2위가 75,000,000 으로 내림차순', view.secondRow[0]==='2' && view.secondRow[3]==='75,000,000', JSON.stringify(view.secondRow));
  ok('비중 % 가 표시된다 (1위 7.4%)', view.firstRow[4]==='7.4%', JSON.stringify(view.firstRow));
  ok('비중 막대가 행마다 그려진다', view.bars>=20, String(view.bars));

  // ② 전년 대비 증감
  const dlt=await pg.evaluate(()=>{
    var rows=[].slice.call(document.querySelectorAll('#fxSumBody table')[0].querySelectorAll('tbody tr'));
    var g=function(i){ var td=rows[i].querySelectorAll('td'); return td.length>5?(td[5].innerText||'').trim():''; };
    return { r1:g(0), r2:g(1), r3:g(2) };
  });
  ok('전년 절반이었던 1위는 ▲100.0%', dlt.r1==='▲100.0%', dlt.r1);
  ok('전년 2배였던 2위는 ▼50.0%', dlt.r2==='▼50.0%', dlt.r2);
  ok('전년 자료가 없는 곳은 "신규"', dlt.r3==='신규', dlt.r3);

  // ③ TOP 20 + 더보기
  const top=await pg.evaluate(()=>{
    var t=document.querySelectorAll('#fxSumBody table')[0];
    var rows=[].slice.call(t.querySelectorAll('tbody tr'));
    var ranks=rows.map(function(r){ return (r.querySelector('td')?r.querySelector('td').innerText:'').trim(); }).filter(function(x){ return /^\d+$/.test(x); });
    var btn=[].slice.call(t.querySelectorAll('button')).map(function(b){ return (b.innerText||'').trim(); });
    return { last:ranks[ranks.length-1], n:ranks.length, btn:btn, txt:(t.innerText||'') };
  });
  ok('기본은 TOP 20 까지만 (20행)', top.n===20 && top.last==='20', top.n+' / '+top.last);
  ok('[전체 26곳 보기] 버튼이 있다', top.btn.some(function(b){ return /전체 26곳 보기/.test(b); }), JSON.stringify(top.btn));
  ok('상위 20곳 누적 비중 안내가 있다', /상위 20곳 = 전체의/.test(top.txt), top.txt.slice(0,30));
  ok('합계 (26곳) 줄이 있다', /합계 \(26곳\)/.test(top.txt), '');

  const exp=await pg.evaluate(()=>{
    try{ __T("fxSumRankMore('s')"); }catch(_e){ return {n:-1,last:'',btn:[],err:String(_e)}; }
    var t=document.querySelectorAll('#fxSumBody table')[0];
    var ranks=[].slice.call(t.querySelectorAll('tbody tr')).map(function(r){ return (r.querySelector('td')?r.querySelector('td').innerText:'').trim(); }).filter(function(x){ return /^\d+$/.test(x); });
    var btn=[].slice.call(t.querySelectorAll('button')).map(function(b){ return (b.innerText||'').trim(); });
    return { n:ranks.length, last:ranks[ranks.length-1], btn:btn };
  });
  ok('[전체 보기] 를 누르면 26곳 전부 나온다', exp.n===26 && exp.last==='26', exp.n+' / '+exp.last);
  ok('펼친 뒤에는 [TOP 20만 보기] 로 바뀐다', exp.btn.some(function(b){ return /TOP 20만 보기/.test(b); }), JSON.stringify(exp.btn));

  const back=await pg.evaluate(()=>{
    try{ __T("fxSumRankMore('s')"); }catch(_e){ return -1; }
    var t=document.querySelectorAll('#fxSumBody table')[0];
    return [].slice.call(t.querySelectorAll('tbody tr')).map(function(r){ return (r.querySelector('td')?r.querySelector('td').innerText:'').trim(); }).filter(function(x){ return /^\d+$/.test(x); }).length;
  });
  ok('다시 누르면 TOP 20 으로 돌아온다', back===20, String(back));

  // ④ 매입 표는 따로 접힌다 (4곳뿐이라 더보기 없음) + 매입 순위 내용
  const pur=await pg.evaluate(()=>{
    var t=document.querySelectorAll('#fxSumBody table')[1];
    var rows=[].slice.call(t.querySelectorAll('tbody tr'));
    var f=[].slice.call(rows[0].querySelectorAll('td')).map(function(x){return (x.innerText||'').trim();});
    return { f:f, nbtn:t.querySelectorAll('button').length, txt:(t.innerText||'') };
  });
  ok('매입 1위는 매입업체A 7,000,000 (70.0%)', pur.f[3]==='7,000,000' && pur.f[4]==='70.0%', JSON.stringify(pur.f));
  ok('매입은 2곳뿐이라 더보기 버튼이 없다', pur.nbtn===0, String(pur.nbtn));
  ok('매입 합계 (2곳) 줄이 있다', /합계 \(2곳\)/.test(pur.txt), '');

  // ⑤ 검색이 순위표에도 적용된다
  const srch=await pg.evaluate(()=>{
    __T("_fxSumQ='매출업체1'; _fxRenderSumBody();");
    var t=document.querySelectorAll('#fxSumBody table')[0];
    var names=[].slice.call(t.querySelectorAll('tbody tr')).map(function(r){ var td=r.querySelectorAll('td'); return td.length>1?(td[1].innerText||'').trim():''; });
    __T("_fxSumQ=''; _fxRenderSumBody();");
    return names.filter(function(n){ return /매출업체/.test(n); }).length;
  });
  ok('거래처 검색이 순위표에도 걸린다 (매출업체1,10~19 = 11곳)', srch===11, String(srch));

  // ⑥ 월별 모드는 그대로
  const mon=await pg.evaluate(()=>{
    __T("_fxSumMode='month'; _fxRenderSumBody();");
    var txt=document.getElementById('fxSumBody').innerText||'';
    __T("_fxSumMode='vendor'; _fxRenderSumBody();");
    return { m:/1월/.test(txt)&&/공급가액/.test(txt), rk:/매출 순위/.test(txt) };
  });
  ok('월별 모드는 그대로 월 표가 나온다', mon.m && !mon.rk, JSON.stringify(mon));

  // ⑦ 엑셀 내보내기가 두 시트로 만들어진다
  const xls=await pg.evaluate(async()=>{
    window.__wb=null;
    __T("_ensureXlsxLib=async function(){ window.XLSX={ utils:{ book_new:function(){return {SheetNames:[],Sheets:{}};}, aoa_to_sheet:function(a){return {__aoa:a, '!ref':'A1:A1'};}, book_append_sheet:function(wb,ws,nm){wb.SheetNames.push(nm); wb.Sheets[nm]=ws;}, decode_range:function(){return {s:{r:0,c:0},e:{r:0,c:0}};}, encode_cell:function(){return 'A1';} }, writeFile:function(wb,fn){ window.__wb={wb:wb, fn:fn}; } }; };");
    __T("_fxXlsStyle=function(){};");
    await __T("fxSumXls()");
    await new Promise(r=>setTimeout(r,300));
    if(!window.__wb) return {err:'no wb'};
    var wb=window.__wb.wb;
    var s=wb.Sheets[wb.SheetNames[0]].__aoa;
    return { names:wb.SheetNames, fn:window.__wb.fn, head:s[0], row1:s[1] };
  });
  ok('엑셀이 매출 순위 / 매입 순위 두 시트로 나온다', JSON.stringify(xls.names)===JSON.stringify(['매출 순위','매입 순위']), JSON.stringify(xls.names||xls.err));
  ok('엑셀 파일명이 거래처순위', /거래처순위/.test(String(xls.fn||'')), String(xls.fn));
  ok('엑셀 머리글에 순위·비중·증감이 들어간다',
     Array.isArray(xls.head) && xls.head[0]==='순위' && xls.head.indexOf('비중(%)')>=0 && xls.head.indexOf('증감(%)')>=0, JSON.stringify(xls.head));
  ok('엑셀 1행이 1위 78,000,000 · 비중 7.4 · 증감 100',
     Array.isArray(xls.row1) && xls.row1[0]===1 && xls.row1[4]===78000000 && xls.row1[5]===7.4 && xls.row1[7]===100, JSON.stringify(xls.row1));

  ok('pageerror 없음', errs.length===0, errs.join(' | '));

  await b.close();
  let p=0; P.forEach(x=>{ if(x[1])p++; console.log((x[1]?'  OK  ':'  FAIL')+'  '+x[0]+(x[1]?'':'   → '+x[2])); });
  console.log('['+LABEL+'] '+p+'/'+P.length);
})();
