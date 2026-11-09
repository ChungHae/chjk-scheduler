// r261 테스트 — 규격 한 품번 붙여넣기 자동 채움 · 다운로드/메일 뒤 자동 비우기 + 다시 열기
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs=require('fs'), path=require('path');
const file=path.resolve(process.argv[2]||'d261/test/index.html');
let pass=0, fail=0; function ok(c,m){ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} }
(async()=>{
  const src=fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){','window._xlsxStyleReady=true; window.__T=function(c){return eval(c);}; function _vacUnlimited(id){');
  const tmp=path.join(path.dirname(file),'_h_r261.html'); fs.writeFileSync(tmp,src);
  const br=await chromium.launch(); const pg=await br.newPage({viewport:{width:1400,height:900}}); const errs=[]; pg.on('pageerror',e=>errs.push(String(e)));
  await pg.route('**/*',r=>r.request().url().startsWith('file://')?r.continue():r.abort());
  await pg.goto('file://'+tmp); await pg.waitForTimeout(2500);
  await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  const T=c=>pg.evaluate(c2=>window.__T(c2),c);
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; saveAll=function(){};
    window.mine={spec:'AN30-03',name:'소음기',e:3420,buy:2050,sell:2600};
    window.mine2={spec:'AN30-03-X',name:'소음기X',e:5000,buy:3000,sell:3500};
    quoteVendors=[{id:'vA',name:'테스트상사'}]; _qCurId='vA'; _qRows=[mine,mine2]; _qPriceIdx={}; _qAllIdx={}; _qAllIdx[_qNorm(mine.spec)]=[{vid:'vA',vname:'테스트상사',r:mine}]; _qAllIdx[_qNorm(mine2.spec)]=[{vid:'vA',vname:'테스트상사',r:mine2}]; _qAllReady=true;
    _qIsSmc=function(){return false;};
    _qCart=[{vid:'vA',vname:'테스트상사',spec:'',name:'',qty:1,manual:true}];
    document.querySelectorAll('.page-section').forEach(function(p){p.classList.remove('active')}); var qp=document.getElementById('pageEstimate'); if(qp) qp.classList.add('active'); renderQCart(); 'ok'`);
  const spec=await pg.$('#qCart input[data-mf="spec"]');
  ok(!!spec, '규격 칸 있음');
  await spec.focus(); await spec.evaluate(el=>el.select());
  await pg.evaluate(()=>{ const el=document.querySelector('#qCart input[data-mf="spec"]'); el.focus(); window.__ae=(document.activeElement===el); const dt=new DataTransfer(); dt.setData('text/plain','AN30-03'); el.dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true})); });
  await pg.waitForTimeout(300);
  ok(await T(`_qCart[0].spec==='AN30-03' && _qCart[0].buy===2050 && _qCart[0].sell===2600 && _qCart[0].name==='소음기'`), '같은 규격 붙여넣기 → 클릭 없이 가격까지 채움 (AN30-03-X 와 헷갈리지 않음)');
  ok(await pg.evaluate(()=>{ const b=document.getElementById('qcsBox'); return !b || b.style.display==='none'; }), '목록 창 닫힘');
  // 없는 규격
  await T(`_qCart.push({vid:'vA',vname:'테스트상사',spec:'',qty:1,manual:true}); renderQCart(); 'ok'`);
  await pg.evaluate(()=>{ const el=[...document.querySelectorAll('#qCart input[data-mf="spec"]')][1]; el.focus(); el.select(); const dt=new DataTransfer(); dt.setData('text/plain','ZZZ-999'); el.dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true})); });
  await pg.waitForTimeout(200);
  ok(await T(`_qCart[1].spec==='ZZZ-999' && (_qCart[1].buy==null)`), '없는 규격은 입력한 그대로(가격 없음)');
  // 다운로드 뒤 비우기
  await T(`quoteSaved=[{id:'Q1',title:'테스트상사-20261109-01'}]; _qLoadedId='Q1'; _qQuoteNo='테스트상사-20261109-01'; window.__loaded=null; qLoadSaved=function(id){ window.__loaded=id; }; _qAfterOut('엑셀 다운로드'); 'ok'`);
  ok(await T(`_qCart.length===0 || !_qCartHasContent()`), '저장된 견적 → 다운로드 뒤 목록 비움');
  ok(await pg.evaluate(()=>document.getElementById('qOutToast').style.display==='flex' && /엑셀 다운로드 완료/.test(document.getElementById('qOutToast').innerText)), '안내 + [다시 열기]');
  await pg.evaluate(()=>{ document.querySelector('#qOutToast button').click(); });
  ok(await T(`window.__loaded`)==='Q1', '[다시 열기] → 방금 저장한 견적 불러오기');
  await T(`_qCart=[{vid:'vA',vname:'테스트상사',spec:'AN30-03',sell:2600,qty:1}]; _qLoadedId='Q9'; window.__info=[]; showInfoModal=function(t,m){ window.__info.push(t+'|'+m); }; _qAfterOut('엑셀 다운로드'); 'ok'`);
  ok(await T(`_qCart.length===1`) && /저장되지 않아/.test(await T(`window.__info.join()`)), '저장 안 된 견적은 비우지 않음');
  const src2=fs.readFileSync(file,'utf8');
  ok(/_qAfterOut\('엑셀 다운로드'\)/.test(src2) && /_qAfterOut\('HTML 다운로드'\)/.test(src2) && /_qAfterOut\('히트판 엑셀'\)/.test(src2) && /_qAfterOut\('메일 발송'\)/.test(src2), '엑셀·HTML·히트판·메일 경로 연결 (PDF 는 기존 r186 비우기)');
  const re=errs.filter(e=>!/net::|Failed to fetch|firebase|XLSX|cdnjs/.test(e)); ok(re.length===0,'페이지 오류 없음'+(re.length?' — '+re[0]:''));
  console.log(`\n결과: ${pass} 통과 / ${fail} 실패`); await br.close(); try{fs.unlinkSync(tmp);}catch(e){} process.exit(fail?1:0);
})();
