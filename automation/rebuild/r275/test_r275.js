// r275 테스트 — 회의록: 한 칸에 막 적고 저장 → 이름 눌러 담당 지정
const { chromium } = require('playwright'); const fs=require('fs'), path=require('path');
const file=path.resolve(process.argv[2]||'/home/claude/d275/index.html');
let pass=0, fail=0; function ok(c,m){ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} }
(async()=>{
  const src=fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){','window.__T=function(c){return eval(c);}; function _vacUnlimited(id){');
  const tmp=path.join(path.dirname(file),'_h_r275.html'); fs.writeFileSync(tmp,src);
  const br=await chromium.launch(); const errs=[];
  const pg=await br.newPage({viewport:{width:1300,height:900}}); pg.on('pageerror',e=>errs.push(String(e)));
  await pg.route('**/*', r=>r.request().url().startsWith('file://')?r.continue():r.abort());
  await pg.goto('file://'+tmp); await pg.waitForTimeout(2500); await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  const T=c=>pg.evaluate(c2=>window.__T(c2),c);
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울'},{id:'m2',name:'함현식',group:'서울'},{id:'m3',name:'김은석',group:'화성'}]; myMemberId='m1'; _qLeaveGuard=function(){return false;}; meetings=[]; memoLines=[]; switchPage('meeting'); mtNew(); 'ok'`); await pg.waitForTimeout(400);
  ok(await pg.evaluate(()=>[...document.querySelectorAll('#mtBody textarea')].filter(t=>!t.closest('details:not([open])')).length)===1 && await pg.evaluate(()=>!document.getElementById('mtRepIn')), '작성란은 하나 (업무 작성란 없음)');
  ok(await pg.evaluate(()=>{ const d=document.querySelector('#mtBody details.mt-more'); return d && !d.open; }), '목표는 접혀 있음');
  await pg.fill('#mtAgIn','신규 거래처 발굴 방문 영업\n- SMC 가격표 11월분 갱신\n함현식 이노로보틱스 칠러 대체품 협의\n함현식이 말한 재고 정리 건\n견적: 대국산기 회신');
  await pg.press('#mtAgIn','Control+Enter'); await pg.waitForTimeout(300);
  const mid=await T('_mtOpen');
  ok(await T('_mtFind(_mtOpen).agenda.length')===4 && await T('_mtFind(_mtOpen).agenda[1].text')==='SMC 가격표 11월분 갱신', '이름 없는 4줄 → 회의 내용 (앞의 - 는 뗌)');
  ok(await T(`_mtFind(_mtOpen).reports.find(function(r){return r.name==='함현식';}).items.length`)===1 && await T(`memoLines.length`)===1 && await T('memoLines[0].owner')==='함현식', '"함현식 ○○" 줄은 바로 함현식 담당 + 일정 1줄 ("함현식이…" 는 아님)');
  ok(await T('_mtFind(_mtOpen).agenda[3].text')==='견적: 대국산기 회신', '적은 그대로 저장 (제목 분리 안 함)');
  ok(await pg.evaluate(()=>document.querySelectorAll('#mtBody .mt-sec .mt-it .mt-who button').length)>=8, '줄마다 참석자 이름 버튼');
  await pg.click('#mtBody .mt-it:has-text("신규 거래처 발굴") .mt-who button:has-text("김재성")'); await pg.waitForTimeout(300);
  ok(await T('_mtFind(_mtOpen).agenda.length')===3 && await T(`_mtFind(_mtOpen).reports.find(function(r){return r.name==='김재성';}).items[0].text`)==='신규 거래처 발굴 방문 영업', '이름 누르면 그 사람 담당으로 이동');
  ok(await T(`memoLines.filter(function(l){return l.owner==='김재성';}).length`)===1, '담당자 일정에 1줄');
  ok(await T('Object.keys(_mtFind(_mtOpen).del||{}).length')===1, '옮긴 줄은 묘비 기록(동기화 때 되살아나지 않음)');
  // 다른 사람(참석자 아님) → select
  await pg.selectOption('#mtBody .mt-it:has-text("SMC 가격표") .mt-who select','김은석'); await pg.waitForTimeout(300);
  ok(await T(`_mtFind(_mtOpen).reports.find(function(r){return r.name==='김은석';}).items.length`)===1 && await T(`_mtFind(_mtOpen).attendees.indexOf('김은석')>=0`), '참석자 아닌 사람도 선택 → 담당 + 참석자에 추가');
  // 담당 바꾸기: 김재성 → 함현식, 일정 줄이 넘어간다
  await pg.selectOption('#mtBody .mt-rep:has(.nm:text-is("김재성")) .mt-it .mt-who select','함현식'); await pg.waitForTimeout(300);
  ok(await T(`_mtFind(_mtOpen).reports.find(function(r){return r.name==='함현식';}).items.length`)===2 && await T(`memoLines.filter(function(l){return l.owner==='김재성';}).length`)===0 && await T(`memoLines.filter(function(l){return l.owner==='함현식';}).length`)===2 && await T('memoLines.length')===3, '담당 바꾸기 → 일정 줄도 새 담당자에게');
  ok(await T(`(function(){ var it=_mtFind(_mtOpen).reports.find(function(r){return r.name==='함현식';}).items[1]; var l=memoLines.find(function(x){return x.id===it.memoId;}); return !!l && l.mtRef.iid===it.id; })()`), '일정 줄 ↔ 회의록 항목 연결 유지');
  // 담당 없음
  await pg.selectOption('#mtBody .mt-rep:has(.nm:text-is("김은석")) .mt-it .mt-who select',''); await pg.waitForTimeout(300);
  ok(await T('_mtFind(_mtOpen).agenda.length')===3 && await T(`memoLines.filter(function(l){return l.owner==='김은석';}).length`)===0, '담당 없음 → 회의 내용으로 돌아가고 일정 줄 제거');
  // 완료 체크·삭제 기존대로
  const iid=await T('_mtFind(_mtOpen).agenda[0].id'); await T(`mtToggle(_mtOpen,'${iid}'); 'ok'`); ok(await T('_mtFind(_mtOpen).agenda[0].done')===true, '완료 체크 그대로 동작');
  // 인쇄본·확정본에는 버튼 없음
  ok(!/mt-who/.test(await T('_mtDocHtml(_mtFind(_mtOpen), true)')) && !/3\. 담당자별 목표/.test(await T('_mtDocHtml(_mtFind(_mtOpen), true)')), '인쇄본: 담당 버튼 없음 · 빈 목표 구역 생략');
  await T(`_mtFind(_mtOpen).status='final'; renderMeetingPage(true); 'ok'`); await pg.waitForTimeout(200);
  ok(await pg.evaluate(()=>document.querySelectorAll('#mtBody .mt-who').length)===0 && await pg.evaluate(()=>!document.getElementById('mtAgIn')), '확정본: 작성란·담당 버튼 없음');
  ok(errs.length===0, '오류 없음 '+errs.slice(0,2).join(' | '));
  console.log(`\n${pass} passed, ${fail} failed`); await br.close(); process.exit(fail?1:0);
})();
