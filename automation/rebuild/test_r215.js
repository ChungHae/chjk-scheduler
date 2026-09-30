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

  // ① 탭 순서
  const nav=await pg.evaluate(()=>{
    __T("switchPage('fx')");
    return [].slice.call(document.querySelectorAll('#acctSubNav .sub-tab')).map(b=>({t:(b.innerText||'').trim(), p:b.dataset.page}));
  });
  ok('탭 순서가 집계·입출금·미수현황·카드매출·자료 업로드 (r215)',
     JSON.stringify(nav.map(x=>x.t))===JSON.stringify(['집계','입출금','미수현황','카드매출','자료 업로드']), JSON.stringify(nav.map(x=>x.t)));
  ok('page 값도 순서대로 fxsum·armatch·fx·cardsales·fxup',
     JSON.stringify(nav.map(x=>x.p))===JSON.stringify(['fxsum','armatch','fx','cardsales','fxup']), JSON.stringify(nav.map(x=>x.p)));
  for(const [p,t] of [['fxsum','sum'],['fx','ar'],['fxup','up']]){
    const r=await pg.evaluate((a)=>{ __T("switchPage('"+a+"')"); return __T("_fxTab"); }, p);
    ok('순서를 바꿔도 '+p+' → _fxTab='+t, r===t, String(r));
  }

  // ② 인쇄본 높이 맞춤
  const r=await pg.evaluate(async()=>{
    var d=document.createElement('div'); d.innerHTML='<input id="nyCorp" value="다온자동화"><input id="nyAmt" value="4,184,895"><input id="nyRep" value="홍길동"><input id="nyTel" value="010-1234-5678"><input id="nyAddr" value="경기도 화성시 동탄대로 12, 동탄빌딩 3층"><input id="nyDate" value="2026-09-30"><span id="nyMsg"></span>';
    document.body.appendChild(d);
    __T("fxNySetRgn('화성')");
    window.__cap=null; __T("_nyPrintHtml=function(h){ window.__cap=h; };");
    await __T("fxNyPrint()"); await new Promise(x=>setTimeout(x,600));
    const html=window.__cap;
    // 같은 조건으로 높이를 다시 재 본다
    const f=document.createElement('iframe');
    f.setAttribute('style','position:fixed;left:-10000px;top:0;width:170mm;height:2000mm;border:0;opacity:0');
    document.body.appendChild(f);
    const dd=f.contentWindow.document; dd.open(); dd.write(html); dd.close();
    const hpt=dd.body.getBoundingClientRect().height*72/96;
    const lh=(html.match(/body\{[^}]*line-height:([\d.]+)pt/)||[])[1];
    f.remove();
    return { html, hpt:Math.round(hpt*10)/10, lh:parseFloat(lh), base:__T("_nyLineFactor()"), frame: !!document.getElementById('nyFitFrame') };
  });
  ok('A4 본문 높이(785.2pt)를 넘지 않는다', r.hpt<=785.2, 'h='+r.hpt);
  ok('A4 한 장을 꽉 채운다 (740pt 이상) (r215)', r.hpt>=740, 'h='+r.hpt);
  ok('줄높이가 기본 계수보다 넓어졌다 (r215)', r.lh > 9.5*r.base + 0.01, 'lh='+r.lh+' base*9.5='+Math.round(9.5*r.base*100)/100);
  ok('재기용 틀(nyFitFrame)은 남지 않는다', r.frame===false, String(r.frame));
  ok('명판·인감에 height 가 지정된다 (r215)', /width:6cm;height:[\d.]+cm/.test(r.html) && /width:1\.5cm;height:[\d.]+cm/.test(r.html), '');
  const sps=(r.html.match(/height:(\d+(?:\.\d+)?)pt;font-size:0/g)||[]).map(s=>parseFloat(s.match(/height:([\d.]+)pt/)[1]));
  ok('문단 간격(docx after+before)은 그대로',
     JSON.stringify(sps)===JSON.stringify([2,10,2,5,2,7,15,3,3,3,3,3,3,2,14,14,6]), JSON.stringify(sps));
  ok('7개 항목·계좌표는 그대로', /7\. 원만한 해결을/.test(r.html) && /140-013-471920/.test(r.html), '');

  const p2=await (await b.newContext()).newPage();
  await p2.setContent(r.html, {waitUntil:'load'});
  const buf=await p2.pdf({format:'A4', printBackground:true, margin:{top:'1.1cm',right:'2.0cm',bottom:'0.9cm',left:'2.0cm'}});
  const pages=(buf.toString('latin1').match(/\/Type\s*\/Page[^s]/g)||[]).length;
  ok('그래도 A4 한 장', pages===1, 'pages='+pages);
  fs.writeFileSync('/tmp/h/ny_print_r215.pdf', buf);

  console.log('=== ['+LABEL+'] r215 점검 ===');
  let pass=0; P.forEach(([n,c,e])=>{ if(c)pass++; console.log((c?'  PASS  ':'  FAIL  ')+n+(c?'':'  << '+e)); });
  console.log('---\n통과 '+pass+'/'+P.length+'\npageerrors: '+(errs.length?errs.join('\n'):'없음'));
  await b.close(); process.exit(pass===P.length?0:1);
})();
