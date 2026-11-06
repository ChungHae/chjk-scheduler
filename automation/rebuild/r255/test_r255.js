// r255 테스트 — 브랜드 추천 · 담당자 칩 · 문의 메일 발송(replyTo/cc) · 문의함 · 엑셀 합치기
const { chromium } = require('/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const file = path.resolve(process.argv[2] || 'd255/test/index.html');
let pass=0, fail=0; function ok(c,m){ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} }
(async()=>{
  const src=fs.readFileSync(file,'utf8').replace('  function _vacUnlimited(id){','window._xlsxStyleReady=true; window.__T=function(c){return eval(c);}; function _vacUnlimited(id){');
  const tmp=path.join(path.dirname(file),'_h_r255.html'); fs.writeFileSync(tmp,src);
  const br=await chromium.launch(); const pg=await br.newPage({viewport:{width:1400,height:900}}); const errs=[]; pg.on('pageerror',e=>errs.push(String(e)));
  const sent=[];
  await pg.route('**/*', async r=>{ const u=r.request().url(); if(u.startsWith('file://')) return r.continue();
    if(u.startsWith('https://w.test/send')){ sent.push(JSON.parse(r.request().postData())); return r.fulfill({status:200,contentType:'application/json',body:'{"ok":true}'}); }
    return r.abort(); });
  await pg.goto('file://'+tmp); await pg.waitForTimeout(3000);
  await pg.evaluate(()=>{ document.getElementById('authGate').style.display='none'; });
  const T=c=>pg.evaluate(c2=>window.__T(c2),c);
  await T(`_authUser={id:'kjs',name:'김재성',role:'admin'}; members=[{id:'m1',name:'김재성',group:'서울',phone:'010-0000-0000'}]; debouncedFbSave=function(){}; window.__saved=0; saveAll=function(){ window.__saved++; }; window.__info=[]; showInfoModal=function(t,m){ window.__info.push(t+'|'+m); };
    _mailLoadCfg=async function(){ return {url:'https://w.test', key:'k1'}; };
    purchaseVendors=[ {id:'v1',brand:'CKD',distributor:'이나코퍼레이션',contacts:[{role:'과장',name:'김동형',phone:'',email:'kim@ina.test'}]},
      {id:'v2',brand:'FESTO',distributor:'다스코리아',contacts:[{role:'',name:'박태준',phone:'',email:'tj@das.test'},{role:'',name:'이한범',phone:'',email:'hb@das.test'}]},
      {id:'v3',brand:'FESTO',distributor:'한국훼스토',contacts:[{role:'',name:'',phone:'',email:'sales@festo.test'}]},
      {id:'v4',brand:'PISCO',distributor:'유니온테크',keywords:'피스코',contacts:[{role:'',name:'유니온',phone:'',email:'uvf@uvf.test'}]} ];
    pvInq=[]; 'ok'`);

  console.log('▶ 1) 브랜드 추천');
  ok(await T(`_pvGuessBrand('4F720-15-AC220V')`)==='CKD', 'CKD 4F → CKD');
  ok(await T(`_pvGuessBrand('DSNU-20-50-PPV-A')`)==='FESTO', 'FESTO DSNU');
  ok(await T(`_pvGuessBrand('PC6-01')`)==='PISCO', 'PISCO PC6');
  ok(await T(`_pvGuessBrand('SY5120-5LZD-01')`)==='', 'SMC 품번은 추천 없음');
  ok(await T(`_pvResolveBrand('피스코')`)==='PISCO', '별칭(검색어) → 등록 브랜드');

  console.log('▶ 2) 견적 목록에서 문의 창');
  await T(`_qCart=[{vname:'㈜테스트',spec:'4F720-15-AC220V',name:'솔레노이드밸브',qty:3},{vname:'㈜테스트',spec:'4K210-08',name:'',qty:2},{vname:'㈜테스트',spec:'',name:'',qty:1}]; _qQuoteNo='테스트-20261106-01'; pvInqOpen({fromCart:true}); 'ok'`);
  await pg.waitForTimeout(200);
  ok(await pg.evaluate(()=>document.getElementById('pvInqOverlay').style.display==='flex'), '문의 창 열림');
  ok(await T(`window._pvq.items.length`)===2, '품번 있는 줄만 2건');
  ok(await T(`window._pvq.brand`)==='CKD' && await pg.evaluate(()=>document.getElementById('pvqBrand').value==='CKD'), '브랜드 CKD 자동 선택');
  ok(await pg.evaluate(()=>document.querySelectorAll('#pvInqOverlay .ml-chip').length)===1, 'CKD 담당자 칩 1개');
  ok(await T(`window._pvq.to.join()`)==='kim@ina.test', '대리점이 하나면 담당자 자동 받는 사람');
  const subj=await pg.evaluate(()=>document.getElementById('pvqSubj').value);
  ok(/^\[충해전기\] CKD 견적 · 납기 문의 — 4F720-15-AC220V 외 1건 \[CHJK-Q\d{6}-01\]$/.test(subj), '제목: '+subj);
  const body=await pg.evaluate(()=>document.getElementById('pvqBody').value);
  ok(body.indexOf('이나코퍼레이션 김동형 님, 안녕하세요.')===0 && body.indexOf('1. 4F720-15-AC220V — 솔레노이드밸브  × 3')>0 && body.indexOf('2. 4K210-08  × 2')>0, '본문: 인사·품번 줄');
  ok(body.indexOf('김재성 · 010-0000-0000')>0, '본문 서명에 직원 이름·전화');

  console.log('▶ 3) 브랜드 바꾸면 칩·받는 사람 갱신');
  await T(`pvqBrand('FESTO'); 'ok'`);
  ok(await pg.evaluate(()=>document.querySelectorAll('#pvInqOverlay .ml-chip').length)===3, 'FESTO 담당자 칩 3개(두 대리점)');
  ok(await T(`window._pvq.to.length`)===0, '대리점 둘 이상이면 받는 사람 비움');
  await T(`pvqChip(0); pvqChip(2); 'ok'`);
  ok(await T(`window._pvq.to.join()`)==='tj@das.test,sales@festo.test', '칩 눌러 받는 사람 2명');
  ok(await pg.evaluate(()=>document.getElementById('pvqTo').value)==='tj@das.test, sales@festo.test', '받는 사람 칸 반영');
  await T(`pvqChip(0); 'ok'`); ok(await T(`window._pvq.to.join()`)==='sales@festo.test', '칩 다시 누르면 빠짐');
  await T(`pvqMy('kjs@chjk.co.kr'); 'ok'`);
  ok(await T(`window._pvq.cc`)==='kjs@chjk.co.kr', '내 메일 적으면 참조에도');

  console.log('▶ 4) 보내기 → Worker 호출 · 문의함 기록');
  await pg.evaluate(()=>{ document.getElementById('pvqDue').value='11/20 까지'; document.getElementById('pvqDue').dispatchEvent(new Event('change')); });
  await T(`pvqKind('alt', true); 'ok'`);
  await T(`pvInqSend()`); await pg.waitForTimeout(500);
  ok(sent.length===1, 'Worker /send 1회 호출');
  const m=sent[0]||{};
  ok(m.to==='sales@festo.test' && m.cc==='kjs@chjk.co.kr' && m.replyTo==='kjs@chjk.co.kr', 'to/cc/replyTo 정확: '+JSON.stringify([m.to,m.cc,m.replyTo]));
  ok(m.account==='seoul' && /^충해전기.{0,3} 김재성$/.test(m.fromName), '계정 seoul · 보내는 이름');
  ok(/견적 · 납기 · 대체품 문의/.test(m.subject), '제목에 문의 종류 반영: '+m.subject);
  ok(/희망 납기: 11\/20 까지/.test(m.text), '본문에 희망 납기');
  ok(/<table/.test(m.html) && m.html.indexOf('4F720-15-AC220V')>0 && !/1\. 4F720/.test(m.html), 'HTML 본문은 품번 표');
  ok(await T(`pvInq.length`)===1 && await T(`pvInq[0].status`)==='wait' && await T(`pvInq[0].quoteNo`)==='테스트-20261106-01', '문의함에 대기 기록 + 견적번호');
  ok(await T(`members[0].email`)==='kjs@chjk.co.kr', '내 메일을 팀원 정보에 기억');
  ok(await pg.evaluate(()=>document.getElementById('pvInqOverlay').style.display==='none'), '창 닫힘');
  ok(await T(`window.__info[window.__info.length-1]`).then(s=>/문의 발송 완료/.test(s)), '완료 안내');

  console.log('▶ 5) 문의함');
  await T(`pvInqBox(); 'ok'`); await pg.waitForTimeout(100);
  ok(await pg.evaluate(()=>document.querySelectorAll('#pvInqBoxOverlay .pvi-row').length)===1, '대기 1건 표시');
  await T(`pvInqSet(pvInq[0].id,'reply'); 'ok'`);
  ok(await T(`pvInq[0].status`)==='reply' && await pg.evaluate(()=>document.querySelectorAll('#pvInqBoxOverlay .pvi-row').length)===0, '회신 받음 → 대기 목록에서 빠짐');
  await T(`pvInqBox('all'); 'ok'`);
  ok(await pg.evaluate(()=>document.querySelectorAll('#pvInqBoxOverlay .pvi-row').length)===1, '전체 탭에는 보임');
  await T(`window._pvInqFilter='wait'; pvInqOpen({vendorId:'v4'}); 'ok'`);
  ok(await T(`window._pvq.brand`)==='PISCO' && await T(`window._pvq.to.join()`)==='uvf@uvf.test' && await T(`window._pvq.my`)==='kjs@chjk.co.kr', '매입처 카드에서 열면 브랜드·담당자·내 메일 채워짐');
  ok(await T(`window._pvq.no`)!==await T(`pvInq[0].no`), '문의번호 순번 증가');

  console.log('▶ 6) 엑셀 업로드 합치기');
  const r=await T(`JSON.stringify(_pvMergeEntries([{brand:'ckd',distributor:'이나코퍼레이션',email:'',contacts:[{role:'',name:'김동형',phone:'010-1',email:'kim@ina.test'},{role:'',name:'신규',phone:'',email:'new@ina.test'}]},{brand:'NITTA',distributor:'니타코리아',email:'rep@nitta.test',contacts:[{role:'',name:'배기덕',phone:'',email:'gd@nitta.test'}]}]))`);
  const rr=JSON.parse(r);
  ok(rr.added===1 && rr.merged===1 && rr.contacts===3, '추가 1 · 합침 1 · 담당자 3: '+r);
  ok(await T(`purchaseVendors[0].contacts.length`)===2 && await T(`purchaseVendors[0].contacts[0].phone`)==='010-1', '같은 메일 담당자는 합치고(전화 보강) 새 담당자만 추가');
  ok(await T(`purchaseVendors.length`)===5 && await T(`purchaseVendors[4].contacts.map(c=>c.email).join()`)==='gd@nitta.test,rep@nitta.test', 'NITTA 신규 + 대표 메일 담당자');

  console.log('▶ 7) 메뉴·툴바·카드');
  await T(`qOpenDlMenu && typeof qOpenDlMenu; 'ok'`).catch(()=>{});
  ok((await pg.evaluate(()=>document.body.innerHTML)).indexOf('pvInqOpen({fromCart:true})')>0, '견적 다운로드 메뉴에 [매입처에 문의 메일]');
  ok(await pg.evaluate(()=>!!document.getElementById('pvInqBoxBtn')), '매입처 툴바 문의함 버튼');
  await T(`renderPurchasePage(); 'ok'`);
  ok(await pg.evaluate(()=>document.querySelectorAll('#purchaseList .pv-mail-btn').length)===5, '카드마다 ✉ 문의 버튼');
  ok(await pg.evaluate(()=>document.querySelector('#pvInqBoxBtn .pvi-badge').style.display==='none'), '대기 0이면 뱃지 숨김');
  await T(`pvInq[0].status='wait'; renderPurchasePage(); 'ok'`);
  ok(await pg.evaluate(()=>document.querySelector('#pvInqBoxBtn .pvi-badge').textContent)==='1', '대기 1 → 뱃지 1');

  const realErrs=errs.filter(e=>!/net::|Failed to fetch|NetworkError|fb\.test|firebase|XLSX|cdnjs/.test(e));
  ok(realErrs.length===0, '페이지 오류 없음'+(realErrs.length?(' — '+realErrs.slice(0,3).join(' | ')):''));
  console.log(`\n결과: ${pass} 통과 / ${fail} 실패`);
  await br.close(); try{ fs.unlinkSync(tmp); }catch(e){}
  process.exit(fail?1:0);
})();
