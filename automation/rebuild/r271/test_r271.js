// r271 테스트 — 최근 작업한 견적
const { chromium } = require('playwright'); const fs=require('fs'), path=require('path');
const file=path.resolve(process.argv[2]||'/home/claude/d271b/index.html');
let pass=0, fail=0; function ok(c,m){ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} }
(async()=>{
  const src=fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){','window.__T=function(c){return eval(c);}; function _vacUnlimited(id){');
  const tmp=path.join(path.dirname(file),'_h_r271.html'); fs.writeFileSync(tmp,src);
  const br=await chromium.launch(); const pg=await br.newPage({viewport:{width:1400,height:900}}); const errs=[]; pg.on('pageerror',e=>errs.push(String(e)));
  await pg.route('**/*', r=>r.request().url().startsWith('file://')?r.continue():r.abort());
  await pg.goto('file://'+tmp); await pg.waitForTimeout(2500); await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  const T=c=>pg.evaluate(c2=>window.__T(c2),c);
  const H=3600e3, now=Date.now();
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; try{localStorage.removeItem('q_load_sort')}catch(e){}
    window.__loaded=null; qLoadSaved=function(id){ window.__loaded=id; };
    quoteSaved=[
      {id:'a',title:'대국산기-20261117-01',vname:'대국산기',count:3,total:1000,savedBy:'김재성',savedAt:${now}-5*${H}},
      {id:'b',title:'우진전자-20261110-02',vname:'우진전자',count:2,total:2000,savedBy:'김재성',savedAt:${now}-200*${H},upd:${now}-0.2*${H},note:'재견적'},
      {id:'c',title:'솔브레인-20261116-01',vname:'솔브레인',count:1,total:300,savedBy:'이영희',savedAt:${now}-1*${H}},
      {id:'d',title:'TEXON-20261112-01',vname:'TEXON',count:4,total:500,savedBy:'김재성',savedAt:${now}-80*${H}}
    ]; switchPage('estimate'); 'ok'`);
  await pg.waitForTimeout(300);
  ok(await pg.evaluate(()=>!!document.getElementById('qRecentBtn')), '견적 툴바에 [최근 작업] 버튼');
  await pg.click('#qRecentBtn'); await pg.waitForTimeout(200);
  let t=await pg.evaluate(()=>document.getElementById('qRecentPop').innerText);
  const order=await pg.evaluate(()=>[...document.querySelectorAll('#qRecentPop [onclick^="qRecentLoad"]')].map(e=>e.getAttribute('onclick').match(/'(\w)'/)[1]).join(''));
  ok(order==='bad', '내 견적만 · 최근 작업순 (어제 다시 고친 옛 견적이 맨 위): '+order);
  ok(/12분 전|11분 전|13분 전/.test(t) && /재견적/.test(t), '언제 작업했는지 · 메모 표시');
  await T(`qRecentToggle(true)`); const o2=await pg.evaluate(()=>[...document.querySelectorAll('#qRecentPop [onclick^="qRecentLoad"]')].map(e=>e.getAttribute('onclick').match(/'(\w)'/)[1]).join(''));
  ok(o2==='bcad', '[전체] → 다른 직원 견적 포함: '+o2);
  await pg.evaluate(()=>document.querySelector('#qRecentPop [onclick^="qRecentLoad"]').click()); await pg.waitForTimeout(100);
  ok(await T(`window.__loaded`)==='b' && await pg.evaluate(()=>document.getElementById('qRecentPop').style.display)==='none', '누르면 바로 불러오고 닫힘');
  await pg.click('#qRecentBtn'); await pg.mouse.click(1300,850); await pg.waitForTimeout(100);
  ok(await pg.evaluate(()=>document.getElementById('qRecentPop').style.display)==='none', '바깥 누르면 닫힘');
  // 불러오기 창
  await T(`_qCurId=''; qOpenLoad(); qLoadResetFilters()`); await pg.waitForTimeout(200);
  const lo=await pg.evaluate(()=>[...document.querySelectorAll('#qLoadList button.btn-primary')].map(b=>b.getAttribute('onclick').match(/'(\w)'/)[1]).join(''));
  ok(lo==='bcad', '불러오기 기본 = 최근 작업순: '+lo);
  ok(await pg.evaluate(()=>document.getElementById('qLoadSort').value)==='work' && /최근 작업/.test(await pg.evaluate(()=>document.getElementById('qLoadList').innerText)), '정렬 선택칸 + "최근 작업 …" 표시');
  await T(`qLoadSortSet('date')`); const ld=await pg.evaluate(()=>[...document.querySelectorAll('#qLoadList button.btn-primary')].map(b=>b.getAttribute('onclick').match(/'(\w)'/)[1]).join(''));
  ok(ld==='acdb', '견적일순으로 바꾸면 견적번호 날짜순: '+ld);
  ok(await T(`localStorage.getItem('q_load_sort')`)==='date', '정렬 선택 기억');
  const re=errs.filter(e=>!/net::|Failed to fetch|firebase|XLSX|cdnjs/.test(e)); ok(re.length===0,'페이지 오류 없음'+(re.length?' — '+re[0]:''));
  console.log(`\n결과: ${pass} 통과 / ${fail} 실패`); await br.close(); try{fs.unlinkSync(tmp);}catch(e){} process.exit(fail?1:0);
})();
