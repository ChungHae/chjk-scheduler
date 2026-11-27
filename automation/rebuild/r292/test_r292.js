// r292 테스트 — 칸마다 인쇄 글자 크기를 따로 (상호·성명 10 / 등록번호 12 / 년월일 10 / 총금액 12)
//  사용:  node test_r292.js <index.html(__T 주입본)> [라벨]
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
    __T("_fbDbUrl='https://stub'; _asCfgLoaded=true; _asPos=Object.assign({},_AS_POS0);");
    __T("switchPage('audit')");
  });
  await pg.waitForTimeout(500);

  const q = await pg.evaluate(() => { var o = __T("P()");
    return { fs:o.fs, sub:o.fsSub, head:o.fsHead, biz:o.fsBiz, date:o.fsDate, tot:o.fsTot, min:o.fsMin }; });
  if (typeof q.tot !== 'number') {
    ['손잡이 넷','상호·성명 10pt','등록번호 12pt','년월일 10pt','총금액 12pt'].forEach(n => ok('r292 기능 없음 — ' + n, false));
    ok('pageerror 없음', errs.length === 0, errs.slice(0,2).join(' | '));
    await b.close(); return out();
  }

  // ── ① 기본값 ──
  ok('상호·성명 기본 10pt', q.head === 10, q.head);
  ok('사업자등록번호 기본 12pt', q.biz === 12, q.biz);
  ok('년월일 기본 10pt', q.date === 10, q.date);
  ok('총금액 줄 기본 12pt', q.tot === 12, q.tot);
  ok('본문(fs) 10pt · 작은 칸(fsSub) 9pt 는 그대로', q.fs === 10 && q.sub === 9, JSON.stringify([q.fs, q.sub]));
  ok('r291 의 11pt 한 덩어리가 사라졌다', q.head !== 11 || q.biz !== 11, JSON.stringify(q));

  // ── ② 실제로 찍히는 크기 ──
  const g = await pg.evaluate(() => {
    var rows = [{ spec:'ABC-1', name:'품목', qty:12, price:1000, supply:12000, tax:1200 }];
    var dr = { vid:'v1', vname:'가나', biz:'999-99-99999', ceo:'라마', addr:'서울', total:11000, supply:10000, tax:1000 };
    var html = __T("_asDocHtml")(dr, [{ ship:'20260101', date:'2026-11-27', no:7, rows:rows, memo:'비고글',
                                        total:11000, supply:10000, tax:1000 }], 'form');
    var css = (html.match(/<style>([\s\S]*?)<\/style>/) || [,''])[1];
    var body = html.replace(/^[\s\S]*<body>/, '').replace(/<\/body>[\s\S]*$/, '');
    var d = document.createElement('div'); d.style.cssText = 'position:relative';
    d.innerHTML = '<style>' + css + '</style>' + body;
    document.body.appendChild(d);
    var fs = [].slice.call(d.querySelector('.as-pos .as-slip').querySelectorAll('.as-f'));
    function pick(re){ return fs.filter(function(e){ return re.test(e.textContent); })[0]; }
    function px(e){ return e ? parseFloat(getComputedStyle(e).fontSize) : null; }
    var r = { year:px(pick(/^2026$/)), mon:px(pick(/^11$/)), day:px(pick(/^27$/)),
              biz:px(pick(/^999-99-99999$/)), vname:px(pick(/^가나$/)), ceo:px(pick(/^라마$/)),
              totKo:px(pick(/整$/)), totNo:px(pick(/^\(₩/)), memo:px(pick(/^비고글$/)),
              item:px(pick(/^품목/)), qty:px(pick(/^12$/)) };
    d.remove(); return r;
  });
  const PX = pt => pt * 4 / 3, near = (v, pt) => v != null && Math.abs(v - PX(pt)) < 0.6;
  ok('년 숫자가 10pt', near(g.year, 10), g.year);
  ok('월 숫자가 10pt', near(g.mon, 10), g.mon);
  ok('일 숫자가 10pt', near(g.day, 10), g.day);
  ok('사업자등록번호가 12pt', near(g.biz, 12), g.biz);
  ok('상호가 10pt', near(g.vname, 10), g.vname);
  ok('성명이 10pt', near(g.ceo, 10), g.ceo);
  ok('총금액 한글이 12pt', near(g.totKo, 12), g.totKo);
  ok('총금액 숫자가 12pt', near(g.totNo, 12), g.totNo);
  ok('비고는 9pt 그대로', near(g.memo, 9), g.memo);
  ok('품목·수량은 10pt 그대로', near(g.item, 10) && near(g.qty, 10), JSON.stringify([g.item, g.qty]));

  // ── ③ 넘치면 여전히 줄어든다 ──
  const shr = await pg.evaluate(() => {
    // 총금액은 줄 합계에서 나온다 — 큰 줄 하나로 아주 긴 한글 금액을 만든다
    var dr = { vid:'v1', vname:'가', biz:'999-99-99999', ceo:'라', addr:'서울' };
    var html = __T("_asDocHtml")(dr, [{ ship:'20260101', date:'2026-11-27', no:1,
      rows:[{spec:'A',name:'B',qty:1,price:987654321098,supply:987654321098,tax:98765432110}], memo:'' }], 'form');
    var css = (html.match(/<style>([\s\S]*?)<\/style>/) || [,''])[1];
    var body = html.replace(/^[\s\S]*<body>/, '').replace(/<\/body>[\s\S]*$/, '');
    var d = document.createElement('div'); d.style.cssText = 'position:relative';
    d.innerHTML = '<style>' + css + '</style>' + body; document.body.appendChild(d);
    var fs = [].slice.call(d.querySelector('.as-pos .as-slip').querySelectorAll('.as-f'));
    var e = fs.filter(function(x){ return /整$/.test(x.textContent); })[0];
    var w = e ? e.getBoundingClientRect().width : 0, sw = e ? e.scrollWidth : 0;
    var r = { px:e?parseFloat(getComputedStyle(e).fontSize):null, fits: sw <= w + 1,
              t:e?e.textContent:'' };
    d.remove(); return r;
  });
  ok('아주 긴 총금액은 12pt 아래로 줄어든다', shr.px != null && shr.px < PX(12) - 0.6, shr.px);
  ok('줄여서 칸 안에 들어간다', shr.fits, JSON.stringify(shr));

  // ── ④ 저장·[인쇄 보정] ──
  const src = await pg.evaluate(() => document.documentElement.innerHTML);
  ['fsHead','fsBiz','fsDate','fsTot'].forEach(k =>
    ok('손잡이 목록에 ' + k, new RegExp("'" + k + "'").test(src.split('_AS_KNOBS')[1].slice(0, 260))));
  ['fsHead','fsBiz','fsDate','fsTot'].forEach(k =>
    ok('[인쇄 보정] 창에 ' + k + ' 칸', src.indexOf("fld('" + k + "'") >= 0));
  const saved = await pg.evaluate(() => { var o = {}; __T("_AS_KNOBS").forEach(function(k){ o[k] = __T("P()")[k]; });
    return Object.keys(o).filter(function(k){ return typeof o[k] !== 'number'; }); });
  ok('저장되는 손잡이 값이 모두 숫자', saved.length === 0, JSON.stringify(saved));

  // r291 이 한 일은 그대로
  ok('글자 종류별 글꼴(ASmix) 그대로', /font-family:ASmix,Batang,'바탕'/.test(await pg.evaluate(() => __T("_asWrapDoc([], P())"))));

  ok('pageerror 없음', errs.length === 0, errs.slice(0,2).join(' | '));
  await b.close(); return out();

  function out(){
    let p = 0; P.forEach(x => { if (x[1]) p++; console.log((x[1]?'  OK  ':'  FAIL') + '  ' + x[0] + (x[1]?'':'   → ' + x[2])); });
    console.log('\n[' + LABEL + '] ' + p + '/' + P.length);
    process.exit(p === P.length ? 0 : 1);
  }
})().catch(e => { console.error('EXC', e); process.exit(2); });
