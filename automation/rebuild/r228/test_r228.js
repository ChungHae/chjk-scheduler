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
    __T("debouncedFbSave=function(){}");
    window.__info=[]; window.__conf=[];
    __T("showInfoModal=function(t,m){ window.__info.push({t:t,m:m}); };");
    __T("showConfirmModal=function(t,m,ok,lb,cl){ window.__conf.push({t:t,m:m,lb:lb}); window.__confOk=ok; };");
    // 다운로드 추적
    window.__dl=[];
    __T("_ensureXlsxLib=async function(){ window.XLSX={ utils:{book_new:function(){return{SheetNames:[],Sheets:{}};},aoa_to_sheet:function(a){return{__aoa:a};},book_append_sheet:function(w,s,n){w.SheetNames.push(n);w.Sheets[n]=s;},encode_col:function(c){return String.fromCharCode(65+c);},encode_cell:function(o){return String.fromCharCode(65+o.c)+(o.r+1);},decode_range:function(){return{s:{r:0,c:0},e:{r:0,c:0}};}}, writeFile:function(wb,fn){ window.__dl.push(fn); } }; };");
    __T("_ensurePdfMake=async function(){ return { createPdf:function(){ return { download:function(fn){ window.__dl.push(fn); }, getBlob:function(cb){ cb(new Blob(['x'])); } }; } }; };");
    __T("_qPdfFontLoad=async function(){ return 'NotoSansKR'; };");
    __T("_qBuildPdfDoc=function(){ return {content:[]}; };");
    __T("_qPersistQuote=async function(){ return true; };");
    __T("_qResetQuoteScreen=function(){};");
    // 견적 한 줄
    __T("_qCart=[{vname:'테스트상사', name:'품목A', spec:'ABC-1', qty:2, sell:10000, unit:'EA', buy:8000}]; _qQuoteNo='TEST-20261013-01';");
    __T("_qCartHasContent=function(){ return true; }; _qEnsureQuoteNo=function(){};");
  });

  // ① qDownloadPdf → PDF 만
  const dl=await pg.evaluate(async()=>{
    window.__dl=[];
    await window.qDownloadPdf('p');
    await new Promise(r=>setTimeout(r,1200));   // r218 의 0.6초 지연보다 길게
    return window.__dl.slice();
  });
  ok('qDownloadPdf 가 PDF 하나만 내려받는다 (r228)', dl.length===1 && /\.pdf$/.test(dl[0]), JSON.stringify(dl));
  ok('받는 파일명이 견적서 <번호>.pdf', dl[0]==='견적서 TEST-20261013-01.pdf', JSON.stringify(dl));

  // ② 확인창 문구
  const cf=await pg.evaluate(async()=>{
    window.__conf=[]; window.__dl=[]; window.__info=[];
    await window.qSavePdfQuote('p');
    await new Promise(r=>setTimeout(r,200));
    var c=window.__conf[0]||{};
    if(window.__confOk) window.__confOk();
    await new Promise(r=>setTimeout(r,1400));
    return { msg:c.m||'', lb:c.lb||'', dl:window.__dl.slice(), info:window.__info.map(function(x){return x.m;}) };
  });
  ok('확인창이 "PDF 파일을 다운로드합니다"', /PDF 파일을 다운로드합니다/.test(cf.msg) && !/엑셀/.test(cf.msg), cf.msg.replace(/\n/g,'|'));
  ok('확인창 파일명 안내에 .xlsx 가 없다', /\.pdf/.test(cf.msg) && !/\.xlsx/.test(cf.msg), cf.msg.replace(/\n/g,'|'));
  ok('저장 후 다운로드도 PDF 하나만', cf.dl.length===1 && /\.pdf$/.test(cf.dl[0]), JSON.stringify(cf.dl));
  ok('완료 안내가 "PDF 로 내려받았습니다"', cf.info.some(function(m){ return /PDF 로 내려받았습니다/.test(m); }) && !cf.info.some(function(m){ return /엑셀/.test(m); }), JSON.stringify(cf.info));

  // ③ 일반 엑셀 버튼은 그대로 (견적목록 엑셀)
  const xl=await pg.evaluate(async()=>{
    window.__dl=[];
    try{ await window.exportQuoteExcel(); }catch(e){ return {err:String(e).slice(0,120)}; }
    await new Promise(r=>setTimeout(r,400));
    return { dl:window.__dl.slice() };
  });
  ok('"일반 엑셀" 버튼은 그대로 엑셀을 만든다', xl.dl && xl.dl.length===1 && /^견적목록_.*\.xlsx$/.test(xl.dl[0]), JSON.stringify(xl));

  // ④ 고객용 견적서 생성기는 남아 있다 (나중에 되살릴 수 있게)
  const keep=await pg.evaluate(()=>{
    var r={};
    ['_qBuildQuoteSheetWb','_qPrepQuoteXlsx','_qSaveQuoteXlsx','_qBuildQuoteXlsxWb'].forEach(function(n){
      try{ r[n]=typeof __T(n); }catch(e){ r[n]='none'; }
    });
    return r;
  });
  ok('_qBuildQuoteSheetWb / _qPrepQuoteXlsx / _qSaveQuoteXlsx 는 남아 있다',
     keep._qBuildQuoteSheetWb==='function' && keep._qPrepQuoteXlsx==='function' && keep._qSaveQuoteXlsx==='function', JSON.stringify(keep));

  ok('pageerror 없음', errs.length===0, errs.join(' | '));

  await b.close();
  let p=0; P.forEach(x=>{ if(x[1])p++; console.log((x[1]?'  OK  ':'  FAIL')+'  '+x[0]+(x[1]?'':'   → '+x[2])); });
  console.log('['+LABEL+'] '+p+'/'+P.length);
})();
