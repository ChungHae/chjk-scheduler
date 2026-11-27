// r279 테스트 — 매입처를 업무 하위로 · 감사 안내 간략화 · 엑셀 끌어다 놓기
//  사용:  node test_r279.js <index.html(__T 주입본)> [라벨]
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
    __T("_qBlobGet=async function(){ return [{spec:'CDJ2F16-60Z-B',name:'CYLINDER'}]; };");
  });

  const hasDrop = await pg.evaluate(()=>{ try{ return typeof __T("_asBindDrop")==='function'; }catch(e){ return false; } });
  if(!hasDrop){
    ['상단 탭에서 매입처 빠짐','업무 하위 탭 순서','매입처 열림','설명 문구 삭제','안내 간략','드롭 자리','드롭 연결','끌어다 놓기 동작']
      .forEach(n => ok('r279 기능 없음 — ' + n, false));
    ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
    await b.close(); return out();
  }

  // ── ① 매입처 자리 옮김 ──
  ok('상단 탭에 매입처가 없다',
     await pg.evaluate(()=>!document.querySelector('.page-nav .page-tab[data-page="purchase"]')));
  const nav = await pg.evaluate(()=>Array.from(document.querySelectorAll('.page-nav .page-tab')).map(b=>b.textContent.trim()).join(','));
  ok('상단 메뉴에서 매입처만 빠졌다',
     ['일정,견적,발주,업무,재고,회계,자료실,내규','일정,견적,발주,거래명세서,업무,재고,회계,자료실,내규',
      '일정,견적,발주,업무,회계,자료실,내규','일정,견적,발주,거래명세서,업무,회계,자료실,내규'].indexOf(nav)>=0, nav);   // r282: 재고도 업무 하위로
  const sub = await pg.evaluate(()=>Array.from(document.querySelectorAll('#etcSubNav .sub-tab')).map(b=>b.textContent.trim()).join(','));
  ok('업무 하위 탭에 사이트·매입처·감사가 이 순서로 있다',
     ['사이트,매입처,감사','사이트,매입처,재고,감사'].indexOf(sub)>=0, sub);   // r282: 재고가 매입처와 감사 사이로

  await pg.evaluate(()=>__T("switchPage('purchase')")); await pg.waitForTimeout(800);
  ok('매입처를 열면 업무 탭이 켜진다',
     await pg.evaluate(()=>document.getElementById('tabEtc').classList.contains('active')
       && document.getElementById('pagePurchase').classList.contains('active')));
  ok('업무 하위 탭 줄이 보이고 매입처가 활성',
     await pg.evaluate(()=>getComputedStyle(document.getElementById('etcSubNav')).display!=='none'
       && document.querySelector('.sub-tab[data-page="purchase"]').classList.contains('active')));
  ok('매입처 화면이 그려진다',
     await pg.evaluate(()=>document.getElementById('pagePurchase').innerHTML.length>200));
  ok('다른 탭으로 가면 업무 하위 줄이 숨는다', await (async()=>{
       await pg.evaluate(()=>__T("switchPage('files')")); await pg.waitForTimeout(400);   // r282: 재고가 업무 하위로
       return pg.evaluate(()=>getComputedStyle(document.getElementById('etcSubNav')).display==='none');
     })());

  // ── ② 감사 화면 ──
  await pg.evaluate(()=>__T("switchPage('audit')")); await pg.waitForTimeout(900);
  const aud = await pg.evaluate(()=>document.getElementById('pageAudit').innerHTML);
  ok('툴바 설명 문구가 없다', !/SMC 유저특가 엑셀 → 거래명세표/.test(aud));
  ok('옛 "쓰는 방법" 안내가 없다', !/쓰는 방법/.test(aud));
  ok('안내가 짧다(①~⑤ 목록 없음)', !/①/.test(aud) && !/⑤/.test(aud));
  ok('[엑셀 올리기] 는 그대로', /엑셀 올리기/.test(aud));

  // ── ③ 끌어다 놓기 ──
  ok('끌어다 놓는 자리가 있다',
     await pg.evaluate(()=>!!document.getElementById('asDrop')) && /끌어다 놓으세요/.test(aud));
  ok('드롭 받을 준비가 됐다', await pg.evaluate(()=>document.getElementById('pageAudit').__asDrop===1));
  // r290→r291: outline(상자 바깥) → 드롭 칸 안쪽 inset 그림자. 페이지 전체에는 표시하지 않는다.
  ok('끌어오면 표시가 바뀐다', await pg.evaluate(()=>{
       var el=document.getElementById('pageAudit');
       var z=document.getElementById('asDrop');
       var dt=new DataTransfer(); dt.items.add(new File(['x'],'a.xls',{type:'application/vnd.ms-excel'}));
       el.dispatchEvent(new DragEvent('dragover',{bubbles:true,cancelable:true,dataTransfer:dt}));
       var on=!(el.style.outline||'') && !(el.style.boxShadow||'')
              && /inset/.test(z?z.style.boxShadow:'')
              && /27, 58, 107|1B3A6B|#1b3a6b/i.test(z?z.style.borderColor:'');
       el.dispatchEvent(new DragEvent('dragleave',{bubbles:true,dataTransfer:dt}));
       var off=!(el.style.boxShadow||'') && !(z&&z.style.boxShadow);
       return on && off;
     }));

  const dropped = await pg.evaluate(async()=>{
    var html='<table><tr><td>유저</td><td>유저명</td><td>품번</td><td>수량</td><td>유저특가</td><td>물류출하일</td></tr>'
      +'<tr><td>H0T</td><td>하나코리아</td><td>CDJ2F16-60Z-B</td><td>2</td><td>15,500</td><td>20261106</td></tr></table>';
    var dt=new DataTransfer();
    dt.items.add(new File([html],'유저특가.xls',{type:'application/vnd.ms-excel'}));
    document.getElementById('pageAudit').dispatchEvent(new DragEvent('drop',{bubbles:true,cancelable:true,dataTransfer:dt}));
    await new Promise(r=>setTimeout(r,1200));
    return document.getElementById('pageAudit').innerHTML;
  });
  ok('끌어다 놓으면 엑셀을 읽는다', /하나코리아/.test(dropped) && /유저특가\.xls/.test(dropped),
     dropped.slice(0,120));

  const badDrop = await pg.evaluate(async()=>{
    window.__INFO='';
    var dt=new DataTransfer(); dt.items.add(new File(['x'],'사진.png',{type:'image/png'}));
    document.getElementById('pageAudit').dispatchEvent(new DragEvent('drop',{bubbles:true,cancelable:true,dataTransfer:dt}));
    await new Promise(r=>setTimeout(r,500));
    return window.__INFO;
  });
  ok('엑셀이 아니면 안내한다', /엑셀/.test(badDrop), badDrop);

  ok('pageerror 없음', errs.length===0, errs.slice(0,2).join(' | '));
  await b.close(); return out();

  function out(){
    let p=0; P.forEach(x=>{ if(x[1]) p++; console.log((x[1]?'  OK  ':'  FAIL')+'  '+x[0]+(x[1]?'':'   → '+x[2])); });
    console.log('\n['+LABEL+'] '+p+'/'+P.length);
    process.exit(p===P.length?0:1);
  }
})();
