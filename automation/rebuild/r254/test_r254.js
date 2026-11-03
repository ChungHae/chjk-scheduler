// r254 테스트 — 회계 > 자료 검색 (입금자명·거래처명 → 내역과 처리 결과)
//  사용:  node test_r254.js <r254 적용된 index.html> [라벨]
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const FILE = process.argv[2], LABEL = process.argv[3] || '?';
let pass = 0, fail = 0;
const P = [];
const ok = (n, c, e) => P.push([n, !!c, e === undefined ? '' : String(e)]);
(async () => {
  const b = await chromium.launch({});
  const pg = await (await b.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:950} })).newPage();
  await pg.route(/^https?:\/\//, r => r.abort());
  const errs = []; pg.on('pageerror', e => errs.push(String(e).slice(0, 200)));
  await pg.goto('file://' + FILE); await pg.waitForTimeout(3200);
  const T = c => pg.evaluate(c2 => window.__T(c2), c);

  await pg.evaluate(() => {
    var g = document.getElementById('authGate'); if(g) g.style.display = 'none';
    __T("_authUser={id:'chjk',name:'김재성',role:'master'}"); __T("_fbDbUrl='https://stub'");
    __T("_fxLoaded=true"); __T("debouncedFbSave=function(){}"); __T("_fxSave=function(){}");
    __T("_fxSaveBig=async function(){}"); __T("_fxEnsureData=async function(){}");
    __T("showInfoModal=function(){}; showConfirmModal=function(t,m,ok){ok&&ok();};");
    __T("fxAdjusts=[]; fxOpenings={}; fxTerms={}; fxExcluded=[]; fxAlias={}; _fxRenderUnasg=function(){};");
    var NOW = Date.now();
    var D = [
      // 홍길동 — 배정 2건(○○상사 1 · △△테크 1) · 제외 1 · 보류 1 · 미배정 1
      { id:'d1', biz:'서울', date:'2026-10-13', kind:'bank', bank:'신한', amount:1200000, payer:'홍길동',
        vendor:'(주)○○상사', asgAt:NOW-3600000, asgBy:'함현식' },
      { id:'d2', biz:'서울', date:'2026-09-30', kind:'bank', bank:'국민', amount:350000, payer:'홍길동',
        vendor:'△△테크' },
      { id:'d3', biz:'서울', date:'2026-08-21', kind:'bank', bank:'하나', amount:5000, payer:'홍길동',
        excluded:true, exAt:NOW-86400000 },
      { id:'d4', biz:'서울', date:'2026-07-01', kind:'bank', bank:'기업', amount:70000, payer:'홍길동',
        held:true, heldAt:NOW-7200000 },
      { id:'d5', biz:'서울', date:'2026-06-02', kind:'bank', bank:'우리', amount:9000, payer:'홍길동' },
      // 사업장 이동 배정 (서울 계좌 → 화성 거래처)
      { id:'d6', biz:'화성', obiz:'서울', date:'2026-05-02', kind:'bank', bank:'기업', amount:30114981,
        payer:'유일에너테크(주)', vendor:'주식회사 성원에너텍' },
      // 어음
      { id:'d7', biz:'화성', date:'2026-04-01', kind:'note', bank:'신한어음', amount:4300000,
        payer:'신진엠텍', vendor:'신진엠텍' },
      // 비슷한 이름 후보용
      { id:'d8', biz:'서울', date:'2026-03-03', kind:'bank', bank:'신한', amount:1000, payer:'홍길순' }
    ];
    window.__D = D;
    __T("fxSalesInv=[]; fxPurchInv=[]; fxDeposits=window.__D; _fxCacheBump++;");
  });

  console.log('▶ 1) 탭·진입');
  ok('회계 하위탭에 [자료 검색] 이 있다', await T(`!!document.querySelector('.sub-tab[data-page="fxfind"]')`));
  // 적용 전 빌드에는 기능이 없다 — 던지지 말고 FAIL 로 보고한다
  const hasFeature = await T(`typeof window.fxFindInput==='function' && typeof _ffBuild==='function'`);
  if(!hasFeature){
    ['진입 _fxTab','검색칸','pageFx 재사용','안내문','5건 찾기','요약 건수·합계','요약 배정 분포','요약 제외·보류·미배정',
     '최신순','거래처명 표시','배정 시각·사람','제외 표시','제외 시각','보류','미배정','은행·금액·입금자',
     '거래처명 검색','표기 차이 무시','사업장 이동','공백 무시','어음 구분','없음 안내','출금 안내',
     '비슷한 이름','후보 클릭','속도 1차','속도 2차','200건 제한','더보기','더보기 사라짐','asgAt 보존','다른 탭 유지']
      .forEach(n => ok('r254 기능 없음 — ' + n, false));
    ok('pageerror 없음', errs.length === 0, errs.slice(0,2).join(' | '));
    await b.close();
    let p0 = 0; P.forEach(x => { if(x[1]) p0++; console.log((x[1] ? '  OK  ' : '  FAIL') + '  ' + x[0] + (x[1] ? '' : '   → ' + x[2])); });
    console.log('[' + LABEL + '] ' + p0 + '/' + P.length); return;
  }

  const entered = await pg.evaluate(async () => {
    window.__T("switchPage('fxfind')");
    await new Promise(r => setTimeout(r, 700));
    return { tab: window.__T('_fxTab'), hasInput: !!document.getElementById('fxFindInput'),
             pageActive: (document.getElementById('pageFx') || {}).className || '' };
  });
  ok('진입하면 _fxTab 이 find', entered.tab === 'find', entered.tab);
  ok('검색칸이 생긴다', entered.hasInput);
  ok('기존 회계 화면(pageFx)을 그대로 쓴다', /active/.test(entered.pageActive), entered.pageActive);
  const empty = await T(`document.getElementById('fxFindBody').innerText`);
  ok('처음에는 안내문', /찾을 이름을 입력/.test(String(empty)) && /출금 내역은 아직/.test(String(empty)), String(empty).slice(0, 60));

  console.log('▶ 2) 이름으로 찾기 — 요약과 처리 결과');
  const r1 = await pg.evaluate(async () => {
    window.__T("fxFindInput('홍길동')");
    await new Promise(r => setTimeout(r, 400));
    var h = document.getElementById('fxFindBody');
    return { txt: (h.innerText || '').replace(/\s+/g, ' '),
             rows: h.querySelectorAll('tbody tr').length,
             cells: [].slice.call(h.querySelectorAll('tbody tr')).map(tr => [].slice.call(tr.children).map(td => (td.innerText || '').trim())) };
  });
  ok('5건을 찾는다', r1.rows === 5, r1.rows);
  ok('요약에 건수와 합계', /홍길동 — 5건 · 합계 1,634,000원/.test(r1.txt), r1.txt.slice(0, 90));
  ok('요약에 배정 분포', /배정 2건\(\(주\)○○상사 1 · △△테크 1\)/.test(r1.txt), r1.txt.slice(0, 160));
  ok('요약에 제외·보류·미배정 건수', /제외 1건/.test(r1.txt) && /보류 1건/.test(r1.txt) && /미배정 1건/.test(r1.txt), r1.txt.slice(0, 200));
  ok('최신 거래일이 맨 위', r1.cells[0][0] === '2026.10.13', JSON.stringify(r1.cells[0]));
  ok('배정된 건은 거래처명이 처리 칸에', r1.cells[0][5] === '(주)○○상사', JSON.stringify(r1.cells[0]));
  ok('배정 시각·사람이 보인다', /배정 .*함현식/.test(r1.cells[0][6]), r1.cells[0][6]);
  const ex = r1.cells.find(c => c[0] === '2026.08.21') || [];
  ok('제외된 건은 "제외" 로 표시', ex[5] === '제외', JSON.stringify(ex));
  ok('제외 시각도 보인다', /제외 \d{4}\.\d{2}\.\d{2}/.test(ex[6] || ''), ex[6]);
  const hd = r1.cells.find(c => c[0] === '2026.07.01') || [];
  ok('보류 건은 "보류"', hd[5] === '보류', JSON.stringify(hd));
  const un = r1.cells.find(c => c[0] === '2026.06.02') || [];
  ok('아무것도 안 된 건은 "미배정"', un[5] === '미배정', JSON.stringify(un));
  ok('은행·금액·입금자가 같이 나온다', /입금 · 신한/.test(r1.cells[0][1]) && /1,200,000/.test(r1.cells[0][3]) && r1.cells[0][4] === '홍길동', JSON.stringify(r1.cells[0]));

  console.log('▶ 3) 배정된 거래처명으로도 찾는다 · 표기 차이 무시');
  const r2 = await pg.evaluate(async () => {
    window.__T("fxFindInput('성원에너텍')"); await new Promise(r => setTimeout(r, 400));
    var h = document.getElementById('fxFindBody');
    return { rows: h.querySelectorAll('tbody tr').length, txt: (h.innerText || '').replace(/\s+/g, ' '),
             cells: [].slice.call(h.querySelectorAll('tbody tr')[0].children).map(td => (td.innerText || '').trim()) };
  });
  ok('거래처명으로 찾으면 그 입금이 나온다', r2.rows === 1, r2.rows);
  ok('"주식회사" 를 빼고 쳐도 찾는다', /성원에너텍/.test(r2.cells[5]), JSON.stringify(r2.cells));
  ok('사업장 이동 배정이 보인다 (서울 → 화성)', /서울/.test(r2.cells[2]) && /화성 배정/.test(r2.cells[2]), r2.cells[2]);
  const r3 = await pg.evaluate(async () => {
    window.__T("fxFindInput('유일 에너테크')"); await new Promise(r => setTimeout(r, 400));
    return document.getElementById('fxFindBody').querySelectorAll('tbody tr').length;
  });
  ok('공백·(주) 표기가 달라도 찾는다', r3 === 1, r3);
  const r4 = await pg.evaluate(async () => {
    window.__T("fxFindInput('신진엠텍')"); await new Promise(r => setTimeout(r, 400));
    var tds = [].slice.call(document.getElementById('fxFindBody').querySelectorAll('tbody tr')[0].children).map(td => (td.innerText || '').trim());
    return tds;
  });
  ok('어음도 "어음" 으로 구분해 나온다', /어음/.test(r4[1]), JSON.stringify(r4));

  console.log('▶ 4) 없는 이름');
  const r5 = await pg.evaluate(async () => {
    window.__T("fxFindInput('없는사람')"); await new Promise(r => setTimeout(r, 400));
    var h = document.getElementById('fxFindBody');
    return { txt: (h.innerText || '').replace(/\s+/g, ' '), btns: h.querySelectorAll('button').length };
  });
  ok('"없습니다" 라고 알려 준다', /없는사람 이\(가\) 없습니다/.test(r5.txt), r5.txt.slice(0, 90));
  ok('출금은 검색되지 않는다고 함께 안내', /출금 내역은 아직 보관하지 않아/.test(r5.txt));
  const r6 = await pg.evaluate(async () => {
    window.__T("fxFindInput('홍길도')"); await new Promise(r => setTimeout(r, 400));
    var h = document.getElementById('fxFindBody');
    return { txt: (h.innerText || '').replace(/\s+/g, ' '), names: [].slice.call(h.querySelectorAll('button')).map(x => (x.innerText || '').trim()) };
  });
  ok('비슷한 이름 후보를 보여 준다', r6.names.indexOf('홍길동') >= 0 && r6.names.indexOf('홍길순') >= 0, JSON.stringify(r6.names));
  const r7 = await pg.evaluate(async () => {
    var b = [].slice.call(document.getElementById('fxFindBody').querySelectorAll('button')).find(x => (x.innerText || '').trim() === '홍길동');
    b.click(); await new Promise(r => setTimeout(r, 200));
    return { rows: document.getElementById('fxFindBody').querySelectorAll('tbody tr').length,
             input: (document.getElementById('fxFindInput') || {}).value };
  });
  ok('후보를 누르면 바로 그 이름으로 다시 찾는다', r7.rows === 5 && r7.input === '홍길동', JSON.stringify(r7));

  console.log('▶ 5) 많아도 빠르다 · 더보기');
  const perf = await pg.evaluate(async () => {
    var big = [];
    for(var i = 0; i < 11000; i++){
      big.push({ id:'x'+i, biz:(i%2?'서울':'화성'), date:'2024-01-0' + (1 + i%9), kind:'bank', bank:'신한',
                 amount:(i*13)%900000, payer:(i%37===0 ? '홍길동' : ('거래처' + (i%1400))), vendor:(i%3 ? ('업체' + (i%900)) : '') });
    }
    window.__D2 = big;
    window.__T("fxDeposits=window.__D2; _fxCacheBump++;");
    var t0 = performance.now();
    window.__T("fxFindInput('홍길동')"); await new Promise(r => setTimeout(r, 400));
    var t1 = performance.now();                    // 색인 만들기 포함
    var t2 = performance.now();
    window.__T("fxFindInput('거래처77')"); await new Promise(r => setTimeout(r, 400));
    var t3 = performance.now();                    // 색인 재사용
    var h = document.getElementById('fxFindBody');
    return { first: Math.round(t1 - t0 - 400), second: Math.round(t3 - t2 - 400),
             rows: h.querySelectorAll('tbody tr').length, txt: (h.innerText || '').replace(/\s+/g, ' ') };
  });
  ok('11,000건에서도 첫 검색이 1초 안에 끝난다', perf.first < 1000, perf.first + 'ms');
  ok('두 번째 검색은 색인을 다시 쓴다 (300ms 이내)', perf.second < 300, perf.second + 'ms');
  const more = await pg.evaluate(async () => {
    window.__T("fxFindInput('홍길동')"); await new Promise(r => setTimeout(r, 400));
    var h = document.getElementById('fxFindBody');
    var n1 = h.querySelectorAll('tbody tr').length;
    var txt1 = (h.innerText || '');
    var btn = [].slice.call(h.querySelectorAll('button')).find(x => /더보기/.test(x.innerText || ''));
    if(btn){ btn.click(); await new Promise(r => setTimeout(r, 250)); }
    var h2 = document.getElementById('fxFindBody');
    var total = Number((((h2.innerText || '').match(/— ([\d,]+)건/) || [])[1] || '0').replace(/,/g, ''));
    var stillMore = [].slice.call(h2.querySelectorAll('button')).some(x => /더보기/.test(x.innerText || ''));
    return { n1: n1, n2: h2.querySelectorAll('tbody tr').length, hadMore: !!btn, total: total, stillMore: stillMore };
  });
  ok('한 번에 200건까지만 그린다', more.n1 === 200, more.n1);
  ok('[더보기] 로 나머지를 볼 수 있다', more.hadMore && more.n2 === Math.min(more.total, 400) && more.n2 > more.n1, JSON.stringify(more));
  ok('다 보여 주면 [더보기] 가 사라진다', more.n2 >= more.total ? !more.stillMore : more.stillMore, JSON.stringify(more));

  console.log('▶ 6) 배정 시각·사람을 더 이상 지우지 않는다');
  const keep = await T(`(function(){ var e={asgBat:'b1',asgAt:111,asgBy:'김재성',asgU:{v:'x'}}; _fxAsgClear(e); return JSON.stringify(e); })()`);
  ok('_fxAsgClear 가 asgAt·asgBy 를 남긴다', /"asgAt":111/.test(String(keep)) && /"asgBy":"김재성"/.test(String(keep)) && !/asgBat/.test(String(keep)), String(keep));

  console.log('▶ 7) 다른 회계 탭은 그대로');
  const other = await pg.evaluate(async () => {
    window.__T("fxDeposits=window.__D; _fxCacheBump++;");
    window.__T("switchPage('fxsum')"); await new Promise(r => setTimeout(r, 400));
    var a = window.__T('_fxTab');
    window.__T("switchPage('fx')"); await new Promise(r => setTimeout(r, 400));
    return a + '/' + window.__T('_fxTab');
  });
  ok('집계·미수현황 탭 전환이 그대로', other === 'sum/ar', other);
  ok('pageerror 없음', errs.length === 0, errs.join(' | '));

  await b.close();
  let p = 0; P.forEach(x => { if(x[1]) p++; console.log((x[1] ? '  OK  ' : '  FAIL') + '  ' + x[0] + (x[1] ? '' : '   → ' + x[2])); });
  console.log('[' + LABEL + '] ' + p + '/' + P.length);
})();
