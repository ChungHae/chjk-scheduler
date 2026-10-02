const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b218/testpage/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  // 하니스: eval 창구 + 외부 라이브러리(XLSX·pdfMake) 대역 — 파일명·호출만 기록
  const STUB = `
  window.__DL=[];
  window._xlsxStyleReady=true;
  window.XLSX={ utils:{ aoa_to_sheet:function(a){ var ws={'!ref':'A1'}; for(var r=0;r<a.length;r++) for(var c=0;c<a[r].length;c++){ var v=a[r][c]; if(v===''||v==null) continue; ws[XLSX.utils.encode_cell({r:r,c:c})]={v:v}; } ws.__rows=a.length; return ws; },
      encode_cell:function(p){ var s=''; var n=p.c+1; while(n>0){ var m=(n-1)%26; s=String.fromCharCode(65+m)+s; n=Math.floor((n-1)/26); } return s+(p.r+1); },
      book_new:function(){ return {Sheets:{},SheetNames:[]}; }, book_append_sheet:function(wb,ws,n){ wb.Sheets[n]=ws; wb.SheetNames.push(n); } },
    writeFile:function(wb,fn){ window.__DL.push({t:'xlsx',fn:fn,rows:wb.Sheets[wb.SheetNames[0]].__rows}); } };
  window.pdfMake={ createPdf:function(dd){ return { download:function(fn){ window.__DL.push({t:'pdf',fn:fn}); }, getBlob:function(cb){ cb(new Blob(['x'])); } }; } };
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r218.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  await pg.route('**/*', r => { const u=r.request().url(); if(u.startsWith('file://')) r.continue(); else r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  const setup = () => T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; quoteVendors=[{id:'qv1',name:'주식회사 케이에스',count:1}]; _qCurId='qv1'; switchPage('quote');
    _qCart=[{vid:'qv1',vname:'주식회사 케이에스',spec:'LVMK205-5K',name:'VALVE',e:28390,buy:17320,sell:18830,qty:2},{vid:'qv1',vname:'주식회사 케이에스',spec:'KPH04-01',name:'FITTING',e:2800,buy:2100,sell:2420,qty:1}];
    _qQuoteNo='주식회사 케이에스-20261002-01'; _qLoadedId='q_t'; _qPdfFontP=Promise.resolve({normal:'a',bold:'b'}); window.__DL=[]; 'ok'`);

  console.log('▶ 엑셀 워크북 분리');
  await setup();
  ok(await T(`typeof _qBuildQuoteXlsxWb==='function' && typeof _qPrepQuoteXlsx==='function' && typeof _qSaveQuoteXlsx==='function'`), '_qBuildQuoteXlsxWb / _qPrepQuoteXlsx / _qSaveQuoteXlsx 존재');
  ok(await T(`(function(){ var wb=_qBuildQuoteXlsxWb(); var ws=wb.Sheets['견적목록']; return wb.SheetNames[0]==='견적목록' && ws.A1.v==='주식회사 케이에스-20261002-01' && ws.D3.v==='LVMK205-5K' && ws.H3.v===37660; })()`), '워크북 내용: 견적번호·규격·금액');

  console.log('▶ 일반 엑셀 버튼은 그대로 (견적목록_거래처_날짜.xlsx 하나)');
  await T(`exportQuoteExcel(); 'ok'`); await pg.waitForTimeout(400);
  ok(await T(`__DL.length===1 && __DL[0].t==='xlsx' && /^견적목록_주식회사 케이에스_\\d{8}\\.xlsx$/.test(__DL[0].fn)`), '파일 1개: '+(await T(`__DL[0]&&__DL[0].fn`)));

  console.log('▶ PDF 다운로드 → PDF + 엑셀 동시 저장 (같은 파일명)');
  await setup();
  await T(`qDownloadPdf('p'); 'ok'`); await pg.waitForTimeout(1200);
  const dl = JSON.parse(await T(`JSON.stringify(__DL)`));
  ok(dl.length===2, '파일 2개 내려감 ('+dl.map(d=>d.fn).join(' / ')+')');
  ok(dl[0] && dl[0].t==='pdf' && dl[0].fn==='견적서 주식회사 케이에스-20261002-01.pdf', 'PDF 먼저');
  ok(dl[1] && dl[1].t==='xlsx' && dl[1].fn==='견적서 주식회사 케이에스-20261002-01.xlsx' && dl[1].rows>=5, '같은 이름의 .xlsx 가 이어서 (행 '+(dl[1]&&dl[1].rows)+')');

  console.log('▶ 미리보기·저장 안내문');
  ok(await T(`(function(){ var s=document.documentElement.innerHTML; return true; })()`) && src.indexOf("PDF 와 엑셀 파일을 함께 다운로드합니다")>=0 && src.split('PDF·엑셀로 내려받았습니다').length===3, '확인창·완료 안내문에 엑셀 명시 (미리보기·qSavePdfQuote 두 곳)');
  ok(src.indexOf("_qSaveQuoteXlsx(_xwb, _fn);   // r218\n")>=0 && src.split('var _xwb=await _qPrepQuoteXlsx();').length===3, '미리보기 [저장 후 다운로드]·qDownloadPdf 두 경로 모두 엑셀 연결');

  console.log('▶ 엑셀 라이브러리 실패 시에도 PDF 는 그대로');
  await setup();
  await T(`window._xlsxStyleReady=false; window._xlsxStyleLoading=Promise.reject(new Error('no lib')); window._xlsxStyleLoading.catch(function(){}); 'ok'`);
  await T(`qDownloadPdf('l'); 'ok'`); await pg.waitForTimeout(1200);
  ok(await T(`__DL.length===1 && __DL[0].t==='pdf'`), 'PDF 만 내려가고 오류 없음');
  await T(`window._xlsxStyleReady=true; window._xlsxStyleLoading=null; 'ok'`);

  ok(errs.length===0, 'pageerror 0'+(errs.length?(' — '+errs.join(' | ')):''));
  console.log(`\n결과: ${pass}/${pass+fail}`);
  fs.unlinkSync(tmp); await br.close(); process.exit(fail?1:0);
})();
