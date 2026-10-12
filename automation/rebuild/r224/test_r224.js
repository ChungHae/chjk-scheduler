const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b224/testpage/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  // 하니스: Firebase 대역(_fbFetch 를 eval 창구에서 교체) + XLSX 대역
  const STUB = `
  window.__FB={}; window.__FBLOG=[]; window.__DL=[];
  window._xlsxStyleReady=true;
  window.XLSX={ read:function(){ return {SheetNames:['s'],Sheets:{s:{}}}; }, utils:{ sheet_to_json:function(){ return window.__AOA||[]; }, aoa_to_sheet:function(a){ return {__aoa:a}; }, book_new:function(){ return {Sheets:{},SheetNames:[]}; }, book_append_sheet:function(wb,ws,n){ wb.Sheets[n]=ws; wb.SheetNames.push(n); } }, writeFile:function(wb,fn){ window.__DL.push({fn:fn, aoa:wb.Sheets[wb.SheetNames[0]].__aoa}); } };
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r224.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  await pg.route('**/*', r => { const u=r.request().url(); if(u.startsWith('file://')) r.continue(); else r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  const show = (id) => pg.evaluate((id)=>{ document.querySelectorAll('.page-section').forEach(p=>{ if(p.id===id) p.style.display='block'; }); }, id);

  // Firebase 대역: /teamdata_test_carduse/<path>.json 를 메모리 객체로
  await T(`
    window.__FB={ shinhan:{ '20261005':{ 'shinhan_A1':{id:'shinhan_A1',issuer:'shinhan',date:'20261005',time:'12:10',cardNoMasked:'5432-****-****-1234',merchant:'김밥천국 구로점',mbiz:'',amount:9000,approvalNo:'A1',status:'approved'},
                                          'shinhan_A2':{id:'shinhan_A2',issuer:'shinhan',date:'20261005',time:'15:40',cardNoMasked:'5432-****-****-1234',merchant:'(주)대한공구',mbiz:'123-45-67890',amount:110000,approvalNo:'A2',status:'approved'} },
                            '20261007':{ 'shinhan_A3':{id:'shinhan_A3',issuer:'shinhan',date:'20261007',time:'09:00',cardNoMasked:'5432-****-****-9999',merchant:'SK주유소',mbiz:'',amount:70000,approvalNo:'A3',status:'approved',holderHint:'함현식'},
                                          'shinhan_A4':{id:'shinhan_A4',issuer:'shinhan',date:'20261007',time:'09:30',cardNoMasked:'5432-****-****-1234',merchant:'김밥천국 구로점',mbiz:'',amount:8000,approvalNo:'A4',status:'cancelled'} } },
                 hana:{ '20260915':{ 'hana_B1':{id:'hana_B1',issuer:'hana',date:'20260915',cardNoMasked:'****1234',merchant:'스타벅스',amount:12000,approvalNo:'B1',status:'approved'} } },
                 _meta:{ shinhan:{lastSyncedAt:'2026-10-12T01:00:00Z'} }, _cards:{ '1234':{issuer:'shinhan',holder:'김재성',label:'영업용'} }, _tags:{}, _learn:{}, _cats:null };
    function _fbGetPath(url){ var m=String(url).match(/teamdata_test_carduse\\/(.+?)\\.json/); return m?m[1].split('/'):null; }
    _fbFetch=async function(url, opts){
      var p=_fbGetPath(url); if(!p) return {ok:false,status:404,json:async function(){return null;}};
      var method=(opts&&opts.method)||'GET'; window.__FBLOG.push(method+' '+p.join('/'));
      var node=window.__FB; for(var i=0;i<p.length-1;i++){ if(node[p[i]]==null) node[p[i]]={}; node=node[p[i]]; } var last=p[p.length-1];
      if(method==='GET'){ var v=(p.length===1)?window.__FB[last]:node[last]; return {ok:true,status:200,json:async function(){ return v===undefined?null:JSON.parse(JSON.stringify(v)); }}; }
      var body=opts.body?JSON.parse(opts.body):null;
      if(method==='PUT'){ if(p.length===1) window.__FB[last]=body; else node[last]=body; }
      else if(method==='PATCH'){ var tgt=(p.length===1)?(window.__FB[last]=window.__FB[last]||{}):(node[last]=node[last]||{}); for(var k in body) tgt[k]=body[k]; }
      else if(method==='DELETE'){ if(p.length===1) delete window.__FB[last]; else delete node[last]; }
      return {ok:true,status:200,json:async function(){return null;}};
    };
    _fbDbUrl='https://x.test'; _authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울'},{id:'m2',name:'함현식',group:'서울'}]; myMemberId='m1';
    fxPurchInv=[{biz:'서울',date:'20261001',vendor:'(주)대한공구',vbiz:'123-45-67890',supply:100000,tax:10000,total:110000}]; _fxLoaded=true; _fxEnsureData=async function(){};
    memoLines=[]; 'ok'`);

  console.log('▶ 회계 > 카드사용 탭');
  ok(await T(`!!document.querySelector('.sub-tab[data-page="carduse"]') && !!document.getElementById('pageCardUse')`), '서브탭·페이지 존재');
  await T(`switchPage('carduse'); 'ok'`); await pg.waitForTimeout(600); await show('pageCardUse');
  ok(await T(`document.getElementById('pageCardUse').classList.contains('active') && document.getElementById('acctSubNav').style.display==='flex'`), '회계 서브탭 안에서 열림');
  ok(await T(`_cu.recs.length===5 && _cu.ym==='202610'`), '자료 5건 로드 · 최근 달(2026-10) 자동 선택');
  ok(await T(`document.getElementById('cuMonthLbl').textContent==='2026년 10월'`), '월 표시');
  const tiles = await T(`document.getElementById('cuTiles').innerText`);
  ok(tiles.indexOf('189,000원')>=0 && tiles.indexOf('3건')>=0 && tiles.indexOf('취소 1')>=0, '타일: 이달 189,000원 · 3건 · 취소 1 ('+tiles.replace(/\n/g,' / ')+')');
  ok(tiles.indexOf('미분류')>=0 && /미분류\s*\n?\s*3건/.test(tiles), '미분류 3건');
  ok(/중복 의심\s*\n?\s*1건/.test(tiles), '매입계산서 중복 의심 1건 (대한공구 110,000 = 계산서)');
  const sub = await T(`document.getElementById('cuSub').innerText`);
  ok(sub.indexOf('****-1234 영업용')>=0 && sub.indexOf('김재성')>=0 && sub.indexOf('함현식')>=0, '카드별(별칭)·사용자별 소계 (이용자명 힌트 함현식 인식)');
  ok(await T(`document.querySelectorAll('#cuBody tr').length===4 && document.querySelectorAll('#cuBody tr.cancel').length===1 && document.querySelectorAll('#cuBody .cu-chip').length===1`), '목록 4줄 · 취소 1줄 · 계산서 중복 칩 1개');

  console.log('▶ 용도 분류 + 가맹점 학습');
  await T(`cuSetUse('shinhan_A1','식비'); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`__FB._tags.shinhan_A1.use==='식비' && __FB._tags.shinhan_A1.by==='김재성' && __FB._learn[_cuMerKey('김밥천국 구로점')].use==='식비'`), '태그 저장(PATCH) + 가맹점 학습 저장');
  ok(await T(`_cuUse(_cu.recs.find(function(r){return r.id==='shinhan_A4';}))==='식비'`), '같은 가맹점 다른 건은 자동으로 식비');
  ok((await T(`document.getElementById('cuTiles').innerText`)).match(/미분류\s*\n?\s*2건/)!=null, '미분류 2건으로 줄어듦');
  await T(`cuSetWho('shinhan_A3','김재성'); 'ok'`); await pg.waitForTimeout(100);
  ok(await T(`__FB._tags.shinhan_A3.who==='김재성' && _cuWho(_cu.recs.find(function(r){return r.id==='shinhan_A3';}))==='김재성'`), '사용자 지정 저장');
  await T(`cuSetMemo('shinhan_A2','볼트 50개'); 'ok'`); await pg.waitForTimeout(100);
  ok(await T(`__FB._tags.shinhan_A2.memo==='볼트 50개'`), '메모 저장');

  console.log('▶ 필터');
  await T(`document.getElementById('cuUseF').value='__none'; cuSetFilter(); 'ok'`);
  ok(await T(`document.querySelectorAll('#cuBody tr').length===2`), '미분류만 → 2줄 (대한공구·SK주유소)');
  await T(`document.getElementById('cuUseF').value=''; document.getElementById('cuDupOnly').checked=true; cuSetFilter(); 'ok'`);
  ok(await T(`document.querySelectorAll('#cuBody tr').length===1 && document.getElementById('cuBody').innerText.indexOf('대한공구')>=0`), '계산서 중복만 → 대한공구 1줄');
  await T(`document.getElementById('cuDupOnly').checked=false; cuSetFilter(); cuMonthDelta(-1); 'ok'`);
  ok(await T(`_cu.ym==='202609' && document.querySelectorAll('#cuBody tr').length===1 && document.getElementById('cuBody').innerText.indexOf('스타벅스')>=0`), '이전 달(9월) → 하나카드 스타벅스 1줄');
  await T(`cuMonthDelta(1); 'ok'`);

  console.log('▶ 카드 등록 · 용도 목록');
  await T(`cuOpenCards(); document.getElementById('cuNewL4').value='9999'; document.getElementById('cuNewIss').value='shinhan'; document.getElementById('cuNewWho').value='함현식'; document.getElementById('cuNewLabel').value='화성'; cuAddCard(); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`__FB._cards['9999'].holder==='함현식' && document.getElementById('cuCardsOverlay').innerText.indexOf('****-9999')>=0`), '카드 9999 → 함현식 등록 (PUT)');
  await T(`document.getElementById('cuCardsOverlay').style.display='none'; _cu.cats=['식비','자재']; 'ok'`);
  ok(await T(`document.querySelectorAll('#cuBody tr')[0] && _cuCats().length===2`), '용도 목록 교체 반영');
  await T(`_cu.cats=null; _cuRenderAll(); 'ok'`);

  console.log('▶ 엑셀 다운로드 / 업로드(머리글 자동 판별)');
  await T(`cuExport(); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`__DL.length===1 && __DL[0].fn==='카드사용_202610.xlsx' && __DL[0].aoa.length===5 && __DL[0].aoa[0][0]==='일자' && __DL[0].aoa.some(function(r){ return r[5]==='(주)대한공구' && r[14]==='계산서 20261001'; })`), '엑셀: 머리글+4줄, 계산서 중복 표시');
  await T(`window.__AOA=[['신한카드 법인 이용내역'],[],['이용일자','이용시간','카드번호','이용가맹점','사업자등록번호','이용금액','승인번호','거래구분','이용자'],['2026.10.08','11:20','5432-****-****-1234','다이소 구로점','321-11-22222','15,000','C100','승인','김재성'],['2026-10-09','','5432-****-****-9999','GS칼텍스','','50000','C101','취소','함현식'],[45938,'08:00','****1234','김밥천국 구로점','','7,000','C102','정상','']];
    _cuUpIss='shinhan'; _cuUpFile={name:'x.xlsx', arrayBuffer:async function(){ return new ArrayBuffer(1); }}; cuDoUpload(); 'ok'`); await pg.waitForTimeout(600);
  ok(await T(`__FB.shinhan['20261008'] && __FB.shinhan['20261008']['shinhan_C100'].amount===15000 && __FB.shinhan['20261008']['shinhan_C100'].mbiz==='321-11-22222'`), '2026.10.08 → 20261008 · 금액 콤마 제거 · 사업자번호 정규화');
  ok(await T(`__FB.shinhan['20261009']['shinhan_C101'].status==='cancelled'`), '거래구분 "취소" → cancelled');
  ok(await T(`__FB.shinhan['20251008'] && __FB.shinhan['20251008']['shinhan_C102'] && __FB.shinhan['20251008']['shinhan_C102'].amount===7000`), '엑셀 날짜 일련번호(45938=2025-10-08) 변환');
  ok(await T(`__FB._meta.shinhan.source==='upload' && _cu.recs.length===8`), '메타 갱신 + 화면 재로드 (8건)');
  ok(await T(`_cuUse(_cu.recs.find(function(r){return r.id==='shinhan_C102';}))==='식비'`), '새로 올라온 김밥천국 건도 학습된 용도 자동');

  console.log('▶ 개인 일정: 내 카드 + 배너');
  await T(`switchPage('memo'); 'ok'`); await pg.waitForTimeout(400);
  ok(await T(`!!document.querySelector('#pageMemo .mm-smc.cu') && document.querySelector('#pageMemo .mm-smc.cu').innerText.indexOf('미분류')>=0`), '메모장에 "내 카드 사용 미분류 N건" 배너');
  ok(await T(`!!document.querySelector('#pageMemo button[data-tip="내 카드 사용"]')`), '메모장 툴바에 내 카드 버튼');
  await T(`cuOpenMine(); 'ok'`); await pg.waitForTimeout(300);
  const mine = await T(`document.getElementById('cuMineBody').innerText`);
  ok(mine.indexOf('2026년 10월')>=0 && mine.indexOf('김밥천국')>=0 && mine.indexOf('다이소')>=0 && mine.indexOf('GS칼텍스')<0, '본인(김재성) 카드 건만 — 함현식 카드(GS칼텍스) 제외');
  ok(mine.indexOf('SK주유소')>=0, '사용자 지정으로 넘겨받은 건(SK주유소)도 보임');
  await T(`cuSetUse('shinhan_A2','자재·부품'); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`__FB._tags.shinhan_A2.use==='자재·부품' && document.getElementById('cuMineBody').innerText.indexOf('자재·부품')>=0`), '내 카드 창에서 용도 선택 → 저장 + 창 갱신');
  await T(`_authUser={id:'h',name:'함현식',role:'member'}; 'ok'`);
  await T(`cuOpenMine(); 'ok'`); await pg.waitForTimeout(200);
  const mine2 = await T(`document.getElementById('cuMineBody').innerText`);
  ok(mine2.indexOf('GS칼텍스')>=0 && mine2.indexOf('김밥천국')<0 && mine2.indexOf('SK주유소')<0, '함현식으로 보면 본인 카드(9999) 건만');
  ok(errs.length===0, 'pageerror 0'+(errs.length?(' — '+errs.join(' | ')):''));
  console.log(`\n결과: ${pass}/${pass+fail}`);
  fs.unlinkSync(tmp); await br.close(); process.exit(fail?1:0);
})();
