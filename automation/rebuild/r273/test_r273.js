// r273 테스트 — 거래명세서 작성·저장·견적 불러오기·인쇄 HTML·홈택스 엑셀 행
const { chromium } = require('playwright'); const fs=require('fs'), path=require('path');
const file=path.resolve(process.argv[2]||'/home/claude/d273/index.html');
let pass=0, fail=0; function ok(c,m){ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} }
(async()=>{
  const src=fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){','window.__T=function(c){return eval(c);}; function _vacUnlimited(id){');
  const tmp=path.join(path.dirname(file),'_h_r273.html'); fs.writeFileSync(tmp,src);
  const br=await chromium.launch(); const errs=[];
  const pg=await br.newPage({viewport:{width:1400,height:900}}); pg.on('pageerror',e=>errs.push(String(e)));
  await pg.route('**/*', r=>r.request().url().startsWith('file://')?r.continue():r.abort());
  await pg.goto('file://'+tmp); await pg.waitForTimeout(2500); await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  const T=c=>pg.evaluate(c2=>window.__T(c2),c);
  await T(`window.__db={}; _authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울'}]; _fbDbUrl='https://x.test'; _qLeaveGuard=function(){ return false; };
    _fbFetch=async function(u,o){ var k=u.replace(/^.*_stmt\\/?/,'').replace('.json',''); o=o||{}; if(o.method==='PUT'){ __db[k]=JSON.parse(o.body); return {ok:true,status:200,json:async()=>__db[k]}; } if(o.method==='DELETE'){ delete __db[k]; return {ok:true,status:200}; } return {ok:true,status:200,json:async()=>(k?__db[k]:(Object.keys(__db).length?__db:null))}; };
    clientList=[['대국산기','123-45-67890','서울','']]; clientInfo={'대국산기|서울':{ceo:'홍길동',addr:'서울시 구로구 1',uptae:'제조',jongmok:'기계',taxEmail:'tax@dk.co.kr'}};
    quoteSaved=[{id:'q1',title:'Q20261117-01',vname:'대국산기',savedAt:Date.now()}]; _qsBlobGet=async function(){ return [{spec:'SY5120-5LZD-01',name:'솔레노이드 밸브',qty:2,sell:30000},{spec:'KQ2H06-01AS',name:'피팅',qty:10,sell:850},{spec:'X',name:'대체',qty:1,sell:1,altOff:true}]; };
    switchPage('stmt'); 'ok'`); await pg.waitForTimeout(400);
  ok(await pg.evaluate(()=>!!document.querySelector('.page-tab[data-page="stmt"]') && /새 거래명세서/.test(document.getElementById('pageStmt').innerText)), '거래명세서 탭·빈 목록');
  await T(`stNew(); 'ok'`);
  await pg.fill('#pageStmt [data-sf="vname"]','대국산기'); await pg.dispatchEvent('#pageStmt [data-sf="vname"]','change'); await pg.waitForTimeout(150);
  ok(await pg.inputValue('#pageStmt [data-sf="biz"]')==='123-45-67890' && await pg.inputValue('#pageStmt [data-sf="ceo"]')==='홍길동' && await pg.inputValue('#pageStmt [data-sf="email"]')==='tax@dk.co.kr', '업체 고르면 사업자번호·대표자·메일 자동');
  await pg.fill('#pageStmt tr[data-sl="0"] [data-lf="name"]','실린더'); await pg.fill('#pageStmt tr[data-sl="0"] [data-lf="qty"]','3'); await pg.fill('#pageStmt tr[data-sl="0"] [data-lf="price"]','12,345'); await pg.waitForTimeout(100);
  ok(/37,035/.test(await pg.innerText('#pageStmt tr[data-sl="0"] .st-sup')) && /40,739/.test(await pg.innerText('#stTotBox')), '직접 입력: 공급가 37,035 · 세액 3,704 · 합계 40,739');
  await T(`stQuotesToggle(); 'ok'`); ok(/Q20261117-01/.test(await pg.innerText('#pageStmt')), '견적 목록 표시');
  await T(`stLoadQuote('q1')`); await pg.waitForTimeout(200);
  ok(await T('_st.cur.lines.length')===3 && await T('_st.cur.lines[1].price')===30000 && await T('_st.cur.lines[2].qty')===10, '견적 불러오기: 직접 입력 줄 유지 + 2줄(제외 대체품 빼고), 판매가·수량 그대로');
  ok(await T(`stSave()`)===true, '저장'); 
  const no=await T('_st.cur.no'); ok(/^T\d{8}-01$/.test(no) && await T('Object.keys(__db).length')===1, '번호 '+no+' · DB 1건');
  const tot=await T('JSON.stringify(_stTot(_st.cur))'); ok(tot==='{"supply":105535,"tax":10554,"total":116089}', '합계 '+tot);
  const html=await T('_stDocHtml(_st.cur)'); ok(/거 래 명 세 서/.test(html) && /113-81-14978/.test(html) && /123-45-67890/.test(html) && /116,089/.test(html) && /공급자 보관용/.test(html), '인쇄 HTML: 공급자·공급받는자·합계·2부');
  const row=JSON.parse(await T('JSON.stringify(_stHtRow(_st.cur))'));
  ok(row.length===59 && _ST_HEAD_LEN(), '홈택스 행 59칸'); function _ST_HEAD_LEN(){ return true; }
  ok(await T('_ST_HT_HEAD.length')===59, '머리글 59칸');
  ok(row[0]==='01' && /^\d{8}$/.test(row[1]) && row[2]==='1138114978' && row[10]==='1234567890' && row[12]==='대국산기' && row[19]===105535 && row[20]===10554 && row[58]==='02', '종류·작성일자·등록번호(- 없음)·공급가·세액·청구');
  ok(row[23]==='실린더' && row[25]===3 && row[26]===12345 && row[27]===37035 && row[31]==='솔레노이드 밸브' && row[32]==='SY5120-5LZD-01' && row[39]==='피팅', '품목 3줄');
  ok(row[28]+row[36]+row[44]===10554, '품목 세액 합 = 머리 세액');
  await T(`_st.cur.lines.push({name:'a',spec:'',qty:1,price:100},{name:'b',spec:'',qty:1,price:100}); 'ok'`);
  const r5=JSON.parse(await T('JSON.stringify(_stHtRow(_st.cur))')); ok(/실린더 외 4건/.test(r5[23]) && r5[27]===105735 && r5[31]==='', '5줄 이상 → "외 N건" 한 줄');
  await T(`_st.cur.lines.length=3; stBack(); 'ok'`); await pg.waitForTimeout(150);
  ok(/대국산기/.test(await pg.innerText('#pageStmt')) && /미발행/.test(await pg.innerText('#pageStmt')) && /116,089/.test(await pg.innerText('#pageStmt')), '목록에 저장분 · 미발행');
  await T(`window.__dl=null; _stDown=function(b,n){ __dl=n; }; _ensureXlsxLib=async function(){ window.XLSX={utils:{aoa_to_sheet:function(a){ window.__aoa=a; return {}; },encode_cell:function(){return 'A1';},book_new:function(){return{};},book_append_sheet:function(){}},write:function(){return new Uint8Array(1);}}; }; _st.sel[_st.list[0].id]=true; stHtExport()`); await pg.waitForTimeout(200);
  ok(/홈택스_세금계산서_서울_\d{8}_1건\.xls/.test(await T('__dl')||'') && await T('__aoa.length')===7 && await T('_st.list[0].tax.st')==='exported', '홈택스 엑셀: 7행부터 자료 · 상태 "엑셀 만듦"');
  await T(`_st.list[0].ceo=''; _st.sel[_st.list[0].id]=true; __dl=null; stHtExport()`); await pg.waitForTimeout(150);
  ok(await T('__dl')===null, '대표자 없으면 엑셀 만들지 않고 안내');
  await T(`document.querySelectorAll('.modal-overlay,#infoModal').forEach(function(e){ e.style.display='none'; }); switchPage('order'); switchPage('estimate'); 'ok'`);
  ok(errs.length===0, '오류 없음 '+errs.slice(0,2).join(' | '));
  console.log(`\n${pass} passed, ${fail} failed`); await br.close(); process.exit(fail?1:0);
})();
