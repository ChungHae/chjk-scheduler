// r262 테스트 — 옵션 툴팁·우클릭 메뉴·옵션 보기 저장 · 변경 제안 줄·취소·이력·여러 줄 등록 · 원장 보호
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs=require('fs'), path=require('path');
const file=path.resolve(process.argv[2]||'d262/test/index.html');
let pass=0, fail=0; function ok(c,m){ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} }
(async()=>{
  const src=fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){','window.__T=function(c){return eval(c);}; function _vacUnlimited(id){');
  const tmp=path.join(path.dirname(file),'_h_r262.html'); fs.writeFileSync(tmp,src);
  const br=await chromium.launch(); const pg=await br.newPage({viewport:{width:1400,height:900}}); const errs=[]; pg.on('pageerror',e=>errs.push(String(e)));
  await pg.route('**/*',r=>r.request().url().startsWith('file://')?r.continue():r.abort());
  await pg.goto('file://'+tmp); await pg.waitForTimeout(2500);
  await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  const T=c=>pg.evaluate(c2=>window.__T(c2),c);
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; saveAll=function(){ window.__saved=(window.__saved||0)+1; };
    window.altRow={spec:'VP342R-5DZ1-01A-F',name:'3포트 솔레노이드밸브',e:52000,buy:30000,sell:36000};
    quoteVendors=[{id:'vA',name:'테스트상사'}]; _qCurId='vA'; _qRows=[altRow]; _qPriceIdx={}; _qAllIdx={}; _qAllIdx[_qNorm(altRow.spec)]=[{vid:'vA',vname:'테스트상사',r:altRow}]; _qAllReady=true; _qIsSmc=function(){return false;};
    _qCart=[{vid:'vA',vname:'테스트상사',spec:'25A-PF2M721-02-DW-M',name:'디지털 플로우 스위치',qty:2,sell:150000},{vid:'vA',vname:'테스트상사',spec:'VP342R-5DZ1-01B',name:'솔밸브',qty:4,e:50000,buy:29000,sell:35000}];
    document.querySelectorAll('.page-section').forEach(function(p){p.classList.remove('active')}); document.getElementById('pageEstimate').classList.add('active'); renderQCart(); 'ok'`);
  const t0=await pg.evaluate(()=>document.querySelector('#qCart input[data-mf="spec"]').getAttribute('title')||'');
  ok(/25A = 이차전지/.test(t0) && /DW \(설명 미등록\)/.test(t0) && /우클릭/.test(t0), '마우스 올리면 옵션 요약(25A 기본 설명 · 미등록 표시): '+t0.split('\n').join(' | '));
  // 우클릭 메뉴
  await pg.evaluate(()=>{ const el=document.querySelector('#qCart input[data-mf="spec"]'); el.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,clientX:300,clientY:300})); });
  ok(await pg.evaluate(()=>document.getElementById('qSpecMenu').style.display==='block' && /옵션 보기/.test(document.getElementById('qSpecMenu').innerText) && /변경 제안 넣기/.test(document.getElementById('qSpecMenu').innerText)), '우클릭 메뉴: 옵션 보기 · 변경 제안 넣기');
  await pg.evaluate(()=>{ [...document.querySelectorAll('#qSpecMenu .qsm-it')].find(e=>/옵션 보기/.test(e.innerText)).click(); });
  ok(await pg.evaluate(()=>document.getElementById('qOptOverlay').style.display==='flex' && document.querySelectorAll('#qOptOverlay .qov-in').length===5), '옵션 보기: 25A(앞 사양) · PF2M721(본체) · 02 · DW · M(옵션) 5칸');
  const codes=await pg.evaluate(()=>[...document.querySelectorAll('#qOptOverlay .qov-in')].map(i=>i.dataset.kind+':'+i.dataset.code).join(','));
  console.log('    칸:', codes);
  await pg.evaluate(()=>{ const ins=[...document.querySelectorAll('#qOptOverlay .qov-in')]; const f=(code,v)=>{ const x=ins.find(i=>i.dataset.code===code); if(x) x.value=v; }; f('PF2M721','디지털 플로우 스위치'); f('DW','테스트 설명 DW'); });
  await T(`qOptSave(); 'ok'`);
  ok(await T(`optDict.series['PF2M7']||optDict.series['PF2M']||Object.keys(optDict.series).join()`)!=='' && /테스트 설명 DW/.test(await T(`JSON.stringify(optDict.tok)`)), '설명 저장 → 팀 공용 사전');
  await T(`_qCart.push({vid:'vA',vname:'테스트상사',spec:'PF2M721-01-DW',qty:1}); renderQCart(); 'ok'`);
  const t2=await pg.evaluate(()=>[...document.querySelectorAll('#qCart input[data-mf="spec"]')][2].getAttribute('title'));
  ok(/DW = 테스트 설명 DW/.test(t2) && /시리즈: /.test(t2), '같은 시리즈 다른 품번에도 설명 표시');
  // 변경 제안
  await T(`_qCart.pop(); qAltOpen(1); 'ok'`);
  await pg.evaluate(()=>{ document.getElementById('qaltTo').value='VP342R-5DZ1-01A-F OR VP342R-5DZ1-01'; document.getElementById('qaltEta').value='2~3주'; });
  await T(`qAltApply(); 'ok'`);
  ok(await T(`_qCart.length===3 && _qCart[2].spec==='VP342R-5DZ1-01A-F' && _qCart[2].altOf==='VP342R-5DZ1-01B'`), '원래 줄 바로 아래 제안 줄 추가');
  ok(await T(`_qCart[1].altOff===true && _qCart[1].disc==='재고 없음 · 아래 변경 제안'`), '원래 줄: 재고 없음 표시 · 금액 제외(단종 칸 사용)');
  ok(await T(`_qCart[2].buy===30000 && _qCart[2].sell===36000 && _qCart[2].qty===4`), '제안 품번 단가는 원장에서(이 거래처 이력) · 수량 이어받음');
  ok(await T(`_qCart[2].eta`)==='변경 제안 · 재고 없음 · 일본 재고 · 납기 2~3주 · 대안: VP342R-5DZ1-01', '예상납기 칸에 "변경 제안 · 사유 · 납기 · 대안" (PDF·엑셀·HTML 에 그대로 나감)');
  ok(await T(`_qAltOf('VP342R-5DZ1-01B').length===1`), '변경 제안 이력 저장');
  ok(await pg.evaluate(()=>[...document.querySelectorAll('#qCart input[data-mf="spec"]')][2].getAttribute('data-alt')==='1' && [...document.querySelectorAll('#qCart input[data-mf="spec"]')][1].getAttribute('data-altoff')==='1'), '견적 화면 표시(제안 줄 주황 · 원래 줄 취소선)');
  // 원장 보호
  await T(`_fbDbUrl='x'; _isViewer=function(){return false;}; window.__blob=null; _qBlobPut=async function(id,rows){ window.__blob=JSON.parse(JSON.stringify(rows)); }; _qRows=[{spec:'VP342R-5DZ1-01B',e:50000,buy:29000,sell:35000,eta:'1주'},altRow]; 'ok'`);
  await T(`_qFlushLedgerFromCart()`); await pg.waitForTimeout(100);
  const led=await T(`JSON.stringify(window.__blob)`); console.log('    원장:', led);
  ok(led && !/재고 없음/.test(led) && !/변경 제안/.test(led), '원장에는 재고 없음·변경 제안 문구가 남지 않음 (단가만 갱신)');
  // 취소
  await T(`qAltCancel(1); 'ok'`);
  ok(await T(`_qCart.length===2 && !_qCart[1].altOff && !_qCart[1].disc`), '변경 제안 취소 → 원래대로');
  // 이력 툴팁 + 다시 쓰기
  const t3=await pg.evaluate(()=>[...document.querySelectorAll('#qCart input[data-mf="spec"]')][1].getAttribute('title'));
  ok(/이전 변경 제안: → VP342R-5DZ1-01A-F OR VP342R-5DZ1-01/.test(t3) && /재고 다시 확인/.test(t3), '다음에 같은 품번 → 이전 제안 이력 툴팁');
  await T(`qAltOpen(1,true); 'ok'`);
  ok(await pg.evaluate(()=>document.getElementById('qaltTo').value)==='VP342R-5DZ1-01A-F OR VP342R-5DZ1-01', '[이전 제안 다시 쓰기] → 제안 품번 미리 채움');
  // 여러 줄 등록
  await T(`qAltListOpen(); 'ok'`);
  await pg.evaluate(()=>{ document.getElementById('qaltBulk').value='25A-IRV20-C08GN   → 25A-IRV20-C10GN 변경 제안\nSRH3011-02 → SRH3011-02-R OR SRH4011-02  변경 제안\n25A-ISE20A-V-M5-JB  →  25A-ISE20A-V-M5-JB 변경 제안\n이상한 줄'; });
  await T(`qAltBulkSave(); 'ok'`);
  const msg=await pg.evaluate(()=>document.getElementById('qaltBulkMsg').innerText);
  ok(/2건 등록/.test(msg) && /같아 건너뜀: 25A-ISE20A-V-M5-JB/.test(msg) && /형식 확인: 이상한 줄/.test(msg), '여러 줄 등록: '+msg);
  ok(await T(`_qAltOf('SRH3011-02')[0].alt`)==='SRH3011-02-R OR SRH4011-02', 'OR 여러 대안 저장');
  const re=errs.filter(e=>!/net::|Failed to fetch|firebase|XLSX|cdnjs/.test(e)); ok(re.length===0,'페이지 오류 없음'+(re.length?' — '+re[0]:''));
  console.log(`\n결과: ${pass} 통과 / ${fail} 실패`); await br.close(); try{fs.unlinkSync(tmp);}catch(e){} process.exit(fail?1:0);
})();
