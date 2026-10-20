// r241 테스트 — 메모장 안내 배너가 메모 목록 아래로 (내 목표 카드는 위)
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'b241/test/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const STUB = `
  window._xlsxStyleReady=true;
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r241.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1400,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  await pg.route('**/*', r => { if(r.request().url().startsWith('file://')) return r.continue(); r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  const today=await T(`_mmToday()`);
  await T(`
    _authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울'},{id:'m2',name:'함현식',group:'서울'}];
    debouncedFbSave=function(){}; saveAll=function(){};
    smcQueue=[{id:'sq1',spec:'AF20-02',status:'wait',at:Date.now()}];
    clientPend=[{name:'임시업체',by:'김재성',at:Date.now(),status:'wait'}];
    memoLines=[{id:'mm1',owner:'김재성',text:'오늘 할 일',parent:'',kind:'memo',vendor:'',to:'',name:'',phone:'',when:{date:'',time:''},date:'${today}',createdAt:1,done:false,doneAt:0,feedback:[],card:'',linked:{}}];
    meetings=[{id:'mtg',date:'${today}',title:'회의',author:'김재성',attendees:['김재성'],agenda:[],reports:[],goals:[{name:'김재성',items:[{id:'g1',title:'내 목표 1',detail:'',subs:[],at:1,upd:1}]}],updatedAt:1,createdAt:1}];
    switchPage('memo'); renderMemoPage(true); 'ok'`);
  await pg.waitForTimeout(300);
  const order = await T(`(function(){ var L=document.getElementById('mmList'); var out=[]; Array.prototype.forEach.call(L.children, function(el){ out.push(el.className.split(' ')[0]); }); return out; })()`);
  console.log('   순서:', JSON.stringify(order));
  ok(order[0]==='mt-goal-card', '맨 위 = 내 목표 카드');
  ok(order.indexOf('mm-row')>=0 && order.indexOf('mm-banners-bottom')>order.indexOf('mm-row'), '메모 줄 다음에 안내 배너 묶음');
  const bot = await T(`document.querySelector('#mmList .mm-banners-bottom').innerText`);
  ok(bot.indexOf('SMC 가격 확인 대기')>=0 && bot.indexOf('업체 정보 등록 대기')>=0, '아래 묶음에 SMC 대기 · 업체 등록 대기 배너 ('+bot.replace(/\n/g,' ').slice(0,80)+'…)');
  ok(await T(`!document.querySelector('#mmList > .mm-smc')`), '위에는 안내 배너 없음');
  await T(`memoLines=[]; renderMemoPage(true); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`var L=document.getElementById('mmList'); L.innerText.indexOf('SMC 가격 확인 대기')>=0 && L.querySelector('.mm-banners-bottom')===L.lastElementChild`), '메모가 없어도 배너는 아래에');
  ok(errs.length===0, '페이지 오류 없음'+(errs.length?(' — '+errs.slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(_e){}
  process.exit(fail?1:0);
})();
