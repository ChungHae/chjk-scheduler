// r276 테스트 — 상단 [업무] · 하위 탭 [사이트] 이름과 동작
//  사용:  node test_r276.js <index.html(__T 주입본)> [라벨]
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const FILE = process.argv[2], LABEL = process.argv[3] || '?';
const P = [];
const ok = (n, c, e) => P.push([n, !!c, e === undefined ? '' : String(e)]);

(async () => {
  const b = await chromium.launch({});
  const pg = await (await b.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:950} })).newPage();
  await pg.route(/^https?:\/\//, r => r.abort());
  const errs=[]; pg.on('pageerror', e=>errs.push(String(e).slice(0,200)));
  await pg.goto('file://'+FILE); await pg.waitForTimeout(3200);
  const T = c => pg.evaluate(c2 => window.__T(c2), c);

  await pg.evaluate(() => {
    var g=document.getElementById('authGate'); if(g) g.style.display='none';
    __T("_authUser={id:'chjk',name:'김재성',role:'master'}");
    __T("debouncedFbSave=function(){}; doFbSave=function(){}; saveAll=function(){};");
  });

  // ── 이름 ──
  ok('상단 탭 이름 = 업무',
     await pg.evaluate(()=>document.getElementById('tabEtc').textContent.trim()==='업무'),
     await pg.evaluate(()=>document.getElementById('tabEtc').textContent.trim()));
  ok('하위 탭 이름 = 사이트',
     await pg.evaluate(()=>document.querySelector('.sub-tab[data-page="links"]').textContent.trim()==='사이트'),
     await pg.evaluate(()=>document.querySelector('.sub-tab[data-page="links"]').textContent.trim()));
  ok('페이지 제목 = 사이트',
     await pg.evaluate(()=>document.querySelector('#pageLinks .inv-flat-label').textContent.trim()==='사이트'),
     await pg.evaluate(()=>document.querySelector('#pageLinks .inv-flat-label').textContent.trim()));
  ok('화면에 옛 이름 "업무 사이트" 없음',
     await pg.evaluate(()=>!/업무\s*사이트/.test(document.body.innerHTML)));

  // ── 메뉴 순서(r252 가 정한 순서에서 이름만 바뀐다) ──
  const labels = await pg.evaluate(()=>Array.from(document.querySelectorAll('.page-nav .page-tab')).map(b=>b.textContent.trim()).join(','));
  // 정식(r272)에는 [거래명세서] 가 없고 테스트(r273 이후)에는 있다 — 둘 다 인정하되 '업무' 자리는 발주 다음으로 고정
  const NAV_OK = ['일정,견적,발주,업무,재고,회계,자료실,내규',
                  '일정,견적,발주,거래명세서,업무,재고,회계,자료실,내규'];   // r279: 매입처는 업무 하위로
  ok('상단 메뉴 순서·이름', NAV_OK.indexOf(labels)>=0, labels);

  // ── 동작은 그대로 ──
  ok('id·data-page 그대로',
     await pg.evaluate(()=>!!document.getElementById('tabEtc') && !!document.getElementById('etcSubNav')
       && !!document.querySelector('.sub-tab[data-page="links"]') && !!document.getElementById('pageLinks')));
  await pg.evaluate(()=>document.getElementById('tabEtc').click());
  await pg.waitForTimeout(500);
  ok('[업무] 누르면 사이트 페이지가 열린다',
     await pg.evaluate(()=>document.getElementById('pageLinks').classList.contains('active')
       && document.getElementById('tabEtc').classList.contains('active')));
  ok('하위 탭 줄이 보인다',
     await pg.evaluate(()=>getComputedStyle(document.getElementById('etcSubNav')).display!=='none'));
  ok('하위 탭이 활성 표시된다',
     await pg.evaluate(()=>document.querySelector('.sub-tab[data-page="links"]').classList.contains('active')));
  ok('검색칸·지역 필터 그대로',
     await pg.evaluate(()=>!!document.getElementById('linksSearch') && !!document.getElementById('linksRegionFilter')));
  ok('다른 탭으로 가면 하위 탭 줄이 숨는다', await (async()=>{
       await pg.evaluate(()=>__T("switchPage('inventory')")); await pg.waitForTimeout(400);
       return pg.evaluate(()=>getComputedStyle(document.getElementById('etcSubNav')).display==='none');
     })());

  ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
  await b.close(); return out();

  function out(){
    let p=0; P.forEach(x=>{ if(x[1]) p++; console.log((x[1]?'  OK  ':'  FAIL')+'  '+x[0]+(x[1]?'':'   → '+x[2])); });
    console.log('\n['+LABEL+'] '+p+'/'+P.length);
    process.exit(p===P.length?0:1);
  }
})();
