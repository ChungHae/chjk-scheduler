// r236 테스트 — 회의록 동시 작성 병합. 두 탭(A·B)이 가짜 Firebase(메모리) 를 공유하며 같은 회의록에 동시에 쓴다.
//  사용:  node test_r236.js <r236 적용된 index.html>
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b236/test/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const STUB = `
  window._xlsxStyleReady=true;
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r236.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch();
  // ── 가짜 Firebase: teamdata_test 아래 키별 저장. PATCH 는 키 병합, GET /x.json 은 그 키 ──
  const DB = {}; let patchLog = [];
  async function route(r){
    const req=r.request(); const u=req.url();
    if(u.startsWith('file://')) return r.continue();
    const m=u.match(/\/teamdata_[a-z]+(?:\/([^.?]+))?\.json/);
    if(m){
      const key=m[1];
      if(req.method()==="PATCH"){ const b=JSON.parse(req.postData()); patchLog.push(Object.keys(b)); if(process.env.DBG&&b.sched_meetings){ const mt=b.sched_meetings[0]; console.log("    [PATCH]", Date.now()%100000, JSON.stringify(mt?(mt.agenda||[]).map(a=>a.id+(a.done?"✓":"")):null), JSON.stringify(mt&&mt.del), JSON.stringify(b.sched_meetings_del)); } Object.assign(DB, b); return r.fulfill({status:200, contentType:'application/json', body:'{}'}); }
      if(req.method()==='GET'){ const v=key?(key==='_updatedAt'?(DB._updatedAt||0):(DB[key]===undefined?null:DB[key])):DB; return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify(v)}); }
    }
    r.abort();
  }
  async function openClient(name){
    const ctx=await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1400,height:900} });
    const pg=await ctx.newPage(); const errs=[]; pg.on('pageerror', e=>errs.push(String(e)));
    await pg.route('**/*', route);
    await pg.goto('file://'+tmp); await pg.waitForTimeout(6000);
    await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
    const T=c=>pg.evaluate(c2=>window.__T(c2), c);
    await T(`
      _fbDbUrl='https://fb.test'; _fbReady=true; _fbLoadedOnce=true; _authUser={id:'${name}',name:'${name}',role:'admin'};
      members=[{id:'m1',name:'김재성',group:'서울'},{id:'m2',name:'함현식',group:'서울'}];
      _fbFetch=async function(url,opts){ return fetch(url,opts); };
      _isViewer=function(){ return false; };
      memoLines=[]; personalSchedules=[];
      'ok'`);
    return { pg, T, errs, name };
  }
  const A=await openClient('김재성'), B=await openClient('함현식');
  const M0={ id:'mt1', date:'2026-10-16', time:'10:00', place:'서울', title:'주간회의', author:'김재성', attendees:['김재성','함현식'], agenda:[{id:'a0',title:'기존',text:'x',done:false,at:1}], reports:[], updatedAt:1, createdBy:'김재성' };
  DB.sched_meetings=[M0]; DB._updatedAt=1;
  for(const C of [A,B]) await C.T(`meetings=${JSON.stringify([M0])}; _mtDelMap={}; _mtDirty=false; _fbLastUpdatedAt=1; 'ok'`);

  console.log('▶ 1) 두 사람이 1초 안에 각자 저장 (A 안건 2건 · B 업무 2건)');
  await A.T(`var m=_mtFind('mt1'); m.agenda.push({id:'aA1',title:'A안건1',text:'',done:false,by:'김재성',at:Date.now()},{id:'aA2',title:'A안건2',text:'',done:false,by:'김재성',at:Date.now()}); m.updatedAt=Date.now(); _mtSave(); 'ok'`);
  await B.T(`var m=_mtFind('mt1'); m.reports.push({name:'함현식',items:[{id:'iB1',text:'B업무1',done:false,by:'함현식',at:Date.now()},{id:'iB2',text:'B업무2',done:false,by:'함현식',at:Date.now()}]}); m.updatedAt=Date.now(); _mtSave(); 'ok'`);
  await A.pg.waitForTimeout(6000);   // 같은 순간 저장 → 2.5초 뒤 검증(_mtVerify)이 다시 합쳐 올리는 시간까지
  let sv=DB.sched_meetings[0]; 
  ok(sv.agenda.map(a=>a.id).sort().join()==='a0,aA1,aA2' && sv.reports.length===1 && sv.reports[0].items.map(i=>i.id).join()==='iB1,iB2', '서버: A 안건 2 + B 업무 2 모두 남음 (이전엔 나중 저장이 덮어씀)');
  ok(patchLog.length>=2 && patchLog.every(k=>k.includes('sched_meetings_del')), '묘비 키도 같이 올라감');
  // 양쪽 폴링 후 서로 것 보임
  await A.T(`_pollSync(true); 'ok'`); await B.T(`_pollSync(true); 'ok'`); await A.pg.waitForTimeout(800);
  ok(await A.T(`_mtFind('mt1').reports.length===1 && _mtFind('mt1').reports[0].items.length===2`), 'A 화면에 B 업무 2건');
  ok(await B.T(`_mtFind('mt1').agenda.length===3`), 'B 화면에 A 안건 포함 3건');

  console.log('▶ 2) A 가 항목 삭제, 동시에 B 가 그 항목을 완료 체크 → 삭제가 이김(되살아나지 않음)');
  await A.T(`mtDelItem('mt1','aA1'); 'ok'`);
  await B.T(`mtToggle('mt1','aA1'); 'ok'`);
  await A.pg.waitForTimeout(8000);   // 같은 순간 올림 → 검증·재병합까지
  sv=DB.sched_meetings[0];
  ok(!sv.agenda.some(a=>a.id==='aA1') && sv.del && sv.del.aA1, '서버에서 aA1 삭제 유지 (묘비)');
  await A.T(`_pollSync(true); 'ok'`); await B.T(`_pollSync(true); 'ok'`); await B.pg.waitForTimeout(800);
  ok(await B.T(`!_mtFind('mt1').agenda.some(function(a){ return a.id==='aA1'; })`), 'B 화면에서도 사라짐');

  console.log('▶ 3) 같은 항목 완료 체크 충돌 → 나중 조작(upd 큰 쪽)이 이김');
  await A.T(`mtToggle('mt1','aA2'); 'ok'`);   // A: done
  await A.pg.waitForTimeout(300);
  await B.T(`var it=_mtItem(_mtFind('mt1'),'aA2'); it.done=true; it.doneAt=Date.now(); it.upd=Date.now(); it.done=false; it.doneAt=0; it.upd=Date.now()+5; _mtFind('mt1').updatedAt=Date.now(); _mtSave(); 'ok'`);   // B: 더 나중에 해제
  await A.pg.waitForTimeout(1500); await B.pg.waitForTimeout(1500);
  sv=DB.sched_meetings[0];
  ok(sv.agenda.find(a=>a.id==='aA2').done===false, '서버: 더 나중 조작(B 해제) 반영');

  console.log('▶ 4) 폴링이 로컬의 안 올린 변경을 덮지 않음');
  await B.T(`var m=_mtFind('mt1'); m.agenda.push({id:'aB9',title:'B안건9',text:'',done:false,at:Date.now()}); m.updatedAt=Date.now(); _mtDirty=true; save('sched_meetings',meetings); 'ok'`);
  DB._updatedAt=Date.now()+1; // 서버에 새 판이 있는 척
  await B.T(`_fbLastUpdatedAt=0; _pollSync(true); 'ok'`); await B.pg.waitForTimeout(800);
  ok(await B.T(`_mtFind('mt1').agenda.some(function(a){ return a.id==='aB9'; })`), '폴링 뒤에도 B 의 미전송 안건 유지');
  await B.T(`debouncedFbSave(); 'ok'`); await B.pg.waitForTimeout(1500);
  ok(DB.sched_meetings[0].agenda.some(a=>a.id==='aB9'), '이어서 서버에 올라감');

  console.log('▶ 5) 회의록 자체 삭제 묘비');
  await A.T(`_pollSync(true); 'ok'`); await A.pg.waitForTimeout(500);
  await A.T(`showConfirmModal=function(t,m,cb){ cb(); }; mtDelete('mt1'); 'ok'`); await A.pg.waitForTimeout(1500);
  ok(DB.sched_meetings.length===0 && DB.sched_meetings_del && DB.sched_meetings_del.mt1, '서버에서 회의록 삭제 + 묘비');
  await B.T(`var m=_mtFind('mt1'); if(!m){ m=JSON.parse(JSON.stringify(${JSON.stringify(M0)})); meetings.push(m); }   /* 폴링을 못 받은 옛 사본이라고 가정 */ m.agenda.push({id:'aB10',title:'늦은 추가',text:'',done:false,at:Date.now()}); m.updatedAt=Date.now(); _mtSave(); 'ok'`); await B.pg.waitForTimeout(1500);
  ok((DB.sched_meetings||[]).length===0, 'B 가 뒤늦게 저장해도 삭제된 회의록이 되살아나지 않음');

  console.log('▶ 6) 저장 후 검증(_mtVerify): 서버에 내 항목이 빠져 있으면 다시 올림');
  DB.sched_meetings=[{ id:'mt2', date:'2026-10-17', title:'t2', attendees:[], agenda:[{id:'z1',title:'z',at:1}], reports:[], updatedAt:1 }];
  await A.T(`_mtDelMap={}; meetings=[{ id:'mt2', date:'2026-10-17', title:'t2', attendees:[], agenda:[{id:'z1',title:'z',at:1},{id:'z2',title:'mine',at:2}], reports:[], updatedAt:2 }]; _mtDirty=false; 'ok'`);
  await A.T(`_mtVerify(); 'ok'`); await A.pg.waitForTimeout(1800);
  ok(DB.sched_meetings[0].agenda.some(a=>a.id==='z2'), '빠진 z2 를 다시 합쳐 올림');

  ok(A.errs.length===0 && B.errs.length===0, '페이지 오류 없음'+((A.errs.length||B.errs.length)?(' — '+A.errs.concat(B.errs).slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(_e){}
  process.exit(fail?1:0);
})();
