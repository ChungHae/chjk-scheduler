// 충해전기 사내전산 — 대성산업 WMIS 발주 중계 Worker (Cloudflare Workers)  v1 (r266, 2026-11-12)
// 사내전산(chunghae.github.io/chjk-scheduler) 견적 화면의 [대성 발주] 가 이 Worker 를 부르면
// Worker 가 대성 WMIS(customer.wmis.co.kr) 에 대리점 계정으로 로그인해 품번 조회·발주 저장을 대신 한다.
//
// 설정(Workers 대시보드 > Settings > Variables and Secrets — 셋 다 'Secret'):
//   WMIS_ID   = 대성 WMIS 아이디
//   WMIS_PW   = 대성 WMIS 비밀번호
//   WMIS_KEY  = 사내전산이 부를 때 붙이는 열쇠 (아무 긴 문자열 — 사내전산 [대성 설정]에 같은 값을 넣는다)
//   ALLOW_ORIGIN (선택, 기본 https://chunghae.github.io)
//
// 요청 (모두 헤더 X-Wmis-Key: <WMIS_KEY>)
//   GET  /ping                       → { ok, user:"S0***", cust:"…", deliv:{…} }  (실제 로그인까지 시험)
//   POST /lookup {items:[{pn,qty}]}  → { ok, items:[{pn, found, code, name, price, stock:{…}, cands:[…]}] }
//   POST /order  {deli:{…}, deliDate, remk, items:[{code,qty,pn}], dryRun}
//                                    → { ok, orderNo, status, errChk }   dryRun 이면 보낼 내용만 돌려줌
// 비밀번호는 이 Worker 의 보안 비밀에만 있다. 응답·로그 어디에도 내보내지 않는다.

const BASE = 'https://customer.wmis.co.kr';
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36';

export default {
  async fetch(request, env) {
    const origin = env.ALLOW_ORIGIN || 'https://chunghae.github.io';
    const cors = {
      'Access-Control-Allow-Origin': origin,
      'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, X-Wmis-Key',
      'Access-Control-Max-Age': '86400',
    };
    const json = (obj, status) => new Response(JSON.stringify(obj), { status: status || 200, headers: Object.assign({ 'Content-Type': 'application/json; charset=utf-8' }, cors) });
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    const url = new URL(request.url);
    if (!env.WMIS_KEY || request.headers.get('X-Wmis-Key') !== env.WMIS_KEY) return json({ ok: false, error: '열쇠(X-Wmis-Key)가 맞지 않습니다' }, 401);
    if (!env.WMIS_ID || !env.WMIS_PW) return json({ ok: false, error: 'Worker 에 WMIS_ID / WMIS_PW 가 설정되지 않았습니다' }, 500);
    try {
      const s = await wmisLogin(env);
      if (request.method === 'GET' && url.pathname === '/ping') {
        const deliv = await getDeliv(s).catch(() => null);
        return json({ ok: true, user: mask(env.WMIS_ID), cust: s.sess.custName || s.sess.custId || '', deliv });
      }
      if (request.method !== 'POST') return json({ ok: false, error: 'not found' }, 404);
      let body; try { body = await request.json(); } catch (e) { return json({ ok: false, error: 'JSON 본문이 아닙니다' }, 400); }
      if (url.pathname === '/lookup') return json(await doLookup(s, body));
      if (url.pathname === '/order') return json(await doOrder(s, body));
      return json({ ok: false, error: 'not found' }, 404);
    } catch (e) {
      return json({ ok: false, error: String(e && e.message || e) }, 502);
    }
  },
};

function mask(u) { u = String(u || ''); return u.length > 2 ? u.slice(0, 2) + '***' : '***'; }

// ── 세션: 요청마다 새로 로그인 (WMIS 세션이 짧고, 다른 곳 로그인과 엉키지 않게) ──
async function wmisLogin(env) {
  const jar = {};
  const s = { jar, sess: {} };
  await req(s, '/a09/w/login', { method: 'GET' });                         // JSESSIONID 받기
  const r = await req(s, '/a09/w/login/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json, text/javascript, */*; q=0.01' },
    body: new URLSearchParams({ userid: env.WMIS_ID, password: env.WMIS_PW }).toString(),
  });
  if (r.status === 401) throw new Error('대성 로그인 실패 — Worker 의 WMIS_ID / WMIS_PW 를 확인하세요');
  if (!r.ok) throw new Error('대성 로그인 응답 이상 (HTTP ' + r.status + ')');
  const main = await req(s, '/a09/w/main', { method: 'GET' });
  s.sess = parseSession(await main.text());
  if (!s.sess.compCode) throw new Error('대성 로그인 뒤 세션 정보를 읽지 못했습니다');
  return s;
}
// 페이지에 박힌 '{compCode=A000000001, custId=…, …}' 를 읽는다
function parseSession(html) {
  const m = html.match(/\$\.each\('\{([^']*)\}'\.replace/) || html.match(/'\{(compCode=[^']*)\}'/);
  const o = {};
  if (!m) return o;
  m[1].split(',').forEach(kv => { const i = kv.indexOf('='); if (i > 0) o[kv.slice(0, i).replace(/\s/g, '')] = kv.slice(i + 1).trim(); });
  return o;
}
async function req(s, path, opt) {
  const h = Object.assign({ 'User-Agent': UA, 'Referer': BASE + '/a09/w/main' }, opt.headers || {});
  const ck = Object.keys(s.jar).map(k => k + '=' + s.jar[k]).join('; ');
  if (ck) h['Cookie'] = ck;
  const r = await fetch(BASE + path, { method: opt.method || 'GET', headers: h, body: opt.body, redirect: 'manual' });
  const sc = r.headers.getSetCookie ? r.headers.getSetCookie() : (r.headers.get('set-cookie') ? [r.headers.get('set-cookie')] : []);
  sc.forEach(c => { const p = String(c).split(';')[0]; const i = p.indexOf('='); if (i > 0) s.jar[p.slice(0, i).trim()] = p.slice(i + 1).trim(); });
  return r;
}
async function getJson(s, path, params) {
  const q = params ? ('?' + new URLSearchParams(params).toString()) : '';
  const r = await req(s, path + q, { method: 'GET', headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json' } });
  if (!r.ok) throw new Error('대성 조회 실패 ' + path + ' (HTTP ' + r.status + ')');
  return r.json();
}
async function postJson(s, path, obj) {
  const r = await req(s, path, { method: 'POST', headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json; charset=UTF-8' }, body: JSON.stringify(obj) });
  const t = await r.text();
  if (!r.ok) throw new Error('대성 저장 실패 (HTTP ' + r.status + ') ' + t.slice(0, 200));
  try { return JSON.parse(t); } catch (e) { return { raw: t.slice(0, 500) }; }
}

// ── 이하 조회·발주 (WMIS 화면 로직 그대로) ──
const STORE_NAMES = { storeAma00: '서울', storeAmc02: 'BDC', storeAmc00: '부산', storeAmd00: '대구' };
const normPn = x => String(x || '').toUpperCase().replace(/[\s\-_.\/]/g, '');
function stockOf(r) { const o = {}; Object.keys(STORE_NAMES).forEach(k => { if (r[k] != null) o[STORE_NAMES[k]] = Number(r[k]) || 0; }); return o; }
async function searchItem(s, pn) {
  const rows = await getJson(s, '/a09/w/agt/stockQ/selectGridStockQ3', { compCode: s.sess.compCode, searchType: 'itemName', keyword: pn, stockYn: '%', langCode: 'ko', makerCd: '%' });
  return Array.isArray(rows) ? rows : [];
}
// 품번 → 대성 상품코드·대리점가·재고. 품명(itemName)이 품번과 정확히 같은 것만 '찾음', 나머지는 후보로.
async function doLookup(s, body) {
  const items = (Array.isArray(body.items) ? body.items : []).slice(0, 80);
  const out = [];
  for (const it of items) {
    const pn = String(it && it.pn || '').trim();
    if (!pn) { out.push({ pn, found: false, cands: [] }); continue; }
    let rows = [];
    try { rows = await searchItem(s, pn); } catch (e) { out.push({ pn, found: false, error: String(e.message || e), cands: [] }); continue; }
    const key = normPn(pn);
    const hit = rows.find(r => normPn(r.itemName) === key) || rows.find(r => normPn(r.itemCd) === key);
    const conv = r => ({ code: r.itemCd, pn: r.itemName, name: r.makerName || '', price: Number(r.unitPrice) || 0, stock: stockOf(r) });
    if (hit) out.push(Object.assign({ pn, found: true }, conv(hit), { name: hit.makerName || '' }));
    else out.push({ pn, found: false, cands: rows.slice(0, 5).map(conv) });
  }
  const deliv = await getDeliv(s).catch(() => null);
  return { ok: true, items: out, deliv };
}
async function getDeliv(s) {
  return getJson(s, '/a09/w/agt/saleOrdE/getCustDeliveryInfo', { custId: s.sess.userId });
}
const ymd = d => String(d || '').replace(/[^0-9]/g, '').slice(0, 8);
function todayKst() { const d = new Date(Date.now() + 9 * 3600000); return d.toISOString().slice(0, 10).replace(/-/g, ''); }
// 발주 저장 — WMIS 주문등록 화면의 addMain(신규) → popRefGoodsCallback(상품 추가) → calcAmount(금액 계산) → saveMain(저장) 과 같은 값을 만든다.
async function doOrder(s, body) {
  const cust = s.sess.userId;
  const items = (Array.isArray(body.items) ? body.items : []).filter(x => x && x.code && Number(x.qty) > 0);
  if (!items.length) throw new Error('발주할 품목이 없습니다');
  if (items.length > 60) throw new Error('한 번에 60품목까지만 발주할 수 있습니다');
  const seen = {}; for (const x of items) { if (seen[x.code]) throw new Error('같은 상품코드가 두 번 있습니다: ' + x.code); seen[x.code] = 1; }
  const deliDate = ymd(body.deliDate); if (deliDate.length !== 8) throw new Error('납품요청일이 이상합니다');
  const def = await getDeliv(s).catch(() => ({}));
  const d = body.deli || {};
  const storeR = await req(s, '/a09/w/agt/saleOrdE/selectMajorStoreCd?' + new URLSearchParams({ p_CUST_ID: cust }), { method: 'GET', headers: { 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/json' } });
  const store = (await storeR.text()).trim();
  let cred = {};
  try { const c = await getJson(s, '/a09/w/agt/saleOrdE/WSP_QR_WCA01MP_7', { custId: cust }); if (Array.isArray(c) && c.length === 1) cred = c[0]; } catch (e) {}
  const grid = []; let sumAmt = 0;
  for (const x of items) {
    const qty = Math.floor(Number(x.qty));
    const r5 = await getJson(s, '/a09/w/agt/saleOrdE/WSP_QR_WZA01MP_5', { p_CUST_ID: cust, p_ITEM_CD: x.code, p_STORE_CD: store });
    const b = Array.isArray(r5) ? r5[0] : null;
    if (!b || !b.ITEM_NAME) throw new Error('대성에서 상품을 찾지 못했습니다: ' + (x.pn || x.code));
    const r43 = await getJson(s, '/a09/w/agt/saleOrdE/WSP_QR_WZA01MP_43', { p_CUST_ID: cust, p_ITEM_CD: x.code, p_ORDR_QTY: qty, p_UNIT_PRICE: b.UNIT_PRICE });
    const unit = Number(b.UNIT_PRICE) || 0, ctp = Number(r43.p_RTN_CUSTTYPE_PRICE) || 0, std = Number(r43.p_RTN_UNIT_PRICE) || 0;
    const sale = qty * unit, vat = Math.floor(sale * 0.1), sum = Number((sale + vat).toFixed(0));
    sumAmt += sum;
    const rate = ctp === 0 ? (std === 0 ? '' : Number((unit / std * 100).toFixed(0))) : Number((unit / ctp * 100).toFixed(0));
    // 화면: addRows(상품 추가) → 수량 입력 → calcAmount 뒤 getGridDataAll(true) 와 같은 줄
    grid.push({ check: 'false', ITEM_CD: x.code, ITEM_NAME: b.ITEM_NAME, ORDR_QTY: String(qty), LIMIT_QTY: 0,
      CUST_TYPE_UNIT_PRICE: String(r43.p_RTN_CUSTTYPE_PRICE), STD_PRICE: String(r43.p_RTN_UNIT_PRICE), CONT_PRICE: String(r43.p_RTN_CONT_PRICE), UNIT_PRICE: b.UNIT_PRICE,
      SALE_PRICE: String(sale), VAT_AMT: String(vat), STOCK: b.STOCK, BEFR_OUT_QTY: b.BEFR_OUT_QTY,
      AVAIL_QTY: '0', EXPT_UNIT_PRICE: '0', SALE_RATE: String(rate === '' ? 0 : rate), SUM_PRICE: String(sum), CUST_RQST_NO: '', CUST_RQST_YN: '' });
  }
  const credTotal = Number(cred.credAmtSum || 0) + Number(cred.thisBillSelf || 0) + Number(cred.bill75 || 0) * 0.75 + Number(cred.bill50 || 0) * 0.5 + Number(cred.bill25 || 0) * 0.25;
  const over = credTotal + Number(cred.thisOrderAamt || 0) - Number(cred.credLimit || 0);
  // 화면의 $.fnGetGroupData(...Save) 와 같은 모양: 빈 칸(새 주문의 주문번호·상태·담당 등)은 아예 보내지 않는다(JSON.stringify 가 undefined 를 뺌)
  const hasCred = cred.credLimit != null;
  const form = {
    CUST_ID: cust, CUST_NAME: s.sess.userName || undefined,
    OUT_AMT: '0', SUM_ORDR_AMT: sumAmt,
    deliType: String(d.type || def.deliType || '').slice(0, 100), deliCmpy: String(d.cmpy != null && d.cmpy !== '' ? d.cmpy : (def.deliCmpy || '')).slice(0, 100),
    deliPlace: String(d.addr || def.deliPlace || '').slice(0, 200), deliTel: String(d.tel || def.deliTel || '').slice(0, 40),
    remk: String(body.remk || '').slice(0, 300) || undefined,
    CUST_LIMIT_AMT: hasCred ? cred.credLimit : undefined, ORDR_CRED: hasCred ? cred.thisOrderAmt : undefined,
    TOTAL_CRED_AMT: hasCred ? credTotal.toFixed(0) : undefined, CRED_AMT: hasCred ? cred.credAmtSum : undefined,
    BEFR_0_AR: cred.credAmtThis, BEFR_1_AR: cred.credAmt1, BEFR_2_AR: cred.credAmt2, BEFR_3_AR: cred.credAmt3,
    OWNS_BILL: cred.thisBillSelf, BILL_75: cred.bill75, BILL_50: cred.bill50, BILL_25: cred.bill25, BILL_0: cred.bill0,
    CUST_OVER_YN: 'N', OVER_LIMIT_BEFR: hasCred ? Number(credTotal.toFixed(0)) + Number(cred.thisOrderAmt || 0) - Number(cred.credLimit || 0) : undefined,
    orderDate: todayKst(), deliDate,
    grid,
  };
  if (body.dryRun) return { ok: true, dryRun: true, payload: form, overLimit: over > 0 };
  const res = await postJson(s, '/a09/w/agt/saleOrdE/saveCustOrderInfo', form);
  const ec = res && res.errChk;
  if (ec === 'OK') return { ok: true, orderNo: res.CUST_ORDER_NO || '', seq: res.CUST_ORDER_NO_SEQ || '', sum: sumAmt, overLimit: over > 0 };
  if (ec === 'EMPTY') throw new Error('대성: 등록된 영업담당자가 없습니다 — 대성 영업담당자에게 문의');
  throw new Error('대성 저장 응답: ' + (ec || JSON.stringify(res).slice(0, 200)));
}
