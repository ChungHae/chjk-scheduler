// r253 테스트 — 자료 백업(자동 일일 스냅샷 · 상태 밖 키 보관 · 없는 키 되살리기)
//  사용:  node test_r253.js <r253 적용된 index.html> [라벨]
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path'), os = require('os');
const file = path.resolve(process.argv[2] || '/tmp/h/live.html');
const LABEL = process.argv[3] || '?';
let pass = 0, fail = 0;
function ok(c, msg, extra){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg, extra===undefined?'':('   → '+extra)); } }
(async () => {
  const STUB = `
  window._xlsxStyleReady=true;
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  let src = fs.readFileSync(file, 'utf8');
  if(src.indexOf('window.__T=') < 0) src = src.replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(os.tmpdir(), '_h_r253.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch();

  // ── 가짜 Firebase ──
  const DB = {};            // teamdata_test 아래 키
  const ACC = { u1:{id:'chjk'} };
  const BK = {};            // teamdata_backup/teamdata_test/<day>
  const log = [];           // {m, p}
  function J(v){ return JSON.stringify(v===undefined?null:v); }
  async function route(r){
    const req = r.request(), u = req.url(), m = req.method();
    if(u.startsWith('file://')) return r.continue();
    const P = u.replace(/^https?:\/\/[^/]+/, '').replace(/\?.*$/, '');
    const shallow = /shallow=true/.test(u);
    log.push({ m, p:P });
    const okJ = b => r.fulfill({status:200, contentType:'application/json', body:b});
    let mm;
    if((mm = P.match(/^\/teamdata_backup\/teamdata_test\/([^./]+)\.json$/))){
      if(m === 'PUT'){ BK[mm[1]] = JSON.parse(req.postData()); return okJ('{}'); }
      if(m === 'DELETE'){ delete BK[mm[1]]; return okJ('{}'); }
      if(m === 'GET'){ const v = BK[mm[1]]; return okJ(J(shallow ? (v===undefined?null:true) : v)); }
    }
    if(P === '/teamdata_backup/teamdata_test.json'){
      if(m === 'GET'){ const o = {}; Object.keys(BK).forEach(k => o[k] = true); return okJ(J(Object.keys(o).length ? o : null)); }
    }
    if(P === '/teamdata_test_accounts.json' && m === 'GET') return okJ(J(ACC));
    if((mm = P.match(/^\/teamdata_test\/([^./]+)\.json$/))){
      if(m === 'PUT'){ DB[mm[1]] = JSON.parse(req.postData()); return okJ('{}'); }
      if(m === 'DELETE'){ delete DB[mm[1]]; return okJ('{}'); }
      if(m === 'GET') return okJ(J(DB[mm[1]]));
    }
    if(P === '/teamdata_test.json'){
      if(m === 'GET'){ if(shallow){ const o = {}; Object.keys(DB).forEach(k => o[k] = true); return okJ(J(o)); } return okJ(J(DB)); }
      if(m === 'PATCH'){ Object.assign(DB, JSON.parse(req.postData())); return okJ('{}'); }
      if(m === 'PUT'){ return okJ('{}'); }   // 일어나면 안 되는 일 — 로그로 잡는다
    }
    if(/teamdata_[a-z_]*\.json/.test(P)) return okJ('null');
    r.abort();
  }
  const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1400,height:900} });
  const pg = await ctx.newPage(); const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  await pg.route('**/*', route);
  await pg.goto('file://' + tmp); await pg.waitForTimeout(6000);
  await pg.evaluate(() => { var g = document.getElementById('authGate'); if(g) g.style.display = 'none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);

  // 상태 노드: 상태 키 몇 개 + '상태 밖' 키 (이번 사고로 사라졌던 것들)
  for(const k of ['sched_members','sched_entries','sched_config','sched_memos','sched_meetings','sched_quote_saved',
                  'sched_client_list','sched_files','sched_personal','sched_projects','sched_issues','sched_categories'])
    DB[k] = [1];
  DB.sched_mail_cfg = { url:'https://w.example', key:'k' };
  DB.sched_doc_assets = { seal:'AAAA' };
  DB.sched_rules = [{ t:'내규' }];
  DB.sched_notice_seen = { nt1:{ chjk:1 } };

  await T(`
    _fbDbUrl='https://fb.test'; _fbReady=true; _fbLoadedOnce=true;
    _authUser={id:'chjk',name:'김재성',role:'admin'};
    _fbFetch=async function(url,opts){ return fetch(url,opts); };
    _isViewer=function(){ return false; };
    showInfoModal=function(){}; showConfirmModal=function(t,m,cb){ cb && cb(); };
    try{ localStorage.removeItem('sched_bk_day'); }catch(e){}
    'ok'`);

  console.log('▶ 1) 관리자에게만 [백업] 버튼');
  const admShown = await T(`applyConfig(); var b=document.getElementById('btnBackupMgr'); b && b.style.display!=='none'`);
  ok(admShown, '관리자면 헤더에 [백업] 버튼이 보인다');
  const staffHidden = await T(`_authUser={id:'kim',name:'함현식',role:'staff'}; applyConfig(); var b=document.getElementById('btnBackupMgr'); b && b.style.display==='none'`);
  ok(staffHidden, '일반 직원에게는 안 보인다');
  await T(`_authUser={id:'chjk',name:'김재성',role:'admin'}; applyConfig(); 'ok'`);

  // 적용 전 빌드에서는 기능 자체가 없다 — 던지지 말고 FAIL 로 보고한다
  const hasFeature = await T(`typeof _bkSnapshot==='function' && typeof _bkEnsureDaily==='function' && typeof window.bkOpen==='function'`);
  if(!hasFeature){
    ['스냅샷 생성','상태 전체 담기','계정도 담기','부모 노드 PUT 금지','상태 자식 키 안 건드림',
     '사고 키 포함','_bkFetchExtras','중복 제외','설정 키 포함','하루 한 번','직원 제외',
     '빈 자료 거부','보관 정리','최근 14개','매월 1일분','없는 키 되살리기','있는 키 보존']
      .forEach(n => ok(false, 'r253 기능 없음 — ' + n));
    ok(errs.length === 0, 'pageerror 없음', errs.slice(0,2).join(' | '));
    await br.close(); console.log('[' + LABEL + '] ' + pass + '/' + (pass + fail)); return;
  }

  console.log('▶ 2) 백업은 별도 노드에만 쓴다 (부모 노드 PUT 금지)');
  log.length = 0;
  const day = await T(`_bkSnapshot()`);
  ok(/^\d{4}-\d{2}-\d{2}$/.test(String(day)), '오늘 날짜로 스냅샷 생성', String(day));
  ok(!!BK[day] && BK[day].state && Object.keys(BK[day].state).length >= 16, '스냅샷에 상태 노드 전체가 담긴다', BK[day] ? Object.keys(BK[day].state).length : 'none');
  ok(!!BK[day].accounts, '계정 노드도 함께 담긴다');
  ok(!log.some(x => x.m === 'PUT' && x.p === '/teamdata_test.json'), '`teamdata_test` 부모 노드에는 PUT 하지 않는다', JSON.stringify(log.filter(x=>x.m!=='GET')));
  ok(!log.some(x => x.m === 'PUT' && /^\/teamdata_test\//.test(x.p)), '상태 자식 키도 건드리지 않는다(읽기만)');

  console.log('▶ 3) 사라졌던 상태 밖 키가 백업에 들어간다');
  const inSnap = await pg.evaluate(k => k, Object.keys(BK[day].state));
  ok(['sched_mail_cfg','sched_doc_assets','sched_rules','sched_notice_seen'].every(k => inSnap.indexOf(k) >= 0),
     '메일 설정 · 명판/인감 · 내규 · 공지 확인 모두 포함', JSON.stringify(inSnap.filter(k=>/mail|assets|rules|notice/.test(k))));
  const exKeys = String(await T(`_bkFetchExtras().then(function(o){ return Object.keys(o).sort().join(','); })`)).split(',').filter(Boolean);
  ok(['sched_mail_cfg','sched_doc_assets','sched_rules','sched_notice_seen'].every(k => exKeys.indexOf(k) >= 0),
     '_bkFetchExtras 가 사고로 사라졌던 키를 모두 집어낸다', exKeys.join(','));
  const mainKeys = await T(`Object.keys(_fullBackupMain()).join(',')`);
  const mainSet = String(mainKeys).split(',');
  ok(exKeys.every(k => mainSet.indexOf(k) < 0), '_fullBackupMain 에 이미 있는 키는 중복으로 안 담는다');
  // 앱이 올리지만 _fullBackupMain 에는 없던 키들(sched_price_note·sched_meetings_del·sched_quote_del·sched_links_ts)도
  // 이제 extra 로 함께 백업된다 — 기존 백업 파일의 또 다른 구멍이었다.
  ok(exKeys.indexOf('sched_price_note') >= 0 && exKeys.indexOf('sched_quote_del') >= 0,
     '기존 백업이 놓치던 설정 키도 함께 담긴다', exKeys.join(','));

  console.log('▶ 4) 자동 일일 백업은 하루 한 번');
  await T(`try{ localStorage.removeItem('sched_bk_day'); }catch(e){} 'ok'`);
  delete BK[day]; log.length = 0;
  await T(`_bkEnsureDaily()`); await pg.waitForTimeout(400);
  const first = log.filter(x => x.m === 'PUT' && /teamdata_backup/.test(x.p)).length;
  await T(`_bkEnsureDaily()`); await pg.waitForTimeout(400);
  const total = log.filter(x => x.m === 'PUT' && /teamdata_backup/.test(x.p)).length;
  ok(first === 1 && total === 1, '두 번 불러도 백업은 한 번만', first + '/' + total);
  const staffNo = await T(`_authUser={id:'kim',name:'함현식',role:'staff'}; try{ localStorage.removeItem('sched_bk_day'); }catch(e){} _bkEnsureDaily().then(function(){ return 'done'; })`);
  await pg.waitForTimeout(300);
  ok(log.filter(x => x.m === 'PUT' && /teamdata_backup/.test(x.p)).length === 1, '일반 직원 접속으로는 백업하지 않는다', String(staffNo));
  await T(`_authUser={id:'chjk',name:'김재성',role:'admin'}; 'ok'`);

  console.log('▶ 5) 빈 자료로는 백업하지 않는다 (빈 스냅샷 방지)');
  const keep = Object.keys(DB).slice();
  const savedDB = {}; keep.forEach(k => { savedDB[k] = DB[k]; delete DB[k]; });
  DB.sched_members = [1];
  const guard = await T(`_bkSnapshot().then(function(){return 'OK';}).catch(function(e){return 'ERR:'+(e&&e.message||e);})`);
  ok(String(guard).indexOf('ERR:') === 0 && /너무 적어/.test(String(guard)), '자료가 비면 오류를 던지고 덮어쓰지 않는다', String(guard).slice(0, 60));
  Object.keys(DB).forEach(k => delete DB[k]); keep.forEach(k => DB[k] = savedDB[k]);

  console.log('▶ 6) 보관 정리 — 최근 14개 + 매월 1일분');
  Object.keys(BK).forEach(k => delete BK[k]);
  for(let i = 0; i < 40; i++){
    const d = new Date(Date.now() - i*86400000).toISOString().slice(0, 10);
    BK[d] = { day:d, state:{ a:1 } };
  }
  const olds = Object.keys(BK).sort().reverse();
  const pruned = await T(`_bkPrune()`);
  const left = Object.keys(BK).sort().reverse();
  ok(pruned > 0 && left.length < olds.length, '오래된 백업을 정리한다', olds.length + ' → ' + left.length);
  ok(olds.slice(0, 14).every(d => left.indexOf(d) >= 0), '최근 14개는 남는다');
  ok(olds.filter(d => /-01$/.test(d)).every(d => left.indexOf(d) >= 0), '매월 1일분은 남는다', JSON.stringify(olds.filter(d=>/-01$/.test(d))));

  console.log('▶ 7) 없는 키만 되살리기 (11-02 사고 복구)');
  Object.keys(BK).forEach(k => delete BK[k]);
  await T(`try{ localStorage.removeItem('sched_bk_day'); }catch(e){} 'ok'`);
  const d2 = await T(`_bkSnapshot()`);
  const beforeRules = JSON.stringify(DB.sched_rules);
  delete DB.sched_mail_cfg; delete DB.sched_doc_assets;     // 사고 재현
  DB.sched_rules = [{ t:'내규(나중에 고친 것)' }];            // 지금 것이 더 새 것
  await T(`bkRestoreMissing('${d2}')`); await pg.waitForTimeout(700);
  ok(!!DB.sched_mail_cfg && !!DB.sched_doc_assets, '사라진 메일 설정·명판/인감이 되살아난다');
  ok(JSON.stringify(DB.sched_rules) !== beforeRules, '지금 있는 키(내규)는 덮어쓰지 않는다', JSON.stringify(DB.sched_rules));

  console.log('▶ 8) 페이지 오류 없음');
  ok(errs.length === 0, 'pageerror 없음', errs.slice(0, 2).join(' | '));

  await br.close();
  console.log('[' + LABEL + '] ' + pass + '/' + (pass + fail));
})();
