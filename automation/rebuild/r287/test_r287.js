// r287 테스트 — 글자를 양식의 '칸' 안에 앉힌다 · 주소 두 줄 · 자동 축소 · 양식 그림을 페이지 전체에
//  사용:  node test_r287.js <index.html(__T 주입본)> [라벨]
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
    __T("_fbDbUrl='https://stub';");
    __T("_asCfgLoaded=true; _asPos=Object.assign({},_AS_POS0);");
    __T("switchPage('audit')");
  });
  await pg.waitForTimeout(500);

  const has = await pg.evaluate(() => typeof __T("_asPitch") === 'function' && typeof __T("_asTwoLines") === 'function');
  if (!has) {
    ['칸 좌표','품목 윗 여백','주소 두 줄','자동 축소','양식 그림 페이지','보정 제외']
      .forEach(n => ok('r287 기능 없음 — ' + n, false));
    ok('pageerror 없음', errs.length === 0, errs.slice(0,2).join(' | '));
    await b.close(); return out();
  }

  // ── ① 좌표표가 칸(배열) 으로 바뀌었나 ───────────────────────────
  const pos = await pg.evaluate(() => __T("JSON.stringify(_AS_POS0)"));
  const p0 = JSON.parse(pos);
  ok('칸 좌표가 배열로 들어 있다', Array.isArray(p0.cVname) && p0.cVname.length === 4, pos.slice(0,80));
  ok('프린터 보정값(r283 실측)은 그대로 둔다', p0.offX === -0.7 && p0.sclX === 0.9924 && p0.sclY === 0.9950);
  ok('옛 점 좌표(noX·rowY·cNameL)는 없다', p0.noX === undefined && p0.rowY === undefined && p0.cNameL === undefined);
  ok('품목표 안쪽 값이 있다', p0.rowTop === 60.94 && p0.rowBot === 110.09 && p0.rowPad > 0);
  ok('손잡이에 rowPad 가 들어가고 rowY 는 빠졌다', await pg.evaluate(() =>
     __T("_AS_KNOBS.indexOf('rowPad')") >= 0 && __T("_AS_KNOBS.indexOf('rowY')") < 0));

  // ── ② 칸 좌표가 양식 선 안에 들어가나 ───────────────────────────
  ok('수량·단가·공급가액·세액 칸이 표 세로선과 같다',
     p0.xQty[0] === 97.04 && p0.xPrice[0] === 107.62 && p0.xSup[0] === 128.80 && p0.xTax[1] === 171.49);
  ok('공급받는자 칸이 양식 칸과 같다',
     p0.cVname[0] === 100.60 && p0.cVname[2] === 135.58 && p0.cCeo[0] === 141.89 && p0.cAddr[3] === 43.98);

  // ── ③ 품목 13줄이 표 안에 고르게 들어가나 ───────────────────────
  const rows = await pg.evaluate(() => {
    var p = __T("P()"), pitch = __T("_asPitch(P())");
    var top = p.rowTop + p.rowPad, bot = top + 13*pitch;
    return { pitch: pitch, top: top, bot: bot, rowTop: p.rowTop, rowBot: p.rowBot };
  });
  ok('첫 줄이 표 윗선에서 떨어져 있다', rows.top > rows.rowTop + 0.5, JSON.stringify(rows));
  ok('열세 줄이 표 바닥선을 넘지 않는다', rows.bot <= rows.rowBot + 0.001, JSON.stringify(rows));
  ok('줄 간격이 예전(3.5417)보다 넓다', rows.pitch > 3.5417, String(rows.pitch));

  // ── ④ 글자 폭 셈 · 자동 축소 · 두 줄 쪼개기 ─────────────────────
  const w10 = await pg.evaluate(() => __T("_asTextW('가나다', 10)"));
  ok('한글 3자 폭 = 10pt × 3', Math.abs(w10 - 3*10*0.3528) < 0.01, String(w10));
  const sh = await pg.evaluate(() => __T("_asShrink('주식회사 한국정밀기계공업사', 32.18, 9, 6.5)"));
  ok('긴 상호는 글자를 줄인다', sh < 9 && sh >= 6.5, String(sh));
  const sh2 = await pg.evaluate(() => __T("_asShrink('대성정밀', 32.18, 9, 6.5)"));
  ok('짧은 상호는 줄이지 않는다', sh2 === 9, String(sh2));
  const two = await pg.evaluate(() => __T("JSON.stringify(_asTwoLines('경기도 화성시 팔탄면 율암리 산업단지 2로 123번길 45 대성빌딩 3층 301호', 65, 9))"));
  ok('긴 주소는 두 줄로 쪼갠다', JSON.parse(two).length === 2, two.slice(0,70));
  const one = await pg.evaluate(() => __T("JSON.stringify(_asTwoLines('서울 구로구 198', 65, 9))"));
  ok('짧은 주소는 한 줄 그대로', JSON.parse(one).length === 1, one);

  // ── ⑤ 실제로 그려 보기 ──────────────────────────────────────────
  const made = await pg.evaluate(() => {
    var rows = []; for (var i = 1; i <= 13; i++) rows.push({ spec:'P-'+i, name:'품목'+i, qty:i, price:100*i, supply:100*i*i, tax:10*i*i });
    window.__DR = { vid:'v1', vname:'주식회사 한국정밀기계공업사', biz:'220-81-45678', ceo:'홍길동',
                    addr:'경기도 화성시 팔탄면 율암리 산업단지 2로 123번길 45 대성빌딩 3층 301호' };
    window.__DC = [{ ship:'20260101', date:'2026-11-26', no:17, rows:rows, memo:'비고시험' }];
    return __T("_asDocHtml(window.__DR, window.__DC, 'form')");
  });
  ok('미리보기 HTML 이 만들어진다', made.length > 2000);
  ok('한 장에 전표 두 벌', (made.match(/class="as-pos"/g) || []).length === 2);
  ok('비고가 들어간다', made.indexOf('비고시험') >= 0);
  ok('계 합계가 들어간다', made.indexOf('8,190') >= 0 || /as-f/.test(made));

  const geo = await pg.evaluate(() => {
    var html = __T("_asDocHtml(window.__DR, window.__DC, 'form')");
    var css = (html.match(/<style>([\s\S]*?)<\/style>/) || [,''])[1];
    var body = html.replace(/^[\s\S]*<body>/, '').replace(/<\/body>[\s\S]*$/, '');
    var d = document.createElement('div');
    d.style.cssText = 'position:relative';
    d.innerHTML = '<style>' + css + '</style>' + body;
    document.body.appendChild(d);
    var pos0 = d.querySelector('.as-pos');
    var slip = pos0.querySelector('.as-slip');
    var fs = [].slice.call(slip.querySelectorAll('.as-f'));
    var sb = slip.getBoundingClientRect();
    var mm = sb.width / 171;
    var r = fs.map(function (e) {
      var b = e.getBoundingClientRect();
      return { t: e.textContent, x1: (b.left - sb.left)/mm, x2: (b.right - sb.left)/mm,
               y1: (b.top - sb.top)/mm, y2: (b.bottom - sb.top)/mm, fs: parseFloat(getComputedStyle(e).fontSize) };
    });
    var out = { n: r.length,
      no: r.filter(function(e){return e.t==='17';})[0],
      yr: r.filter(function(e){return e.t==='2026';})[0],
      mo: r.filter(function(e){return e.t==='11';})[0],
      addr: r.filter(function(e){return /화성시|대성빌딩/.test(e.t);}),
      vn: r.filter(function(e){return /한국정밀/.test(e.t);})[0],
      vnAll: r.filter(function(e){return /한국정밀|기계공업사|주식회사/.test(e.t);}),
      row1: r.filter(function(e){return /^품목1\s/.test(e.t);})[0],
      row13: r.filter(function(e){return /^품목13\s/.test(e.t);})[0] };
    d.remove(); return out;
  });
  ok('번호가 18.50mm 칸선을 넘지 않는다', geo.no && geo.no.y2 <= 18.46, geo.no && JSON.stringify(geo.no));
  ok('번호가 라벨(25.55mm) 오른쪽에 있다', geo.no && geo.no.x1 >= 25.5, geo.no && String(geo.no.x1));
  ok('년 숫자가 년 글자(148.59mm)를 침범하지 않는다', geo.yr && geo.yr.x2 <= 148.5, geo.yr && String(geo.yr.x2));
  ok('월 숫자가 년·월 글자 사이에 있다', geo.mo && geo.mo.x1 >= 150.8 && geo.mo.x2 <= 156.5, geo.mo && JSON.stringify(geo.mo));
  ok('긴 주소가 두 줄로 그려진다', geo.addr.length === 2, String(geo.addr.length));
  ok('주소 두 줄이 칸(35.48~43.98) 안에 있다',
     geo.addr.length === 2 && geo.addr[0].y1 >= 35.4 && geo.addr[1].y2 <= 44.05,
     JSON.stringify(geo.addr.map(function(a){return [a.y1,a.y2];})));
  // r290: 상호도 한 줄 → 두 줄 → 그래도 넘치면 축소 차례로 바뀌었다
  ok('긴 상호는 두 줄이거나 글자가 작아진다',
     geo.vnAll.length === 2 || (geo.vn && geo.vn.fs < 12),
     JSON.stringify(geo.vnAll.map(function(e){ return [e.t, e.fs]; })));
  ok('첫 품목 줄이 표 윗선에서 떨어져 있다', geo.row1 && geo.row1.y1 >= 61.5, geo.row1 && String(geo.row1.y1));
  ok('열세째 품목 줄이 바닥선(110.09) 안에 있다', geo.row13 && geo.row13.y2 <= 110.1, geo.row13 && String(geo.row13.y2));
  ok('품명이 세로선(8.08mm) 오른쪽에서 시작한다', geo.row1 && geo.row1.x1 >= 8.0, geo.row1 && String(geo.row1.x1));

  // ── ⑥ 양식 그림은 페이지 전체에 ─────────────────────────────────
  const noimg = await pg.evaluate(() => __T("_asDocHtml(window.__DR, window.__DC, 'form')").indexOf('class="as-pageform"') < 0);
  ok('그림이 없으면 전표마다 SVG 를 쓴다', noimg);
  const withimg = await pg.evaluate(() => {
    __T("_asFormImg='data:image/png;base64,AAAA'; _asFormTried=true;");
    var h = __T("_asDocHtml(window.__DR, window.__DC, 'form')");
    __T("_asFormImg=null;");
    return { page: (h.match(/class="as-pageform"/g) || []).length, slip: (h.match(/class="as-form"/g) || []).length };
  });
  ok('그림이 있으면 페이지마다 한 번만 깐다', withimg.page === 1, JSON.stringify(withimg));
  ok('그림이 있으면 전표 SVG 는 그리지 않는다', withimg.slip === 0, JSON.stringify(withimg));
  ok('페이지 그림 CSS 가 A4 전체', await pg.evaluate(() =>
     /\.as-pageform\{[^}]*width:210mm[^}]*height:297mm/.test(__T("_asDocHtml(window.__DR, window.__DC, 'form')"))));

  // ── ⑦ 미리보기는 프린터 보정을 빼고 그린다 ──────────────────────
  const calib = await pg.evaluate(() => {
    __T("_asPos.offX=-5; _asPos.sclX=0.9;");
    var f = __T("_asSlipHtml(window.__DC[0],0,1,{biz:'1',vname:'가',ceo:'나',addr:'다',supply:1,tax:0,total:1},'form')");
    var g = __T("_asSlipHtml(window.__DC[0],0,1,{biz:'1',vname:'가',ceo:'나',addr:'다',supply:1,tax:0,total:1},false)");
    __T("_asPos.offX=0; _asPos.sclX=1;");
    return { form: /left:26\.5mm/.test(f), print: /left:26\.5mm/.test(g) };
  });
  ok('미리보기는 보정 없이 원래 좌표로', calib.form, JSON.stringify(calib));
  ok('인쇄는 보정을 그대로 반영한다', !calib.print, JSON.stringify(calib));

  // ── ⑧ 긴 금액·긴 품명은 칸 안에서 글자를 줄인다 ─────────────────
  const amt = await pg.evaluate(() => {
    function fsOf(total){
      var rows=[{spec:'X',name:'Y',qty:1,price:1,supply:Math.round(total/1.1),tax:total-Math.round(total/1.1)}];
      var dr={ vid:'v1', vname:'가', biz:'1', ceo:'나', addr:'다' };
      var h=__T("_asDocHtml")(dr, [{ship:'20261101',date:'2026-11-03',no:3,rows:rows,memo:''}], false);
      var d=document.createElement('div'); d.innerHTML=h.replace(/^[\s\S]*<body>/,'').replace('</body></html>','');
      var e=[].slice.call(d.querySelectorAll('.as-f')).filter(function(x){ return /整$/.test(x.textContent); })[0];
      return e ? parseFloat(e.style.fontSize) : null;
    }
    // r293: 한글+숫자가 한 세트로 빈칸 전체를 쓰므로 어지간한 금액은 줄지 않는다 — 더 긴 값으로 본다
    return { short: fsOf(1811007), huge: fsOf(987654321), vast: fsOf(108641975320) };
  });
  ok('긴 한글 금액은 칸에 맞게 작아진다', amt.vast !== null && amt.vast < amt.short, JSON.stringify(amt));
  ok('보통 금액은 줄지 않는다', amt.huge === amt.short, JSON.stringify(amt));
  // r292: 총금액 줄은 전용 손잡이 fsTot(기본 12pt) — 없으면 예전처럼 fs
  ok('짧은 금액은 기본 크기 그대로',
     amt.short === (await pg.evaluate(() => { var q = __T("P()"); return q.fsTot == null ? q.fs : q.fsTot; })),
     JSON.stringify(amt));
  const longName = await pg.evaluate(() => {
    var nm='아주아주 긴 품목 이름입니다 그리고 규격도 길어요 ABCDEFGHIJKLMNOPQRSTUVWXYZ-0123456789-XYZ';
    var rows=[{spec:nm,name:'',qty:1,price:1,supply:1,tax:0}];
    var dr={ vid:'v1', vname:'가', biz:'1', ceo:'나', addr:'다' };
    var h=__T("_asDocHtml")(dr, [{ship:'20261101',date:'2026-11-03',no:3,rows:rows,memo:''}], false);
    var d=document.createElement('div'); d.innerHTML=h.replace(/^[\s\S]*<body>/,'').replace('</body></html>','');
    var e=[].slice.call(d.querySelectorAll('.as-f')).filter(function(x){ return x.textContent.indexOf('아주아주')===0; })[0];
    return e ? parseFloat(e.style.fontSize) : null;
  });
  ok('긴 품명도 칸에 맞게 작아진다', longName !== null && longName < 10, String(longName));

  ok('pageerror 없음', errs.length === 0, errs.slice(0,2).join(' | '));
  await b.close(); return out();

  function out(){
    let p = 0; P.forEach(x => { if (x[1]) p++; console.log((x[1]?'  OK  ':'  FAIL') + '  ' + x[0] + (x[1]?'':'   → ' + x[2])); });
    console.log('\n[' + LABEL + '] ' + p + '/' + P.length);
    process.exit(p === P.length ? 0 : 1);
  }
})();
