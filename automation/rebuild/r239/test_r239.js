// r239 테스트 — ① PDF 안내문 법인명 줄 분리(화성영업소가 2페이지로 밀리지 않음, 실제 pdfmake+폰트로 페이지 수 확인)
//                ② 메일 보내기 HTML 첨부 기본 해제(PDF 만) · 본문 첨부 안내 PDF 만
//  사용:  node test_r239.js <r239 적용된 index.html>   (cdnjs·jsdelivr 네트워크 필요)
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b239/test/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
async function pdfPages(buf){
  const { PDFDocument } = require('/home/claude/.npm-global/lib/node_modules/pdf-lib');
  const doc = await PDFDocument.load(buf); return doc.getPageCount();
}
(async () => {
  const STUB = `
  window._xlsxStyleReady=true;
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r239.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  const sent=[]; let cfgStore={ url:'https://worker.test', key:'k-123', cc:'' };
  await pg.route('**/*', r => { const u=r.request().url();
    if(u.startsWith('file://') || /cdnjs\.cloudflare\.com|cdn\.jsdelivr\.net/.test(u)) return r.continue();
    if(u.indexOf('sched_mail_cfg.json')>=0) return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify(cfgStore)});
    if(u.indexOf('worker.test/send')>=0){ const b=JSON.parse(r.request().postData()); sent.push(b); return r.fulfill({status:200, contentType:'application/json', headers:{'access-control-allow-origin':'*'}, body:JSON.stringify({ok:true,id:'<x@chjk.co.kr>'})}); }
    r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  await T(`
    _fbDbUrl='https://fb.test'; _authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'화성',phone:'010-5228-2922'}];
    _fbPutOk=async function(){ return true; }; debouncedFbSave=function(){}; saveAll=function(){};
    _fbFetch=async function(url,opts){ return fetch(url,opts); };
    _nyLoadAssets=async function(){ return {}; }; _qPriceIdx={}; clientInfo={};
    _qQuoteNo='성기웅-20261019-01'; _qLoadedId='qid1'; quoteSaved=[{id:'qid1',title:'성기웅-20261019-01',vname:'충해)성기웅',count:3,total:934250,savedBy:'김재성',savedAt:Date.now()}];
    _qPersistQuote=async function(){};
    _qCart=[{spec:'MGPM20-25Z',name:'실린더',qty:5,sell:89690,vname:'충해)성기웅',info:{maker:'SMC'}},{spec:'KQ2H06-01AS',name:'피팅',qty:100,sell:990,vname:'충해)성기웅',info:{maker:'SMC'}},{spec:'AW20-02BG-A',name:'레귤레이터',qty:8,sell:48500,vname:'충해)성기웅',info:{maker:'SMC'}}]; _qNego=0; _qCols=[];
    window._qPdfOrient='p';
    'ok'`);

  console.log('▶ 1) 화성 직원 PDF — 실제 pdfmake 로 만들어 페이지 수 확인');
  const b64 = await T(`(async function(){ var b=await _qMakePdfBlob(); var ab=await b.arrayBuffer(); var u=new Uint8Array(ab), s=''; for(var i=0;i<u.length;i+=0x8000) s+=String.fromCharCode.apply(null,u.subarray(i,i+0x8000)); return btoa(s); })()`);
  const buf = Buffer.from(b64,'base64'); fs.writeFileSync('/tmp/r239_hs.pdf', buf);
  const pages = await pdfPages(buf);
  ok(buf.length>20000 && buf.slice(0,5).toString()==='%PDF-', '실제 PDF 생성 ('+buf.length+' bytes)');
  ok(pages===1, '품목 3건 세로 견적서 = 1페이지 (화성영업소 줄이 2페이지로 밀리지 않음) — pages='+pages);
  const noteTexts = await T(`(function(){ var dd=_qBuildPdfDoc({orient:'p',font:'Pretendard'}); var col=dd.content[dd.content.length-1].columns[0].stack; return col.map(function(x){ return x.text; }); })()`);
  ok(noteTexts.length===5 && noteTexts[4]==='— 충해전기㈜ 화성영업소' && noteTexts[3].indexOf('airmall24.co.kr')>=0 && noteTexts[3].indexOf('충해전기')<0, '안내문: 온라인몰 줄 + 법인명 별도 줄 (5줄) — '+JSON.stringify(noteTexts.slice(3)));

  console.log('▶ 2) 서울 직원도 1페이지');
  await T(`members[0].group='서울'; 'ok'`);
  const b64s = await T(`(async function(){ var b=await _qMakePdfBlob(); var ab=await b.arrayBuffer(); var u=new Uint8Array(ab), s=''; for(var i=0;i<u.length;i+=0x8000) s+=String.fromCharCode.apply(null,u.subarray(i,i+0x8000)); return btoa(s); })()`);
  const pagesS = await pdfPages(Buffer.from(b64s,'base64'));
  ok(pagesS===1, '서울 견적서도 1페이지 — pages='+pagesS);

  console.log('▶ 2-b) 가로 · 비고 2줄 · 담당자 있음 — 전부 1페이지');
  async function pagesOf(expr){ const b=await T(`(async function(){ ${expr}; var b=await _qMakePdfBlob(); var ab=await b.arrayBuffer(); var u=new Uint8Array(ab), s=''; for(var i=0;i<u.length;i+=0x8000) s+=String.fromCharCode.apply(null,u.subarray(i,i+0x8000)); return btoa(s); })()`); return pdfPages(Buffer.from(b,'base64')); }
  let n=await pagesOf(`members[0].group='화성'; window._qPdfOrient='l'`); ok(n===1, '화성 가로 — pages='+n);
  n=await pagesOf(`window._qPdfOrient='p'; _qMemo='납기 2주 소요\\n도면 확인 요망'`); ok(n===1, '화성 세로 + 비고 2줄 — pages='+n);
  n=await pagesOf(`window._qPdfOrient='l'`); ok(n===1, '화성 가로 + 비고 2줄 — pages='+n);
  n=await pagesOf(`window._qPdfOrient='p'; _qMemo=''; var mg=document.getElementById('qManager'); if(mg){ mg.disabled=false; mg.value='홍길동'; }`); ok(n===1, '세로 + 담당자 — pages='+n);
  n=await pagesOf(`var mg=document.getElementById('qManager'); if(mg){ mg.value=''; } _qCart=_qCart.concat(_qCart,_qCart,_qCart,_qCart,_qCart,_qCart).slice(0,21)`); ok(n===1, '세로 품목 21건(빈 행 0) — pages='+n);
  n=await pagesOf(`_qCart=_qCart.slice(0,3); window._qPdfOrient='p'`); ok(n===1, '원상 복구 3건 — pages='+n);

  console.log('▶ 3) 메일 보내기 — HTML 첨부 기본 해제');
  await T(`window.__info=[]; showInfoModal=function(t,m){ window.__info.push(t+'|'+m); }; switchPage('quote'); qOpenMailSend(); 'ok'`); await pg.waitForTimeout(600);
  ok(await T(`document.getElementById('mlAttPdf').checked && !document.getElementById('mlAttHtml').checked`), '첨부 기본: PDF ✓ · HTML ✗');
  ok(await T(`document.getElementById('mlBody').value.indexOf('· 첨부: 견적서 PDF\\n')>=0 && document.getElementById('mlBody').value.indexOf('HTML')<0`), '본문 첨부 안내 = PDF 만');
  await T(`document.getElementById('mlTo').value='test@example.com'; qMailSendNow(); 'ok'`);
  for(let i=0;i<80 && !(await T(`(window.__info||[]).some(function(x){ return x.indexOf('메일 발송 완료')>=0; })`)); i++) await pg.waitForTimeout(150);
  ok(sent.length===1 && sent[0].attachments.length===1 && /\.pdf$/.test(sent[0].attachments[0].name), '발송 요청 첨부 = PDF 1개 ('+(sent[0]&&sent[0].attachments.map(a=>a.name).join(', '))+')');
  await T(`qOpenMailSend(); 'ok'`); await pg.waitForTimeout(400);
  await T(`document.getElementById('mlAttHtml').checked=true; document.getElementById('mlTo').value='test@example.com'; window.__info=[]; qMailSendNow(); 'ok'`);
  for(let i=0;i<80 && !(await T(`(window.__info||[]).some(function(x){ return x.indexOf('메일 발송 완료')>=0; })`)); i++) await pg.waitForTimeout(150);
  ok(sent.length===2 && sent[1].attachments.length===2 && /\.html$/.test(sent[1].attachments[1].name), '체크하면 HTML 도 첨부됨 (선택은 유지)');

  ok(errs.length===0, '페이지 오류 없음'+(errs.length?(' — '+errs.slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(_e){}
  process.exit(fail?1:0);
})();
