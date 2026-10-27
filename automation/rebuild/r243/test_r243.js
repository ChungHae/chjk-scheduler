// r243 테스트 — 영업 자료(제안서) 담당자 치환 다운로드 (실제 pdf-lib·fontkit CDN + 내장 글꼴, 결과 PDF 는 python(pymupdf) 로 검사)
//  사용:  node test_r243.js <r243 적용된 index.html> [template.pdf]   (cdnjs·jsdelivr 네트워크 필요)
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path'), cp = require('child_process');
const file = path.resolve(process.argv[2] || 'b243/test/index.html');
const tpl = path.resolve(process.argv[3] || '/home/claude/prop/template.pdf');
let pass = 0, fail = 0;
function ok(c, msg){ if(c){ pass++; console.log('  ✓', msg); } else { fail++; console.log('  ✗', msg); } }
function pdfInfo(buf, tag){
  const p='/tmp/r243_'+tag+'.pdf'; fs.writeFileSync(p, buf);
  const py=`import pymupdf,json,sys\nd=pymupdf.open(sys.argv[1])\nout=[]\nfor pg in d:\n  out.append([s['text'] for b in pg.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans'] if (s['bbox'][1]<50 and s['bbox'][0]>380) or (s['bbox'][1]>775 and s['bbox'][0]>380)])\nprint(json.dumps({'pages':len(d),'hdrft':out,'all':d[0].get_text()[:200]}, ensure_ascii=False))`;
  return JSON.parse(cp.execFileSync('python3',['-I','-c',py,p],{encoding:'utf8',stdio:['ignore','pipe','ignore']}));
}
(async () => {
  const STUB = `
  window._xlsxStyleReady=true;
  window.__T=function(c){return eval(c);};
  function _vacUnlimited(id){`;
  const src = fs.readFileSync(file, 'utf8').replace('  function _vacUnlimited(id){', STUB);
  const tmp = path.join(path.dirname(file), '_h_r243.html'); fs.writeFileSync(tmp, src);
  const br = await chromium.launch(); const ctx = await br.newContext({ timezoneId:'Asia/Seoul', viewport:{width:1400,height:900} });
  const pg = await ctx.newPage(); const errs=[]; pg.on('pageerror', e => errs.push(String(e)));
  const tplB64 = fs.readFileSync(tpl).toString('base64');
  let fullFontFetched=false;
  await pg.route('**/*', r => { const u=r.request().url();
    if(u.startsWith('file://') || /cdnjs\.cloudflare\.com|cdn\.jsdelivr\.net/.test(u)){ if(/Pretendard-Bold\.ttf/.test(u)) fullFontFetched=true; return r.continue(); }
    if(u.startsWith('data:')) return r.continue();
    r.abort(); });
  await pg.goto('file://' + tmp); await pg.waitForTimeout(3500);
  await pg.evaluate(() => { document.getElementById('authGate').style.display='none'; });
  const T = c => pg.evaluate(c2 => window.__T(c2), c);
  await pg.evaluate(b64 => { window.__tpl='data:application/pdf;base64,'+b64; }, tplB64);
  await T(`
    _fbDbUrl='https://fb.test'; _authUser={id:'kjs',name:'김재성',role:'admin'};
    members=[{id:'m1',name:'김재성',position:'팀장',group:'서울',phone:'010-5228-2922'},{id:'m2',name:'함현식',position:'과장',group:'화성',phone:'010-5646-4475'},{id:'m3',name:'홍길동',position:'대리',group:'서울',phone:'010-1111-2222'}];
    debouncedFbSave=function(){}; saveAll=function(){ window.__saved=(window.__saved||0)+1; }; memoLines=[]; meetings=[];
    filesList=[{id:'f_sd1',name:'SMC 플로 컨트롤러 제안서.pdf',category:'영업자료(제안서)',group:'충해전기',type:'application/pdf',size:1745001,byName:'김재성',ts:Date.now()},
               {id:'f_other',name:'사업자등록증.pdf',category:'사업자등록증',group:'충해전기',type:'application/pdf',size:1000,byName:'김재성',ts:1}];
    _fbFileGet=async function(id){ return id==='f_sd1' ? window.__tpl : 'data:text/plain;base64,aGk='; };
    window.__dl=[]; HTMLAnchorElement.prototype.click=function(){ if(this.download) window.__dl.push(this.download); };
    'ok'`);

  console.log('▶ 1) 일정 툴바 [영업 자료] → 목록 창');
  ok(await T(`!!document.querySelector('#pageMemo .qic[onclick="sdOpenList()"]')`), '일정 툴바에 버튼');
  ok(await T(`FILE_CATS.indexOf('영업자료(제안서)')>=0`), "자료실 분류에 '영업자료(제안서)'");
  await T(`sdOpenList(); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`document.getElementById('sdOverlay').style.display==='flex' && document.querySelectorAll('#sdOverlay .sd-row').length===1`), '영업 자료 1건만 목록 (다른 분류는 제외)');
  ok(await T(`document.getElementById('sdWho').value==='김재성'`), '담당자 기본 = 나');
  ok(await T(`document.getElementById('sdWho').options.length===3 && document.getElementById('sdWho').options[1].text.indexOf('함현식 과장 · 010-5646-4475')>=0`), '직원 선택지에 직급·전화');
  ok(await T(`!!document.querySelector('#sdOverlay button[onclick*="sdCfgEdit"]')`), '관리자: [치환 위치] 버튼');

  console.log('▶ 2) 함현식 선택 → PDF 받기 (내장 글꼴)');
  await T(`document.getElementById('sdWho').value='함현식'; document.getElementById('sdWho').dispatchEvent(new Event('change')); 'ok'`);
  await T(`document.querySelector('#sdOverlay .sd-get').click(); 'ok'`);
  for(let i=0;i<200 && !(await T(`!!window._sdLastOut`)); i++) await pg.waitForTimeout(200);
  const out1 = Buffer.from(await T(`(function(){ var u=window._sdLastOut, s=''; for(var i=0;i<u.length;i+=0x8000) s+=String.fromCharCode.apply(null,u.subarray(i,i+0x8000)); return btoa(s); })()`), 'base64');
  ok(out1.length>100000 && out1.slice(0,5).toString()==='%PDF-', '결과 PDF 생성 ('+out1.length+' bytes)');
  ok(JSON.stringify(await T(`window.__dl`))==='["SMC 플로 컨트롤러 제안서 (함현식).pdf"]', '파일명 = 원본명 (이름).pdf');
  const i1 = pdfInfo(out1,'hhs');
  ok(i1.pages===2, '2페이지 유지');
  ok(i1.hdrft.every(p => p.indexOf('담당 함현식 과장 010-5646-4475')>=0 && p.indexOf('상담 · 견적 문의 함현식 과장')>=0 && p.indexOf('010-5646-4475')>=0), '두 페이지 머리글·꼬리글·전화 모두 치환 — '+JSON.stringify(i1.hdrft[0]));
  ok(i1.hdrft.every(p => p.join('').indexOf('김재성')<0), '원래 담당자 이름 없음');
  ok(!fullFontFetched, '내장 부분집합 글꼴로 처리 (전체 글꼴 다운로드 없음)');

  console.log('▶ 3) 내장 글꼴에 없는 이름(홍길동) → 전체 글꼴 내려받아 처리');
  await T(`window._sdLastOut=null; window.__dl=[]; document.getElementById('sdWho').value='홍길동'; document.getElementById('sdWho').dispatchEvent(new Event('change')); document.querySelector('#sdOverlay .sd-get').click(); 'ok'`);
  for(let i=0;i<300 && !(await T(`!!window._sdLastOut`)); i++) await pg.waitForTimeout(200);
  const out2 = Buffer.from(await T(`(function(){ var u=window._sdLastOut, s=''; for(var i=0;i<u.length;i+=0x8000) s+=String.fromCharCode.apply(null,u.subarray(i,i+0x8000)); return btoa(s); })()`), 'base64');
  const i2 = pdfInfo(out2,'hgd');
  ok(fullFontFetched, '전체 글꼴(jsdelivr) 다운로드됨');
  ok(i2.hdrft[0].indexOf('담당 홍길동 대리 010-1111-2222')>=0, '홍길동 치환 — '+JSON.stringify(i2.hdrft[0]));

  console.log('▶ 4) 자료실 ⬇ 도 영업 자료면 내 이름으로 · 다른 분류는 원본 그대로 · 관리자 [원본]');
  await T(`window._sdLastOut=null; window.__dl=[]; _sdPick='함현식'; downloadFile('f_sd1'); 'ok'`);
  for(let i=0;i<200 && !(await T(`!!window._sdLastOut`)); i++) await pg.waitForTimeout(200);
  ok(JSON.stringify(await T(`window.__dl`))==='["SMC 플로 컨트롤러 제안서 (김재성).pdf"]', '자료실 다운로드 = 내 이름(김재성)으로 치환');
  await T(`window.__dl=[]; downloadFile('f_other'); 'ok'`); await pg.waitForTimeout(400);
  ok(JSON.stringify(await T(`window.__dl`))==='["사업자등록증.pdf"]', '다른 분류는 원본 그대로');
  await T(`window.__dl=[]; downloadFile('f_sd1', true); 'ok'`); await pg.waitForTimeout(400);
  ok(JSON.stringify(await T(`window.__dl`))==='["SMC 플로 컨트롤러 제안서.pdf"]', '[원본] = 치환 없이');

  console.log('▶ 5) 치환 위치 설정(관리자) 저장 · 일반 직원 화면');
  await T(`sdCfgEdit('f_sd1'); 'ok'`); await pg.waitForTimeout(100);
  await T(`document.getElementById('sdCfgTa').value='{"slots":[{"template":"담당 {name}","top":33,"h":16,"baseline":44.6,"size":11,"color":[0,0,0],"bg":[255,255,255]}]}'; sdCfgSave('f_sd1'); 'ok'`); await pg.waitForTimeout(100);
  ok(await T(`filesList[0].pcfg && filesList[0].pcfg.slots.length===1 && window.__saved>=1`), 'pcfg 저장 + saveAll');
  await T(`_authUser={id:'hhs',name:'함현식',role:'user'}; _sdPick=''; sdOpenList(); 'ok'`); await pg.waitForTimeout(200);
  ok(await T(`document.getElementById('sdWho').value==='함현식' && !document.querySelector('#sdOverlay button[onclick*="sdCfgEdit"]') && !document.querySelector('#sdOverlay button[onclick*="downloadFile"]')`), '일반 직원: 기본 = 본인, 원본·치환 위치 버튼 없음');

  ok(errs.length===0, '페이지 오류 없음'+(errs.length?(' — '+errs.slice(0,3).join(' | ')):''));
  console.log(`\n${pass} passed, ${fail} failed`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(_e){}
  process.exit(fail?1:0);
})();
