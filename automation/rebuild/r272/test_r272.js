// r272 테스트 — 휴대폰(iPhone 13) 견적·일정·업체 화면이 옆으로 넓어지지 않고, 견적은 카드로 편집
const { chromium, devices } = require('playwright'); const fs=require('fs'), path=require('path');
const file=path.resolve(process.argv[2]||'/home/claude/d272/index.html');
let pass=0, fail=0; function ok(c,m){ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} }
(async()=>{
  const src=fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){','window.__T=function(c){return eval(c);}; function _vacUnlimited(id){');
  const tmp=path.join(path.dirname(file),'_h_r272.html'); fs.writeFileSync(tmp,src);
  const br=await chromium.launch(); const errs=[];
  const ctx=await br.newContext({...devices['iPhone 13']}); const pg=await ctx.newPage(); pg.on('pageerror',e=>errs.push(String(e)));
  await pg.route('**/*', r=>r.request().url().startsWith('file://')?r.continue():r.abort());
  await pg.goto('file://'+tmp); await pg.waitForTimeout(2500); await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  const T=c=>pg.evaluate(c2=>window.__T(c2),c); const W=()=>pg.evaluate(()=>document.documentElement.scrollWidth);
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울'}]; myMemberId='m1'; switchPage('estimate'); 'ok'`); await pg.waitForTimeout(300);
  ok(await W()<=392, '견적: 거래처 고르기 전 화면 폭 = 휴대폰 폭 (전엔 3,486px)');
  await T(`quoteVendors=[{id:'v1',name:'대국산기'}]; _qCurId='v1'; _qCart=[{vid:'v1',vname:'대국산기',spec:'SY5120-5LZD-01',name:'솔레노이드 밸브',qty:2,e:38810,buy:25230,sell:30000},{vid:'v1',vname:'대국산기',spec:'KQ2H06-01AS',qty:10,e:920,buy:700,sell:850,small:true}]; _qNego=1000; renderQCart(); 'ok'`); await pg.waitForTimeout(300);
  ok(await W()<=392, '견적: 품목 있어도 화면 폭 유지');
  ok(await pg.evaluate(()=>document.querySelectorAll('.qmc:not(.qmc-add)').length)===2 && await pg.evaluate(()=>{ const t=document.querySelector('#qCart table'); return !t || t.getBoundingClientRect().height===0; }), '표 대신 카드 2개');
  const t=await pg.evaluate(()=>document.getElementById('qMobCards').innerText.replace(/\s+/g,' '));
  ok(/SY5120-5LZD-01/.test(t) && /60,000/.test(t) && /DC 35%/.test(t) && /소물/.test(t), '카드: 규격·금액·DC·소물 표시');
  ok(/68,500원|67,500원/.test(t), '합계 = 60,000 + 8,500 − NEGO 1,000 = 67,500: '+(t.match(/[\d,]+원/g)||[]).join(','));
  await pg.click('.qmc[data-i="1"] button[aria-label="수량 더하기"]'); await pg.waitForTimeout(150);
  ok(await T('_qCart[1].qty')===11, '수량 + 버튼');
  await pg.fill('.qmc[data-i="0"] .qmc-r input[inputmode="numeric"]:not([type])','32000'); await pg.dispatchEvent('.qmc[data-i="0"] .qmc-r input[inputmode="numeric"]:not([type])','change'); await pg.waitForTimeout(150);
  ok(await T('_qCart[0].sell')==32000, '판매가 바꾸기');
  ok(await pg.evaluate(()=>!!document.querySelector('.qmc-add input[data-mf="spec"]')), '카드 아래 [품목 추가] 규격 입력 (자동완성 그대로)');
  await pg.click('.qmc[data-i="1"] .qmc-del'); await pg.waitForTimeout(150);
  ok(await pg.evaluate(()=>document.querySelectorAll('.qmc:not(.qmc-add)').length)===1, '× 로 품목 빼기');
  const lab=await pg.evaluate(()=>{ const tb=document.querySelector('#qSubQuote > .q-toolbar'); const s=[...tb.children].filter(c=>c.tagName==='SPAN'&&/담당자/.test(c.textContent))[0]; const i=document.getElementById('qManager'); return Math.abs(s.getBoundingClientRect().top-i.getBoundingClientRect().top)<20; });
  ok(lab, '툴바: 이름표와 입력칸이 같은 줄');
  // 일정
  const d=new Date().toISOString().slice(0,10);
  await T(`_qLeaveGuard=function(){ return false; }; 'ok'`);
  await T(`memoLines=[{id:'a',owner:'김재성',text:'미팅 대국산기 14시 견적 협의 및 신규 라인 SMC 실린더 교체 건',parent:'',kind:'meeting',vendor:'대국산기',to:'',name:'',phone:'',when:{date:'',time:''},date:'${d}',createdAt:Date.now(),done:false,feedback:[],card:'',linked:{}}]; switchPage('memo'); try{ renderMemoPage(true); }catch(e){} 'ok'`); await pg.waitForTimeout(700);
  ok(await pg.evaluate(()=>{ const t=document.querySelector('.mm-row .mm-txt'); return t && t.getBoundingClientRect().width>220 && t.getBoundingClientRect().height<90; }), '일정: 메모 글이 한 줄 전체 폭 (전엔 두 글자씩 세로로)');
  await T(`switchPage('clients'); 'ok'`); await pg.waitForTimeout(400);
  ok(await W()<=395, '업체 목록: 화면 폭 유지 (전엔 978px)');
  // 데스크톱은 그대로
  const pd=await br.newPage({viewport:{width:1400,height:900}}); await pd.route('**/*', r=>r.request().url().startsWith('file://')?r.continue():r.abort());
  await pd.goto('file://'+tmp); await pd.waitForTimeout(2500); await pd.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  await pd.evaluate(()=>window.__T(`switchPage('estimate'); quoteVendors=[{id:'v1',name:'대국산기'}]; _qCurId='v1'; _qCart=[{vid:'v1',vname:'대국산기',spec:'A',qty:1,sell:1}]; renderQCart(); 'ok'`)); await pd.waitForTimeout(300);
  ok(await pd.evaluate(()=>!document.getElementById('qMobCards') && getComputedStyle(document.querySelector('#qCart table')).display==='table'), 'PC 화면은 기존 표 그대로');
  const re=errs.filter(e=>!/net::|Failed to fetch|firebase|XLSX|cdnjs/.test(e)); ok(re.length===0,'페이지 오류 없음'+(re.length?' — '+re[0]:''));
  console.log(`\n결과: ${pass} 통과 / ${fail} 실패`); await br.close(); try{fs.unlinkSync(tmp);}catch(e){} process.exit(fail?1:0);
})();
