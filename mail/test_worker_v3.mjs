// mail/worker.js v3 의 /wmis/* 가짜 WMIS 테스트. 실행: sed "s#import { connect } from 'cloudflare:sockets';#const connect=()=>{};#" worker.js > mw.mjs && node test_worker_v3.mjs
import W from './mw.mjs';
let pass=0, fail=0; const ok=(c,m)=>{ if(c){pass++;console.log('  ✓',m);} else {fail++;console.log('  ✗',m);} };
const log=[]; let saved=null; let loginOk=true;
globalThis.fetch = async (url, opt={}) => {
  const u=new URL(url); const p=u.pathname; const ck=(opt.headers&&opt.headers.Cookie)||'';
  log.push({p, m:opt.method||'GET', ck, q:Object.fromEntries(u.searchParams)});
  const J=(o,st=200,h={})=>new Response(JSON.stringify(o),{status:st,headers:Object.assign({'content-type':'application/json'},h)});
  if(p==='/a09/w/login') return new Response('<html>login</html>',{status:200,headers:{'set-cookie':'JSESSIONID=AAA; Path=/; HttpOnly'}});
  if(p==='/a09/w/login/process'){ const b=new URLSearchParams(opt.body); if(!loginOk||b.get('password')!=='pw') return new Response('',{status:401}); return J({tabYn:'N'},200,{'set-cookie':'JSESSIONID=BBB; Path=/'}); }
  if(!ck.includes('JSESSIONID=BBB')) return new Response('stub',{status:200});
  if(p==='/a09/w/main') return new Response("x $.each('{userId=S0757, userName=충해전기(주), compCode=A000000001, compName=에이앤에이사업부, orgCode=1}'.replace(/{/g, '')",{status:200});
  if(p==='/a09/w/agt/stockQ/selectGridStockQ3'){ const k=u.searchParams.get('keyword');
    if(k==='SY5120-5LZD-01') return J([{makerCd:'091',makerName:'SMC',itemCd:'SMC000216197',itemName:'SY5120-5LZD-01',unitPrice:38810,storeAma00:3,storeAmc02:0,storeAmc00:1,storeAmd00:0,sumQty:4}]);
    if(k==='SY5120') return J([{itemCd:'C1',itemName:'SY5120-5LZD-01',unitPrice:1,makerName:'SMC'},{itemCd:'C2',itemName:'SY5120-5LZD-02',unitPrice:2,makerName:'SMC'}]);
    return J([]); }
  if(p==='/a09/w/agt/saleOrdE/getCustDeliveryInfo') return J({deliType:'충해전기',deliCmpy:'구로정기배송',deliPlace:'서울 구로',deliTel:'010-0000-0000'});
  if(p==='/a09/w/agt/saleOrdE/selectMajorStoreCd') return new Response('MA001',{status:200});
  if(p==='/a09/w/agt/saleOrdE/WSP_QR_WCA01MP_7') return J([{credLimit:1000000,thisOrderAmt:0,credAmtSum:100,thisBillSelf:0,credAmtThis:1,credAmt1:2,credAmt2:3,credAmt3:4,bill75:0,bill50:0,bill25:0,bill0:0}]);
  if(p==='/a09/w/agt/saleOrdE/WSP_QR_WZA01MP_5') return J([{BEFR_OUT_QTY:0,CONT_PRICE:0,STD_PRICE:0,UNIT_PRICE:0,CUST_TYPE_UNIT_PRICE:38810,STOCK:0,ITEM_NAME:'SY5120-5LZD-01'}]);
  if(p==='/a09/w/agt/saleOrdE/WSP_QR_WZA01MP_43') return J({p_RTN_CUSTTYPE_PRICE:'38810',p_RTN_CONT_PRICE:'0',p_RTN_UNIT_PRICE:'0'});
  if(p==='/a09/w/agt/saleOrdE/saveCustOrderInfo'){ saved=JSON.parse(opt.body); return J({errChk:'OK',CUST_ORDER_NO:'SO2611120001',CUST_ORDER_NO_SEQ:'1'}); }
  return new Response('nf',{status:404});
};
const env={MAIL_KEY:'k1'}; const CRED={id:'S0757',pw:'pw'};
const call=async(path,body,key='k1',cred=CRED)=>{ const r=await W.fetch(new Request('https://w.test/wmis'+path,{method:'POST',headers:{'X-Mail-Key':key,'Content-Type':'application/json'},body:JSON.stringify(Object.assign({cred},body||{}))}), env); return [r.status, await r.json(), r.headers.get('access-control-allow-origin')]; };
let [st,j,ao]=await call('/ping',null,'bad'); ok(st===401,'열쇠 틀리면 401');
[st,j,ao]=await call('/ping'); ok(st===200&&j.ok&&j.user==='S0***'&&j.deliv.deliCmpy==='구로정기배송','ping: 로그인·기본 배송지'); ok(ao==='https://chunghae.github.io','CORS origin');
ok(!JSON.stringify(j).includes('pw'),'응답에 비밀번호 없음');
[st,j]=await call('/lookup',{items:[{pn:'SY5120-5LZD-01',qty:2},{pn:'SY5120',qty:1},{pn:'XX',qty:1}]});
ok(j.items[0].found&&j.items[0].code==='SMC000216197'&&j.items[0].price===38810&&j.items[0].stock['서울']===3&&j.items[0].stock['부산']===1,'lookup 정확 일치 + 재고 지점명');
ok(!j.items[1].found&&j.items[1].cands.length===2,'부분 일치는 후보로'); ok(!j.items[2].found&&j.items[2].cands.length===0,'없음');
ok(j.deliv&&j.deliv.deliType==='충해전기','lookup 에 기본 배송지');
[st,j]=await call('/order',{deli:{type:'충해전기 화성영업소',cmpy:'택배',addr:'화성 팔탄',tel:'031-352-4475'},deliDate:'2026-11-13',remk:'충해 Q1',items:[{code:'SMC000216197',qty:2,pn:'SY5120-5LZD-01'}],dryRun:true});
ok(j.dryRun&&j.payload.deliDate==='20261113'&&j.payload.grid.length===1&&!saved,'dryRun 은 저장 안 함');
[st,j]=await call('/order',{deli:{type:'충해전기 화성영업소',cmpy:'택배',addr:'화성 팔탄',tel:'031-352-4475'},deliDate:'2026-11-13',remk:'충해 Q1',items:[{code:'SMC000216197',qty:2,pn:'SY5120-5LZD-01'}]});
ok(j.ok&&j.orderNo==='SO2611120001','저장 → 주문번호');
ok(saved&&saved.CUST_ID==='S0757'&&saved.CUST_ORDER_NO===undefined&&saved.deliType==='충해전기 화성영업소'&&saved.deliCmpy==='택배'&&saved.deliPlace==='화성 팔탄','폼: 신규·배송지');
ok(/^\d{8}$/.test(saved.orderDate)&&saved.deliDate==='20261113','날짜 YYYYMMDD');
const g=saved.grid[0]; ok(g.ITEM_CD==='SMC000216197'&&g.ORDR_QTY==='2'&&g.CUST_TYPE_UNIT_PRICE==='38810'&&g.check==='false'&&g.SALE_PRICE==='0','그리드 줄 = 화면과 같은 값');
ok(Object.keys(saved).length>=25,'폼 키 ('+Object.keys(saved).length+')');
saved=null; [st,j]=await call('/order',{deli:{},deliDate:'2026-11-13',items:[{code:'A',qty:1},{code:'A',qty:2}]}); ok(!j.ok&&!saved,'중복 코드 거부');
[st,j]=await call('/order',{deli:{},deliDate:'2026-11-13',items:[{code:'SMC000216197',qty:1}],remk:''}); ok(j.ok&&saved.deliType==='충해전기'&&saved.deliCmpy==='구로정기배송','배송지 비우면 대성 기본값');
[st,j]=await call('/ping',null,'k1',{id:'',pw:''}); ok(st===400&&/아이디/.test(j.error),'아이디 없으면 안내'); loginOk=false; [st,j]=await call('/ping'); ok(st===502&&/로그인 실패/.test(j.error),'로그인 실패 안내');
ok(log.filter(x=>x.p==='/a09/w/login/process').length>=5,'요청마다 새로 로그인'); { const r=await W.fetch(new Request('https://w.test/ping'),{MAIL_KEY:'k1',SMTP_USER:'chjk@chjk.co.kr'}); const jj=await r.json(); ok(jj.ok&&jj.user==='ch***@chjk.co.kr','기존 메일 /ping 그대로'); } loginOk=true; { const r=await W.fetch(new Request('https://w.test/wmis/ping',{method:'POST',headers:{'X-Mail-Key':'k1'},body:JSON.stringify({cred:{id:'x',pw:'y'}})}),{MAIL_KEY:'k1',WMIS_ID:'S0757',WMIS_PW:'pw'}); const jj=await r.json(); ok(jj.ok,'Worker 변수 WMIS_ID/PW 가 있으면 그것 우선'); }
console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail?1:0);
