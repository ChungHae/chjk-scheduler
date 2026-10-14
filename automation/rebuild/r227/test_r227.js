// r227 테스트 — A) 주간 완료 건 ✓(취소선 없음)  B) 신규 영업 응원 배너  C) 업무회의 2주 주기 배너·회의 탭 안내·지난 회의 접기·지난 회의 안건 숨김
//  사용:  node test_r227.js <r227 적용된 index.html>
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b227/test/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const STUB = `
  window._xlsxStyleReady=true;
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r227.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  await pg.route('**/*', r => { const u=r.request().url(); if(u.startsWith('file://')) r.continue(); else r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  const d = (off) => { const x=new Date(); x.setDate(x.getDate()+off); return x.getFullYear()+'-'+String(x.getMonth()+1).padStart(2,'0')+'-'+String(x.getDate()).padStart(2,'0'); };

  await T(`
    _fbDbUrl='https://x.test'; _authUser={id:'kjs',name:'김재성',role:'admin'}; myMemberId='m1';
    members=[{id:'m1',name:'김재성',group:'서울'},{id:'m2',name:'함현식',group:'서울'}];
    _fbPutOk=async function(){ return true; }; debouncedFbSave=function(){};
    clientOwner={}; clientPBase={}; quoteSaved=[]; smcQueue=[]; clientPend=[];
    personalSchedules=[{id:'s1',memberId:'m1',date:'${d(0)}',category:'납품',title:'납품 A',done:true,endDate:'${d(0)}'},{id:'s2',memberId:'m1',date:'${d(0)}',category:'미팅',title:'미팅 B',done:false}];
    projectsList=[]; entries={};
    meetings=[{id:'mt1',date:'${d(-25)}',time:'10:00',place:'서울',title:'9월 회의',author:'김재성',attendees:['김재성'],agenda:[{id:'a1',title:'안건1',text:'x'}],reports:[]},
              {id:'mt2',date:'${d(-29)}',time:'10:00',place:'서울',title:'9월 초 회의',author:'김재성',attendees:['김재성'],agenda:[],reports:[]}];
    memoLines=[{id:'n1',owner:'함현식',text:'신규 대한정밀 견적 방문',kind:'newbiz',vendor:'대한정밀',parent:'',date:'${d(0)}',createdAt:Date.now(),done:false,when:{date:'',time:''},feedback:[],linked:{}},
               {id:'n2',owner:'김재성',text:'신규 한빛테크 상담',kind:'newbiz',vendor:'',parent:'',date:'${d(-1)}',createdAt:Date.now()-86400000,done:true,doneAt:Date.now()-3600000,when:{date:'',time:''},feedback:[],linked:{}},
               {id:'n3',owner:'김재성',text:'신규 옛날업체',kind:'newbiz',vendor:'옛날업체',parent:'',date:'${d(-10)}',createdAt:Date.now()-10*86400000,done:true,doneAt:Date.now()-2*86400000,when:{date:'',time:''},feedback:[],linked:{}},
               {id:'ag1',owner:'김재성',text:'회의 안건(9월 회의) · 안건1: x',kind:'meeting',vendor:'',parent:'',date:'${d(-25)}',createdAt:Date.now()-25*86400000,done:false,when:{date:'${d(-25)}',time:''},feedback:[],linked:{},mtRef:{mid:'mt1',iid:'a1'}},
               {id:'m1',owner:'김재성',text:'오늘 할 일',kind:'memo',vendor:'',parent:'',date:'${d(0)}',createdAt:Date.now(),done:false,when:{date:'',time:''},feedback:[],linked:{}}];
    'ok'`);

  console.log('▶ A) 주간 완료 표시');
  await T(`switchPage('weekly'); 'ok'`); await pg.waitForTimeout(500);
  const wk = await T(`[...document.querySelectorAll('#wkTable .wk-it')].map(function(e){ return e.className+'|'+e.textContent+'|'+getComputedStyle(e).textDecorationLine+'|'+getComputedStyle(e).opacity; }).join(' ; ')`);
  ok(/k-delivery done\|✓ 납품 A\|none\|1/.test(wk), '완료 납품: ✓ 붙고 취소선 없음·흐림 없음 ('+wk+')');
  ok(/k-meeting\|미팅 B\|none\|1/.test(wk), '미완료 미팅 그대로');

  console.log('▶ B) 신규 영업 응원 배너');
  await T(`switchPage('memo'); 'ok'`); await pg.waitForTimeout(600);
  let nb = await T(`[...document.querySelectorAll('#pageMemo .mm-smc.nb')].map(function(e){ return e.className+'|'+e.innerText.replace(/\\s+/g,' '); }).join(' || ')`);
  ok(nb.indexOf('신규 영업 진행 중!')>=0 && nb.indexOf('함현식님 → 대한정밀')>=0 && nb.indexOf('함께 응원해요')>=0, '진행 중 배너: 함현식 → 대한정밀 ('+nb+')');
  ok(nb.indexOf('신규 등록 축하!')>=0 && nb.indexOf('김재성님 한빛테크 상담')>=0 && nb.indexOf('옛날업체')<0, '축하 배너: 1시간 전 완료 건만 (2일 전 완료는 제외)');
  await T(`_authUser={id:'h',name:'함현식',role:'user'}; renderMemoPage(true); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`document.querySelectorAll('#pageMemo .mm-smc.nb').length===2`), '다른 사람(함현식) 메모장에도 같은 배너');
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; 'ok'`);

  console.log('▶ C) 업무회의 2주 주기');
  ok(await T(`_mtDaysSince()===25 && !!_mtDueInfo() && _mtDueInfo().days===25`), '마지막 회의 25일 전 → 회의 필요');
  await T(`renderMemoPage(true); 'ok'`); await pg.waitForTimeout(200);
  let mt = await T(`(document.querySelector('#pageMemo .mm-smc.mt')||{}).innerText||''`);
  ok(mt.indexOf('업무회의 필요')>=0 && mt.indexOf('25일째')>=0 && mt.indexOf('2주마다')>=0, '메모장 배너: 25일째 ('+mt.replace(/\n/g,' ')+')');
  ok(await T(`!document.querySelector('#pageMemo [data-id="ag1"], #pageMemo .mm-line[data-id="ag1"]') && document.body.innerText.indexOf('회의 안건(9월 회의)')<0`), '지난 회의 안건 줄은 일정에서 숨김');
  ok(await T(`document.body.innerText.indexOf('오늘 할 일')>=0`), '일반 메모는 그대로');
  await T(`switchPage('meeting'); renderMeetingPage(true); 'ok'`); await pg.waitForTimeout(400);
  ok(await T(`!!document.querySelector('#pageMeeting .mt-due') && document.querySelector('#pageMeeting .mt-due').innerText.indexOf('25일')>=0`), '회의 탭 상단 회의 필요 안내');
  ok(await T(`document.querySelectorAll('#pageMeeting .mt-row').length===0 && document.querySelector('#pageMeeting .mt-past-tg').innerText.indexOf('지난 회의 2건 보기')>=0 && document.querySelector('#pageMeeting .mt-empty').innerText.indexOf('예정된 회의가 없습니다')>=0`), '지난 회의 2건 접힘 · 예정 없음 안내');
  await T(`mtTogglePast(); 'ok'`); await pg.waitForTimeout(300);
  ok(await T(`document.querySelectorAll('#pageMeeting .mt-row').length===2 && document.querySelector('#pageMeeting .mt-past-tg').innerText.indexOf('지난 회의 접기')>=0`), '[지난 회의 보기] → 2건 펼침');
  await T(`mtTogglePast(); meetings.push({id:'mt3',date:'${d(3)}',time:'14:00',place:'서울',title:'10월 회의',author:'김재성',attendees:[],agenda:[],reports:[]}); renderMeetingPage(true); 'ok'`); await pg.waitForTimeout(300);
  ok(await T(`!document.querySelector('#pageMeeting .mt-due') && document.querySelectorAll('#pageMeeting .mt-row').length===1`), '예정 회의 추가 → 안내 사라지고 예정 1건만');
  ok(await T(`_mtDueInfo()===null`), '예정 회의가 있으면 배너 없음');
  await T(`meetings=[]; 'ok'`);
  ok(await T(`!!_mtDueInfo() && _mtDueInfo().days===null && _mtDueBanner().indexOf('아직 업무회의 기록이 없습니다')>=0`), '회의록 없음 → 안내');
  await T(`meetings=[{id:'mt9',date:'${d(-13)}',time:'',place:'',title:'t',author:'',attendees:[],agenda:[],reports:[]}]; 'ok'`);
  ok(await T(`_mtDueInfo()===null`), '13일 전 회의 → 아직 안내 없음');

  ok(errs.length===0, '페이지 오류 없음'+(errs.length?(' — '+errs.slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(_e){}
  process.exit(fail?1:0);
})();
