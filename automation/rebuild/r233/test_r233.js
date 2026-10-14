// r233 테스트 — HTML 견적서 내보내기 (도면·카탈로그 연동)
//  사용:  node test_r233.js <r233 적용된 index.html>
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
  const tmp = path.join(path.dirname(file), '_h_r233.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch({ args:['--allow-file-access-from-files'] }); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:900}, acceptDownloads:true });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  await pg.route('**/*', r => { const u=r.request().url(); if(u.startsWith('file://')) r.continue(); else r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);

  await T(`
    _fbDbUrl='https://x.test'; _authUser={id:'kjs',name:'김재성',role:'admin'}; myMemberId='m1';
    members=[{id:'m1',name:'김재성',group:'서울',phone:'010-5228-2922'}];
    _fbPutOk=async function(){ return true; }; debouncedFbSave=function(){};
    _qPersistQuote=async function(){ window.__persisted=(window.__persisted||0)+1; };
    _nyLoadAssets=async function(){ return { 'stamp_서울':{b64:'iVBORw0KGgo=',w:760,h:342}, seal:{b64:'iVBORw0KGgo=',w:240,h:240} }; };
    _qPriceIdx={ 'mgpm2025z':{spec:'MGPM20-25Z',maker:'SMC',isSMC:true}, 'pjg25n':{spec:'PJG-25-N',maker:'CONVUM'} };
    _qQuoteNo='HINTER-20261008-01';
    _qCart=[
      {spec:'MGPM20-25Z', name:'가이드 부착 박형 실린더', qty:85, sell:89690, vname:'HINTER', info:{maker:'SMC'}},
      {spec:'PJG-25-N', name:'패드', qty:10, sell:26250, vname:'HINTER'},
      {spec:'NK-100', name:'커플러', qty:2, sell:5000, vname:'HINTER', info:{maker:'NITTA MOORE'}, eta:'3일'},
      {spec:'ZZZ-1', name:'단종품', qty:1, sell:null, disc:'단종', vname:'HINTER'}
    ];
    _qNego=1000; _qCols=[{id:'c1',title:'비고',pos:'amt'}]; _qCart[0].cx={c1:'대량'};
    var mg=document.getElementById('qManager'); if(mg){ mg.disabled=false; mg.value='조영훈'; }
    'ok'`);

  console.log('▶ A) 다운로드 메뉴');
  await T(`switchPage('quote'); qOpenDownloadMenu(); 'ok'`); await pg.waitForTimeout(300);
  const menu = await T(`document.getElementById('qDlMenuOverlay').innerText`);
  ok(menu.indexOf('HTML 견적서')>=0 && menu.indexOf('일반 엑셀')>=0 && menu.indexOf('히트판 엑셀')>=0, 'HTML 견적서 버튼 + 기존 엑셀 2종 그대로');
  ok(await T(`!!document.querySelector('#qDlMenuOverlay button[onclick*="qExportHtml"]')`), 'qExportHtml 연결');
  await T(`document.getElementById('qDlMenuOverlay').style.display='none'; 'ok'`);

  console.log('▶ B) HTML 생성');
  await T(`window.__html=null; _qBuildQuoteHtml().then(function(h){ window.__html=h; }); 'ok'`);
  for(let i=0;i<40 && !(await T(`!!window.__html`)); i++) await pg.waitForTimeout(100);
  const html = await T(`window.__html||''`);
  ok(html.length>5000 && /^<!DOCTYPE html>/.test(html), 'HTML 문서 생성 ('+html.length+'자)');
  ok(html.indexOf('HINTER-20261008-01')>=0 && html.indexOf('HINTER')>=0 && html.indexOf('조영훈')>=0, '견적번호·수신·담당자');
  // 공급가액 = 89690*85 + 26250*10 + 5000*2 - 1000 = 7623650+262500+10000-1000 = 7895150
  ok(html.indexOf('7,895,150')>=0 && html.indexOf('789,515')>=0 && html.indexOf('8,684,665')>=0, '공급가액·부가세·합계 (NEGO 반영)');
  ok(html.indexOf('총 98 EA')>=0 && html.indexOf('4품목')>=0, '품목·수량 요약');
  ok(/partNumber=MGPM20-25Z/.test(html) && html.indexOf('class="mk SMC"')>=0, 'SMC → 웹카탈로그 링크 + 배지');
  ok(html.indexOf('class="qcv" data-pn="PJG-25-N"')>=0 && html.indexOf('class="mk CONVUM"')>=0 && html.indexOf('전체 카탈로그')>=0, 'CONVUM → 도면 DB 자리 + 전체 카탈로그 (가격표 메이커로 판정)');
  ok(/google\.com\/search\?q=NK-100\+NITTA/.test(html) && html.indexOf('class="mk NITTA"')>=0, '그 외 메이커 → 검색');
  ok(html.indexOf('class="dc">단종')>=0 && html.indexOf('NEGO 할인')>=0, '단종 표시 · NEGO 줄');
  ok(html.indexOf('비고 대량')>=0 && html.indexOf('예상납기')>=0 && html.indexOf('>3일<')>=0, '사용자 열 · 예상납기');
  ok(html.indexOf('data:image/png;base64,iVBORw0KGgo=')>=0 && html.indexOf('class="st"')>=0 && html.indexOf('class="sl"')>=0, '명판·인감 포함');
  ok(html.indexOf('010-5228-2922')>=0 && html.indexOf('충해전기㈜')>=0 && html.indexOf('113-81-14978')>=0, '공급자·담당 연락처');
  ok(html.indexOf('확인 사항')>=0 && html.indexOf('부가가치세 별도')>=0, '확인 사항 기본 문구');
  ok(html.indexOf('사양 해설')<0 && html.indexOf('제품 사양')<0, '사양 해설·카탈로그 발췌 없음 (품목명 한 줄만)');
  ok(html.indexOf('매입')<0 && html.indexOf('DC율')<0 && html.indexOf('E가')<0 && html.indexOf('마진')<0, '내부 단가 정보 없음');

  console.log('▶ C) 생성된 파일 동작');
  const out = path.join(path.dirname(file), '_r233_out.html'); fs.writeFileSync(out, html);
  const p2 = await ctx.newPage(); const errs2=[]; p2.on('pageerror', e => errs2.push(String(e)));
  await p2.route('**/*', r => { const u=r.request().url();
    if(u.startsWith('file://')) return r.continue();
    if(u.indexOf('/rest/v1/drawings')>=0){ return r.fulfill({status:200, contentType:'application/json', headers:{'access-control-allow-origin':'*'}, body:JSON.stringify([{model_name:'PJG-25-N',cad_2d_url:'drawings/2d/a.dwg',cad_3d_url:null,pdf_url:'https://x/p.pdf',thumbnail_url:'drawings/thumbnails/t.png'}])}); }
    if(u.indexOf('/thumbnails/')>=0){ return r.fulfill({status:200, contentType:'image/png', body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==','base64')}); }
    r.abort(); });
  await p2.goto('file://'+out); await p2.waitForTimeout(1500);
  const links = await p2.evaluate(() => [...document.querySelectorAll('.qcv a')].map(a=>a.textContent+'|'+a.href).join(' ; '));
  ok(links.indexOf('제품 PDF|https://x/p.pdf')>=0 && links.indexOf('2D|https://rjilxlopauzwzwqmdcre.supabase.co/storage/v1/object/public/drawings/2d/a.dwg')>=0, 'CONVUM 도면 DB 조회 → 제품 PDF · 2D 링크 ('+links+')');
  ok(await p2.evaluate(() => !!document.querySelector('.thumb[data-pn="PJG-25-N"] img')), 'CONVUM 썸네일 표시');
  await p2.click('.thumb[data-pn="PJG-25-N"] img'); await p2.waitForTimeout(200);
  ok(await p2.evaluate(() => getComputedStyle(document.getElementById('zm')).display==='flex'), '썸네일 클릭 → 확대');
  await p2.click('#zm'); await p2.waitForTimeout(200);
  ok(await p2.evaluate(() => getComputedStyle(document.getElementById('zm')).display==='none'), '확대 닫기');
  await p2.evaluate(() => { window.__cp=null; navigator.clipboard.writeText=function(t){ window.__cp=t; return Promise.resolve(); }; });
  await p2.click('.ql.cp[data-pn="MGPM20-25Z"]'); await p2.waitForTimeout(200);
  ok(await p2.evaluate(() => window.__cp==='MGPM20-25Z'), '[복사] → 품번 클립보드');
  ok(await p2.evaluate(() => document.querySelectorAll('table:not(.tot) tbody tr').length===5), '품목 4줄 + NEGO 1줄');
  ok(errs2.length===0, '생성 파일 오류 없음'+(errs2.length?(' — '+errs2.slice(0,2).join(' | ')):''));

  console.log('▶ D) qExportHtml 다운로드');
  const [dl] = await Promise.all([ pg.waitForEvent('download', {timeout:8000}).catch(()=>null), T(`qExportHtml(); 'ok'`) ]);
  // file:// 에서는 blob 이 다른 출처로 잡혀 Chromium 이 download 이름을 무시한다("download") — 서빙(https)에서는 이름이 붙는다. 여기서는 내용만 확인.
  let dlTxt=''; try{ dlTxt=fs.readFileSync(await dl.path(),'utf8'); }catch(_e){}
  ok(!!dl && /^<!DOCTYPE html>/.test(dlTxt) && dlTxt.indexOf('HINTER-20261008-01')>=0, 'HTML 파일 다운로드 (이름: '+(dl?dl.suggestedFilename():'없음')+')');
  await pg.waitForTimeout(600);
  ok(await T(`window.__persisted===1`), '내보내기 전 견적 자동 저장 1회');
  ok(await T(`document.body.innerText.indexOf('HTML 견적서')>=0 && document.body.innerText.indexOf('자동 저장')>=0`), '완료 안내');

  ok(errs.length===0, '페이지 오류 없음'+(errs.length?(' — '+errs.slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); fs.unlinkSync(out); }catch(_e){}
  process.exit(fail?1:0);
})();
