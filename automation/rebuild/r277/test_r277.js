// r277 테스트 — 업무 > 감사: 엑셀 읽기 · 영업일 · 한글 금액 · 13줄 규칙 · 인쇄본
//  사용:  node test_r277.js <index.html(__T 주입본)> [라벨]
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
    __T("window.__INFO=''; showInfoModal=function(t,m){ window.__INFO=(t||'')+' | '+(m||''); };");
    __T("window.__LEDGER=[{spec:'CDJ2F16-60Z-B',name:'CYLINDER'},{spec:'AW10-M5BG-A',name:'REGULATOR'}];");
    __T("_qBlobGet=async function(id){ return JSON.parse(JSON.stringify(window.__LEDGER)); };");
    __T("_qBlobPut=async function(id,rows){ window.__LEDGER=JSON.parse(JSON.stringify(rows)); return true; };");
    __T("_fbDbUrl='https://stub';");
    __T("_fbFetch=async function(u){ return { ok:true, json:async function(){ return null; } }; };");
    __T("_fbPutOk=async function(){ return true; };");
  });

  const has = await T("typeof renderAuditPage==='function'");
  if(!has){
    ['감사 탭','감사 하위 탭','한글 금액','영업일 +2','주말 건너뜀','엑셀 읽기','품목 결합',
     '12줄 이하여백','13줄 여백 없음','14줄 2장','총금액 첫 장','계 마지막 장','번호 1~29','전표 2벌']
      .forEach(n => ok('r277 기능 없음 — ' + n, false));
    ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
    await b.close(); return out();
  }

  // ── 탭 ──
  ok('업무 하위 탭에 [감사]',
     await pg.evaluate(()=>{ var e=document.querySelector('.sub-tab[data-page="audit"]'); return !!e && e.textContent.trim()==='감사'; }));
  ok('감사 페이지 칸 있음', await pg.evaluate(()=>!!document.getElementById('pageAudit')));
  await pg.evaluate(()=>__T("switchPage('audit')")); await pg.waitForTimeout(900);
  ok('[감사] 열면 업무 탭이 켜진다',
     await pg.evaluate(()=>document.getElementById('pageAudit').classList.contains('active')
       && document.getElementById('tabEtc').classList.contains('active')
       && getComputedStyle(document.getElementById('etcSubNav')).display!=='none'));
  ok('안내문·[엑셀 올리기] 보임',
     await pg.evaluate(()=>/엑셀 올리기/.test(document.getElementById('pageAudit').innerHTML)
       && /유저특가/.test(document.getElementById('pageAudit').innerHTML)));

  // ── 한글 금액 (샘플: 1,811,007 → 일백팔십일만천칠원) ──
  ok('한글 금액 — 샘플과 같다', await pg.evaluate(()=>__T("_asKoAmt")(1811007)==='일백팔십일만천칠원'),
     await pg.evaluate(()=>__T("_asKoAmt")(1811007)));
  ok('한글 금액 — 1,000원', await pg.evaluate(()=>__T("_asKoAmt")(1000)==='일천원'), await pg.evaluate(()=>__T("_asKoAmt")(1000)));
  ok('한글 금액 — 20,350원', await pg.evaluate(()=>__T("_asKoAmt")(20350)==='이만삼백오십원'), await pg.evaluate(()=>__T("_asKoAmt")(20350)));
  ok('한글 금액 — 153,450원 (일십 아님)', await pg.evaluate(()=>__T("_asKoAmt")(153450)==='십오만삼천사백오십원'), await pg.evaluate(()=>__T("_asKoAmt")(153450)));
  ok('한글 금액 — 100,000,000원', await pg.evaluate(()=>__T("_asKoAmt")(100000000)==='일억원'), await pg.evaluate(()=>__T("_asKoAmt")(100000000)));

  // ── 영업일 +2 ──
  const d1 = await pg.evaluate(async()=>(await __T("_asAddBizDays")('20261106',2)).date);
  ok('물류출하일 11/06(금) +2영업일 = 11/10(화)', d1==='2026-11-10', d1);
  const d2 = await pg.evaluate(async()=>(await __T("_asAddBizDays")('20261117',2)).date);
  ok('11/17(화) +2영업일 = 11/19(목)', d2==='2026-11-19', d2);
  const d3 = await pg.evaluate(async()=>(await __T("_asAddBizDays")('20261127',2)).date);
  ok('11/27(금) +2영업일 = 12/01(화) — 주말 건너뜀', d3==='2026-12-01', d3);
  const w1 = await pg.evaluate(async()=>(await __T("_asAddBizDays")('20261106',2)).warn);
  ok('공휴일 못 받으면 안내가 붙는다', !!w1, w1);

  // ── 엑셀 읽기 (SMC 유저특가 표) ──
  const parsed = await pg.evaluate(()=>{
    var html='<table><tr><td>의뢰번호</td><td>유저</td><td>유저명</td><td>품번</td><td>수량</td><td>유저특가</td><td>물류출하일</td></tr>'
      +'<tr><td>A1</td><td>H0T</td><td>하나코리아</td><td>CDJ2F16-60Z-B</td><td>2</td><td>15,500</td><td>20261106</td></tr>'
      +'<tr><td>A2</td><td>H0T</td><td>하나코리아</td><td>AW10-M5BG-A</td><td>1</td><td>20,000</td><td>20261106</td></tr>'
      +'<tr><td>A3</td><td>H0T</td><td>하나코리아</td><td>ZSE20AF-R-01-J</td><td>1</td><td>56,500</td><td>20261125</td></tr></table>';
    var buf=new TextEncoder().encode(html).buffer;
    var r=__T("_asParseFile")(buf);
    return { n:r.length, first:r[0], ships:Array.from(new Set(r.map(function(x){return x.ship;}))) };
  });
  ok('엑셀 3줄을 읽는다', parsed.n===3, parsed.n);
  ok('품번·수량·유저특가·유저명을 읽는다',
     parsed.first.spec==='CDJ2F16-60Z-B' && parsed.first.qty===2 && parsed.first.price===15500 && parsed.first.uname==='하나코리아',
     JSON.stringify(parsed.first));
  ok('물류출하일이 2종', parsed.ships.length===2, parsed.ships.join(','));

  // ── 원장 품목 결합 ──
  const draft = await pg.evaluate(async()=>{
    var list=[{ucode:'H0T',uname:'하나코리아',spec:'CDJ2F16-60Z-B',qty:2,price:15500,ship:'20261106'},
              {ucode:'H0T',uname:'하나코리아',spec:'AW10-M5BG-A',qty:1,price:20000,ship:'20261106'},
              {ucode:'H0T',uname:'하나코리아',spec:'NO-SUCH-PN',qty:3,price:1000,ship:'20261106'}];
    var dr=await __T("_asBuildDraft")(list,'v1','하나코리아');
    return { docs:dr.docs.length, rows:dr.docs[0].rows, no:dr.docs[0].no, date:dr.docs[0].date };
  });
  ok('원장에서 품목을 찾아 붙인다', draft.rows[0].name==='CYLINDER', JSON.stringify(draft.rows[0]));
  ok('공급가액 = 수량 × 단가', draft.rows[0].supply===31000 && draft.rows[0].tax===3100, JSON.stringify(draft.rows[0]));
  ok('원장에 없는 품번은 품목이 빈다', draft.rows[2].name==='', JSON.stringify(draft.rows[2]));
  ok('거래명세서 번호가 1~29', draft.no>=1 && draft.no<=29, draft.no);

  // ── 13줄 규칙 · 인쇄본 ──
  const pageInfo = await pg.evaluate(()=>{
    function mk(n){ var rows=[]; for(var i=1;i<=n;i++) rows.push({spec:'P'+i,name:'품목'+i,qty:1,price:1000,supply:1000,tax:100}); return rows; }
    var dr={vid:'',vname:'하나코리아',biz:'111-11-11111',ceo:'홍길동',addr:'서울'};
    function info(n){
      var html=__T("_asDocHtml")(dr,[{ship:'20261106',date:'2026-11-10',no:7,rows:mk(n),memo:''}],false);
      return { pages:(html.match(/class="as-page"/g)||[]).length,
               empty:(html.match(/- 이 하 여 백 -/g)||[]).length,
               total:(html.match(/整/g)||[]).length,
               html:html };
    }
    var a=info(12), b=info(13), c=info(14);
    return { p12:a.pages, e12:a.empty, p13:b.pages, e13:b.empty, p14:c.pages, e14:c.empty,
             t12:a.total, t14:c.total, h14:c.html };
  });
  ok('12줄 → 1장 + 이하여백', pageInfo.p12===1 && pageInfo.e12===2, 'pages '+pageInfo.p12+' 여백 '+pageInfo.e12);
  ok('13줄 → 1장 · 이하여백 없음', pageInfo.p13===1 && pageInfo.e13===0, 'pages '+pageInfo.p13+' 여백 '+pageInfo.e13);
  ok('14줄 → 2장 · 둘째 장에만 이하여백', pageInfo.p14===2 && pageInfo.e14===2, 'pages '+pageInfo.p14+' 여백 '+pageInfo.e14);
  ok('총금액(整)은 첫 장에만 — 전표 2벌이라 2개', pageInfo.t14===2, pageInfo.t14);
  ok('한 장에 전표 2벌', pageInfo.p12===1 && (pageInfo.h14.match(/class="as-slip/g)||[]).length===4,
     (pageInfo.h14.match(/class="as-slip/g)||[]).length);
  ok('품명은 "품목  품번" 으로 찍힌다', /품목1  P1/.test(pageInfo.h14));
  ok('A4 · 여백 0 인쇄 설정', /@page\{size:A4;margin:0\}/.test(pageInfo.h14));
  ok('양식 그림을 넣지 않는다(글자만)', !/<img/i.test(pageInfo.h14) && !/background-image/i.test(pageInfo.h14));

  ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
  await b.close(); return out();

  function out(){
    let p=0; P.forEach(x=>{ if(x[1]) p++; console.log((x[1]?'  OK  ':'  FAIL')+'  '+x[0]+(x[1]?'':'   → '+x[2])); });
    console.log('\n['+LABEL+'] '+p+'/'+P.length);
    process.exit(p===P.length?0:1);
  }
})();
