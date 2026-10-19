// r240 테스트 — 회의록 목표(담당자별) · 세부 항목 이수율 · 메모장 '내 목표' 카드 · 지난 회의 전부 표시 · 동시 작성 병합(goals)
//  사용:  node test_r240.js <r240 적용된 index.html>
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b240/test/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const STUB = `
  window._xlsxStyleReady=true;
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r240.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch();
  const DB = {};
  async function route(r){
    const req=r.request(); const u=req.url();
    if(u.startsWith('file://')) return r.continue();
    const m=u.match(/\/teamdata_[a-z]+(?:\/([^.?]+))?\.json/);
    if(m){ const key=m[1];
      if(req.method()==='PATCH'){ Object.assign(DB, JSON.parse(req.postData())); return r.fulfill({status:200, contentType:'application/json', body:'{}'}); }
      if(req.method()==='GET'){ const v=key?(key==='_updatedAt'?(DB._updatedAt||0):(DB[key]===undefined?null:DB[key])):DB; return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify(v)}); } }
    r.abort();
  }
  async function openClient(name, role){
    const ctx=await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1400,height:900} });
    const pg=await ctx.newPage(); const errs=[]; pg.on('pageerror', e=>errs.push(String(e)));
    await pg.route('**/*', route);
    await pg.goto('file://'+tmp); await pg.waitForTimeout(6000);
    await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
    const T=c=>pg.evaluate(c2=>window.__T(c2), c);
    await T(`
      _fbDbUrl='https://fb.test'; _fbReady=true; _fbLoadedOnce=true; _authUser={id:'${name}',name:'${name}',role:'${role||'user'}'};
      members=[{id:'m1',name:'김재성',group:'서울'},{id:'m2',name:'함현식',group:'서울'}];
      _fbFetch=async function(url,opts){ return fetch(url,opts); };
      _isViewer=function(){ return false; };
      memoLines=[]; personalSchedules=[];
      'ok'`);
    return { pg, T, errs, name };
  }
  const A=await openClient('김재성','admin');
  const past='2026-09-01', today=await A.T(`_mmToday()`);
  const M=[
    { id:'mtOld', date:past, time:'10:00', place:'서울', title:'9월 회의', author:'김재성', attendees:['김재성','함현식'], agenda:[{id:'ao1',title:'지난 안건',text:'x',done:false,at:1}], reports:[], updatedAt:1, createdAt:1 },
    { id:'mtNew', date:today, time:'10:00', place:'서울', title:'이번 회의', author:'김재성', attendees:['김재성','함현식'], agenda:[], reports:[], updatedAt:2, createdAt:2 }
  ];
  DB.sched_meetings=M; DB._updatedAt=3;
  await A.T(`meetings=${JSON.stringify(M)}; _mtDelMap={}; _mtDirty=false; _fbLastUpdatedAt=3; 'ok'`);

  console.log('▶ 1) 지난 회의 접기 없이 전부 최신순');
  await A.T(`switchPage('meeting'); _mtOpen=null; renderMeetingPage(true); 'ok'`); await A.pg.waitForTimeout(300);
  const rows=await A.T(`Array.prototype.map.call(document.querySelectorAll('#mtBody .mt-row .mt-t'), function(e){ return e.textContent.trim().split(' ')[0]; })`);
  ok(rows.length===2 && rows[0]==='이번' && rows[1]==='9월', '목록에 지난 회의 포함, 최신순 — '+JSON.stringify(rows));
  ok(await A.T(`!document.querySelector('#mtBody .mt-past-tg')`), '[지난 회의 N건 보기] 접기 링크 없음');
  ok(await A.T(`typeof _mmPastMeetingLine==='function' && (function(){ var l={mtRef:{mid:'mtOld',iid:'ao1'}}; var hidden=false; try{ var src=_mmVisible.toString(); hidden=src.indexOf('_mmPastMeetingLine(l)) return false')>=0; }catch(_e){} return !hidden; })()`), '일정(메모장)에서 지난 회의 안건 숨김 해제');

  console.log('▶ 2) 회의록에 "3. 담당자별 목표" — 저장·세부 항목·이수율');
  await A.T(`mtOpen('mtNew'); 'ok'`); await A.pg.waitForTimeout(300);
  ok(await A.T(`document.querySelector('#mtBody').innerText.indexOf('3. 담당자별 목표')>=0 && !!document.getElementById('mtGoalIn')`), '목표 칸 + 작성란');
  await A.T(`document.getElementById('mtGoalIn').value='김재성 SMC 가격표 10월분 갱신\\n함현식 신규 거래처 3곳 발굴\\n화성 대리점 방문'; mtSaveGoals('mtNew'); 'ok'`); await A.pg.waitForTimeout(300);
  const g=await A.T(`JSON.stringify(_mtFind('mtNew').goals.map(function(b){ return {n:b.name, t:b.items.map(function(i){ return i.title; })}; }))`);
  ok(g==='[{"n":"김재성","t":["SMC 가격표 10월분 갱신"]},{"n":"함현식","t":["신규 거래처 3곳 발굴","화성 대리점 방문"]}]', '이름 앞머리로 담당 배정, 이름 없는 줄은 바로 위 사람 — '+g);
  ok(await A.T(`document.querySelector('#mtBody').innerText.indexOf('세부 항목 없음')>=0`), '세부 항목 없으면 이수율 대신 안내');
  // 김재성(본인) 세부 항목 추가 2개, 1개 체크
  const gid=await A.T(`_mtFind('mtNew').goals[0].items[0].id`);
  await A.T(`var inp=document.querySelector('#mtBody .mt-goal[data-gid="${gid}"] .mt-goal-add input'); inp.value='SMC 에 10월 가격표 요청'; mtGoalSubAdd('mtNew','${gid}',inp); 'ok'`); await A.pg.waitForTimeout(200);
  await A.T(`var inp=document.querySelector('#mtBody .mt-goal[data-gid="${gid}"] .mt-goal-add input'); inp.value='사내전산 업로드'; mtGoalSubAdd('mtNew','${gid}',inp); 'ok'`); await A.pg.waitForTimeout(200);
  const sid=await A.T(`_mtFind('mtNew').goals[0].items[0].subs[0].id`);
  await A.T(`mtGoalSubToggle('mtNew','${gid}','${sid}',true); 'ok'`); await A.pg.waitForTimeout(200);
  ok(await A.T(`var p=_mtGoalProg(_mtFind('mtNew').goals[0].items[0]); p.d===1 && p.t===2 && p.pct===50`), '이수율 = 세부 항목 완료 비율 (1/2 = 50%)');
  ok(await A.T(`document.querySelector('#mtBody .mt-goal[data-gid="${gid}"] .mt-goal-pct').textContent.indexOf('50%')>=0 && document.querySelector('#mtBody .mt-goal-rep .nm small').textContent.indexOf('이수율 50%')>=0`), '회의록 화면에 50% · 담당자 칸에 이수율');
  await A.T(`mtGoalDetail('mtNew','${gid}','10/20 SMC 영업에 메일 보냄. 회신 대기'); 'ok'`); await A.pg.waitForTimeout(200);
  ok(await A.T(`_mtFind('mtNew').goals[0].items[0].detail.indexOf('회신 대기')>=0 && document.querySelector('#mtBody .mt-goal[data-gid="${gid}"] textarea.mt-goal-detail').value.indexOf('회신 대기')>=0`), '상세 내용 저장·표시');
  // 다른 사람(함현식) 목표는 관리자라도 체크 가능, 일반 직원은 남의 것 불가 — 아래 B 에서 확인
  ok(await A.T(`!!document.querySelector('#mtBody .mt-goal-rep:nth-of-type(2) .mt-goal-add input')`), '관리자는 남의 목표도 편집 칸 보임');

  console.log('▶ 3) 메모장 "내 목표" 카드');
  await A.T(`switchPage('memo'); renderMemoPage(true); 'ok'`); await A.pg.waitForTimeout(300);
  ok(await A.T(`var c=document.querySelector('#mmList .mt-goal-card'); !!c && c.innerText.indexOf('내 목표')>=0 && c.innerText.indexOf('SMC 가격표 10월분 갱신')>=0 && c.innerText.indexOf('이수율 50%')>=0 && c.innerText.indexOf('신규 거래처 3곳')<0`), '카드에 내 목표만 + 이수율');
  await A.T(`var cb=document.querySelector('#mmList .mt-goal-card .mt-goal-sub:not(.done) input'); cb.checked=true; cb.dispatchEvent(new Event('change')); 'ok'`); await A.pg.waitForTimeout(300);
  ok(await A.T(`_mtGoalProg(_mtFind('mtNew').goals[0].items[0]).pct===100 && document.querySelector('#mmList .mt-goal-card').innerText.indexOf('이수율 100%')>=0`), '메모장에서 체크 → 회의록 자료와 같이 100%');
  await A.T(`var ta=document.querySelector('#mmList .mt-goal-card textarea.mt-goal-detail'); ta.value='10/21 가격표 받음'; ta.dispatchEvent(new Event('blur')); 'ok'`); await A.pg.waitForTimeout(300);
  ok(await A.T(`_mtFind('mtNew').goals[0].items[0].detail==='10/21 가격표 받음'`), '메모장 카드에서 상세 내용 수정 → 회의록에 반영');

  console.log('▶ 4) 인쇄본에도 목표');
  const pr=await A.T(`_mtDocHtml(_mtFind('mtNew'), true)`);
  ok(pr.indexOf('3. 담당자별 목표')>=0 && pr.indexOf('SMC 가격표 10월분 갱신')>=0 && pr.indexOf('☑')>=0 && pr.indexOf('<textarea')<0, '인쇄본: 목표·세부(☑) 포함, 입력칸 없음');

  console.log('▶ 5) 일반 직원 B(함현식): 남의 목표는 못 고치고 내 것만');
  const B=await openClient('함현식','user');
  await B.T(`meetings=${JSON.stringify(M)}; _mtDelMap={}; _mtDirty=false; _fbLastUpdatedAt=3; 'ok'`);
  await A.pg.waitForTimeout(1500);   // A 의 저장이 서버에 올라가도록
  await B.T(`_pollSync(true); 'ok'`); await B.pg.waitForTimeout(800);
  ok(await B.T(`var m=_mtFind('mtNew'); !!m.goals && m.goals.length===2 && m.goals[0].items[0].subs.length===2`), 'B 가 폴링으로 A 의 목표·세부 항목을 받음');
  await B.T(`switchPage('meeting'); mtOpen('mtNew'); 'ok'`); await B.pg.waitForTimeout(300);
  ok(await B.T(`!document.querySelector('#mtBody .mt-goal[data-gid="${gid}"] input[type=checkbox]') && !!document.querySelector('#mtBody .mt-goal-rep:nth-of-type(2) .mt-goal-add input')`), '김재성 목표는 읽기 전용, 함현식 목표는 편집 가능');
  const gidB=await B.T(`_mtFind('mtNew').goals[1].items[0].id`);
  await B.T(`var inp=document.querySelector('#mtBody .mt-goal[data-gid="${gidB}"] .mt-goal-add input'); inp.value='후보 업체 리스트'; mtGoalSubAdd('mtNew','${gidB}',inp); 'ok'`);
  await B.pg.waitForTimeout(1500);
  const sv=DB.sched_meetings.find(x=>x.id==='mtNew');
  ok(sv.goals[1].items[0].subs.length===1 && sv.goals[0].items[0].subs.length===2 && sv.goals[0].items[0].detail==='10/21 가격표 받음', '서버: B 의 세부 항목 + A 의 목표 내용 모두 유지 (goals 병합)');

  console.log('▶ 6) 동시 수정 병합 — A 가 세부 항목 추가, B 가 같은 순간 자기 항목 체크');
  await A.T(`_pollSync(true); 'ok'`); await A.pg.waitForTimeout(500);
  await A.T(`var it=_mtFind('mtNew').goals[0].items[0]; it.subs.push({id:'msA3',text:'A 추가',done:false,at:Date.now(),upd:Date.now()}); it.upd=Date.now(); _mtFind('mtNew').updatedAt=Date.now(); _mtSave(); 'ok'`);
  await B.T(`var it=_mtFind('mtNew').goals[1].items[0]; it.subs[0].done=true; it.subs[0].upd=Date.now(); it.upd=Date.now(); _mtFind('mtNew').updatedAt=Date.now(); _mtSave(); 'ok'`);
  await A.pg.waitForTimeout(5000);
  const sv2=DB.sched_meetings.find(x=>x.id==='mtNew');
  ok(sv2.goals[0].items[0].subs.some(s=>s.id==='msA3') && sv2.goals[1].items[0].subs[0].done===true, '서버에 A 의 추가와 B 의 체크가 모두 남음');

  ok(A.errs.length===0 && B.errs.length===0, '페이지 오류 없음'+((A.errs.length||B.errs.length)?(' — '+A.errs.concat(B.errs).slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(_e){}
  process.exit(fail?1:0);
})();
