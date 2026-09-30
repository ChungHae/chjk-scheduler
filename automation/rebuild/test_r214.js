const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs=require('fs');
const FILE=process.argv[2], LABEL=process.argv[3]||'?';
const ASSETS=JSON.parse(fs.readFileSync('/tmp/h/ny_assets_real.json','utf8'));
(async()=>{
  const b=await chromium.launch({});
  const pg=await (await b.newContext({timezoneId:'Asia/Seoul', viewport:{width:1400,height:900}})).newPage();
  await pg.route(/^https?:\/\//, r=>r.abort());
  const errs=[]; pg.on('pageerror',e=>errs.push(String(e).slice(0,180)));
  await pg.goto('file://'+FILE); await pg.waitForTimeout(3200);
  const P=[]; const ok=(n,c,e)=>P.push([n,!!c,e]);

  await pg.evaluate((A)=>{
    document.getElementById('authGate').style.display='none';
    __T("_authUser={id:'chjk',name:'chjk',role:'admin'}"); __T("_fbDbUrl='https://stub'");
    __T("_fxLoaded=true"); __T("debouncedFbSave=function(){}"); __T("_fxSave=function(){}");
    __T("_fxSaveBig=async function(){}"); __T("_fxEnsureData=async function(){}");
    __T("showInfoModal=function(t,m){window.__i={t:t,m:m};}; showConfirmModal=function(t,m,ok){ok&&ok();};");
    window.__A=A; __T("_nyAssets=window.__A;");
    __T("fxSalesInv=[]; fxDeposits=[]; fxAdjusts=[]; fxOpenings={}; fxTerms={}; fxExcluded=[]; fxAlias={};");
  }, ASSETS);

  // ── ② 탭 구조 ──
  const nav=await pg.evaluate(()=>{
    __T("switchPage('fx')");
    const acct=[].slice.call(document.querySelectorAll('#acctSubNav .sub-tab')).map(b=>({t:(b.innerText||'').trim(), p:b.dataset.page, hidden:b.style.display==='none'}));
    return { acct, fxSubNav: !!document.getElementById('fxSubNav') };
  });
  ok('상위 탭이 입출금·미수현황·집계·자료 업로드·카드매출 5개 (r214)',
     JSON.stringify(nav.acct.map(x=>x.t))===JSON.stringify(['입출금','미수현황','집계','자료 업로드','카드매출']), JSON.stringify(nav.acct));
  ok('page 값이 armatch/fx/fxsum/fxup/cardsales',
     JSON.stringify(nav.acct.map(x=>x.p))===JSON.stringify(['armatch','fx','fxsum','fxup','cardsales']), JSON.stringify(nav.acct.map(x=>x.p)));
  ok('아래 소카테고리 줄(fxSubNav)이 없어졌다 (r214)', nav.fxSubNav===false, String(nav.fxSubNav));

  const go=async(page)=>pg.evaluate((p)=>{
    __T("switchPage('"+p+"')");
    const act=[].slice.call(document.querySelectorAll('#acctSubNav .sub-tab')).filter(b=>b.classList.contains('active')).map(b=>(b.innerText||'').trim());
    return { tab:__T("_fxTab"), page:document.getElementById('pageFx').classList.contains('active'),
             acctOn:document.getElementById('acctSubNav').style.display,
             label:(document.querySelector('#fxToolbar .inv-flat-label')||{}).innerText||'',
             active:act };
  }, page);
  let g=await go('fx');
  ok('미수현황 → _fxTab=ar · pageFx 표시', g.tab==='ar' && g.page && /미수 현황/.test(g.label), JSON.stringify(g));
  ok('미수현황 탭에 active 표시', JSON.stringify(g.active)===JSON.stringify(['미수현황']), JSON.stringify(g.active));
  g=await go('fxsum');
  ok('집계 → _fxTab=sum (r214)', g.tab==='sum' && g.page, JSON.stringify(g));
  ok('집계 탭에 active 표시', JSON.stringify(g.active)===JSON.stringify(['집계']), JSON.stringify(g.active));
  g=await go('fxup');
  ok('자료 업로드 → _fxTab=up (r214)', g.tab==='up' && g.page, JSON.stringify(g));
  g=await go('cardsales');
  ok('카드매출로 가도 회계 서브탭은 그대로 보인다', g.acctOn==='flex', JSON.stringify(g));

  // 옛 fxSwitchTab 호환
  const compat=await pg.evaluate(()=>{ __T("fxSwitchTab('sum')"); return __T("_fxTab"); });
  ok('옛 fxSwitchTab 호출도 동작한다 (호환 래퍼)', compat==='sum', String(compat));

  // 마스터가 아니면 '자료 업로드' 버튼이 숨는다
  const hid=await pg.evaluate(()=>{
    __T("_authUser={id:'kim',name:'김직원',role:'admin'}");
    __T("switchPage('fx')");
    const b=document.getElementById('acctTabFxUp');
    return { hidden: b ? (b.style.display==='none') : 'no-btn', tab:__T("_fxTab") };
  });
  ok('마스터가 아니면 자료 업로드 탭이 숨는다', hid.hidden===true, JSON.stringify(hid));
  await pg.evaluate(()=>{ __T("_authUser={id:'chjk',name:'chjk',role:'admin'}"); __T("switchPage('fx')"); });

  // ── ① 인쇄 줄간격 ──
  const lf=await pg.evaluate(()=>{ try{ return { f:__T("_nyLineFactor()") }; }catch(e){ return { f:'없음' }; } });
  ok('줄높이 계수를 이 브라우저에서 잰다 (0.8~2.5em × 1.22917 범위)',
     typeof lf.f==='number' && lf.f>0.98 && lf.f<3.08, JSON.stringify(lf));

  const html=await pg.evaluate(async()=>{
    try{ __T("_nyLFCache=1.6497;"); }catch(e){}   // 사용자 PC 실측값으로 고정해 비교
    var d=document.createElement('div'); d.innerHTML='<input id="nyCorp" value="다온자동화"><input id="nyAmt" value="4,184,895"><input id="nyRep" value="홍길동"><input id="nyTel" value="010-1234-5678"><input id="nyAddr" value="경기도 화성시 동탄대로 12, 동탄빌딩 3층"><input id="nyDate" value="2026-09-30"><span id="nyMsg"></span>';
    document.body.appendChild(d);
    __T("fxNySetRgn('화성')");
    window.__cap=null; __T("_nyPrintHtml=function(h){ window.__cap=h; };");
    await __T("fxNyPrint()"); await new Promise(r=>setTimeout(r,200));
    return window.__cap;
  });
  ok('본문 줄높이 9.5 × 1.6497 = 15.67pt (워드와 같음)', /line-height:15\.67pt/.test(html), (html.match(/line-height:[\d.]+pt/g)||[]).join(','));
  ok('제목 22 × 1.6497 = 36.29pt', /line-height:36\.29pt/.test(html), '');
  ok('소제목·날짜 10.5 × 1.6497 = 17.32pt', /line-height:17\.32pt/.test(html), '');
  ok('발신인명 11.5 × 1.6497 = 18.97pt', /line-height:18\.97pt/.test(html), '');
  ok('r212 의 좁은 값(14.19pt)은 더 이상 없다', !/line-height:14\.19pt/.test(html), '');
  const sps=(html.match(/height:(\d+(?:\.\d+)?)pt;font-size:0/g)||[]).map(s=>parseFloat(s.match(/height:([\d.]+)pt/)[1]));
  ok('문단 간격(docx after+before)은 그대로',
     JSON.stringify(sps)===JSON.stringify([2,10,2,5,2,7,15,3,3,3,3,3,3,2,14,14,6]), JSON.stringify(sps));

  const p2=await (await b.newContext()).newPage();
  await p2.setContent(html, {waitUntil:'load'});
  const buf=await p2.pdf({format:'A4', printBackground:true, margin:{top:'1.1cm',right:'2.0cm',bottom:'0.9cm',left:'2.0cm'}});
  const pages=(buf.toString('latin1').match(/\/Type\s*\/Page[^s]/g)||[]).length;
  ok('간격을 늘려도 A4 한 장에 들어간다', pages===1, 'pages='+pages);
  fs.writeFileSync('/tmp/h/ny_print_r214.pdf', buf);

  console.log('=== ['+LABEL+'] r214 점검 ===');
  let pass=0; P.forEach(([n,c,e])=>{ if(c)pass++; console.log((c?'  PASS  ':'  FAIL  ')+n+(c?'':'  << '+e)); });
  console.log('---\n통과 '+pass+'/'+P.length+'\npageerrors: '+(errs.length?errs.join('\n'):'없음'));
  await b.close(); process.exit(pass===P.length?0:1);
})();
