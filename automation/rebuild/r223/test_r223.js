const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b223/testpage/index.html');
const dump = process.argv[3] || '';   // 워크시트 JSON 덤프 경로 (openpyxl 로 실제 xlsx 를 만들어 검증)
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  // 하니스: XLSX 대역 (encode_col/encode_cell 은 진짜 규칙, 워크북은 셀 객체 그대로 보관) + pdfMake 대역
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
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r223.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  await pg.route('**/*', r => { const u=r.request().url(); if(u.startsWith('file://')) r.continue(); else r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  const setup = () => T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'화성',phone:'010-0000-0000'}]; quoteVendors=[{id:'qv1',name:'주식회사 케이에스',count:1}]; _qCurId='qv1'; switchPage('quote');
    _qCart=[{vid:'qv1',vname:'주식회사 케이에스',spec:'LVMK205-5K',name:'VALVE',e:28390,buy:17320,sell:18830,qty:2,eta:'3~4일'},{vid:'qv1',vname:'주식회사 케이에스',spec:'KPH04-01',name:'FITTING',e:2800,buy:2100,sell:2420,qty:1},{vid:'qv1',vname:'주식회사 케이에스',spec:'OLD-999',name:'단종품',disc:'단종',qty:1}];
    _qCols=[{id:'cx1',title:'코드',pos:'name'}]; _qNego=1000; _qMemo='납기는 발주 후 확정'; _qQuoteNo='주식회사 케이에스-20261008-01'; _qLoadedId='q_t'; _qPdfFontP=Promise.resolve({normal:'a',bold:'b'}); window.__DL=[];
    var mg=document.getElementById('qManager'); if(mg){ mg.disabled=false; mg.value='홍길동'; } 'ok'`);

  console.log('▶ PDF 다운로드 → PDF + 고객용 견적서 엑셀');
  await setup();
  await T(`qDownloadPdf('p'); 'ok'`); await pg.waitForTimeout(1200);
  const dl = JSON.parse(await T(`JSON.stringify(__DL.map(function(d){ return {t:d.t,fn:d.fn,sheet:d.sheet}; }))`));
  ok(dl.length===2 && dl[0].t==='pdf' && dl[1].t==='xlsx' && dl[1].fn==='견적서 주식회사 케이에스-20261008-01.xlsx', '파일 2개: PDF + 같은 이름의 .xlsx');
  ok(dl[1].sheet==='견적서', '시트 이름 "견적서" (견적목록 아님)');
  const ws = JSON.parse(await T(`JSON.stringify(__DL[1].ws)`));
  const V = ref => (ws[ref]||{}).v, Fm = ref => (ws[ref]||{}).f;
  const all = Object.keys(ws).filter(k=>k[0]!=='!');
  const txt = all.map(k=>String(ws[k].v==null?'':ws[k].v)).join('|');
  ok(V('A1')==='견 적 서', '제목');
  ok(txt.indexOf('주식회사 케이에스 귀하')>=0 && txt.indexOf('담당자 : 홍길동님')>=0 && txt.indexOf('견적일자 : 2026. 10. 08')>=0 && txt.indexOf('견적번호 : 주식회사 케이에스-20261008-01')>=0, '받는이 블록: 귀하·담당자·견적일자·견적번호');
  ok(txt.indexOf('충해전기㈜ 화성영업소')>=0 && txt.indexOf('406-85-02616')>=0 && txt.indexOf('김재성 / 010-0000-0000')>=0, '공급자 박스(화성) + 담당자');
  // 표 머리글
  const hdrRow = all.find(k=>ws[k].v==='No'); const hr = Number(hdrRow.replace(/[A-Z]/g,''));
  const hdr = ['A','B','C','D','E','F','G','H'].map(c=>V(c+hr));
  ok(JSON.stringify(hdr)===JSON.stringify(['No','품목','코드','규격','수량','단가','금액','예상납기']), '머리글 순서(커스텀 열 "코드"는 품목 뒤): '+hdr.join('/'));
  ok(txt.indexOf('E가')<0 && txt.indexOf('구매가')<0 && txt.indexOf('마진')<0 && txt.indexOf('DC')<0, '내부 단가(E가·구매가·마진·DC) 없음');
  const r1=hr+1;
  ok(V('A'+r1)===1 && V('B'+r1)==='VALVE' && V('D'+r1)==='LVMK205-5K' && V('E'+r1)===2 && V('F'+r1)===18830 && V('H'+r1)==='3~4일', '1행 값');
  ok(Fm('G'+r1)==='IF(OR(F'+r1+'="",E'+r1+'=""),"",F'+r1+'*E'+r1+')', '금액 = 단가×수량 수식: '+Fm('G'+r1));
  ok(V('G'+(hr+3))==='단종' && !Fm('G'+(hr+3)), '단가 없는 단종 줄은 문구');
  ok(V('B'+(hr+4))==='NEGO 할인' && V('G'+(hr+4))===-1000, 'NEGO 줄 (-1,000)');
  ok(!!Fm('G'+(hr+10)) && !!Fm('G'+(hr+23)) && !ws['G'+(hr+24)], '빈 줄(23행까지)에도 금액 수식 · 24행째는 없음');
  const supRef = all.find(k=>ws[k].v==='공급가액'); const sr=Number(supRef.replace(/[A-Z]/g,''));
  ok(Fm('G'+sr)==='SUM(G'+(hr+1)+':G'+(hr+23)+')', '공급가액 = SUM(금액 전체 범위): '+Fm('H'+sr));
  ok(Fm('G'+(sr+1))==='ROUND(G'+sr+'*0.1,0)' && Fm('G'+(sr+2))==='G'+sr && Fm('G'+(sr+3))==='G'+sr+'+G'+(sr+1), '부가세·합계·부가세 포함 수식');
  const amtRef = all.find(k=>/^"견적금액/.test(ws[k].f||''));
  ok(!!amtRef && (ws[amtRef].f||'').indexOf('TEXT(G'+(sr+2))>=0, '머리 견적금액은 합계 셀 참조 수식');
  ok(txt.indexOf('· 비고 : 납기는 발주 후 확정')>=0 && txt.indexOf('유효기간은 발행일로부터 30일')>=0 && txt.indexOf('협의에 따릅니다. — 충해전기㈜ 화성영업소')>=0, '안내문 + 비고');
  ok((ws['!merges']||[]).length>10 && (ws['!cols']||[]).length===8 && !!ws['!ref'], '병합·열폭·범위 지정');
  if(dump){ fs.writeFileSync(dump, JSON.stringify(ws)); console.log('  · 워크시트 덤프:', dump); }

  console.log('▶ 일반 엑셀 버튼은 여전히 견적목록');
  await T(`window.__DL=[]; exportQuoteExcel(); 'ok'`); await pg.waitForTimeout(400);
  ok(await T(`__DL.length===1 && __DL[0].sheet==='견적목록' && /^견적목록_/.test(__DL[0].fn)`), '견적목록 시트 · 견적목록_ 파일명');
  ok(errs.length===0, 'pageerror 0'+(errs.length?(' — '+errs.join(' | ')):''));
  console.log(`\n결과: ${pass}/${pass+fail}`);
  fs.unlinkSync(tmp); await br.close(); process.exit(fail?1:0);
})();
