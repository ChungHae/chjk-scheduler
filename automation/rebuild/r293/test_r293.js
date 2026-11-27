// r293 테스트 — 총금액 한글+숫자가 한 세트(cTot). 빈칸 전체가 폭이라 12pt 를 지킨다.
//  사용:  node test_r293.js <index.html(__T 주입본)> [라벨]
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

  const p0 = await pg.evaluate(() => { var q = __T("P()");
    return { tot:q.cTot, gap:q.totGap, ko:q.cTotKo, no:q.cTotNo, fsTot:q.fsTot, pad:q.pad, min:q.fsMin }; });
  if (!p0.tot) {
    ['한 칸으로 합침','간격 손잡이','12pt 유지'].forEach(n => ok('r293 기능 없음 — ' + n, false));
    ok('pageerror 없음', errs.length === 0, errs.slice(0,2).join(' | '));
    await b.close(); return out();
  }

  // ── ① 칸 ──
  ok('총금액이 한 칸(cTot)', Array.isArray(p0.tot) && p0.tot.length === 4, JSON.stringify(p0.tot));
  ok('옛 두 칸(cTotKo·cTotNo)은 없다', p0.ko === undefined && p0.no === undefined,
     JSON.stringify([p0.ko, p0.no]));
  ok('왼쪽은 그대로 47.5mm', Math.abs(p0.tot[0] - 47.50) < 0.01, p0.tot[0]);
  ok('오른쪽이 빈칸 끝 171.0mm', Math.abs(p0.tot[2] - 171.00) < 0.01, p0.tot[2]);
  ok('쓸 수 있는 폭이 120mm 넘는다', (p0.tot[2] - p0.tot[0]) - 2*p0.pad > 120,
     ((p0.tot[2]-p0.tot[0]) - 2*p0.pad).toFixed(1));
  ok('간격 손잡이(totGap)가 있다', typeof p0.gap === 'number' && p0.gap > 0, p0.gap);

  // ── ② 실제로 찍히는 모습 ──
  const rows = await pg.evaluate(() => {
    function one(sup){
      var tax = Math.round(sup * 0.1);
      var html = __T("_asDocHtml")({ vid:'v', vname:'가', biz:'1', ceo:'나', addr:'다' },
        [{ ship:'20260101', date:'2026-11-27', no:1,
           rows:[{ spec:'A', name:'B', qty:1, price:sup, supply:sup, tax:tax }], memo:'' }], 'form');
      var css = (html.match(/<style>([\s\S]*?)<\/style>/) || [,''])[1];
      var body = html.replace(/^[\s\S]*<body>/, '').replace(/<\/body>[\s\S]*$/, '');
      var d = document.createElement('div'); d.style.cssText = 'position:relative';
      d.innerHTML = '<style>' + css + '</style>' + body; document.body.appendChild(d);
      var fs = [].slice.call(d.querySelector('.as-pos .as-slip').querySelectorAll('.as-f'));
      var ko = fs.filter(function(e){ return /整$/.test(e.textContent); })[0];
      var no = fs.filter(function(e){ return /^\(₩/.test(e.textContent); })[0];
      // 글자가 실제로 차지하는 자리는 Range 로 잰다 (칸은 글자보다 넓다)
      function span(el){ var rg = document.createRange(); rg.selectNodeContents(el);
        var b = rg.getBoundingClientRect(); rg.detach && rg.detach(); return b; }
      var kt = span(ko), nt = span(no), sb = d.querySelector('.as-pos').getBoundingClientRect();
      var r = { koPt:+(parseFloat(getComputedStyle(ko).fontSize)*0.75).toFixed(2),
                noPt:+(parseFloat(getComputedStyle(no).fontSize)*0.75).toFixed(2),
                koEnd:kt.right, noLeft:nt.left, noRight:nt.right,
                slipL:sb.left, slipR:sb.right, w:sb.width,
                koTxt:ko.textContent, noTxt:no.textContent };
      d.remove(); return r;
    }
    return { small:one(153450), mid:one(5433120), big:one(597541864), vast:one(108641975320) };
  });
  const mm = (r, px) => (px - r.slipL) / r.w * 171;   // 전표 폭 171mm 기준

  ['small','mid','big'].forEach(k => {
    const r = rows[k];
    ok('보통 금액은 한글이 12pt — ' + k, r.koPt === 12, r.koPt + ' / ' + r.koTxt);
    ok('보통 금액은 숫자도 12pt — ' + k, r.noPt === 12, r.noPt);
  });
  ['small','mid','big','vast'].forEach(k => {
    const r = rows[k];
    ok('한글과 숫자가 같은 크기 — ' + k, r.koPt === r.noPt, JSON.stringify([r.koPt, r.noPt]));
    ok('숫자가 한글 뒤에 온다(안 겹친다) — ' + k, r.noLeft >= r.koEnd - 0.5,
       JSON.stringify([mm(r, r.koEnd).toFixed(1), mm(r, r.noLeft).toFixed(1)]));
    ok('숫자가 칸 오른쪽 끝(171mm)을 넘지 않는다 — ' + k, mm(r, r.noRight) <= 171.2,
       mm(r, r.noRight).toFixed(1));
  });
  ok('한글이 길수록 숫자가 오른쪽으로 밀린다',
     rows.small.noLeft < rows.big.noLeft, JSON.stringify([mm(rows.small, rows.small.noLeft).toFixed(1),
                                                          mm(rows.big, rows.big.noLeft).toFixed(1)]));
  ok('한글과 숫자 사이가 간격(totGap)만큼',
     Math.abs((mm(rows.mid, rows.mid.noLeft) - mm(rows.mid, rows.mid.koEnd)) - p0.gap) < 2.0,
     (mm(rows.mid, rows.mid.noLeft) - mm(rows.mid, rows.mid.koEnd)).toFixed(2));
  ok('아주 긴 금액이라야 비로소 줄어든다', rows.vast.koPt < 12 && rows.vast.koPt >= p0.min,
     rows.vast.koPt + ' / ' + rows.vast.koTxt);
  ok('9자리 금액까지는 12pt 그대로', rows.big.koPt === 12, rows.big.koPt + ' / ' + rows.big.koTxt);

  // ── ③ 저장 · [인쇄 보정] ──
  const src = await pg.evaluate(() => document.documentElement.innerHTML);
  ok('totGap 이 저장되는 손잡이 목록에 있다', /_AS_KNOBS = \[[\s\S]{0,320}?'totGap'/.test(src));
  ok('[인쇄 보정] 창에 간격 칸', src.indexOf("fld('totGap'") >= 0);
  ok('옛 cTotKo·cTotNo 자취가 없다', src.indexOf('cTotKo') < 0 && src.indexOf('cTotNo') < 0);
  const bad = await pg.evaluate(() => __T("_AS_KNOBS").filter(function(k){ return typeof __T("P()")[k] !== 'number'; }));
  ok('저장되는 손잡이 값이 모두 숫자', bad.length === 0, JSON.stringify(bad));

  ok('pageerror 없음', errs.length === 0, errs.slice(0,2).join(' | '));
  await b.close(); return out();

  function out(){
    let p = 0; P.forEach(x => { if (x[1]) p++; console.log((x[1]?'  OK  ':'  FAIL') + '  ' + x[0] + (x[1]?'':'   → ' + x[2])); });
    console.log('\n[' + LABEL + '] ' + p + '/' + P.length);
    process.exit(p === P.length ? 0 : 1);
  }
})().catch(e => { console.error('EXC', e); process.exit(2); });
