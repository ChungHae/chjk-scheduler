const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs=require('fs'), path=require('path');
const file = path.resolve(process.argv[2]); const LABEL=process.argv[3]||'?';
let pass=0, fail=0;
function ok(c,msg){ if(c){pass++;console.log('  ✓',msg);} else {fail++;console.log('  ✗',msg);} }
(async()=>{
  // r223 과 같은 XLSX 대역 (수식·셀 보존)
  const STUB = `
  window.__DL=[]; window._xlsxStyleReady=true;
  window.XLSX={ utils:{
      encode_col:function(n){ var s=''; n=n+1; while(n>0){ var m=(n-1)%26; s=String.fromCharCode(65+m)+s; n=Math.floor((n-1)/26); } return s; },
      encode_cell:function(p){ return XLSX.utils.encode_col(p.c)+(p.r+1); },
      aoa_to_sheet:function(a){ var ws={}; for(var r=0;r<a.length;r++) for(var c=0;c<a[r].length;c++){ var v=a[r][c]; if(v===''||v==null) continue; ws[XLSX.utils.encode_cell({r:r,c:c})]={v:v}; } ws.__rows=a.length; return ws; },
      book_new:function(){ return {Sheets:{},SheetNames:[]}; }, book_append_sheet:function(wb,ws,n){ wb.Sheets[n]=ws; wb.SheetNames.push(n); } },
    writeFile:function(wb,fn){ window.__DL.push({t:'xlsx',fn:fn,sheet:wb.SheetNames[0],ws:wb.Sheets[wb.SheetNames[0]]}); } };
  window.pdfMake={ createPdf:function(dd){ return { download:function(fn){ window.__DL.push({t:'pdf',fn:fn}); }, getBlob:function(cb){ cb(new Blob(['x'])); } }; } };
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join('/tmp/h', '_h_r229.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const pg = await (await br.newContext({timezoneId:'Asia/Seoul', viewport:{width:1500,height:900}})).newPage();
  const errs=[]; pg.on('pageerror', e=>errs.push(String(e).slice(0,160)));
  await pg.route('**/*', r => { const u=r.request().url(); if(u.startsWith('file://')) r.continue(); else r.abort(); });
  await pg.goto('file://'+tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(()=>{ var g=document.getElementById('authGate'); if(g) g.style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);

  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'화성',phone:'010-0000-0000'}]; quoteVendors=[{id:'qv1',name:'주식회사 케이에스',count:1}]; _qCurId='qv1'; switchPage('quote');
    _qCart=[{vid:'qv1',vname:'주식회사 케이에스',spec:'LVMK205-5K',name:'VALVE',e:28390,buy:17320,sell:18830,qty:2,eta:'3~4일'},{vid:'qv1',vname:'주식회사 케이에스',spec:'KPH04-01',name:'FITTING',e:2800,buy:2100,sell:2420,qty:1}];
    _qCols=[]; _qNego=0; _qMemo=''; _qQuoteNo='주식회사 케이에스-20261013-01'; _qLoadedId='q_t';
    _qPersistQuote=async function(){ return true; }; _qCartHasContent=function(){ return true; };
    var mg=document.getElementById('qManager'); if(mg){ mg.disabled=false; mg.value='홍길동'; } window.__DL=[]; 'ok'`);

  console.log('▶ [일반 엑셀] = 고객용 견적서 양식 (r229)');
  await T(`exportQuoteExcel(); 'ok'`); await pg.waitForTimeout(900);
  const dl = JSON.parse(await T(`JSON.stringify(__DL.map(function(d){return {t:d.t,fn:d.fn,sheet:d.sheet};}))`));
  ok(dl.length===1 && dl[0].t==='xlsx', '엑셀 파일 하나');
  ok(dl.length===1 && dl[0].sheet==='견적서', '시트 이름 "견적서" (견적목록 아님): '+(dl[0]||{}).sheet);
  ok(dl.length===1 && dl[0].fn==='견적서 주식회사 케이에스-20261013-01.xlsx', 'PDF 와 같은 파일명 견적서 <번호>.xlsx: '+(dl[0]||{}).fn);
  ok(dl.length===1 && !/^견적목록_/.test(dl[0].fn), '옛 "견적목록_업체_날짜" 파일명이 아니다');

  const ws = JSON.parse(await T(`JSON.stringify(__DL[0].ws)`));
  const V = r => (ws[r]||{}).v, Fm = r => (ws[r]||{}).f;
  const all = Object.keys(ws).filter(k=>k[0]!=='!');
  const txt = all.map(k=>String(ws[k].v==null?'':ws[k].v)).join('|');
  ok(V('A1')==='견 적 서', '제목 "견 적 서"');
  ok(txt.indexOf('주식회사 케이에스 귀하')>=0 && txt.indexOf('견적번호 : 주식회사 케이에스-20261013-01')>=0, '받는이 블록(귀하·견적번호)');
  ok(txt.indexOf('충해전기㈜ 화성영업소')>=0 && txt.indexOf('406-85-02616')>=0, '공급자 박스');
  ok(txt.indexOf('E가')<0 && txt.indexOf('구매가')<0 && txt.indexOf('마진')<0 && txt.indexOf('DC')<0, '내부 단가(E가·구매가·마진·DC) 없음');
  const hdrRow = all.find(k=>ws[k].v==='No'); const hr = Number(String(hdrRow).replace(/[A-Z]/g,''));
  ok(!!hdrRow && V('B'+hr)==='품목' && V('C'+hr)==='규격' && V('D'+hr)==='수량' && V('E'+hr)==='단가' && V('F'+hr)==='금액', '품목표 머리글');
  ok(!!Fm('F'+(hr+1)) && /IF\(OR\(/.test(Fm('F'+(hr+1))), '금액이 수식: '+Fm('F'+(hr+1)));
  const supRef = all.find(k=>ws[k].v==='공급가액'); const sr = Number(String(supRef).replace(/[A-Z]/g,''));
  ok(!!supRef && /^SUM\(/.test(Fm('F'+sr)||''), '공급가액이 SUM 수식: '+Fm('F'+sr));

  console.log('▶ 옛 견적목록 생성기는 사라졌다');
  const gone = await T(`(function(){ try{ return typeof _qBuildQuoteXlsxWb; }catch(e){ return 'none'; } })()`);
  ok(gone==='undefined' || gone==='none', '_qBuildQuoteXlsxWb 없음: '+gone);
  const keep = await T(`JSON.stringify({sheet:typeof _qBuildQuoteSheetWb, hit:typeof window.qExportHitpan, exp:typeof window.exportQuoteExcel})`);
  ok(/"sheet":"function"/.test(keep) && /"hit":"function"/.test(keep) && /"exp":"function"/.test(keep), '견적서 생성기·히트판·일반 엑셀 함수는 그대로: '+keep);

  console.log('▶ PDF 다운로드는 여전히 PDF 만 (r228)');
  await T(`window.__DL=[]; _ensurePdfMake=async function(){ return window.pdfMake; }; _qPdfFontLoad=async function(){ return 'f'; }; _qBuildPdfDoc=function(){ return {content:[]}; }; _qEnsureQuoteNo=function(){}; qDownloadPdf('p'); 'ok'`);
  await pg.waitForTimeout(1200);
  const dl2 = JSON.parse(await T(`JSON.stringify(__DL.map(function(d){return d.t;}))`));
  ok(dl2.length===1 && dl2[0]==='pdf', 'PDF 하나만: '+JSON.stringify(dl2));

  ok(errs.length===0, 'pageerror 0'+(errs.length?(' — '+errs.join(' | ')):''));
  console.log(`\n[${LABEL}] ${pass}/${pass+fail}`);
  fs.unlinkSync(tmp); await br.close(); process.exit(fail?1:0);
})();
