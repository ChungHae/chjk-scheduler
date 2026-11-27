// r291 테스트 — 글씨체를 글자 종류(숫자·영문 / 한글)로 가르기 · 상대방 칸 글자 키우기 · 끌어오기 표시 범위
//  사용:  node test_r291.js <index.html(__T 주입본)> [라벨]
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

  const has = await pg.evaluate(() => typeof __T("_AS_FAM_FACE") === 'string');
  if (!has) {
    ['글자 종류별 글꼴','상대방 칸 글자 크기','끌어오기 표시'].forEach(n => ok('r291 기능 없음 — ' + n, false));
    ok('pageerror 없음', errs.length === 0, errs.slice(0,2).join(' | '));
    await b.close(); return out();
  }

  // ── ① 글꼴 정의 ──
  const F = await pg.evaluate(() => ({
    lat: __T("_AS_FAM_LAT"), kor: __T("_AS_FAM_KOR"),
    mix: __T("_AS_FAM"), row: __T("_AS_FAM_ROW"), face: __T("_AS_FAM_FACE")
  }));
  ok('숫자·영문 글꼴은 고정폭 바탕체', /^BatangChe/.test(F.lat), F.lat);
  ok('한글 글꼴은 바탕', /^Batang,/.test(F.kor) && !/BatangChe/.test(F.kor), F.kor);
  ok('전표 글꼴은 섞은 글꼴(ASmix)이 먼저', /^ASmix,/.test(F.mix), F.mix);
  ok('섞은 글꼴의 뒷차례에 바탕이 먼저', /^ASmix,Batang,'바탕'/.test(F.mix), F.mix);
  ok('글꼴 이름 어디에도 큰따옴표가 없다',           // style="..." 안에 들어가면 속성이 깨진다
     [F.lat, F.kor, F.mix, F.row, F.face].every(x => String(x).indexOf('"') < 0));
  ok('@font-face 가 두 벌', (F.face.match(/@font-face/g) || []).length === 2, F.face.slice(0,60));
  ok('unicode-range 로 가른다', (F.face.match(/unicode-range/g) || []).length === 2);
  ok('영문·숫자 범위에 바탕체를 건다',
     /local\('BatangChe'\)[\s\S]{0,80}unicode-range:U\+0020-024F/.test(F.face));
  ok('한글 범위에 바탕을 건다',
     /local\('Batang'\)[\s\S]{0,120}U\+AC00-D7FF/.test(F.face));

  const doc = await pg.evaluate(() => __T("_asWrapDoc([], P())"));
  ok('인쇄 문서에 @font-face 가 들어간다', /@font-face\{font-family:ASmix/.test(doc));
  ok('전표 기본 글꼴이 섞은 글꼴', /\.as-slip\{[^}]*font-family:ASmix,Batang,'바탕'/.test(doc));
  ok('옛 글꼴 지정이 남아 있지 않다', !/font-family:Batang,"바탕",BatangChe/.test(doc));

  // ── ② 칸마다 글꼴을 따로 주지 않는다 ──
  const g = await pg.evaluate(() => {
    var rows = []; for (var i = 1; i <= 3; i++) rows.push({ spec:'ABC-'+i, name:'품목'+i, qty:7000+i, price:800+i, supply:5000+i, tax:60+i });
    var dr = { vid:'v1', vname:'가나 주식회사', biz:'999-99-99999', ceo:'라마', addr:'서울 어딘가' };
    var html = __T("_asDocHtml")(dr, [{ ship:'20260101', date:'2026-11-27', no:7, rows:rows, memo:'메모' }], 'form');
    var css = (html.match(/<style>([\s\S]*?)<\/style>/) || [,''])[1];
    var body = html.replace(/^[\s\S]*<body>/, '').replace(/<\/body>[\s\S]*$/, '');
    var d = document.createElement('div'); d.style.cssText = 'position:relative';
    d.innerHTML = '<style>' + css + '</style>' + body;
    document.body.appendChild(d);
    var slip = d.querySelector('.as-pos .as-slip');
    var fs = [].slice.call(slip.querySelectorAll('.as-f'));
    var inline = fs.filter(function(e){ return /font-family/.test(e.getAttribute('style') || ''); }).length;
    function pick(re){ return fs.filter(function(e){ return re.test(e.textContent); })[0]; }
    function info(e){ if(!e) return null; var c = getComputedStyle(e);
      return { fam:c.fontFamily, al:c.textAlign, px:parseFloat(c.fontSize), t:e.textContent.slice(0,14) }; }
    var r = { inline:inline, slipFam:getComputedStyle(slip).fontFamily,
              no:info(pick(/^1$/)), name:info(pick(/^품목1/)), qty:info(pick(/^7,001$/)),
              sup:info(pick(/^5,001$/)), empty:info(pick(/이 하 여 백/)),
              biz:info(pick(/^999-99-99999$/)), vname:info(pick(/^가나/)), ceo:info(pick(/^라마$/)) };
    d.remove(); return r;
  });
  ok('칸에 font-family 를 직접 쓰지 않는다', g.inline === 0, g.inline);
  const isMix = f => /^ASmix/.test(String(f).replace(/["']/g, ''));
  ok('전표가 섞은 글꼴을 쓴다', isMix(g.slipFam), g.slipFam);
  ['no','name','qty','sup','empty','biz','vname','ceo'].forEach(k =>
    ok('모든 칸이 같은 글꼴 — ' + k, g[k] && isMix(g[k].fam), g[k] && g[k].fam));
  ok('번호는 가운데 정렬 그대로', g.no && g.no.al === 'center', g.no && g.no.al);
  ok('수량·금액은 오른쪽 정렬 그대로', g.qty && g.qty.al === 'right' && g.sup && g.sup.al === 'right');
  ok('품명은 왼쪽 정렬 그대로', g.name && g.name.al === 'left', g.name && g.name.al);

  // ── ③ 상호·성명·사업자등록번호를 키웠다 ──
  const knob = await pg.evaluate(() => { var q = __T("P()"); return { head:q.fsHead, fs:q.fs, sub:q.fsSub }; });
  ok('fsHead 손잡이가 있다', typeof knob.head === 'number', JSON.stringify(knob));
  ok('fsHead 가 본문(fs)보다 크다', knob.head > knob.fs, JSON.stringify(knob));
  ok('fsHead 가 작은 칸(fsSub)보다 크다', knob.head > knob.sub, JSON.stringify(knob));
  const PX = pt => pt * 4 / 3;
  ok('사업자등록번호가 fsHead 크기', g.biz && Math.abs(g.biz.px - PX(knob.head)) < 0.6, g.biz && g.biz.px);
  ok('상호가 fsHead 크기', g.vname && Math.abs(g.vname.px - PX(knob.head)) < 0.6, g.vname && g.vname.px);
  ok('성명이 fsHead 크기', g.ceo && Math.abs(g.ceo.px - PX(knob.head)) < 0.6, g.ceo && g.ceo.px);
  ok('예전 크기(9pt·10pt)로 찍히지 않는다',
     g.vname && Math.abs(g.vname.px - 12) > 0.6 && g.biz && Math.abs(g.biz.px - PX(knob.fs)) > 0.6);

  const src = await pg.evaluate(() => document.documentElement.innerHTML);
  ok('fsHead 가 저장되는 손잡이 목록에 있다', /_AS_KNOBS = \[[^\]]*'fsHead'\]/.test(src));
  ok('[인쇄 보정] 창에 칸이 있다', src.indexOf("fld('fsHead'") >= 0);

  // ── ④ 끌어오기 표시는 드롭 칸 안에서만 ──
  await pg.evaluate(() => __T("asTab('new'); _asDrafts=[]; _asRaw=null; _asFileName=''; _asShowInput=false; _asRender();"));
  await pg.waitForTimeout(400);
  const dz = await pg.evaluate(() => {
    var el = document.getElementById('pageAudit'), z = document.getElementById('asDrop');
    if (!z) return null;
    var w0 = z.getBoundingClientRect().width;
    __T("_asDropOn(true)");
    var on = { page:el.style.boxShadow, pageOut:el.style.outline, zs:z.style.boxShadow,
               zb:getComputedStyle(z).borderColor, w:z.getBoundingClientRect().width,
               bs:getComputedStyle(z).boxSizing };
    __T("_asDropOn(false)");
    var off = { page:el.style.boxShadow, zs:z.style.boxShadow, zb:getComputedStyle(z).borderColor,
                w:z.getBoundingClientRect().width };
    return { w0:w0, on:on, off:off };
  });
  ok('페이지 전체에는 아무 표시도 걸지 않는다', dz && !dz.on.page && !dz.on.pageOut, dz && JSON.stringify(dz.on));
  ok('드롭 칸 안쪽(inset) 그림자로 표시한다', dz && /inset/.test(dz.on.zs), dz && dz.on.zs);
  ok('드롭 칸 테두리가 남색으로 바뀐다', dz && /27, 58, 107/.test(dz.on.zb), dz && dz.on.zb);
  ok('끌기를 멈추면 모두 사라진다',
     dz && !dz.on.page && !dz.off.zs && !/27, 58, 107/.test(dz.off.zb), dz && JSON.stringify(dz.off));
  ok('드롭 칸 크기가 변하지 않는다',
     dz && Math.abs(dz.on.w - dz.w0) < 0.5 && Math.abs(dz.off.w - dz.w0) < 0.5,
     dz && JSON.stringify([dz.w0, dz.on.w, dz.off.w]));
  ok('드롭 칸이 border-box', dz && dz.on.bs === 'border-box', dz && dz.on.bs);

  // 실제 끌어오기 이벤트로도 같은지
  const drag = await pg.evaluate(() => {
    var el = document.getElementById('pageAudit'), z = document.getElementById('asDrop');
    var dt = new DataTransfer(); dt.items.add(new File(['x'], 'a.xls', { type:'application/vnd.ms-excel' }));
    el.dispatchEvent(new DragEvent('dragover', { bubbles:true, cancelable:true, dataTransfer:dt }));
    var on = { page:el.style.boxShadow, zs:z.style.boxShadow };
    el.dispatchEvent(new DragEvent('dragleave', { bubbles:true, dataTransfer:dt }));
    return { on:on, off:{ zs:z.style.boxShadow } };
  });
  ok('실제 끌어오기에서도 칸 안에만 표시된다',
     !drag.on.page && /inset/.test(drag.on.zs) && !drag.off.zs, JSON.stringify(drag));

  ok('pageerror 없음', errs.length === 0, errs.slice(0,2).join(' | '));
  await b.close(); return out();

  function out(){
    let p = 0; P.forEach(x => { if (x[1]) p++; console.log((x[1]?'  OK  ':'  FAIL') + '  ' + x[0] + (x[1]?'':'   → ' + x[2])); });
    console.log('\n[' + LABEL + '] ' + p + '/' + P.length);
    process.exit(p === P.length ? 0 : 1);
  }
})().catch(e => { console.error('EXC', e); process.exit(2); });
