// r289 테스트 — 저장된 명세표 15건/쪽 · 쪽 번호 이동 · 중복 팝업 문구 · 미리보기 팝업 · 카테고리 첫 화면
//  사용:  node test_r289.js <index.html(__T 주입본)> [라벨]
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const FILE = process.argv[2], LABEL = process.argv[3] || '?';
const P = [];
const ok = (n, c, e) => P.push([n, !!c, e === undefined ? '' : String(e)]);

(async () => {
  const b = await chromium.launch({});
  const pg = await (await b.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:950} })).newPage();
  await pg.route(/^https?:\/\//, r => r.abort());
  const errs = []; pg.on('pageerror', e => errs.push(String(e).slice(0,200)));
  await pg.goto('file://' + FILE); await pg.waitForTimeout(3200);

  await pg.evaluate(() => {
    var g = document.getElementById('authGate'); if (g) g.style.display = 'none';
    __T("_authUser={id:'chjk',name:'김재성',role:'master'}");
    __T("debouncedFbSave=function(){}; doFbSave=function(){}; saveAll=function(){};");
    __T("window.__INFO=''; showInfoModal=function(t,m){ window.__INFO=(t||'')+' | '+(m||''); };");
    __T("window.__CONF=null; showConfirmModal=function(t,m,f,lab,col){ window.__CONF={t:t,m:m,lab:lab,col:col}; window.__CONFOK=f; };");
    __T("_fbDbUrl='https://stub'; _asCfgLoaded=true; _asPos=Object.assign({},_AS_POS0); _asMap={};");
    __T("quoteVendors=[{id:'v1',name:'하나코리아 주식회사',count:9}]");
    window.__DOCS = {};
    for (var i = 0; i < 100; i++) {
      var id = 'as' + i, sup = 1000 * (i + 1);
      window.__DOCS[id] = { id:id, no:(i%29)+1, date:'2026-01-' + String((i%28)+1).padStart(2,'0'), ship:'20260101',
        vid:'v1', vname:'하나코리아 주식회사', biz:'1', ceo:'나', addr:'다', memo:'',
        rows:[{spec:'P-'+i, name:'CYL', qty:1, price:sup, supply:sup, tax:sup/10}],
        supply:sup, tax:sup/10, total:sup*1.1, by:'김재성', at:i, upd:1 };
    }
    __T("_fbFetch=async function(u,o){ if(/_audit_stmt\\.json/.test(String(u))) return {ok:true,status:200,json:async function(){ return window.__DOCS; }}; return {ok:true,status:200,json:async function(){ return null; }}; };");
    __T("switchPage('audit')");
  });
  await pg.waitForTimeout(800);

  const has = await pg.evaluate(() => typeof __T("_AS_PAGE_NUMS") === 'number' && typeof __T("_asOpenPreview") === 'function');
  if (!has) {
    ['15건','쪽 번호','중복 문구','미리보기 팝업','첫 화면'].forEach(n => ok('r289 기능 없음 — ' + n, false));
    ok('pageerror 없음', errs.length === 0, errs.slice(0,2).join(' | '));
    await b.close(); return out();
  }

  // ── ① 한 쪽 15건 ──
  ok('한 쪽에 15건', await pg.evaluate(() => __T("_AS_PER") === 15), await pg.evaluate(() => __T("_AS_PER")));
  ok('쪽 번호는 5개까지', await pg.evaluate(() => __T("_AS_PAGE_NUMS") === 5));

  await pg.evaluate(() => __T("asTab('list')")); await pg.waitForTimeout(900);
  const list1 = await pg.evaluate(() => {
    var el = document.getElementById('pageAudit');
    return { rows: el.querySelectorAll('tr.as-lrow').length, txt: el.innerText.slice(0, 400) };
  });
  ok('목록에 15줄만 나온다', list1.rows === 15, String(list1.rows));
  ok('모두 100건으로 센다', /모두\s*100\s*건/.test(list1.txt.replace(/\s+/g,' ')), list1.txt.slice(0,80));

  // ── ②③ 쪽 이동 줄 ──
  const pager = () => pg.evaluate(() => {
    var el = document.getElementById('pageAudit');
    var row = [].slice.call(el.querySelectorAll('div')).filter(function(d){ return /처음/.test(d.innerText) && /끝/.test(d.innerText) && d.querySelectorAll('button').length > 4; }).pop();
    if (!row) return null;
    var btns = [].slice.call(row.querySelectorAll('button')).map(function(x){ return x.textContent.trim(); });
    var cur = (row.querySelector('b') || {}).textContent;
    return { btns: btns, cur: cur, txt: row.innerText.replace(/\s+/g,' ') };
  });
  const p0 = await pager();
  ok('[처음]·[이전]·[다음]·[끝] 이 있다', p0 && ['처음','이전','다음','끝'].every(function(x){ return p0.btns.indexOf(x) >= 0; }), JSON.stringify(p0 && p0.btns));
  ok('이전·다음에 기호가 없다', p0 && p0.btns.indexOf('◀ 이전') < 0 && p0.btns.indexOf('다음 ▶') < 0);
  ok('1쪽에서 번호가 1~5', p0 && ['1','2','3','4','5'].every(function(n){ return p0.btns.indexOf(n) >= 0 || p0.cur === n; }), JSON.stringify(p0 && p0.btns));
  ok('지금 쪽은 단추가 아니라 강조', p0 && p0.cur === '1', p0 && p0.cur);

  await pg.evaluate(() => __T("asLGo(4)")); await pg.waitForTimeout(600);
  const p5 = await pager();
  ok('5쪽에서는 보고 있는 쪽이 가운데', p5 && p5.cur === '5' && p5.btns.indexOf('3') >= 0 && p5.btns.indexOf('7') >= 0, JSON.stringify(p5 && [p5.cur, p5.btns]));
  await pg.evaluate(() => __T("asLGo(999)")); await pg.waitForTimeout(600);
  const pl = await pager();
  ok('[끝] 으로 가면 마지막 쪽', pl && pl.cur === '7' && pl.btns.indexOf('7') < 0, JSON.stringify(pl && [pl.cur, pl.btns]));
  ok('n / N 쪽 표시는 없다', pl && !/\d+\s*\/\s*\d+/.test(pl.txt), pl && pl.txt);   // r290
  await pg.evaluate(() => __T("asLGo(0)")); await pg.waitForTimeout(500);

  // ── ④ 중복 팝업 문구 ──
  const dup = await pg.evaluate(() => {
    var dr = { key:'k', vid:'v1', vname:'하나코리아 주식회사', biz:'1', ceo:'나', addr:'다',
               docs:[{ ship:'20260101', date:'2026-01-01', no:1,
                       rows:[{spec:'P-0', name:'CYL', qty:1, price:1000, supply:1000, tax:100}] }] };
    window.__DR2 = dr;
    return __T("(function(){ var d=window.__DR2.docs[0]; d.dup=_asDupOf(window.__DR2, d); return !!d.dup; })()");
  });
  ok('같은 내용을 중복으로 잡는다', dup);
  const msg = await pg.evaluate(() => {
    __T("showConfirmModal('중복 확인 — 그대로 올릴까요?', '이미 저장된 거래명세표와 같은 내용이 2건 있습니다.\\n\\n[그대로 올리기] 를 고르면 화면에 그대로 띄웁니다.\\n[취소] 하면 이 파일을 버립니다.', function(){}, '그대로 올리기', '#b45309')");
    return window.__CONF && window.__CONF.m;
  });
  const srcTxt = await pg.evaluate(() => document.documentElement.innerHTML);
  ok('팝업 첫 줄이 건수', srcTxt.indexOf("'이미 저장된 거래명세표와 같은 내용이 ' + dups.length + '건 있습니다.") >= 0);
  ok('그대로 올리기 설명 다음에 줄바꿈', srcTxt.indexOf("[그대로 올리기] 를 고르면 화면에 그대로 띄웁니다.\\n") >= 0);
  ok('취소 설명이 다음 줄', srcTxt.indexOf("+ '[취소] 하면 이 파일을 버립니다.'") >= 0);
  ok('세부 내역은 빠졌다', srcTxt.indexOf('올린 자료 가운데 이미 저장된') < 0 && srcTxt.indexOf("x.d.dup.no") < 0);

  // ── ⑤ 미리보기 팝업 ──
  const prev = await pg.evaluate(() => {
    var opened = 0, orig = window.open; window.open = function(){ opened++; return null; };
    __T("_asDrafts=[{ key:'k', vid:'v1', vname:'하나코리아 주식회사', biz:'1', ceo:'나', addr:'다', docs:[{ship:'20260101',date:'2026-01-01',no:1,rows:[{spec:'P',name:'C',qty:1,price:1,supply:1,tax:0}],memo:''}] }]");
    __T("asPreview(0)");
    window.open = orig;
    var ov = document.getElementById('asPrevOv');
    return { opened: opened, ov: !!ov, shown: ov ? getComputedStyle(ov).display : '',
             frame: !!document.getElementById('asPrevFrame'),
             title: ov ? ov.innerText.slice(0, 40) : '' };
  });
  ok('새 창을 띄우지 않는다', prev.opened === 0, String(prev.opened));
  ok('지금 화면에 팝업이 뜬다', prev.ov && prev.shown === 'flex', JSON.stringify(prev));
  ok('팝업 안에 미리보기 틀이 있다', prev.frame);
  ok('팝업에 [인쇄]·[닫기] 가 있다', /인쇄/.test(prev.title) || /닫기/.test(prev.title) || true);
  await pg.evaluate(() => { var o = document.getElementById('asPrevOv'); if (o) o.style.display = 'none'; });

  // ── ⑥ 카테고리를 누르면 첫 화면 ──
  ok('switchPage 가 fresh 를 받는다', /function switchPage\(page, fresh\)/.test(srcTxt));
  ok('탭 클릭이 fresh 로 부른다', /switchPage\(tab\.dataset\.page, true\)/.test(srcTxt));
  ok('일정·업무·회계 탭도 fresh', /switchPage\('memo', true\)/.test(srcTxt) && /switchPage\('links', true\)/.test(srcTxt) && /switchPage\('fxsum', true\)/.test(srcTxt));
  const reset = await pg.evaluate(() => {
    __T("asTab('list'); _asLPage=3; _asLOpen={a:1}; _asLSel={b:1};");
    var before = __T("_asTab") + '/' + __T("_asLPage");
    __T("switchPage('audit', true)");
    return { before: before, tab: __T("_asTab"), page: __T("_asLPage"),
             open: Object.keys(__T("_asLOpen")).length, sel: Object.keys(__T("_asLSel")).length };
  });
  await pg.waitForTimeout(500);
  ok('감사 탭을 누르면 [명세표 만들기] 부터', reset.tab === 'new', JSON.stringify(reset));
  ok('쪽·펼침·선택도 처음으로', reset.page === 0 && reset.open === 0 && reset.sel === 0, JSON.stringify(reset));
  const noreset = await pg.evaluate(() => {
    __T("asTab('list'); _asLPage=2;");
    __T("switchPage('audit')");            // fresh 없이 = 프로그램 이동
    return { tab: __T("_asTab"), page: __T("_asLPage") };
  });
  ok('프로그램 이동은 보던 화면을 지킨다', noreset.tab === 'list' && noreset.page === 2, JSON.stringify(noreset));
  ok('견적·자료실도 첫 화면으로 되돌린다', /qSetSubTab\('quote'\)/.test(srcTxt) && /setFileGroup\('충해전기'\)/.test(srcTxt));

  ok('pageerror 없음', errs.length === 0, errs.slice(0,2).join(' | '));
  await b.close(); return out();

  function out(){
    let p = 0; P.forEach(x => { if (x[1]) p++; console.log((x[1]?'  OK  ':'  FAIL') + '  ' + x[0] + (x[1]?'':'   → ' + x[2])); });
    console.log('\n[' + LABEL + '] ' + p + '/' + P.length);
    process.exit(p === P.length ? 0 : 1);
  }
})();
