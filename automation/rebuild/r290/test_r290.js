// r290 테스트 — 품목 줄만 고정폭 바탕체, 나머지는 바탕 그대로
//  사용:  node test_r290.js <index.html(__T 주입본)> [라벨]
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

  if (!(await pg.evaluate(() => typeof __T("_AS_FAM_ROW") === 'string'))) {
    ['품목 줄 글꼴','정렬 유지','이하여백은 그대로'].forEach(n => ok('r290 기능 없음 — ' + n, false));
    ok('pageerror 없음', errs.length === 0, errs.slice(0,2).join(' | '));
    await b.close(); return out();
  }

  ok('품목 줄 글꼴이 바탕체 먼저', await pg.evaluate(() => /^BatangChe/.test(__T("_AS_FAM_ROW"))), await pg.evaluate(() => __T("_AS_FAM_ROW")));
  ok('글꼴 이름에 큰따옴표를 쓰지 않는다',            // style="..." 안이라 큰따옴표면 속성이 깨진다
     await pg.evaluate(() => __T("_AS_FAM_ROW").indexOf('"') < 0), await pg.evaluate(() => __T("_AS_FAM_ROW")));
  ok('전표 기본 글꼴은 바탕 그대로', await pg.evaluate(() =>
     /font-family:Batang,"바탕",BatangChe/.test(__T("_asWrapDoc([], P())"))));

  const g = await pg.evaluate(() => {
    var rows = []; for (var i = 1; i <= 3; i++) rows.push({ spec:'ABC-'+i, name:'품목'+i, qty:7000+i, price:800+i, supply:5000+i, tax:60+i });
    var dr = { vid:'v1', vname:'가나 주식회사', biz:'999-99-99999', ceo:'라', addr:'마' };
    var html = __T("_asDocHtml")(dr, [{ ship:'20260101', date:'2026-11-27', no:7, rows:rows, memo:'메모' }], 'form');
    var css = (html.match(/<style>([\s\S]*?)<\/style>/) || [,''])[1];
    var body = html.replace(/^[\s\S]*<body>/, '').replace(/<\/body>[\s\S]*$/, '');
    var d = document.createElement('div'); d.style.cssText = 'position:relative';
    d.innerHTML = '<style>' + css + '</style>' + body;
    document.body.appendChild(d);
    var fs = [].slice.call(d.querySelector('.as-pos .as-slip').querySelectorAll('.as-f'));
    function pick(re){ return fs.filter(function(e){ return re.test(e.textContent); })[0]; }
    function info(e){ if(!e) return null; var c = getComputedStyle(e);
      return { fam: c.fontFamily, al: c.textAlign, t: e.textContent.slice(0,16) }; }
    var r = { no: info(pick(/^1$/)), name: info(pick(/^품목1/)), qty: info(pick(/^7,001$/)),
              sup: info(pick(/^5,001$/)), empty: info(pick(/이 하 여 백/)),
              ko: info(pick(/整$/)), vname: info(pick(/가나/)) };
    d.remove(); return r;
  });
  const isChe = f => /BatangChe/.test(String(f).split(',')[0]);
  ok('번호 칸이 바탕체', g.no && isChe(g.no.fam), g.no && g.no.fam);
  ok('품명 및 규격이 바탕체', g.name && isChe(g.name.fam), g.name && g.name.fam);
  ok('수량이 바탕체', g.qty && isChe(g.qty.fam), g.qty && g.qty.fam);
  ok('공급가액이 바탕체', g.sup && isChe(g.sup.fam), g.sup && g.sup.fam);
  ok('번호는 가운데 정렬 그대로', g.no && g.no.al === 'center', g.no && g.no.al);
  ok('수량·금액은 오른쪽 정렬 그대로', g.qty && g.qty.al === 'right' && g.sup && g.sup.al === 'right',
     JSON.stringify([g.qty && g.qty.al, g.sup && g.sup.al]));
  ok('품명은 왼쪽 정렬 그대로', g.name && g.name.al === 'left', g.name && g.name.al);
  ok('- 이 하 여 백 - 은 바탕 그대로', g.empty && !isChe(g.empty.fam), g.empty && g.empty.fam);
  ok('총금액 한글도 바탕 그대로', g.ko && !isChe(g.ko.fam), g.ko && g.ko.fam);
  ok('공급받는자 상호도 바탕 그대로', g.vname && !isChe(g.vname.fam), g.vname && g.vname.fam);

  // ── 쪽 표시 없애기 · [선택 삭제] 팝업 문구 ──
  const src = await pg.evaluate(() => document.documentElement.innerHTML);
  ok("쪽 이동 줄에 'n / N' 표시가 없다", src.indexOf("'+(_asLPage+1)+' / '+pages+'") < 0);
  ok('[처음]·[끝] 은 그대로', src.indexOf("_asBtn('처음','asLGo(0)')") >= 0 && src.indexOf("_asBtn('끝','asLGo('+(pages-1)+')')") >= 0);
  ok('선택 삭제 팝업이 한 줄', src.indexOf("'총 '+recs.length+'건의 거래명세표를 삭제합니다. 되돌릴 수 없습니다.'") >= 0);
  ok('선택 삭제 팝업에 세부 내역 없음', src.indexOf('고른 거래명세표를 모두 지웁니다') < 0 && src.indexOf("recs.slice(0,6).map") < 0);

  // ── 상호·주소: 한 줄 → 두 줄 → 축소 차례 ──
  const steps = await pg.evaluate(() => {
    function rep(ch, n){ var t=''; while(n-->0) t+=ch; return t; }
    function draw(vname, addr){
      var rows=[{spec:'A',name:'B',qty:1,price:1,supply:1,tax:0}];
      var dr={ vid:'v1', vname:vname, biz:'1', ceo:'다', addr:addr };
      var html=__T("_asDocHtml")(dr, [{ship:'20260101',date:'2026-11-27',no:1,rows:rows,memo:''}], 'form');
      var css=(html.match(/<style>([\s\S]*?)<\/style>/)||[,''])[1];
      var body=html.replace(/^[\s\S]*<body>/,'').replace(/<\/body>[\s\S]*$/,'');
      var d=document.createElement('div'); d.style.cssText='position:relative';
      d.innerHTML='<style>'+css+'</style>'+body; document.body.appendChild(d);
      var fs=[].slice.call(d.querySelector('.as-pos .as-slip').querySelectorAll('.as-f'));
      function grab(re){ return fs.filter(function(e){ return re.test(e.textContent); })
        .map(function(e){ return { t:e.textContent.slice(0,12), fs:parseFloat(getComputedStyle(e).fontSize) }; }); }
      var r = { vn:grab(/^[가나]/), ad:grab(/^[서어]/) };
      d.remove(); return r;
    }
    var V1 = rep('가',3),                              A1 = rep('서',6);
    var V2 = rep('가',5)+' '+rep('나',5),              A2 = rep('서',11)+' '+rep('어',11);
    var V3 = rep('가',12)+' '+rep('나',12),            A3 = rep('서',25)+' '+rep('어',25);
    return { short:draw(V1,A1), mid:draw(V2,A2), long:draw(V3,A3) };
  });
  const FS9 = 12;   // 9pt = 12px
  const same = v => Math.abs(v - FS9) < 0.6;
  ok('① 짧은 상호는 한 줄 · 원래 크기', steps.short.vn.length === 1 && same(steps.short.vn[0].fs), JSON.stringify(steps.short.vn));
  ok('① 짧은 주소도 한 줄 · 원래 크기', steps.short.ad.length === 1 && same(steps.short.ad[0].fs), JSON.stringify(steps.short.ad));
  ok('② 한 줄을 넘는 상호는 두 줄 · 크기 그대로',
     steps.mid.vn.length === 2 && same(steps.mid.vn[0].fs) && same(steps.mid.vn[1].fs), JSON.stringify(steps.mid.vn));
  ok('② 한 줄을 넘는 주소도 두 줄 · 크기 그대로',
     steps.mid.ad.length === 2 && same(steps.mid.ad[0].fs) && same(steps.mid.ad[1].fs), JSON.stringify(steps.mid.ad));
  ok('③ 두 줄로도 넘치면 그때 작아진다',
     steps.long.vn.length === 2 && steps.long.vn[0].fs < FS9 - 0.6 &&
     steps.long.ad.length === 2 && steps.long.ad[0].fs < FS9 - 0.6,
     JSON.stringify([steps.long.vn[0], steps.long.ad[0]]));

  // ── 끌어다 놓을 때 테두리가 칸 밖으로 나가지 않는다 ──
  const drag = await pg.evaluate(() => {
    __T("asTab('new'); _asDrafts=[]; _asRaw=null; _asFileName=''; _asShowInput=false; _asRender();");
    return null;
  });
  await pg.waitForTimeout(500);
  const dz = await pg.evaluate(() => {
    var el = document.getElementById('pageAudit');
    var z = document.getElementById('asDrop');
    if (!z) return null;
    var b0 = z.getBoundingClientRect();
    __T("_asDropOn(true)");
    var on = { pageShadow: el.style.boxShadow, pageOutline: el.style.outline,
               zBorder: getComputedStyle(z).borderColor, w: z.getBoundingClientRect().width,
               bs: getComputedStyle(z).boxSizing };
    __T("_asDropOn(false)");
    var off = { pageShadow: el.style.boxShadow, w: z.getBoundingClientRect().width };
    return { w0: b0.width, on: on, off: off };
  });
  ok('끌 때 바깥 outline 을 쓰지 않는다', dz && !dz.on.pageOutline, dz && dz.on.pageOutline);
  ok('끌 때 안쪽(inset) 그림자로 표시한다', dz && /inset/.test(dz.on.pageShadow), dz && dz.on.pageShadow);
  ok('끌기를 멈추면 표시가 사라진다', dz && !dz.off.pageShadow, dz && dz.off.pageShadow);
  ok('드롭 칸 크기가 변하지 않는다', dz && Math.abs(dz.on.w - dz.w0) < 0.5 && Math.abs(dz.off.w - dz.w0) < 0.5,
     dz && JSON.stringify([dz.w0, dz.on.w, dz.off.w]));
  ok('드롭 칸이 border-box', dz && dz.on.bs === 'border-box', dz && dz.on.bs);

  ok('pageerror 없음', errs.length === 0, errs.slice(0,2).join(' | '));
  await b.close(); return out();

  function out(){
    let p = 0; P.forEach(x => { if (x[1]) p++; console.log((x[1]?'  OK  ':'  FAIL') + '  ' + x[0] + (x[1]?'':'   → ' + x[2])); });
    console.log('\n[' + LABEL + '] ' + p + '/' + P.length);
    process.exit(p === P.length ? 0 : 1);
  }
})();
