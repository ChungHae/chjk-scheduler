// r281 테스트 — 감사 거래명세표 줄: 접기 단추 맨 앞 · 항목 세로 정렬 · 수량 가운데
//  사용:  node test_r281.js <index.html(__T 주입본)> [라벨]
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
    __T("_fbDbUrl='https://stub';");
    __T("_fbFetch=async function(){ return { ok:true, json:async function(){ return null; } }; };");
    __T("_fbPutOk=async function(){ return true; };");
    __T("_asCfgLoaded=true; _asPos=Object.assign({},_AS_POS0); _asMap={};");
    __T("switchPage('audit')");
  });
  await pg.waitForTimeout(600);

  const has = await pg.evaluate(()=>!!document.querySelector('style, link') && typeof window.asToggleDoc==='function');
  // 전표 3개 — 금액 길이가 크게 다른 것으로 섞는다
  await pg.evaluate(()=>{
    function mk(n,off,p){ var r=[]; for(var i=0;i<n;i++){ var k=off+i,q=(k%7)+1,pr=p+k*131;
      r.push({spec:'P-'+k,name:'CYLINDER',qty:q,price:pr,supply:q*pr,tax:Math.round(q*pr*0.1)}); } return r; }
    window.__DR={ key:'k', ucode:'H0T', uname:'하나코리아', list:[], vid:'v1', vname:'하나코리아 주식회사',
      biz:'357-87-03525', ceo:'윤석봉', addr:'서울',
      docs:[{ship:'20261106',date:'2026-11-10',warn:'',no:12,rows:mk(18,1,10000),memo:''},
            {ship:'20261117',date:'2026-11-19',warn:'',no:5,rows:mk(4,100,250000),memo:''},
            {ship:'20261125',date:'2026-11-27',warn:'',no:28,rows:mk(136,200,7000),memo:''}] };
    __T("_asFileName='x.xls'"); __T("_asRaw=new Array(158)");
    __T("_asDrafts=[window.__DR]"); __T("_asRender()");
  });
  await pg.waitForTimeout(400);

  const rows = await pg.evaluate(()=>document.querySelectorAll('#pageAudit .as-doc-row').length);
  if(!rows){
    ['전표 줄 격자','단추 맨 앞','세로 정렬','수량 가운데'].forEach(n=>ok('r281 기능 없음 — '+n,false));
    ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
    await b.close(); return out();
  }
  ok('전표 줄 3개가 as-doc-row 로 그려진다', rows===3, rows);
  ok('as-doc-row 가 격자다',
     await pg.evaluate(()=>getComputedStyle(document.querySelector('#pageAudit .as-doc-row')).display==='grid'));

  // ① 접기 표시가 맨 앞 (r283: 단추를 없애고 줄 전체를 누른다)
  ok('접기 표시가 줄의 첫 칸',
     await pg.evaluate(()=>Array.prototype.every.call(document.querySelectorAll('#pageAudit .as-doc-row'),
       function(r){ var f=r.children[0]; return f && /[\u25b8\u25be]/.test(f.textContent); })));
  ok('단추 바로 오른쪽이 물류출하일',
     await pg.evaluate(()=>Array.prototype.every.call(document.querySelectorAll('#pageAudit .as-doc-row'),
       function(r){ return /물류출하일/.test(r.children[1].textContent); })));

  // ② 같은 항목끼리 세로로 맞는지 — 실제 좌표로 확인
  const cols = await pg.evaluate(()=>{
    var rs=Array.prototype.slice.call(document.querySelectorAll('#pageAudit .as-doc-row'));
    var out=[];
    for(var c=0;c<5;c++){
      var xs=rs.map(function(r){ return Math.round(r.children[c].getBoundingClientRect().left); });
      out.push({ c:c, xs:xs, same: xs.every(function(x){ return Math.abs(x-xs[0])<=1; }) });
    }
    return out;
  });
  ['접기 단추','물류출하일','발행일','번호','금액'].forEach(function(nm,i){
    ok(nm+' 가 세로로 맞는다', cols[i].same, cols[i].xs.join(','));
  });
  ok('비고는 오른쪽 끝에 맞는다', await pg.evaluate(()=>{
    var rs=Array.prototype.slice.call(document.querySelectorAll('#pageAudit .as-doc-row'));
    var xs=rs.map(function(r){ return Math.round(r.children[5].getBoundingClientRect().right); });
    return xs.every(function(x){ return Math.abs(x-xs[0])<=1; });
  }));

  // ③ 수량 가운데
  await pg.evaluate(()=>__T("asToggleDoc(0,1)")); await pg.waitForTimeout(500);
  const qty = await pg.evaluate(()=>{
    var t=document.querySelector('#pageAudit table'); if(!t) return null;
    var ths=Array.prototype.map.call(t.querySelectorAll('thead th'), function(e){ return e.textContent.trim(); });
    var qi=ths.indexOf('수량');                      // r283: 품목·규격이 나뉘어 자리가 밀렸다
    var th=t.querySelectorAll('thead th')[qi], td=t.querySelectorAll('tbody tr')[0].children[qi];
    return { head:getComputedStyle(th).textAlign, cell:getComputedStyle(td).textAlign,
             headTxt:th.textContent.trim(),
             price:getComputedStyle(t.querySelectorAll('tbody tr')[0].children[qi+1]).textAlign };
  });
  ok('수량 머리가 가운데', qty && qty.head==='center' && qty.headTxt==='수량', qty?JSON.stringify(qty):'(표 없음)');
  ok('수량 칸이 가운데', qty && qty.cell==='center', qty?qty.cell:'');
  ok('단가는 그대로 오른쪽', qty && qty.price==='right', qty?qty.price:'');

  // 접기 동작 유지
  ok('단추를 누르면 표가 열린다/닫힌다', await (async()=>{
      var before = await pg.evaluate(()=>document.querySelectorAll('#pageAudit table').length);
      await pg.evaluate(()=>document.querySelectorAll('#pageAudit .as-doc-row')[1].children[0].click());
      await pg.waitForTimeout(400);
      var after = await pg.evaluate(()=>document.querySelectorAll('#pageAudit table').length);
      return before===1 && after===0;
    })());

  ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
  await b.close(); return out();

  function out(){
    let p=0; P.forEach(x=>{ if(x[1]) p++; console.log((x[1]?'  OK  ':'  FAIL')+'  '+x[0]+(x[1]?'':'   → '+x[2])); });
    console.log('\n['+LABEL+'] '+p+'/'+P.length);
    process.exit(p===P.length?0:1);
  }
})();
