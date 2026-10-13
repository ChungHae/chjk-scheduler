// r226 테스트 — A) SMC 확인 견적가 열  B) 메모장 담당 업체 매출 카드  C) 업체별 소물류 기준가(확판/소물) 선택·배지·구매가 적용
//  사용:  node test_r226.js <r226 적용된 index.html>
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b226/test/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const STUB = `
  window._xlsxStyleReady=true;
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r226.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  await pg.route('**/*', r => { const u=r.request().url(); if(u.startsWith('file://')) r.continue(); else r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  const Y = new Date().getFullYear();

  await T(`
    _fbDbUrl='https://x.test'; _authUser={id:'kjs',name:'김재성',role:'admin'}; myMemberId='m1';
    members=[{id:'m1',name:'김재성',group:'서울'},{id:'m2',name:'함현식',group:'서울'}];
    _fbPutOk=async function(){ return true; }; debouncedFbSave=function(){}; _qBlobPut=async function(){ return true; };
    clientList=[['A전기','111-11-11111']]; customClients=[]; clientOwner={}; clientPBase={}; memoLines=[];
    quoteSaved=[]; for(var i=0;i<6;i++) quoteSaved.push({id:'a'+i,title:'Q',vname:'A전기',vid:'v1',count:1,total:0,savedBy:'김재성',savedAt:i});
    fxSalesInv=[{biz:'서울',date:'${Y}-03-10',vendor:'A전기',vbiz:'111-11-11111',supply:1000000},{biz:'서울',date:'${Y-1}-03-10',vendor:'A전기',vbiz:'111-11-11111',supply:250000}];
    _fxLoaded=false; _fxEnsureData=async function(){ _fxLoaded=true; };
    smcQueue=[{id:'s1',spec:'KQ2L04-01AS',name:'FITTING',e:1320,buy:990,vid:'v1',vname:'A전기',by:'김재성',at:Date.now(),quoteNo:'A전기-20261013-01',status:'wait'},
              {id:'s2',spec:'CJ2L10-20Z',name:'CYL',e:13860,buy:10395,vid:'v1',vname:'A전기',by:'김재성',at:Date.now()-1,quoteNo:'A전기-20261013-01',status:'ok',okE:13860,okHp:null,okSm:null,okBy:'김재성',okAt:Date.now()}];
    'ok'`);

  console.log('▶ A) SMC 확인 견적가 열');
  await T(`_smcFilter='wait'; renderSmcPage(); 'ok'`);
  let ths = await T(`[...document.querySelectorAll('#qSubSmc thead th')].map(function(t){ return t.textContent.trim(); }).join(',')`);
  ok(ths==='No.,규격,품목명,E가,견적가,확판가,소물가,거래처,작성자,날짜,견적번호,처리', '대기 표 머리글에 견적가 열 ('+ths+')');
  let tds = await T(`[...document.querySelector('#smcResult tr[data-id="s1"]').children].map(function(td){ var i=td.querySelector('input'); return i?('['+(i.getAttribute('data-f')||'')+':'+i.value+'|'+(i.placeholder||'')+']'):td.textContent.trim(); }).join(' ')`);
  ok(/\[e:1320\|\] 990 \[hp:\|\] \[sm:\|\]/.test(tds), '대기 줄: E가 1320 · 견적가 990 · 확판가 칸 빈칸(안내값 없음) ('+tds+')');
  await T(`_smcFilter='ok'; renderSmcPage(); 'ok'`);
  tds = await T(`[...document.querySelector('#smcResult tr[data-id="s2"]').children].map(function(td){ return td.textContent.trim(); }).slice(3,7).join(' ')`);
  ok(tds==='13,860 10,395 - -', '등록됨 줄: E가 · 견적가 10,395 · 확판가 - · 소물가 - ('+tds+')');

  console.log('▶ B) 메모장 담당 업체 매출 카드');
  await T(`switchPage('memo'); 'ok'`); await pg.waitForTimeout(800);
  let card = await T(`(document.querySelector('#pageMemo .mm-smc.co')||{}).innerText||''`);
  ok(card.indexOf('내 담당 업체 1곳')>=0 && card.indexOf(String(Y)+'년 매출 1,000,000원')>=0 && card.indexOf(String(Y-1)+'년 250,000원')>=0, '카드: 담당 1곳 · 올해 1,000,000 · 작년 250,000 ('+card.replace(/\n/g,' / ')+')');
  ok(await T(`document.querySelector('#pageMemo .mm-smc.co').getAttribute('onclick')==='coOpenMine()'`), '카드 클릭 → coOpenMine');
  await T(`_authUser={id:'h',name:'함현식',role:'user'}; renderMemoPage(true); 'ok'`);
  ok(await T(`!document.querySelector('#pageMemo .mm-smc.co')`), '담당 없는 사람에게는 카드 없음');
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; 'ok'`);

  console.log('▶ C) 소물류 기준가');
  await T(`switchPage('quote'); 'ok'`); await pg.waitForTimeout(500);
  await T(`quoteVendors=[{id:'v1',name:'A전기',count:0}]; _qCurId='v1'; _qRows=[]; _qLoadedId=null; _qQuoteNo='A전기-20261013-01';
    _priceSyncMap={ 'KQ2L04-01AS':{e:1320, buy:990, small:1056, locked:true}, 'CJ2L10-20Z':{e:13860, buy:10395, small:null, locked:true} }; _priceSyncReady=true;
    _qCart=[ {vid:'v1',vname:'A전기',spec:'KQ2L04-01AS',name:'FITTING',e:1320,buy:990,small:1056,pl:true,sell:1500,qty:2,psrc:'kq2l04-01as'},
             {vid:'v1',vname:'A전기',spec:'CJ2L10-20Z',name:'CYL',e:13860,buy:10395,small:null,pl:true,sell:15000,qty:1,psrc:'cj2l10-20z'},
             {vid:'v1',vname:'A전기',spec:'X-1',name:'ETC',e:1000,buy:800,small:null,pl:false,sell:1200,qty:1,psrc:'x-1'} ];
    _qpbAsked={}; renderQCart(); 'ok'`); await pg.waitForTimeout(400);
  ok(await T(`document.getElementById('qpbOverlay') && document.getElementById('qpbOverlay').style.display==='flex'`), '첫 견적(기준 미정 + 소물가 있는 잠금줄) → 선택 팝업 자동');
  ok(await T(`document.getElementById('qpbOverlay').innerText.indexOf('소물가 있는 규격 1줄')>=0 && document.getElementById('qpbOverlay').innerText.indexOf('확판가만 있는 규격 1줄')>=0`), '팝업 안내: 소물가 있는 규격 1줄 · 확판가만 1줄');
  ok(await T(`document.querySelector('#qMetaInfo .qpb-badge.none') && document.querySelector('#qMetaInfo .qpb-badge').textContent.indexOf('기준가 미정')>=0`), '배지: 기준가 미정');
  ok(await T(`_qCart[0].buy===990 && _qCart[0].hp===990`), '미정 상태: 구매가 = 확판가 990 (hp 보관)');
  await T(`qpbSet('A전기','sm'); 'ok'`); await pg.waitForTimeout(300);
  ok(await T(`document.getElementById('qpbOverlay').style.display==='none' && clientPBase['A전기'].base==='sm'`), '소물가 기준 선택 → 저장 · 팝업 닫힘');
  ok(await T(`_qCart[0].buy===1056 && _qCart[0].hp===990`), '소물가 있는 줄: 구매가 1056(소물가), hp 990 유지');
  ok(await T(`_qCart[1].buy===10395`), '소물가 없는 잠금줄: 구매가 확판가 그대로');
  ok(await T(`_qCart[2].buy===800 && _qCart[2].hp==null`), '비잠금 줄: 영향 없음');
  ok(await T(`document.querySelector('#qMetaInfo .qpb-badge.sm') && document.querySelector('#qMetaInfo .qpb-badge').textContent.indexOf('소물가 기준')>=0`), '배지: 소물가 기준');
  const buyCells = await T(`[...document.querySelectorAll('#qCart tbody tr')].slice(0,2).map(function(tr){ var ins=[...tr.querySelectorAll('input.qc-in[readonly]')]; var b=ins.find(function(i){ return i.title==='소물가 기준'||i.title==='확판가 기준'; }); return b?(b.title+':'+b.value):'?'; }).join(' | ')`);
  ok(buyCells==='소물가 기준:1,056 | 확판가 기준:10,395', '구매가 칸 안내·값 ('+buyCells+')');
  // 마진은 새 구매가 기준
  const mg = await T(`_qMarginOf(_qCart[0].buy,_qCart[0].sell)`);
  ok(Math.abs(mg-(1-1056/1500))<1e-9, '마진율 = 소물가 기준으로 계산');
  // 원장 flush 는 확판가
  await T(`_qRows=[]; window.__fl=0; _qFlushLedgerFromCart().then(function(){ window.__fl=1; }); 'ok'`); await pg.waitForTimeout(500);
  ok(await T(`window.__fl===1`), '원장 flush 완료');
  ok(await T(`_qRows.find(function(r){ return r.spec==='KQ2L04-01AS'; }).buy===990 && _qRows.find(function(r){ return r.spec==='KQ2L04-01AS'; }).small===1056`), '원장 flush: buy=확판가 990 · small 1056');
  await T(`qpbSet('A전기','hp'); 'ok'`); await pg.waitForTimeout(300);
  ok(await T(`_qCart[0].buy===990 && document.querySelector('#qMetaInfo .qpb-badge.hp')`), '확판가 기준으로 되돌림 → 구매가 990 · 배지 hp');
  await T(`qpbSet('A전기',''); 'ok'`);
  ok(await T(`!clientPBase['A전기'] && _qCart[0].buy===990`), '설정 지우기 → 미정(확판가)');
  // 다시 그려도 자동 질문은 업체당 한 번
  await T(`renderQCart(); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`document.getElementById('qpbOverlay').style.display==='none'`), '자동 질문은 같은 업체에 한 번만');
  // 잠금줄 없는 업체 → 배지 없음
  await T(`quoteVendors.push({id:'v2',name:'B산업',count:0}); _qCurId='v2'; _qCart=[{vid:'v2',vname:'B산업',spec:'X-2',name:'',e:100,buy:80,small:null,pl:false,sell:120,qty:1,psrc:'x-2'}]; renderQCart(); 'ok'`);
  ok(await T(`!document.querySelector('#qMetaInfo .qpb-badge')`), '잠금줄 없고 설정도 없으면 배지 없음');

  console.log('▶ 배관');
  const srcTxt = fs.readFileSync(file,'utf8'); const isTest = /\/test\//.test(file) || /testpage/.test(file);
  ok(srcTxt.split("'sched_client_pend','sched_client_owner','sched_client_pbase','sched_meetings'").length-1 === (isTest?3:2), 'KEYS 에 sched_client_pbase ('+(isTest?3:2)+'곳)');
  ok(srcTxt.indexOf("save('sched_client_pbase', clientPBase)")>=0 && srcTxt.split("sched_client_pbase: clientPBase,   // r226\n").length-1===2 && srcTxt.indexOf("clientPBase      = load('sched_client_pbase')")>=0, 'save/푸시/백업/복원 배관');

  ok(errs.length===0, '페이지 오류 없음'+(errs.length?(' — '+errs.slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(_e){}
  process.exit(fail?1:0);
})();
