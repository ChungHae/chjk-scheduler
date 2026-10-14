// r234 테스트 — 견적서 PDF(미리보기·pdfmake)·엑셀·HTML 안내문에 airmall24.co.kr 한 줄
//  사용:  node test_r234.js <r234 적용된 index.html>
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b233/test/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const STUB = `
  window._xlsxStyleReady=true;
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r234.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  await pg.route('**/*', r => { const u=r.request().url(); if(u.startsWith('file://')) r.continue(); else r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  await T(`
    _fbDbUrl='https://x.test'; _authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울'}];
    _fbPutOk=async function(){ return true; }; debouncedFbSave=function(){}; _qPersistQuote=async function(){};
    _nyLoadAssets=async function(){ return {}; }; _qPriceIdx={}; _qQuoteNo='T-20261014-01'; _qMemo='';
    _qCart=[{spec:'KQ2H06-01AS',name:'피팅',qty:10,sell:990,vname:'A전기',info:{maker:'SMC'}}]; _qNego=null; _qCols=[];
    // pdfmake 대역: 문서 정의만 가로챈다
    window.__doc=null; _ensurePdfMake=async function(){ return { createPdf:function(d){ window.__doc=d; return { download:function(){}, getBlob:function(cb){ cb(new Blob(['x'])); } }; } }; };
    _qPdfFontLoad=async function(){ return 'NotoSansKR'; };
    // 엑셀 대역
    window.XLSX={ utils:{ encode_col:function(n){ var s=''; n=n+1; while(n>0){ var m=(n-1)%26; s=String.fromCharCode(65+m)+s; n=Math.floor((n-1)/26); } return s; }, encode_cell:function(p){ return XLSX.utils.encode_col(p.c)+(p.r+1); }, book_new:function(){ return {SheetNames:[],Sheets:{}}; }, book_append_sheet:function(w,s,n){ w.SheetNames.push(n); w.Sheets[n]=s; } }, writeFile:function(wb,fn){ window.__wb=wb; } };
    _ensureXlsxLib=async function(){};
    'ok'`);

  console.log('▶ 엑셀');
  await T(`exportQuoteExcel(); 'ok'`); await pg.waitForTimeout(800);
  const xl = await T(`(function(){ var ws=window.__wb&&window.__wb.Sheets['견적서']; if(!ws) return ''; return Object.keys(ws).filter(function(k){return k[0]!=='!';}).map(function(k){ return ws[k].v; }).filter(function(v){ return typeof v==='string'&&v.indexOf('·')===0; }).join('\\n'); })()`);
  ok(xl.indexOf('airmall24.co.kr')>=0 && xl.indexOf('협의에 따릅니다.')>=0, '엑셀 안내문에 airmall24 줄 (\n'+xl.replace(/\n/g,' / ')+')');

  console.log('▶ PDF (pdfmake)');
  await T(`qDownloadPdf('p'); 'ok'`); await pg.waitForTimeout(1500);
  const doc = await T(`JSON.stringify(window.__doc||{})`);
  ok(doc.indexOf('airmall24.co.kr')>=0, 'pdfmake 문서에 airmall24 줄');
  ok((doc.match(/유효기간은 발행일로부터/g)||[]).length===1 && doc.indexOf('협의에 따릅니다."')>=0, '기존 안내 3줄 유지 + 분리');

  console.log('▶ PDF (미리보기 인쇄판)');
  const prevSrc = await T(`(function(){ var s=qPreviewPdf.toString()+ (typeof _qBuildPreviewHtml==='function'?_qBuildPreviewHtml.toString():''); return s; })()`);
  const fileSrc = fs.readFileSync(file,'utf8');
  ok(fileSrc.indexOf('협의에 따릅니다.<br>· 온라인몰 <b>airmall24.co.kr</b>')>=0, '미리보기 인쇄판 안내문에 airmall24 줄');

  console.log('▶ HTML 견적서');
  await T(`window.__html=null; _qBuildQuoteHtml().then(function(h){ window.__html=h; }); 'ok'`);
  for(let i=0;i<40 && !(await T(`!!window.__html`)); i++) await pg.waitForTimeout(100);
  const html = await T(`window.__html||''`);
  ok(html.indexOf('href="https://airmall24.co.kr"')>=0 && html.indexOf('온라인몰 airmall24.co.kr<br>')>=0, 'HTML 확인 사항 링크 + 꼬리말');

  ok(errs.length===0, '페이지 오류 없음'+(errs.length?(' — '+errs.slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(_e){}
  process.exit(fail?1:0);
})();
