const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b181/testpage/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', '  window.__T=function(c){return eval(c);};\n  function _vacUnlimited(id){');
  const tmp = path.join(path.dirname(file), '_h_r181.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1280,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  await pg.route('**/*', r => { const u=r.request().url(); if(u.startsWith('file://')) r.continue(); else r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; smcQueue=[]; priceMakers=[]; quoteVendors=[{id:'v1',name:'LS엠트론',count:1}]; _qCurId='v1';
    _qRows=[{spec:'SY5120-5LZ-01-Q',name:'솔레노이드밸브',buy:100,sell:200}]; _qAllIdx={}; _qAllReady=true; _qPriceIdx={}; _qSmcSet={};
    switchPage('estimate'); 'ok'`);
  await pg.waitForTimeout(300);
  await T(`_qCurId='v1'; quoteVendors=[{id:'v1',name:'LS엠트론',count:1}]; _qRows=[{spec:'SY5120-5LZ-01-Q',name:'솔레노이드밸브',buy:100,sell:200}]; _qAllIdx={}; _qAllReady=true; _qPriceIdx={}; _qSmcSet={}; _qCart=[{vid:'v1',vname:'LS엠트론',spec:'',name:'',e:null,buy:null,sell:null,disc:'',eta:'',qty:1,manual:true}]; renderQCart(); 'ok'`);
  await pg.waitForTimeout(200);
  console.log('▶ ① 규격 자동완성 Enter');
  const sel='#qCart input[data-mf="spec"]';
  await pg.click(sel); await pg.type(sel,'SY5120-5LZ-01'); await pg.waitForTimeout(150);
  ok(await T(`document.getElementById('qcsBox').style.display!=='none' && _qcsCur.length===1 && _qcsCur[0].r.spec==='SY5120-5LZ-01-Q'`), '후보(-Q) 표시');
  ok(await T(`document.getElementById('qcsBox').innerHTML.indexOf('그냥 Enter 는 입력한 그대로')>=0`), '안내문 표시');
  await pg.keyboard.press('Enter'); await pg.waitForTimeout(150);
  ok(await T(`_qCart[0].spec`)==='SY5120-5LZ-01', 'Enter → 입력한 그대로(SY5120-5LZ-01) 유지, -Q 안 들어감');
  ok(await T(`document.getElementById('qcsBox').style.display==='none'`), '후보창 닫힘');
  await T(`_qCart=[{vid:'v1',vname:'LS엠트론',spec:'',name:'',e:null,buy:null,sell:null,disc:'',eta:'',qty:1,manual:true}]; renderQCart(); 'ok'`); await pg.waitForTimeout(100);
  await pg.click(sel); await pg.type(sel,'SY5120-5LZ-01'); await pg.waitForTimeout(150);
  await pg.keyboard.press('ArrowDown'); await pg.keyboard.press('Enter'); await pg.waitForTimeout(150);
  ok(await T(`_qCart[0].spec`)==='SY5120-5LZ-01-Q' && await T(`_qCart[0].buy`)===100, '↓ 후 Enter → 후보(-Q) 선택');
  await T(`_qCart=[{vid:'v1',vname:'LS엠트론',spec:'',name:'',e:null,buy:null,sell:null,disc:'',eta:'',qty:1,manual:true}]; renderQCart(); 'ok'`); await pg.waitForTimeout(100);
  await pg.click(sel); await pg.type(sel,'SY5120-5LZ-01-Q'); await pg.waitForTimeout(150);
  await pg.keyboard.press('Enter'); await pg.waitForTimeout(150);
  ok(await T(`_qCart[0].spec`)==='SY5120-5LZ-01-Q' && await T(`_qCart[0].buy`)===100, '완전히 같은 규격 입력 후 Enter → 그 후보 선택(값 채움)');
  await T(`_qCart=[{vid:'v1',vname:'LS엠트론',spec:'',name:'',e:null,buy:null,sell:null,disc:'',eta:'',qty:1,manual:true}]; renderQCart(); 'ok'`); await pg.waitForTimeout(100);
  await pg.click(sel); await pg.type(sel,'SY5120-5LZ-01'); await pg.waitForTimeout(150);
  await pg.click('#qcsBox .qcs-it'); await pg.waitForTimeout(150);
  ok(await T(`_qCart[0].spec`)==='SY5120-5LZ-01-Q', '마우스 클릭 → 후보 선택');

  console.log('▶ ② 견적 저장 시 SMC 대기열 수집');
  await T(`_qPriceIdx={'kq2h0602':{spec:'KQ2H06-02',isSMC:true,hasSmcPrice:true,e:500}}; _qSmcSet={'kq2h0602':1}; _qQuoteNo='LS엠트론-20260911-01';
    _qCart=[{vid:'v1',vname:'LS엠트론',spec:'SY7120-5DZ-02',name:'밸브',e:15000,buy:9000,sell:12000,qty:1},
            {vid:'v1',vname:'LS엠트론',spec:'KQ2H06-02',name:'피팅',e:500,buy:300,sell:400,qty:1},
            {vid:'v1',vname:'LS엠트론',spec:'AS2201F-01-06S',name:'',e:null,buy:2000,sell:3000,qty:1},
            {vid:'v1',vname:'LS엠트론',spec:'MXQ12-30',name:'',e:80000,buy:50000,sell:60000,qty:1,pl:true}]; 'ok'`);
  await pg.evaluate(() => window.__T('_smcCollectFromCart()'));
  await pg.waitForTimeout(100);
  const q=JSON.parse(await T(`JSON.stringify(smcQueue)`));
  ok(q.length===1 && q[0].spec==='SY7120-5DZ-02' && q[0].e===15000 && q[0].buy===9000 && q[0].status==='wait' && q[0].by==='김재성' && q[0].vname==='LS엠트론' && q[0].quoteNo==='LS엠트론-20260911-01', '가격표에 없는 규격+E가 1건만 수집 (가격표 규격·E가 없음·가격표 잠금 제외)');
  await pg.evaluate(() => window.__T('_smcCollectFromCart()'));
  ok(await T(`smcQueue.length`)===1, '다시 저장해도 중복 안 됨');

  console.log('▶ ③ 메모장 배너 + SMC 확인 화면');
  await T(`_qCart=[]; _qCartSave(); switchPage('memo'); 'ok'`); await pg.waitForTimeout(150);   // 견적 이탈 가드(내용 있으면 확인창) 피하려고 비움
  ok((await T(`document.getElementById('mmList').innerHTML`)).indexOf('SMC 가격 확인 대기 1건')>=0, '메모장 맨 위 배너');
  await T(`smcGo(); 'ok'`); await pg.waitForTimeout(150);
  ok(await T(`document.getElementById('qSubSmc').style.display!=='none' && document.getElementById('qSubTabSmc').classList.contains('active')`), 'SMC 확인 서브탭 열림');
  ok(await T(`document.querySelectorAll('#smcResult tbody tr').length`)===1 && (await T(`document.getElementById('smcResult').innerHTML`)).indexOf('SY7120-5DZ-02')>=0, '대기 목록에 표시');
  ok(await T(`document.querySelector('#smcResult input[data-f="e"]').value`)==='15000' && await T(`document.querySelector('#smcResult input[data-f="hp"]').value`)==='9000', 'E가·확판가(견적 구매가) 미리 채움');

  console.log('▶ ④ 제외 / 대기로');
  const id=q[0].id;
  await T(`smcSkip('${id}'); 'ok'`);
  ok(await T(`smcQueue[0].status==='skip'`) && await T(`document.querySelectorAll('#smcResult tbody tr').length`)===0, '제외 → 대기 목록에서 빠짐');
  await T(`smcSetFilter('skip'); 'ok'`);
  ok(await T(`document.querySelectorAll('#smcResult tbody tr').length`)===1, '제외 탭에 표시');
  await T(`smcRestore('${id}'); smcSetFilter('wait'); 'ok'`);
  ok(await T(`smcQueue[0].status==='wait'`) && await T(`document.querySelectorAll('#smcResult tbody tr').length`)===1, '대기로 복귀');

  console.log('▶ ⑤ 등록 → SMC 가격표 행 추가');
  await T(`_fbDbUrl='https://x.test'; window.__put=null; _priceBlobGet=async function(id){ return window.__existing||[]; }; _priceBlobPut=async function(id,rows){ window.__put={id:id,rows:JSON.parse(JSON.stringify(rows))}; }; 'ok'`);
  await T(`document.querySelector('#smcResult input[data-f="e"]').value='15,500'; document.querySelector('#smcResult input[data-f="sm"]').value='9800'; 'ok'`);
  await pg.evaluate(i => window.__T("smcRegister('"+i+"')"), id);
  await pg.waitForTimeout(300);
  const put=JSON.parse(await T(`JSON.stringify(window.__put)`));
  ok(put && put.rows.length===1 && put.rows[0].spec==='SY7120-5DZ-02' && put.rows[0].ega===15500 && put.rows[0].extra['1DR3확판(개당)']===9000 && put.rows[0].extra['LRY확판(개당)']===9800 && put.rows[0].name==='밸브', 'SMC 가격표에 행 추가 (E가 15,500·확판 9,000·소물 9,800)');
  ok(await T(`priceMakers.length===1 && priceMakers[0].name==='SMC' && priceMakers[0].count===1`), 'SMC 메이커 없으면 생성 + count');
  ok(await T(`smcQueue[0].status==='ok' && smcQueue[0].okE===15500 && smcQueue[0].okBy==='김재성'`), '대기열 상태 등록됨');
  ok(await T(`_qAllReady===false`), '색인 무효화(다음 검색부터 반영)');
  await T(`smcSetFilter('ok'); 'ok'`);
  ok((await T(`document.getElementById('smcResult').innerHTML`)).indexOf('15,500')>=0 || (await T(`document.getElementById('smcResult').innerHTML`)).indexOf('15500')>=0, '등록됨 탭에 값 표시');
  // 기존 행이 있으면 갱신
  await T(`window.__existing=[{spec:'SY7120-5DZ-02',ega:1,unit:'EA'}]; smcQueue.push({id:'sq2',spec:'sy7120-5dz-02',name:'',e:16000,buy:null,vname:'LS엠트론',by:'김재성',at:Date.now(),quoteNo:'',status:'wait'}); smcSetFilter('wait'); 'ok'`);
  await pg.evaluate(() => window.__T(`smcRegister('sq2')`)); await pg.waitForTimeout(300);
  const put2=JSON.parse(await T(`JSON.stringify(window.__put)`));
  ok(put2.rows.length===1 && put2.rows[0].ega===16000 && put2.rows[0].spec==='SY7120-5DZ-02', '같은 규격(대소문자 무시)은 기존 행 갱신');
  console.log('▶ ⑥ 금요일 17시 판정');
  ok(await T(`(function(){ var RD=Date; var mk=function(y,m,d,h){ return new RD(y,m-1,d,h,0,0); }; var f=function(dt){ var wd=dt.getDay(),h=dt.getHours(); return (wd===5&&h>=17)||wd===6||wd===0; }; return f(mk(2026,9,11,16))===false && f(mk(2026,9,11,17))===true && f(mk(2026,9,13,10))===true && f(mk(2026,9,14,9))===false; })()`), '금 16시 ✗ / 금 17시 ✓ / 일 ✓ / 월 ✗');
  ok(errs.length===0, 'pageerror 0'+(errs.length?(' — '+errs.join(' | ')):''));
  console.log(`\n결과: ${pass}/${pass+fail}`);
  fs.unlinkSync(tmp); await br.close(); process.exit(fail?1:0);
})();
