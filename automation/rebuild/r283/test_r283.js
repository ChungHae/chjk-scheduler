// r283 테스트 — 줄 클릭 접힘/펼침 · 품목·규격 정렬 · 기간 입력 · 파일 비우기 · 칸 높이·정렬
//  사용:  node test_r283.js <index.html(__T 주입본)> [라벨]
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
    __T("window.__CONF=''; showConfirmModal=function(t,m,f){ window.__CONF=(t||'')+' | '+(m||''); window.__CONFOK=f; };");
    __T("_fbDbUrl='https://stub';");
    __T("_asCfgLoaded=true; _asPos=Object.assign({},_AS_POS0); _asMap={};");
    __T("quoteVendors=[{id:'v1',name:'하나코리아 주식회사',count:412}]");
    __T("clientList=[['하나코리아 주식회사','357-87-03525','서울']]");
    window.__DOCS = (function(){ var o={};
      for(var i=0;i<24;i++){ var mon=(i%12)+1, day=((i*5)%27)+1; mon=(mon<10?'0'+mon:''+mon);
        var id='as'+i, sup=2*(100000+i*937);
        o[id]={ id:id, no:(i%29)+1, date:'2026-'+mon+'-'+(day<10?'0'+day:day), ship:'2026'+mon+'01',
          vid:'v1', vname:'하나코리아 주식회사', biz:'357-87-03525', ceo:'윤석봉', addr:'서울', memo:'',
          rows:[{spec:'CDJ2F16-'+(60+i)+'Z-B',name:'CYLINDER',qty:2,price:100000+i*937,supply:sup,tax:Math.round(sup*0.1)}],
          supply:sup, tax:Math.round(sup*0.1), total:Math.round(sup*1.1), by:'김재성', at:1700000000000+i, upd:1 }; }
      return o; })();
    window.__DEL=[];
    __T("_fbFetch=async function(u,o){ if(o&&o.method==='DELETE'){ window.__DEL.push(String(u)); return {ok:true,status:200,json:async function(){return null;}}; } if(/_audit_stmt\\.json/.test(String(u))) return {ok:true,status:200,json:async function(){ return window.__DOCS; }}; return {ok:true,status:200,json:async function(){ return null; }}; };");
    __T("_fbPutOk=async function(){ return true; };");
    __T("switchPage('audit')");
  });
  await pg.waitForTimeout(700);

  const has = await pg.evaluate(()=>typeof window.asLDateIn==='function' && typeof window.asClearFile==='function');
  if(!has){
    ['줄 클릭 펼침','[내역] 단추 없음','품목·규격 분리','규격 정렬','기간 입력','커서 이동','파일 비우기','전표 줄 클릭','번호 가운데','칸 높이','비고 폭','번호칸 높이']
      .forEach(n => ok('r283 기능 없음 — ' + n, false));
    ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
    await b.close(); return out();
  }

  // ─── 저장된 명세표 ───
  await pg.evaluate(()=>__T("asTab('list')")); await pg.waitForTimeout(900);

  ok('[내역] 단추가 없어졌다',
     await pg.evaluate(()=>!/내역/.test(document.getElementById('pageAudit').innerText)
        && !document.querySelector('#pageAudit .as-lrow button[onclick*="asLToggle"]')));
  ok('줄 전체가 누를 수 있는 모양(cursor:pointer)',
     await pg.evaluate(()=>getComputedStyle(document.querySelector('#pageAudit .as-lrow')).cursor==='pointer'));
  ok('줄 맨 앞에 ▸ 표시', await pg.evaluate(()=>/▸/.test(document.querySelector('#pageAudit .as-lrow').innerText)));   // r285: 앞에 체크칸이 하나 생겼다

  // 업체 칸을 눌러 펼친다 (단추가 아닌 자리)
  await pg.evaluate(()=>document.querySelectorAll('#pageAudit .as-lrow')[0].children[2].click());
  await pg.waitForTimeout(450);
  ok('줄 아무 곳이나 누르면 내역이 펼쳐진다',
     await pg.evaluate(()=>/품목/.test(document.getElementById('pageAudit').innerText) && !!document.querySelector('#pageAudit table table')),
     await pg.evaluate(()=>document.querySelectorAll('#pageAudit table').length));
  ok('펼치면 ▾ 로 바뀐다', await pg.evaluate(()=>/▾/.test(document.querySelector('#pageAudit .as-lrow').innerText)));

  // 품목 / 규격 두 칸
  const det = await pg.evaluate(()=>{
    var inner=document.querySelector('#pageAudit table table'); if(!inner) return null;
    var ths=Array.prototype.map.call(inner.querySelectorAll('thead th'), e=>e.textContent.trim());
    var tds=inner.querySelectorAll('tbody tr')[0].children;
    var st=i=>getComputedStyle(tds[i]);
    var outer=document.querySelectorAll('#pageAudit .as-lrow')[0].children;
    var oi=Array.prototype.findIndex.call(outer, function(e){ return /[가-힣]/.test(e.textContent) && !/^\s*\d/.test(e.textContent); });
    return { ths:ths,
      nameAlign:st(1).textAlign, specAlign:st(2).textAlign, noAlign:st(0).textAlign,
      specLeft:Math.round(tds[2].getBoundingClientRect().left),
      vnameLeft:Math.round(outer[oi].getBoundingClientRect().left),
      padTop:st(2).paddingTop, rowH:Math.round(tds[2].getBoundingClientRect().height) };
  });
  ok('내역 머리가 번호·품목·규격 … 로 나뉘었다',
     det && det.ths.slice(0,3).join(',')==='번호,품목,규격', det?det.ths.join(','):'(표 없음)');
  ok('품목·규격 둘 다 왼쪽 정렬', det && det.nameAlign==='left' && det.specAlign==='left',
     det?det.nameAlign+' / '+det.specAlign:'');
  ok('규격이 위 표의 업체와 같은 자리에서 시작', det && Math.abs(det.specLeft-det.vnameLeft)<=2,
     det?('규격 '+det.specLeft+' vs 업체 '+det.vnameLeft):'');
  ok('번호는 가운데 정렬', det && det.noAlign==='center', det?det.noAlign:'');
  ok('칸 높이가 높아졌다(세로 여백 6px 이상)', det && parseFloat(det.padTop)>=6, det?det.padTop:'');

  // [인쇄]·[삭제] 는 줄 접힘과 섞이지 않는다
  await pg.evaluate(()=>{ window.__PRN=''; __T("_asPrintHtml=function(h){ window.__PRN=h; };"); });
  const openBefore = await pg.evaluate(()=>!!document.querySelector('#pageAudit table table'));
  await pg.evaluate(()=>{ var r=document.querySelectorAll('#pageAudit .as-lrow')[0];
    Array.prototype.filter.call(r.querySelectorAll('button'), e=>/인쇄/.test(e.textContent))[0].click(); });
  await pg.waitForTimeout(400);
  ok('[인쇄] 를 눌러도 줄이 접히지 않는다',
     await pg.evaluate(()=>(window.__PRN||'').length>500) && openBefore===await pg.evaluate(()=>!!document.querySelector('#pageAudit table table')));

  await pg.evaluate(()=>{ var r=document.querySelectorAll('#pageAudit .as-lrow')[0];
    Array.prototype.filter.call(r.querySelectorAll('button'), e=>/삭제/.test(e.textContent))[0].click(); });
  await pg.waitForTimeout(300);
  ok('[삭제] 는 확인창만 띄우고 줄을 접지 않는다',
     await pg.evaluate(()=>/거래명세표 삭제/.test(window.__CONF||'') && !!document.querySelector('#pageAudit table table')),
     await pg.evaluate(()=>String(window.__CONF).slice(0,40)));

  // ─── 기간 입력 ───
  await pg.evaluate(()=>__T("asLSet('vname','하나코리아 주식회사')")); await pg.waitForTimeout(400);
  ok('기간 칸이 숫자로 적는 칸이다', await pg.evaluate(()=>{
    var f=document.getElementById('asLFrom'); return !!f && f.type==='text' && f.placeholder==='20260101'; }));
  await pg.click('#asLFrom');
  await pg.type('#asLFrom','20260101',{delay:12});
  await pg.waitForTimeout(500);
  const dt = await pg.evaluate(()=>({
    from:(document.getElementById('asLFrom')||{}).value,
    focus:(document.activeElement||{}).id,
    kept:__T("_asLF").from }));
  ok('20260101 → 2026-01-01 로 바뀐다', dt.from==='2026-01-01' && dt.kept==='2026-01-01', JSON.stringify(dt));
  ok('다 적으면 커서가 끝 날짜 칸으로 넘어간다', dt.focus==='asLTo', dt.focus);
  await pg.type('#asLTo','20260630',{delay:12});
  await pg.waitForTimeout(500);
  const dt2 = await pg.evaluate(()=>({ to:(document.getElementById('asLTo')||{}).value, kept:__T("_asLF").to,
    q:!(document.getElementById('asLQ')||{}).disabled,
    n:document.querySelectorAll('#pageAudit .as-lrow').length }));
  ok('끝 날짜도 같은 방식으로 들어간다', dt2.to==='2026-06-30' && dt2.kept==='2026-06-30', JSON.stringify(dt2));
  ok('업체+기간이 차면 품목 검색칸이 열린다', dt2.q===true);
  ok('기간으로 실제로 걸러진다', dt2.n>0 && dt2.n<24, dt2.n);
  // 말이 안 되는 날짜
  await pg.evaluate(()=>{ var e=document.getElementById('asLTo'); e.value='20261345'; e.dispatchEvent(new Event('input',{bubbles:true})); });
  await pg.waitForTimeout(300);
  ok('없는 날짜는 받지 않고 빨갛게 표시', await pg.evaluate(()=>{
    var e=document.getElementById('asLTo');
    return /220, 38, 38/.test(getComputedStyle(e).borderColor) && __T("_asLF").to==='2026-06-30'; }),
    await pg.evaluate(()=>getComputedStyle(document.getElementById('asLTo')).borderColor+' / '+__T("_asLF").to));

  // ─── 명세표 만들기 ───
  await pg.evaluate(()=>__T("asTab('new')")); await pg.waitForTimeout(400);
  await pg.evaluate(()=>{
    function mk(n){ var r=[]; for(var i=1;i<=n;i++) r.push({spec:'CDJ2F16-'+i+'Z-B',name:'CYLINDER',qty:i,price:1000*i,supply:1000*i*i,tax:100*i*i}); return r; }
    window.__DR={ key:'k', ucode:'H0T', uname:'하나코리아', list:[], vid:'v1', vname:'하나코리아 주식회사',
      biz:'357-87-03525', ceo:'윤석봉', addr:'서울',
      docs:[{ship:'20261106',date:'2026-11-10',warn:'',no:12,rows:mk(6),memo:''},
            {ship:'20261117',date:'2026-11-19',warn:'',no:5,rows:mk(3),memo:''}] };
    __T("_asFileName='유저특가.xls'"); __T("_asRaw=new Array(9)");
    __T("_asDrafts=[window.__DR]"); __T("_asRender()");
  });
  await pg.waitForTimeout(400);

  ok('[다른 파일 올리기]·[비우기] 가 있다', await pg.evaluate(()=>{
    var t=document.getElementById('pageAudit').innerText; return /다른 파일 올리기/.test(t) && /비우기/.test(t); }));
  ok('전표 줄에 접기 단추가 없다', await pg.evaluate(()=>{
    var r=document.querySelector('#pageAudit .as-doc-row');
    return r.children[0].tagName!=='BUTTON' && !/품목 ·/.test(r.textContent); }),
    await pg.evaluate(()=>document.querySelector('#pageAudit .as-doc-row').children[0].tagName));
  ok('전표 줄이 누를 수 있는 모양', await pg.evaluate(()=>
     getComputedStyle(document.querySelector('#pageAudit .as-doc-row')).cursor==='pointer'));
  ok('비고 칸이 300px 로 넓어졌다', await pg.evaluate(()=>{
    var i=Array.prototype.filter.call(document.querySelectorAll('#pageAudit .as-doc-row input'), e=>e.placeholder==='(선택)')[0];
    return Math.round(i.getBoundingClientRect().width)===300; }),
    await pg.evaluate(()=>{ var i=Array.prototype.filter.call(document.querySelectorAll('#pageAudit .as-doc-row input'), e=>e.placeholder==='(선택)')[0];
      return Math.round(i.getBoundingClientRect().width); }));
  ok('번호 칸 높이가 낮아졌다(22px)', await pg.evaluate(()=>{
    var i=document.querySelector('#pageAudit .as-doc-row input');
    return Math.round(i.getBoundingClientRect().height)===22; }),
    await pg.evaluate(()=>Math.round(document.querySelector('#pageAudit .as-doc-row input').getBoundingClientRect().height)));

  // 번호 칸에 적어도 접히지 않는다
  await pg.evaluate(()=>{ var i=document.querySelector('#pageAudit .as-doc-row input'); i.click(); });
  await pg.waitForTimeout(350);
  ok('번호 칸을 눌러도 펼쳐지지 않는다', await pg.evaluate(()=>document.querySelectorAll('#pageAudit table').length===0));

  // 줄 아무 곳(발행일)을 눌러 펼친다
  await pg.evaluate(()=>document.querySelectorAll('#pageAudit .as-doc-row')[0].children[2].click());
  await pg.waitForTimeout(450);
  const mk2 = await pg.evaluate(()=>{
    var t=document.querySelector('#pageAudit table'); if(!t) return null;
    var ths=Array.prototype.map.call(t.querySelectorAll('thead th'), e=>e.textContent.trim());
    var tds=t.querySelectorAll('tbody tr')[0].children;
    return { ths:ths, no:getComputedStyle(tds[0]).textAlign, name:getComputedStyle(tds[1]).textAlign,
             spec:getComputedStyle(tds[2]).textAlign, pad:getComputedStyle(tds[0]).paddingTop,
             arrow:/▾/.test(document.querySelectorAll('#pageAudit .as-doc-row')[0].children[0].textContent) };
  });
  ok('전표 줄을 누르면 품목이 펼쳐진다', !!mk2 && mk2.arrow, mk2?JSON.stringify(mk2.ths):'(표 없음)');
  ok('만들기 내역도 번호·품목·규격 으로 나뉘었다', mk2 && mk2.ths.slice(0,3).join(',')==='번호,품목,규격', mk2?mk2.ths.join(','):'');
  ok('만들기 내역 번호가 가운데 · 품목·규격은 왼쪽',
     mk2 && mk2.no==='center' && mk2.name==='left' && mk2.spec==='left', mk2?JSON.stringify(mk2):'');
  ok('만들기 내역 칸 높이도 높아졌다', mk2 && parseFloat(mk2.pad)>=6, mk2?mk2.pad:'');

  // 비우기
  await pg.evaluate(()=>__T("asClearFile()")); await pg.waitForTimeout(250);
  ok('[비우기] 는 먼저 물어본다', await pg.evaluate(()=>/비우기/.test(window.__CONF||'')), await pg.evaluate(()=>String(window.__CONF).slice(0,60)));
  await pg.evaluate(()=>{ window.__CONFOK(); }); await pg.waitForTimeout(500);
  ok('확인하면 올린 파일과 작성 중인 명세표가 비워진다', await pg.evaluate(()=>
     __T("_asDrafts").length===0 && __T("_asFileName")==='' && !!document.getElementById('asDrop')));

  // ─── 업체 드롭다운: 바깥을 누르면 닫힌다 ───
  await pg.evaluate(()=>__T("asTab('list')")); await pg.waitForTimeout(700);
  await pg.click('#asLV'); await pg.waitForTimeout(300);
  ok('업체 칸을 누르면 목록이 뜬다', await pg.evaluate(()=>getComputedStyle(document.getElementById('asLVdd')).display!=='none'));
  await pg.mouse.click(700, 60);  // 화면의 다른 곳
  await pg.waitForTimeout(300);
  ok('바깥을 누르면 목록이 닫힌다', await pg.evaluate(()=>getComputedStyle(document.getElementById('asLVdd')).display==='none'),
     await pg.evaluate(()=>getComputedStyle(document.getElementById('asLVdd')).display));

  // ─── 인쇄 위치 보정 ───
  const cal = await pg.evaluate(()=>{
    var p=__T("_AS_POS0");
    return { sclX:p.sclX, sclY:p.sclY, offX:p.offX, sumY:p.sumY };
  });
  ok('배율 보정값이 생겼다', cal.sclX>0.98 && cal.sclX<1.02 && cal.sclY>0.98 && cal.sclY<1.02, JSON.stringify(cal));
  ok("'계' 합계가 칸(110.07~118.40) 가운데로 올라왔다", cal.sumY>111 && cal.sumY<114, cal.sumY);

  const pos = await pg.evaluate(()=>{
    var p=__T("_AS_POS0"), s=p.sclX, o=p.offX;
    var rows=[{spec:'X-1',name:'Y',qty:1,price:1000,supply:1000,tax:100}];
    var dr={ vid:'v1', vname:'가', biz:'1', ceo:'나', addr:'다' };
    var h=__T("_asDocHtml")(dr, [{ship:'20261101',date:'2026-11-03',no:3,rows:rows,memo:''}], false);
    var d=document.createElement('div'); d.innerHTML=h.replace(/^[\s\S]*<body>/,'').replace('</body></html>','');
    var fs=Array.prototype.slice.call(d.querySelectorAll('.as-f'));
    var nm=fs.filter(e=>/^Y/.test(e.textContent))[0];          // 품명 (왼쪽 맞춤)
    var tx=fs.filter(e=>/^100$/.test(e.textContent))[0];       // 세액 (오른쪽 맞춤)
    var sum=fs.filter(e=>/^1,000$/.test(e.textContent)).pop();
    return { left:parseFloat(nm.style.left), wantL:(p.cNameL*s+o),
             right:parseFloat(tx.style.right), wantR:(p.slipW-(p.cTaxR*s+o)),
             top:parseFloat(nm.style.top), wantT:(p.rowY*p.sclY+p.offY) };
  });
  ok('왼쪽 맞춤 칸에 배율·이동이 들어간다', Math.abs(pos.left-pos.wantL)<0.01, JSON.stringify(pos));
  ok('오른쪽 맞춤 칸에도 들어간다', Math.abs(pos.right-pos.wantR)<0.01, JSON.stringify(pos));
  ok('세로에도 들어간다', Math.abs(pos.top-pos.wantT)<0.01, JSON.stringify(pos));

  // [인쇄 보정] 창
  await pg.evaluate(()=>__T("asCalib()")); await pg.waitForTimeout(350);
  ok('[인쇄 보정] 창에 가로·세로 배율 칸이 있다', await pg.evaluate(()=>
     !!document.getElementById('asC_sclX') && !!document.getElementById('asC_sclY')));
  ok('보정값은 손잡이 키만 저장한다', await pg.evaluate(()=>{
     var k=__T("_AS_KNOBS"); return k.indexOf('sclX')>=0 && k.indexOf('sumY')<0 && k.indexOf('cTaxR')<0; }));
  await pg.evaluate(()=>{ var o=document.getElementById('asCalOv'); if(o) o.style.display='none'; });

  // ─── 미리보기 양식 ───
  const form = await pg.evaluate(()=>{
    var dr={ vid:'v1', vname:'가', biz:'1', ceo:'나', addr:'다' };
    var h=__T("_asDocHtml")(dr, [{ship:'20261101',date:'2026-11-03',no:3,
      rows:[{spec:'X',name:'Y',qty:1,price:1000,supply:1000,tax:100}],memo:''}], 'form');
    var d=document.createElement('div'); d.innerHTML=h.replace(/^[\s\S]*<body>/,'').replace('</body></html>','');
    var svg=d.querySelector('svg.as-form');
    if(!svg) return null;
    var lines=svg.querySelectorAll('line').length, texts=svg.querySelectorAll('text').length;
    var t=svg.textContent;
    return { lines:lines, texts:texts, t:t,
      title:/거 래 명 세 서/.test(t), biz:/113-81-14978/.test(t), co:/충해전기\(주\)/.test(t),
      ymd:/년/.test(t)&&/월/.test(t)&&/일/.test(t),
      head:/품 명 및 규 격/.test(t)&&/공급가액/.test(t)&&/세   액/.test(t),
      recv:/인 수 자/.test(t)&&/계/.test(t), tot:/총금액/.test(t),
      foot:/신한은행/.test(t)&&/chjk@chjk\.co\.kr/.test(t),
      seal:/인감/.test(t) };
  });
  ok('미리보기에 양식이 그려진다', !!form && form.lines>=20 && form.texts>=30, form?JSON.stringify({l:form.lines,t:form.texts}):'(없음)');
  ok('제목·공급자 정보가 양식대로', form && form.title && form.biz && form.co, form?JSON.stringify(form).slice(0,120):'');
  ok('년·월·일, 품목표 머리, 인수자·계, 총금액, 꼬리말이 있다',
     form && form.ymd && form.head && form.recv && form.tot && form.foot,
     form?JSON.stringify({y:form.ymd,h:form.head,r:form.recv,t:form.tot,f:form.foot}):'');
  ok('인감은 그리지 않는다', form && !form.seal);

  ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
  await b.close(); return out();

  function out(){
    let p=0; P.forEach(x=>{ if(x[1]) p++; console.log((x[1]?'  OK  ':'  FAIL')+'  '+x[0]+(x[1]?'':'   → '+x[2])); });
    console.log('\n['+LABEL+'] '+p+'/'+P.length);
    process.exit(p===P.length?0:1);
  }
})();
