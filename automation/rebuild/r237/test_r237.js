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
    S.push({biz:'화성', date:'2026-10-10', supply:1,tax:0,total:1});
    Pu.push({biz:'서울', date:'2026-09-15', supply:1,tax:0,total:1});
    // 화성 통장 = 신한 + 신한어음 뿐
    D.push({biz:'화성', date:'2026-10-09', kind:'bank', bank:'신한', amount:1});
    D.push({biz:'화성', date:'2026-09-20', kind:'note', bank:'신한어음', amount:1});
    // 서울 통장
    D.push({biz:'서울', date:'2026-10-13', kind:'bank', bank:'국민', amount:1});
    D.push({biz:'서울', date:'2026-10-01', kind:'bank', bank:'기업', amount:1});
    // ★ r237 ①: [사업장 이동 배정] 으로 화성으로 옮긴 서울 기업은행 입금 (실제 2건과 같은 모양)
    D.push({biz:'화성', obiz:'서울', date:'2022-11-21', kind:'bank', bank:'기업', amount:132916053, payer:'유일에너테크(주)'});
    D.push({biz:'화성', obiz:'서울', date:'2024-09-10', kind:'bank', bank:'기업', amount:30114981,  payer:'유일에너테크(주)'});
    // 반대 방향(화성 계좌 → 서울 거래처 배정)도 있다
    D.push({biz:'서울', obiz:'화성', date:'2026-05-02', kind:'bank', bank:'신한', amount:1});
    // ★ r237 ②: iM뱅크 = 숨김
    D.push({biz:'서울', date:'2022-12-25', kind:'bank', bank:'iM', amount:1});
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
             first:(document.getElementById('fxBody').firstElementChild||{}).id, txt:(h.innerText||'').replace(/\s+/g,' ') };
  });
  ok('#fxUpStat 이 업로드 카드들보다 위에 있다', !t.no && t.first==='fxUpStat', String(t.first));
  ok('표(table)를 쓰지 않는다 (r231 간소화 유지)', t.tbl===0, String(t.tbl));
  ok('높이가 160px 이하로 작다', t.h>0 && t.h<=160, t.h+'px');
  ok('줄이 계산서 · 입금 · 어음 세 개', JSON.stringify((t.lines||[]).map(x=>x.lab))===JSON.stringify(['계산서','입금','어음']), JSON.stringify((t.lines||[]).map(x=>x.lab)));

  const chips={}; (t.lines||[]).forEach(l=>l.chips.forEach(c=>{ chips[c.t.split(' ')[0]]=c; }));

  // ── r237 ① 실제 통장(obiz) 기준 ──
  ok('r237: 기업은행 칩에 화성이 안 나온다 (이동 배정 2건)',
     !!chips['기업'] && !/화성/.test(chips['기업'].t), (chips['기업']||{}).t);
  ok('r237: 기업은행 서울은 그대로 2026.10.01', /기업 서울 2026\.10\.01/.test((chips['기업']||{}).t||''), (chips['기업']||{}).t);
  ok('r237: 2024.09.10 (이동 배정분) 이 어디에도 안 보인다', !/2024\.09\.10/.test(t.txt), t.txt.slice(0,160));
  // 반대 방향(화성 계좌 → 서울 거래처)도 '계좌' 쪽인 화성으로 센다
  ok('r237: 화성 계좌 입금은 서울 거래처에 배정돼도 화성으로 센다',
     /신한 화성 2026\.10\.09/.test((chips['신한']||{}).t||'') && !/서울/.test((chips['신한']||{}).t||''), (chips['신한']||{}).t);
  // 이동분도 '서울 계좌' 자료이므로 서울 건수에는 그대로 들어간다 (1 + 이동 2 = 3건)
  ok('r237: 서울 계좌 입금은 배정 사업장과 무관하게 서울 건수 (3건)', /·\s*3건/.test((chips['기업']||{}).tip||''), (chips['기업']||{}).tip);

  // ── r237 ② iM 숨김 ──
  ok('r237: iM 칩이 없다', !chips['iM'], JSON.stringify(Object.keys(chips)));
  ok('r237: 본문에 iM 글자가 없다', !/iM/.test(t.txt), t.txt.slice(0,160));

  // ── 기존 동작(r230~r232) 유지 ──
  ok('매출 칩에 서울·화성 두 날짜', /매출 서울 2026\.09\.30 화성 2026\.10\.10/.test((chips['매출']||{}).t||''), (chips['매출']||{}).t);
  ok('매입은 자료 있는 서울만', /매입 서울 2026\.09\.15/.test((chips['매입']||{}).t||'') && !/화성/.test((chips['매입']||{}).t||''), (chips['매입']||{}).t);
  ok('국민은 서울만', /국민 서울 2026\.10\.13/.test((chips['국민']||{}).t||'') && !/화성/.test((chips['국민']||{}).t||''), (chips['국민']||{}).t);
  ok('신한어음은 화성만', /신한어음 화성 2026\.09\.20/.test((chips['신한어음']||{}).t||'') && !/서울/.test((chips['신한어음']||{}).t||''), (chips['신한어음']||{}).t);
  ok('자료 없는 은행(우리·하나·농협)은 칩이 없다', !chips['우리'] && !chips['하나'] && !chips['농협'], JSON.stringify(Object.keys(chips)));
  ok('날짜가 0000.00.00 년월일 형식 (r232)', /2026\.10\.13/.test(t.txt) && !/\b\d{2}-\d{2}\b/.test(t.txt), t.txt.slice(0,160));
  ok('"마지막 거래일" 안내 한 줄', /마지막 거래일/.test(t.txt), '');

  // 수금 계산은 e.biz 그대로 — 이동 배정분이 화성 수금에 남아 있어야 한다
  const keep=await pg.evaluate(()=>{
    return __T("fxDeposits.filter(function(e){return e.biz==='화성' && e.bank==='기업';}).reduce(function(s,e){return s+e.amount;},0)");
  });
  ok('수금 계산용 biz 는 안 건드린다 (화성 기업 163,031,034 유지)', keep===163031034, String(keep));

  const up=await pg.evaluate(async()=>{
    window.__D.push({biz:'서울', date:'2026-10-14', kind:'bank', bank:'신한', amount:1});
    __T("_fxMetaRefresh()"); await new Promise(r=>setTimeout(r,200));
    return (document.getElementById('fxUpStat').innerText||'').replace(/\s+/g,' ');
  });
  ok('업로드 후 _fxMetaRefresh() 로 갱신 (신한 서울 → 2026.10.14)', /신한 서울 2026\.10\.14/.test(up), up.slice(0,140));

  const safe=await pg.evaluate(async()=>{ __T("switchPage('fxsum')"); await new Promise(r=>setTimeout(r,300));
    try{ __T("_fxMetaRefresh()"); return 'ok'; }catch(e){ return 'ERR '+e.message; } });
  ok('다른 탭에서 불러도 오류 없음', safe==='ok', safe);

  ok('pageerror 없음', errs.length===0, errs.join(' | '));
  await b.close();
  let p=0; P.forEach(x=>{ if(x[1])p++; console.log((x[1]?'  OK  ':'  FAIL')+'  '+x[0]+(x[1]?'':'   → '+x[2])); });
  console.log('['+LABEL+'] '+p+'/'+P.length);
})();
