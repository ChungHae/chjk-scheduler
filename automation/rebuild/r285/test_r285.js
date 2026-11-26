// r285 테스트 — 물류출하일 거르기 · 작성 칸 삭제 · 선택 인쇄/삭제 · 올리기 전 중복 확인 · 배경색 · 양식 그림
//  사용:  node test_r285.js <index.html(__T 주입본)> [라벨]
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
    __T("window.__CONF=null; showConfirmModal=function(t,m,f,lab,col){ window.__CONF={t:t,m:m,lab:lab,col:col}; window.__CONFOK=f; };");
    __T("_fbDbUrl='https://stub';");
    __T("_asCfgLoaded=true; _asPos=Object.assign({},_AS_POS0); _asMap={};");
    __T("quoteVendors=[{id:'v1',name:'하나코리아 주식회사',count:9}]");
    __T("clientList=[['하나코리아 주식회사','357-87-03525','서울']]");
    window.__DOCS={}; window.__DEL=[]; window.__PUT=[];
    for(var i=0;i<8;i++){
      var id='as'+i, sup=1000*(i+1);
      window.__DOCS[id]={ id:id, no:i+1, date:'2026-0'+((i%9)+1)+'-10', ship:'2026010'+((i%9)+1),
        vid:'v1', vname:(i%2?'하나코리아 주식회사':'다른회사'), biz:'1', ceo:'나', addr:'다', memo:'',
        rows:[{spec:'P-'+i,name:'CYLINDER',qty:1,price:sup,supply:sup,tax:sup/10}],
        supply:sup, tax:sup/10, total:sup*1.1, by:'김재성', at:i, upd:1 };
    }
    __T("_fbFetch=async function(u,o){ if(o&&o.method==='DELETE'){ window.__DEL.push(String(u)); return {ok:true,status:200,json:async function(){return null;}}; } if(/_audit_stmt\\.json/.test(String(u))) return {ok:true,status:200,json:async function(){ return window.__DOCS; }}; return {ok:true,status:200,json:async function(){ return null; }}; };");
    __T("_fbPutOk=async function(u,body){ window.__PUT.push(String(u)); return true; };");
    __T("switchPage('audit')");
  });
  await pg.waitForTimeout(700);

  const has = await pg.evaluate(()=>typeof window.asLSelAll==='function' && typeof __T("_asShipOk")==='function');
  if(!has){
    ['물류출하일 거르기','작성 칸 삭제','선택 체크','전체 선택','선택 인쇄','선택 삭제','올리기 전 중복','배경색','양식 그림']
      .forEach(n => ok('r285 기능 없음 — ' + n, false));
    ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
    await b.close(); return out();
  }

  // ── ① 물류출하일 ──
  const shipOk = await pg.evaluate(()=>{
    var f=__T("_asShipOk");
    return { good:f('20261106'), zero:f('00000000'), short:f('202611'), m13:f('20261306'),
             d32:f('20261132'), feb:f('20260230'), leap:f('20260229'), txt:f('날짜없음'), empty:f('') };
  });
  ok('바른 날짜는 받는다', shipOk.good===true, JSON.stringify(shipOk));
  ok('00000000·자릿수 모자람·13월·32일·2월30일·글자·빈칸은 뺀다',
     !shipOk.zero && !shipOk.short && !shipOk.m13 && !shipOk.d32 && !shipOk.feb && !shipOk.leap && !shipOk.txt && !shipOk.empty,
     JSON.stringify(shipOk));
  // 실제 파싱
  const parsed = await pg.evaluate(()=>{
    function td(v){ return '<td>'+v+'</td>'; }
    var head='<tr>'+['유저','유저명','품번','수량','유저특가','물류출하일'].map(td).join('')+'</tr>';
    var rows=[['H0T','하나','P-1','2','1000','20261106'],
              ['H0T','하나','P-2','1','2000','0'],
              ['H0T','하나','P-3','1','3000','20261345'],
              ['H0T','하나','P-4','3','4000','2026.11.17'],
              ['H0T','하나','P-5','1','5000','']].map(function(r){ return '<tr>'+r.map(td).join('')+'</tr>'; }).join('');
    var html='<html><body><table>'+head+rows+'</table></body></html>';
    var buf=new TextEncoder().encode(html).buffer;
    var out=__T("_asParseFile")(buf);
    return { n:out.length, specs:out.map(function(r){ return r.spec; }), ships:out.map(function(r){ return r.ship; }), dropped:__T("_asDropped") };
  });
  ok('올바른 물류출하일만 남는다', parsed.n===2 && parsed.specs.join(',')==='P-1,P-4', JSON.stringify(parsed));
  ok("'2026.11.17' 처럼 점이 있어도 받는다", parsed.ships.indexOf('20261117')>=0, parsed.ships.join(','));
  ok('뺀 줄 수를 센다', parsed.dropped===3, parsed.dropped);

  // ── ②③⑤ 저장된 명세표 ──
  await pg.evaluate(()=>__T("asTab('list')")); await pg.waitForTimeout(900);
  const hd = await pg.evaluate(()=>{
    var t=document.querySelector('#pageAudit table');
    return { ths:Array.prototype.map.call(t.querySelectorAll('thead th'), e=>e.textContent.trim()),
             chk:!!document.getElementById('asLAll'),
             rows:document.querySelectorAll('#pageAudit .as-lrow').length };
  });
  ok("'작성' 칸이 없어졌다", hd.ths.indexOf('작성')<0, hd.ths.join(','));
  ok('맨 앞에 전체 선택 체크칸', hd.chk && hd.ths[0]==='', JSON.stringify(hd.ths));
  ok('줄이 그려진다', hd.rows===8, hd.rows);

  // 한 줄 선택 → 배경색
  await pg.evaluate(()=>document.querySelectorAll('#pageAudit .as-lrow')[0].querySelector('input[type=checkbox]').click());
  await pg.waitForTimeout(400);
  const sel1 = await pg.evaluate(()=>{
    var r=document.querySelectorAll('#pageAudit .as-lrow')[0];
    return { cls:r.className, bg:getComputedStyle(r).backgroundColor,
             txt:document.getElementById('pageAudit').innerText,
             open:document.querySelectorAll('#pageAudit table table').length };
  });
  ok('고른 줄에 as-sel 과 배경색', /as-sel/.test(sel1.cls) && sel1.bg!=='rgba(0, 0, 0, 0)', sel1.cls+' / '+sel1.bg);
  ok('체크해도 내역이 펼쳐지지 않는다', sel1.open===0, sel1.open);
  ok('고른 건수와 단추가 보인다', /1건 골랐습니다/.test(sel1.txt) && /고른 것 인쇄/.test(sel1.txt) && /고른 것 삭제/.test(sel1.txt));

  // 펼친 줄 배경색
  await pg.evaluate(()=>document.querySelectorAll('#pageAudit .as-lrow')[1].children[3].click());
  await pg.waitForTimeout(400);
  ok('펼친 줄에 as-open 과 배경색', await pg.evaluate(()=>{
     var r=document.querySelectorAll('#pageAudit .as-lrow')[1];
     return /as-open/.test(r.className) && getComputedStyle(r).backgroundColor!=='rgba(0, 0, 0, 0)'; }));

  // 전체 선택
  await pg.evaluate(()=>document.getElementById('asLAll').click());
  await pg.waitForTimeout(450);
  ok('전체 선택이 이 쪽 전부를 고른다', await pg.evaluate(()=>
     document.querySelectorAll('#pageAudit .as-lrow.as-sel').length===8 && /8건 골랐습니다/.test(document.getElementById('pageAudit').innerText)),
     await pg.evaluate(()=>document.querySelectorAll('#pageAudit .as-lrow.as-sel').length));

  // 선택 인쇄 — 거래처가 달라도 한 번에
  await pg.evaluate(()=>{ window.__PRN=''; __T("_asPrintHtml=function(h){ window.__PRN=h; };"); });
  await pg.evaluate(()=>__T("asLPrintSel()")); await pg.waitForTimeout(500);
  const prn = await pg.evaluate(()=>({
    len:(window.__PRN||'').length,
    pages:((window.__PRN||'').match(/class="as-page"/g)||[]).length,
    slips:((window.__PRN||'').match(/class="as-slip/g)||[]).length,
    svg:/<svg/.test(window.__PRN||''),
    v1:/하나코리아/.test(window.__PRN||''), v2:/다른회사/.test(window.__PRN||'') }));   // 긴 상호는 칸 폭에 맞춰 두 줄로 흘린다
  ok('고른 8건이 한 문서로 인쇄된다', prn.pages===8 && prn.slips===16, JSON.stringify(prn));
  ok('거래처가 달라도 각자 정보로 찍힌다', prn.v1 && prn.v2);
  ok('인쇄본에는 양식 그림이 없다', !prn.svg && !/as-form/.test(await pg.evaluate(()=>window.__PRN||'')) || !prn.svg,
     String(prn.svg));

  // 선택 삭제
  await pg.evaluate(()=>{ window.__CONF=null; __T("asLDelSel()"); }); await pg.waitForTimeout(350);
  const c1 = await pg.evaluate(()=>window.__CONF);
  ok('선택 삭제는 먼저 물어본다', c1 && /8건 삭제/.test(c1.t) && /되돌릴 수 없습니다/.test(c1.m), c1?JSON.stringify(c1).slice(0,120):'(없음)');
  await pg.evaluate(async ()=>{ await window.__CONFOK(); }); await pg.waitForTimeout(900);
  const del = await pg.evaluate(()=>({ n:window.__DEL.length, left:__T("_asLRows").length,
    txt:document.getElementById('pageAudit').innerText }));
  ok('고른 것이 모두 지워진다', del.n===8 && del.left===0, JSON.stringify({n:del.n,left:del.left}));
  ok('다 지우면 빈 목록 안내', /조건에 맞는 거래명세표가 없습니다/.test(del.txt));

  // ── ④ 올리기 전 중복 확인 ──
  await pg.evaluate(()=>{
    window.__DOCS={ asZ:{ id:'asZ', no:7, date:'2026-11-10', ship:'20261106', vid:'v1',
      vname:'하나코리아 주식회사', biz:'1', ceo:'나', addr:'다', rows:[{spec:'P-1',name:'C',qty:2,price:1000,supply:2000,tax:200}],
      supply:2000, tax:200, total:2200, by:'김', at:1, upd:1 } };
    __T("_asLRows=null"); __T("_asLSel={}"); __T("_asTab='new'"); __T("_asDrafts=[]"); __T("_asFileName=''"); __T("_asRaw=[]");
    __T("_asMap={'H0T|하나':{vid:'v1',vname:'하나코리아 주식회사'}}");
    __T("_asLoadMap=async function(){ return _asMap; };");
    __T("_qBlobGet=async function(){ return [{spec:'P-1',name:'C'}]; };");
    __T("_asAddBizDays=async function(sh,n){ return { date:'2026-11-10', warn:'' }; };");
    __T("_asUsedNos=async function(){ return []; };");
    __T("_asRender()");
  });
  await pg.waitForTimeout(400);
  const mkFile = async () => pg.evaluate(()=>{
    function td(v){ return '<td>'+v+'</td>'; }
    var head='<tr>'+['유저','유저명','품번','수량','유저특가','물류출하일'].map(td).join('')+'</tr>';
    var rows='<tr>'+['H0T','하나','P-1','2','1000','20261106'].map(td).join('')+'</tr>';
    var html='<html><body><table>'+head+rows+'</table></body></html>';
    var f=new File([html],'유저특가.xls',{type:'application/vnd.ms-excel'});
    window.__CONF=null;
    return __T("_asTakeFile")(f);
  });
  await mkFile(); await pg.waitForTimeout(900);
  const c2 = await pg.evaluate(()=>({ conf:window.__CONF, drafts:__T("_asDrafts").length,
    screen:/파일: /.test(document.getElementById('pageAudit').innerText) }));
  ok('중복이면 화면보다 먼저 물어본다', c2.conf && /중복 확인/.test(c2.conf.t) && /같은 내용이 1건/.test(c2.conf.m),
     c2.conf?JSON.stringify(c2.conf).slice(0,160):'(없음)');
  ok('아직 화면에 올리지 않는다', c2.drafts===0 && !c2.screen, JSON.stringify({d:c2.drafts,s:c2.screen}));
  ok('단추가 [그대로 올리기]', c2.conf && c2.conf.lab==='그대로 올리기', c2.conf?c2.conf.lab:'');
  // 취소 = 그대로 버린다
  await pg.evaluate(()=>{ window.__CONF=null; }); await pg.waitForTimeout(150);
  ok('취소하면 파일을 버린다', await pg.evaluate(()=>__T("_asDrafts").length===0 && __T("_asFileName")===''));
  // 다시 올려서 그대로 진행
  await mkFile(); await pg.waitForTimeout(900);
  await pg.evaluate(()=>{ window.__CONFOK(); }); await pg.waitForTimeout(600);
  const c3 = await pg.evaluate(()=>({ drafts:__T("_asDrafts").length,
    txt:document.getElementById('pageAudit').innerText }));
  ok('[그대로 올리기] 면 화면에 올라온다', c3.drafts===1 && /파일: /.test(c3.txt), JSON.stringify({d:c3.drafts}));
  ok('화면에도 중복 표시가 남는다', /같은 내용이 1건/.test(c3.txt), (c3.txt.match(/같은 내용이[^\n]*/)||[''])[0]);

  // 중복이 아니면 바로 올라간다
  await pg.evaluate(()=>{ window.__DOCS={}; __T("_asLRows=null"); __T("_asDrafts=[]"); __T("_asFileName=''"); window.__CONF=null; });
  await mkFile(); await pg.waitForTimeout(900);
  ok('중복이 없으면 묻지 않고 바로 올라간다', await pg.evaluate(()=>
     window.__CONF===null && __T("_asDrafts").length===1));

  // ── ⑥ 양식 그림 ──
  const form = await pg.evaluate(()=>{
    var png='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';
    __T("_asFormImg='"+png+"'");
    var dr={ vid:'v1', vname:'가', biz:'1', ceo:'나', addr:'다' };
    var doc={ ship:'20261101', date:'2026-11-03', no:3, rows:[{spec:'X',name:'Y',qty:1,price:1,supply:1,tax:0}], memo:'' };
    var prev=__T("_asDocHtml")(dr,[doc],'form');
    var print=__T("_asDocHtml")(dr,[doc],false);
    return { prevImg:/<img class="as-form"/.test(prev), prevSvg:/<svg class="as-form"/.test(prev),
             printImg:/as-form" src/.test(print), printSvg:/<svg/.test(print) };
  });
  ok('양식 그림이 있으면 미리보기에 그림을 깐다', form.prevImg && !form.prevSvg, JSON.stringify(form));
  ok('인쇄본에는 그림도 SVG 도 안 들어간다', !form.printImg && !form.printSvg, JSON.stringify(form));
  await pg.evaluate(()=>{ __T("_asFormImg=null"); });
  ok('그림이 없으면 선으로 그린 양식으로 돌아간다', await pg.evaluate(()=>{
    var dr={ vid:'v1', vname:'가', biz:'1', ceo:'나', addr:'다' };
    var doc={ ship:'20261101', date:'2026-11-03', no:3, rows:[{spec:'X',name:'Y',qty:1,price:1,supply:1,tax:0}], memo:'' };
    return /<svg class="as-form"/.test(__T("_asDocHtml")(dr,[doc],'form')); }));
  await pg.evaluate(()=>__T("asCalib()")); await pg.waitForTimeout(350);
  ok('[인쇄 보정] 창에 [양식 그림 등록]', await pg.evaluate(()=>
     /양식 그림 등록/.test(document.getElementById('asCalOv').innerText) && !!document.getElementById('asFormFile')));
  await pg.evaluate(()=>{ var o=document.getElementById('asCalOv'); if(o) o.style.display='none'; });

  ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
  await b.close(); return out();

  function out(){
    let p=0; P.forEach(x=>{ if(x[1]) p++; console.log((x[1]?'  OK  ':'  FAIL')+'  '+x[0]+(x[1]?'':'   → '+x[2])); });
    console.log('\n['+LABEL+'] '+p+'/'+P.length);
    process.exit(p===P.length?0:1);
  }
})();
