const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const FILE=process.argv[2], LABEL=process.argv[3]||'?';
(async()=>{
  const b=await chromium.launch({});
  const pg=await (await b.newContext({timezoneId:'Asia/Seoul', viewport:{width:1400,height:950}})).newPage();
  await pg.route(/^https?:\/\//, r=>r.abort());
  const errs=[]; pg.on('pageerror',e=>errs.push(String(e).slice(0,200)));
  await pg.goto('file://'+FILE); await pg.waitForTimeout(3200);
  const P=[]; const ok=(n,c,e)=>P.push([n,!!c,e===undefined?'':String(e)]);

  await pg.evaluate(()=>{
    var g=document.getElementById('authGate'); if(g) g.style.display='none';
    __T("_authUser={id:'chjk',name:'김재성',role:'master'}"); __T("_fbDbUrl='https://stub'");
    __T("_fxLoaded=true"); __T("debouncedFbSave=function(){}"); __T("_fxSave=function(){}");
    __T("_fxSaveBig=async function(){}"); __T("_fxEnsureData=async function(){}");
    __T("showInfoModal=function(t,m){}; showConfirmModal=function(t,m,ok){ok&&ok();};");
    __T("fxAdjusts=[]; fxOpenings={}; fxTerms={}; fxExcluded=[]; fxAlias={}; _fxRenderUnasg=function(){};");
    var S=[],Pu=[],D=[];
    S.push({biz:'서울', date:'2026-09-30', supply:1,tax:0,total:1});
    S.push({biz:'서울', date:'2026-08-01', supply:1,tax:0,total:1});
    S.push({biz:'화성', date:'2026-10-10', supply:1,tax:0,total:1});
    Pu.push({biz:'서울', date:'2026-09-15', supply:1,tax:0,total:1});          // 화성 매입 없음
    D.push({biz:'서울', date:'2026-08-21', kind:'bank', bank:'신한', amount:1});  // 54일 전 → 빨강
    D.push({biz:'화성', date:'2026-10-09', kind:'bank', bank:'신한', amount:1});
    D.push({biz:'서울', date:'2026-10-13', kind:'bank', bank:'국민', amount:1});
    D.push({biz:'화성', date:'2026-09-20', kind:'note', bank:'신한어음', amount:1});
    D.push({biz:'서울', date:'2022-12-25', kind:'note', bank:'기업어음', amount:1});  // 다른 해
    window.__S=S; window.__P=Pu; window.__D=D;
    __T("fxSalesInv=window.__S; fxPurchInv=window.__P; fxDeposits=window.__D;");
  });

  const t=await pg.evaluate(async()=>{
    __T("switchPage('fxup')");
    await new Promise(r=>setTimeout(r,700));
    var h=document.getElementById('fxUpStat');
    if(!h) return {no:true};
    var lines=[];
    try{
      lines=[].slice.call(h.children[0].children).slice(1).map(function(d){
        return { lab:((d.children[0]||{}).innerText||'').trim(),
                 chips:[].slice.call((d.children[1]||{children:[]}).children).map(function(c){ return {t:(c.innerText||'').replace(/\s+/g,' ').trim(), tip:(c.querySelectorAll('[title]')[0]||{}).title||''}; }) };
      });
    }catch(_e){ lines=[]; }
    return { lines:lines, h:Math.round(h.getBoundingClientRect().height), tbl:h.querySelectorAll('table').length,
             first:(document.getElementById('fxBody').firstElementChild||{}).id, txt:(h.innerText||''),
             red:[].slice.call(h.querySelectorAll('span')).filter(function(s){ return (s.style.color||'').replace(/\s/g,'')==='rgb(220,38,38)'; }).map(function(s){return (s.innerText||'').trim();}) };
  });
  ok('#fxUpStat 이 업로드 카드들보다 위에 있다', !t.no && t.first==='fxUpStat', String(t.first));
  ok('표(table)를 쓰지 않는다 (r231 간소화)', t.tbl===0, String(t.tbl));
  ok('높이가 160px 이하로 작다', t.h>0 && t.h<=160, t.h+'px');
  ok('줄이 계산서 · 입금 · 어음 세 개', JSON.stringify((t.lines||[]).map(x=>x.lab))===JSON.stringify(['계산서','입금','어음']), JSON.stringify((t.lines||[]).map(x=>x.lab)));

  const chips = {}; (t.lines||[]).forEach(l=>l.chips.forEach(c=>{ chips[c.t.split(' ')[0]]=c; }));
  ok('매출 칩에 서울·화성 두 날짜', /매출 서울 09-30 화성 10-10/.test((chips['매출']||{}).t||''), (chips['매출']||{}).t);
  ok('매입은 자료 있는 서울만 (화성 안 나옴)', /매입 서울 09-15/.test((chips['매입']||{}).t||'') && !/화성/.test((chips['매입']||{}).t||''), (chips['매입']||{}).t);
  ok('신한 칩에 서울 08-21 · 화성 10-09', /신한 서울 08-21 화성 10-09/.test((chips['신한']||{}).t||''), (chips['신한']||{}).t);
  ok('국민은 서울만', /국민 서울 10-13/.test((chips['국민']||{}).t||'') && !/화성/.test((chips['국민']||{}).t||''), (chips['국민']||{}).t);
  ok('자료 없는 은행(우리·하나)은 칩이 없다', !chips['우리'] && !chips['하나'], JSON.stringify(Object.keys(chips)));
  ok('45일 넘은 곳만 빨간색 (신한 서울 08-21)', t.red.length>=1 && t.red.indexOf('08-21')>=0, JSON.stringify(t.red));
  ok('45일 안 지난 날짜는 빨갛지 않다', t.red.indexOf('10-09')<0 && t.red.indexOf('10-13')<0, JSON.stringify(t.red));
  ok("올해가 아니면 연도를 앞에 붙인다 ('22 12-25)", /'22 12-25/.test((chips['기업어음']||{}).t||''), (chips['기업어음']||{}).t);
  ok('마우스 올리면 전체 날짜·N일 전·건수가 보인다 (title)',
     /2026-08-21/.test((chips['신한']||{}).tip||'') && /일 전/.test((chips['신한']||{}).tip||'') && /건/.test((chips['신한']||{}).tip||''),
     (chips['신한']||{}).tip);
  ok('"마지막 거래일" 안내 한 줄', /마지막 거래일/.test(t.txt), '');

  const up=await pg.evaluate(async()=>{
    window.__D.push({biz:'서울', date:'2026-10-14', kind:'bank', bank:'신한', amount:1});
    __T("_fxMetaRefresh()"); await new Promise(r=>setTimeout(r,200));
    var h=document.getElementById('fxUpStat');
    return (h.innerText||'').replace(/\s+/g,' ');
  });
  ok('업로드 후 _fxMetaRefresh() 로 갱신 (신한 서울 → 10-14)', /신한 서울 10-14/.test(up), up.slice(0,140));

  const safe=await pg.evaluate(async()=>{ __T("switchPage('fxsum')"); await new Promise(r=>setTimeout(r,300));
    try{ __T("_fxMetaRefresh()"); return 'ok'; }catch(e){ return 'ERR '+e.message; } });
  ok('다른 탭에서 불러도 오류 없음', safe==='ok', safe);

  ok('pageerror 없음', errs.length===0, errs.join(' | '));
  await b.close();
  let p=0; P.forEach(x=>{ if(x[1])p++; console.log((x[1]?'  OK  ':'  FAIL')+'  '+x[0]+(x[1]?'':'   → '+x[2])); });
  console.log('['+LABEL+'] '+p+'/'+P.length);
})();
