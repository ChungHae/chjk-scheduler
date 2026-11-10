// r264 테스트 — 견적 메일 서류 첨부(사업자등록증·통장사본, 지점별)
// (r250 하니스 재사용) — 견적 메일: 업체별 주소록 칩(넣기/빼기/지우기) · 주소록에 저장 · 처음 값 1개 · 자동 저장 체크
//  사용:  node test_r250.js <r250 적용된 index.html>
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'd264/test/index.html');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
(async () => {
  const STUB = `
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r264.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1500,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  const sent=[]; const cfgStore={ url:'https://worker.test', key:'k-123', cc:'' }; const FB={};
  await pg.route('**/*', r => { const u=r.request().url();
    if(u.startsWith('file://') || /cdnjs\.cloudflare\.com|cdn\.jsdelivr\.net/.test(u)) return r.continue();
    if(/(sched_mail_cfg|_settings\/mail_cfg)\.json/.test(u)) return r.fulfill({status:200, contentType:'application/json', body:JSON.stringify(cfgStore)});
    const fm=u.match(/^https:\/\/fb\.test\/(.+?)\.json/); if(fm){ const p=decodeURIComponent(fm[1]); const meth=r.request().method(); const get=k=>{ let n=FB; for(const s of k.split('/')){ if(n==null) return null; n=n[s]; } return n===undefined?null:n; }; const set=(k,v)=>{ const a=k.split('/'); let n=FB; for(let i=0;i<a.length-1;i++){ n[a[i]]=n[a[i]]||{}; n=n[a[i]]; } if(v===null) delete n[a[a.length-1]]; else n[a[a.length-1]]=v; }; if(meth==='GET') return r.fulfill({status:200,contentType:'application/json',body:JSON.stringify(get(p))}); const v=r.request().postData()?JSON.parse(r.request().postData()):null; if(meth==='PUT') set(p,v); else if(meth==='PATCH') set(p,Object.assign({},get(p)||{},v)); else if(meth==='DELETE') set(p,null); return r.fulfill({status:200,contentType:'application/json',body:'{}'}); }
    if(u.indexOf('worker.test/send')>=0){ sent.push(JSON.parse(r.request().postData())); return r.fulfill({status:200, contentType:'application/json', headers:{'access-control-allow-origin':'*'}, body:'{"ok":true}'}); }
    r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  await T(`
    _fbDbUrl='https://fb.test'; _authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울',phone:'010-5228-2922'}];
    _fbPutOk=async function(){ return true; }; debouncedFbSave=function(){ window.__fb=(window.__fb||0)+1; }; saveAll=function(){};
    _fbFetch=async function(url,opts){ return fetch(url,opts); }; _nyLoadAssets=async function(){ return {}; }; _qPriceIdx={};
    clientList=[]; clientInfo={ '충해)성기웅|서울':{ email:'office@sk.com', contacts:[{dept:'',rank:'과장',name:'홍길동',phone:'010-0000-0000',phone2:'',email:'hong@sk.com'},{dept:'',rank:'대리',name:'이몽룡',phone:'',phone2:'',email:'lee@sk.com'}] } }; _ciVer++;
    _qQuoteNo='성기웅-20261027-01'; _qLoadedId='qid1'; quoteSaved=[{id:'qid1',title:'성기웅-20261027-01',vname:'충해)성기웅',count:1,total:1,savedBy:'김재성',savedAt:Date.now()}];
    _qPersistQuote=async function(){}; _qMakePdfBlob=async function(){ return new Blob(['%PDF-1.4'],{type:'application/pdf'}); };
    quoteVendors=[{id:'v1',name:'충해)성기웅'}]; _qCurId='v1';
    _qCart=[{vid:'v1',vname:'충해)성기웅',spec:'MGPM20-25Z',name:'실린더',qty:5,sell:89690,info:{maker:'SMC'}}]; _qNego=0; _qCols=[]; _qMgr='이몽룡';
    window.__info=[]; showInfoModal=function(t,m){ window.__info.push(t+'|'+m); }; showPromptModal=function(t,m,d,fn){ fn(window.__promptAns!=null?window.__promptAns:d); }; showConfirmModal=function(t,m,fn){ fn(); }; _mtToast=function(){};
    switchPage('quote'); 'ok'`);


  const base=await T(`_AUTH_BASE`);
  console.log('▶ 1) 미등록 상태');
  await T(`qOpenMailSend(); 'ok'`); await pg.waitForTimeout(700);
  const t1=await pg.evaluate(()=>document.getElementById('mlDocs').innerText.replace(/\s+/g,' '));
  ok(/사업자등록증 미등록/.test(t1) && /통장사본 미등록/.test(t1) && /서류 등록·변경/.test(t1), '참조 아래 서류 칩(미등록) + 관리자 등록 링크: '+t1.replace(/\n/g,' '));
  console.log('▶ 2) 관리자 등록');
  await T(`docFilesOpen(); 'ok'`); await pg.waitForTimeout(400);
  await pg.evaluate(()=>{ const ins=[...document.querySelectorAll('#docFilesOverlay input[type=file]')]; const mk=(n)=>{ const dt=new DataTransfer(); dt.items.add(new File(['%PDF-1.4 '+n],n,{type:'application/pdf'})); return dt.files; };
    ins[0].files=mk('사업자등록증_서울.pdf'); ins[0].dispatchEvent(new Event('change')); });
  await pg.waitForTimeout(700);
  await pg.evaluate(()=>{ const ins=[...document.querySelectorAll('#docFilesOverlay input[type=file]')]; const dt=new DataTransfer(); dt.items.add(new File(['%PDF-1.4 bank'],'통장사본_서울.pdf',{type:'application/pdf'})); ins[1].files=dt.files; ins[1].dispatchEvent(new Event('change')); });
  await pg.waitForTimeout(700);
  ok(!!(FB[base]&&FB[base].sched_doc_files&&FB[base].sched_doc_files.seoul_biz&&FB[base].sched_doc_files.seoul_bank), '파일은 서버(sched_doc_files/seoul_biz·seoul_bank)에 저장');
  ok(FB[base].sched_doc_files_meta.seoul.biz.name==='사업자등록증_서울.pdf' && !FB[base].sched_doc_files_meta.seoul.biz.b64, '목록(meta)에는 이름·크기만 (파일 내용 없음)');
  await T(`document.getElementById('docFilesOverlay').style.display='none'; _mlDocsRender(); 'ok'`); await pg.waitForTimeout(300);
  const t2=await pg.evaluate(()=>document.getElementById('mlDocs').innerText.replace(/\s+/g,' '));
  ok(/\+ 사업자등록증 서울/.test(t2) && /\+ 통장사본 서울/.test(t2), '등록 후 칩 활성: '+t2.replace(/\n/g,' '));
  console.log('▶ 3) 클릭 첨부 → 발송');
  await pg.evaluate(()=>{ [...document.querySelectorAll('#mlDocs .ml-chip')].forEach(c=>c.click()); });
  await pg.waitForTimeout(300);
  ok(await pg.evaluate(()=>document.querySelectorAll('#mlDocs .ml-chip.on').length)===2, '두 서류 선택(✓)');
  await T(`document.getElementById('mlTo').value='a@b.com'; qMailSendNow(); 'ok'`);
  for(let i=0;i<60 && !sent.length; i++) await pg.waitForTimeout(150);
  const names=(sent[0]&&sent[0].attachments||[]).map(a=>a.name);
  ok(names.includes('사업자등록증 - 충해전기(주).pdf') && names.includes('통장사본 - 충해전기(주).pdf') && names.some(n=>/^견적서/.test(n)), '첨부: '+names.join(', '));
  ok((sent[0].attachments||[]).find(a=>a.name.indexOf('통장사본')===0).b64===Buffer.from('%PDF-1.4 bank').toString('base64'), '서류 내용 그대로 첨부');
  console.log('▶ 4) 화성 계정');
  await T(`_qCart=[{vid:'v1',vname:'충해)성기웅',spec:'MGPM20-25Z',name:'실린더',qty:5,sell:89690}]; _qLoadedId='qid1'; qOpenMailSend(); 'ok'`); await pg.waitForTimeout(700);
  ok(await pg.evaluate(()=>document.querySelectorAll('#mlDocs .ml-chip.on').length)===0, '새로 열면 선택 해제(매번 골라서 첨부)');
  await pg.evaluate(()=>{ const s=document.getElementById('mlAcct'); s.value='hs'; s.dispatchEvent(new Event('change')); }); await pg.waitForTimeout(400);
  ok(/사업자등록증 미등록/.test(await pg.evaluate(()=>document.getElementById('mlDocs').innerText.replace(/\s+/g,' '))), '화성 계정 → 화성 서류(미등록) 표시');
  const re=errs.filter(e=>!/net::|Failed to fetch|firebase|XLSX|cdnjs/.test(e)); ok(re.length===0,'페이지 오류 없음'+(re.length?' — '+re[0]:''));
  console.log(`\n결과: ${pass} 통과 / ${fail} 실패`); await br.close(); try{fs.unlinkSync(tmp);}catch(e){} process.exit(fail?1:0);
})();
