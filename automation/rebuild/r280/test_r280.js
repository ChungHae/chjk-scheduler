// r280 테스트 — 감사: 업체 검색 디자인 통일 · 품목 표 기본 접힘 · 빈 품목 칸 정리
//  사용:  node test_r280.js <index.html(__T 주입본)> [라벨]
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

  await pg.evaluate(() => {
    var g=document.getElementById('authGate'); if(g) g.style.display='none';
    __T("_authUser={id:'chjk',name:'김재성',role:'master'}");
    __T("debouncedFbSave=function(){}; doFbSave=function(){}; saveAll=function(){};");
    __T("window.__INFO=''; showInfoModal=function(t,m){ window.__INFO=(t||'')+' | '+(m||''); };");
    __T("_fbDbUrl='https://stub';");
    __T("_fbFetch=async function(){ return { ok:true, json:async function(){ return null; } }; };");
    __T("_fbPutOk=async function(){ return true; };");
    __T("_qBlobGet=async function(){ return [{spec:'P-0004',name:'CYLINDER'}]; };");
    __T("_asCfgLoaded=true; _asPos=Object.assign({},_AS_POS0); _asMap={};");
    __T("quoteVendors=[{id:'v1',name:'하나코리아 주식회사',count:412},{id:'v2',name:'하나정밀(주)',count:87}]");
    __T("clientList=[['하나코리아 주식회사','357-87-03525','서울'],['하나정밀(주)','123-45-67890','서울'],['하나테크','221-81-55512','화성'],['다른회사','999-99-99999','서울']]");
    __T("switchPage('audit')");
  });
  await pg.waitForTimeout(700);

  const has = await pg.evaluate(()=>typeof window.asVdd==='function' && typeof window.asToggleDoc==='function');
  if(!has){
    ['업체 검색칸','드롭다운 목록','검색 거르기','클릭 연결','키보드 연결','품목 기본 접힘','펼치기','빈 품목 격자']
      .forEach(n => ok('r280 기능 없음 — ' + n, false));
    ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
    await b.close(); return out();
  }

  // ── 업체 연결 안 된 묶음 ──
  await pg.evaluate(()=>{
    window.__DR={ key:'H0T|하나코리아', ucode:'H0T', uname:'하나코리아',
      list:[{ucode:'H0T',uname:'하나코리아',spec:'P-0004',qty:1,price:1000,ship:'20261106'}],
      vid:'', vname:'', biz:'', ceo:'', addr:'', docs:[] };
    __T("_asFileName='x.xls'"); __T("_asRaw=new Array(1)");
    __T("_asDrafts=[window.__DR]"); __T("_asRender()");
  });
  await pg.waitForTimeout(300);

  ok('옛 datalist 가 없다', await pg.evaluate(()=>!document.getElementById('asClients')));
  ok('업체 검색칸이 견적과 같은 q-flat',
     await pg.evaluate(()=>{ var i=document.getElementById('asV0'); return !!i && i.classList.contains('q-flat') && !i.getAttribute('list'); }));
  ok('드롭다운 칸이 있다', await pg.evaluate(()=>!!document.getElementById('asVdd0')));

  await pg.fill('#asV0','하나'); await pg.waitForTimeout(300);
  const dd = await pg.evaluate(()=>{
    var d=document.getElementById('asVdd0');
    return { shown:getComputedStyle(d).display!=='none', n:d.querySelectorAll('.asvd-item').length, html:d.innerHTML };
  });
  ok('검색하면 목록이 뜬다', dd.shown && dd.n===3, 'n='+dd.n);
  ok('원장 있는 업체는 규격 수를 보여 준다', /규격 412/.test(dd.html) && /규격 87/.test(dd.html));
  ok('원장 없는 업체는 "원장 없음"', /원장 없음/.test(dd.html));
  ok('사업자번호를 같이 보여 준다', /357-87-03525/.test(dd.html));
  ok('검색어에 맞는 것만 — "다른회사" 는 빠진다', !/다른회사/.test(dd.html));

  // 클릭 연결
  await pg.evaluate(()=>{ var it=document.querySelectorAll('#asVdd0 .asvd-item')[1]; it.click(); });
  await pg.waitForTimeout(900);
  ok('목록을 누르면 업체가 이어진다',
     await pg.evaluate(()=>{ var d=__T("_asDrafts")[0]; return d.vname==='하나코리아 주식회사' && d.vid==='v1'; }),
     await pg.evaluate(()=>JSON.stringify({v:__T("_asDrafts")[0].vname, id:__T("_asDrafts")[0].vid})));
  ok('이어지면 거래명세표가 만들어진다', await pg.evaluate(()=>__T("_asDrafts")[0].docs.length===1));

  // 키보드 연결
  await pg.evaluate(()=>{ __T("_asDrafts")[0].vname=''; __T("_asDrafts")[0].vid=''; __T("_asDrafts")[0].docs=[]; __T("_asRender()"); });
  await pg.waitForTimeout(300);
  await pg.fill('#asV0','하나정밀'); await pg.waitForTimeout(300);
  await pg.focus('#asV0');
  await pg.keyboard.press('ArrowDown'); await pg.keyboard.press('Enter');
  await pg.waitForTimeout(900);
  ok('↓ + Enter 로도 이어진다', await pg.evaluate(()=>__T("_asDrafts")[0].vname==='하나정밀(주)'),
     await pg.evaluate(()=>__T("_asDrafts")[0].vname));

  // ── 품목 표 기본 접힘 ──
  await pg.evaluate(()=>{
    function mk(n){ var r=[]; for(var i=1;i<=n;i++) r.push({spec:'P-'+i,name:(i%3?'':'CYLINDER'),qty:1,price:1000,supply:1000,tax:100}); return r; }
    window.__DR2={ key:'k', ucode:'H0T', uname:'하나코리아', list:[], vid:'v1', vname:'하나코리아 주식회사',
      biz:'357-87-03525', ceo:'홍길동', addr:'서울',
      docs:[{ship:'20261106',date:'2026-11-10',warn:'',no:7,rows:mk(260),memo:''}] };
    __T("_asDrafts=[window.__DR2]"); __T("_asShowInput=true"); __T("_asRender()");
  });
  await pg.waitForTimeout(400);
  ok('품목 표가 기본으로 접혀 있다',
     await pg.evaluate(()=>document.querySelectorAll('#pageAudit table').length===0));
  ok('접힘 표시(▸)가 줄 맨 앞에 있다',   // r283: '260품목 · 2장' 표시는 없앴다
     await pg.evaluate(()=>/\u25b8/.test(document.querySelector('#pageAudit .as-doc-row').children[0].textContent)),
     await pg.evaluate(()=>document.querySelector('#pageAudit .as-doc-row').children[0].textContent));

  await pg.evaluate(()=>__T("asToggleDoc(0,0)")); await pg.waitForTimeout(500);
  const open = await pg.evaluate(()=>({
    tables:document.querySelectorAll('#pageAudit table').length,
    rows:document.querySelectorAll('#pageAudit table tbody tr').length,
    more:/앞 200줄만 보여 줍니다/.test(document.getElementById('pageAudit').innerText),
    mark:/\u25be/.test(document.querySelector('#pageAudit .as-doc-row').children[0].textContent)
  }));
  ok('누르면 표가 펼쳐진다', open.tables===1 && open.mark, JSON.stringify(open));
  ok('아주 긴 표는 앞 200줄만 그린다', open.rows===200 && open.more, 'rows='+open.rows);

  await pg.evaluate(()=>__T("asToggleDoc(0,0)")); await pg.waitForTimeout(400);
  ok('다시 누르면 접힌다', await pg.evaluate(()=>document.querySelectorAll('#pageAudit table').length===0));

  // ── 빈 품목 칸 ──
  const miss = await pg.evaluate(()=>{
    var g=document.querySelector('#pageAudit div[style*="grid-template-columns"]');
    if(!g) return null;
    var st=getComputedStyle(g);
    return { cells:g.children.length, maxh:st.maxHeight, over:st.overflowY };
  });
  ok('못 찾은 품번이 격자로 들어간다', !!miss && miss.cells>20, miss?JSON.stringify(miss):'(격자 없음)');
  ok('칸이 많아도 안쪽에서만 스크롤된다', !!miss && /px/.test(miss.maxh) && (miss.over==='auto'||miss.over==='scroll'),
     miss?miss.maxh+' / '+miss.over:'');

  await pg.evaluate(()=>{ var i=document.querySelector('#pageAudit input[data-sp]'); i.value='VALVE'; i.dispatchEvent(new Event('input',{bubbles:true})); });
  await pg.waitForTimeout(300);
  ok('품목을 적으면 같은 품번 줄에 바로 들어간다',
     await pg.evaluate(()=>{ var sp=document.querySelector('#pageAudit input[data-sp]').dataset.sp;
       return __T("_asDrafts")[0].docs[0].rows.some(function(r){ return r.spec===sp && r.name==='VALVE'; }); }));
  await pg.evaluate(()=>__T("_asRender()")); await pg.waitForTimeout(300);
  ok('입력한 개수가 표시된다', await pg.evaluate(()=>/1종 입력함/.test(document.getElementById('pageAudit').innerText)));

  ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
  await b.close(); return out();

  function out(){
    let p=0; P.forEach(x=>{ if(x[1]) p++; console.log((x[1]?'  OK  ':'  FAIL')+'  '+x[0]+(x[1]?'':'   → '+x[2])); });
    console.log('\n['+LABEL+'] '+p+'/'+P.length);
    process.exit(p===P.length?0:1);
  }
})();
