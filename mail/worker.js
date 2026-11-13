// 충해전기 사내전산 — 메일 발송 + 대성산업 WMIS 발주 중계 Worker (Cloudflare Workers)  v3 (2026-11-13: /wmis/* 추가)
// v2 (2026-10-17: 서울·화성 발신 계정 2개)
// 사내전산(chunghae.github.io/chjk-scheduler) 의 [메일 보내기] 가 이 Worker 를 호출하면
// 네이버 웍스 SMTP(smtp.worksmobile.com) 로 서울(chjk@chjk.co.kr) 또는 화성(hs-chjk@chjk.co.kr) 계정에서 메일을 보낸다.
//
// 설정(Workers 대시보드 > 설정 > 변수 및 보안 비밀):
//   SMTP_USER     = chjk@chjk.co.kr              (보안 비밀) — 서울 발신 계정
//   SMTP_PASS     = 그 계정의 네이버 웍스 '외부 앱 비밀번호' (보안 비밀)
//   SMTP_USER_HS  = hs-chjk@chjk.co.kr           (보안 비밀) — 화성 발신 계정 (선택)
//   SMTP_PASS_HS  = 그 계정의 외부 앱 비밀번호     (보안 비밀)
//   MAIL_KEY      = 사내전산이 보낼 때 붙이는 열쇠 (보안 비밀, 아무 긴 문자열 — 사내전산 메일 설정에 같은 값을 넣는다)
//   SMTP_HOST / SMTP_PORT / SMTP_SECURE(on|starttls|off) / ALLOW_ORIGIN  (선택)
//
// 요청: POST /send  (헤더 X-Mail-Key: <MAIL_KEY>)
//   { "account":"seoul"|"hs",  "to":"a@b.com, c@d.com", "cc":"", "subject":"…", "text":"…", "html":"<p>…</p>",
//     "fromName":"충해전기㈜ 김재성", "replyTo":"",
//     "attachments":[ { "name":"견적서 X.pdf", "type":"application/pdf", "b64":"JVBERi0…" } ] }
//   account 가 없으면 seoul. hs 인데 SMTP_USER_HS 가 없으면 오류.
// 응답: { ok:true, id:"<message-id>", from:"hs-chjk@chjk.co.kr" }  /  { ok:false, error:"…" }
// ── v3 대성 WMIS (같은 열쇠 X-Mail-Key) ──
//   POST /wmis/ping   {cred:{id,pw}}                         → { ok, user, cust, deliv }  (실제 로그인 시험)
//   POST /wmis/lookup {cred, items:[{pn,qty}]}                → { ok, items:[…], deliv }
//   POST /wmis/order  {cred, deli, deliDate, remk, items:[{code,qty,pn}], dryRun?} → { ok, orderNo }
//   대성 아이디·비밀번호: Worker 변수 WMIS_ID / WMIS_PW 가 있으면 그것, 없으면 사내전산 [대성 설정]에서 보낸 cred.
//   요청마다 새로 로그인하고 세션은 보관하지 않는다. 비밀번호는 응답·로그에 남기지 않는다.
// GET /ping → { ok:true, user:"ch***@chjk.co.kr", accounts:{ seoul:"ch***@…", hs:"hs***@…"|null } }

import { connect } from 'cloudflare:sockets';

export default {
  async fetch(request, env) {
    const origin = env.ALLOW_ORIGIN || 'https://chunghae.github.io';
    const cors = {
      'Access-Control-Allow-Origin': origin,
      'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, X-Mail-Key, X-Wmis-Key',
      'Access-Control-Max-Age': '86400',
    };
    const json = (obj, status) => new Response(JSON.stringify(obj), { status: status || 200, headers: Object.assign({ 'Content-Type': 'application/json; charset=utf-8' }, cors) });
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    const url = new URL(request.url);
    const ACC = {
      seoul: { user: env.SMTP_USER, pass: env.SMTP_PASS, label: '서울' },
      hs:    { user: env.SMTP_USER_HS, pass: env.SMTP_PASS_HS, label: '화성' },
    };
    if (url.pathname.indexOf('/wmis/') === 0) {   // v3: 대성 WMIS 중계
      if (!env.MAIL_KEY || (request.headers.get('X-Mail-Key') || request.headers.get('X-Wmis-Key')) !== env.MAIL_KEY) return json({ ok: false, error: '열쇠(X-Mail-Key)가 맞지 않습니다' }, 401);
      if (request.method !== 'POST') return json({ ok: false, error: 'POST 만 됩니다' }, 405);
      let wb; try { wb = await request.json(); } catch (e) { return json({ ok: false, error: 'JSON 본문이 아닙니다' }, 400); }
      const c = (wb && wb.cred) || {};
      const cred = { id: env.WMIS_ID || String(c.id || '').trim(), pw: env.WMIS_PW || String(c.pw || '') };
      if (!cred.id || !cred.pw) return json({ ok: false, error: '대성 아이디·비밀번호가 없습니다 — 사내전산 [대성 설정]에서 넣어 주세요' }, 400);
      try {
        const s = await wmisLogin(cred);
        const p = url.pathname.slice(6);
        if (p === 'ping') { const deliv = await getDeliv(s).catch(() => null); return json({ ok: true, user: mask(cred.id), cust: s.sess.userName || s.sess.userId || '', deliv }); }
        if (p === 'lookup') return json(await doLookup(s, wb));
        if (p === 'order') return json(await doOrder(s, wb));
        return json({ ok: false, error: 'not found' }, 404);
      } catch (e) { return json({ ok: false, error: String(e && e.message || e) }, 502); }
    }
    if (request.method === 'GET' && url.pathname === '/ping') return json({ ok: true, user: env.SMTP_USER ? maskUser(env.SMTP_USER) : null, accounts: { seoul: ACC.seoul.user ? maskUser(ACC.seoul.user) : null, hs: ACC.hs.user ? maskUser(ACC.hs.user) : null } });
    if (request.method !== 'POST' || url.pathname !== '/send') return json({ ok: false, error: 'not found' }, 404);
    if (!env.MAIL_KEY || request.headers.get('X-Mail-Key') !== env.MAIL_KEY) return json({ ok: false, error: '열쇠(X-Mail-Key)가 맞지 않습니다' }, 401);

    let body;
    try { body = await request.json(); } catch (e) { return json({ ok: false, error: 'JSON 본문이 아닙니다' }, 400); }
    const acctKey = (body.account === 'hs') ? 'hs' : 'seoul';
    const acct = ACC[acctKey];
    if (!acct.user || !acct.pass) return json({ ok: false, error: acctKey === 'hs' ? '화성 발신 계정(SMTP_USER_HS / SMTP_PASS_HS)이 Worker 에 설정되지 않았습니다' : 'SMTP_USER / SMTP_PASS 가 설정되지 않았습니다' }, 500);
    const to = splitAddrs(body.to), cc = splitAddrs(body.cc), bcc = splitAddrs(body.bcc);
    if (!to.length) return json({ ok: false, error: '받는 사람이 없습니다' }, 400);
    const bad = to.concat(cc, bcc).find(a => !/^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$/.test(a));
    if (bad) return json({ ok: false, error: '주소 형식이 이상합니다: ' + bad }, 400);
    const atts = Array.isArray(body.attachments) ? body.attachments : [];
    let total = 0; for (const a of atts) total += (a && a.b64 ? a.b64.length : 0);
    if (total > 18 * 1024 * 1024) return json({ ok: false, error: '첨부가 너무 큽니다 (최대 약 13MB)' }, 413);

    try {
      const mime = buildMime({
        from: acct.user, fromName: body.fromName || '', replyTo: body.replyTo || '',
        to, cc, subject: body.subject || '(제목 없음)', text: body.text || '', html: body.html || '', attachments: atts,
      });
      await smtpSend(env, acct, to.concat(cc, bcc), mime.raw);
      return json({ ok: true, id: mime.id, from: acct.user });
    } catch (e) {
      return json({ ok: false, error: String(e && e.message || e) }, 502);
    }
  },
};

function maskUser(u) { const i = u.indexOf('@'); return i > 1 ? u.slice(0, 2) + '***' + u.slice(i) : '***'; }
function splitAddrs(s) { return String(s || '').split(/[,;\s]+/).map(x => x.trim()).filter(Boolean); }

// ── MIME ─────────────────────────────────────────────────────────────────
function b64utf8(s) { return btoa(String.fromCharCode(...new TextEncoder().encode(s))); }
function encWord(s) { return /^[\x20-\x7e]*$/.test(s) ? s : '=?UTF-8?B?' + b64utf8(s) + '?='; }
function wrap76(b64) { return b64.replace(/.{1,76}/g, '$&\r\n'); }
function fold(s) { return s; }
function buildMime(m) {
  const id = '<' + Date.now().toString(36) + '.' + Math.random().toString(36).slice(2, 10) + '@' + (m.from.split('@')[1] || 'chjk.co.kr') + '>';
  const bnd = 'chjk_' + Math.random().toString(36).slice(2) + Date.now().toString(36);
  const alt = 'alt_' + Math.random().toString(36).slice(2);
  const fromHdr = m.fromName ? encWord(m.fromName) + ' <' + m.from + '>' : m.from;
  const H = [];
  H.push('From: ' + fromHdr);
  H.push('To: ' + m.to.join(', '));
  if (m.cc.length) H.push('Cc: ' + m.cc.join(', '));
  if (m.replyTo) H.push('Reply-To: ' + m.replyTo);
  H.push('Subject: ' + encWord(m.subject));
  H.push('Date: ' + new Date().toUTCString().replace('GMT', '+0000'));
  H.push('Message-ID: ' + id);
  H.push('MIME-Version: 1.0');
  const hasAtt = m.attachments.length > 0;
  const text = m.text || (m.html ? m.html.replace(/<[^>]+>/g, '') : '');
  const html = m.html || ('<pre style="font-family:inherit;white-space:pre-wrap">' + escapeHtml(text) + '</pre>');
  const altPart =
    '--' + alt + '\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n' + wrap76(b64utf8(text)) + '\r\n' +
    '--' + alt + '\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n' + wrap76(b64utf8(html)) + '\r\n' +
    '--' + alt + '--\r\n';
  let body;
  if (!hasAtt) {
    H.push('Content-Type: multipart/alternative; boundary="' + alt + '"');
    body = altPart;
  } else {
    H.push('Content-Type: multipart/mixed; boundary="' + bnd + '"');
    body = '--' + bnd + '\r\nContent-Type: multipart/alternative; boundary="' + alt + '"\r\n\r\n' + altPart;
    for (const a of m.attachments) {
      if (!a || !a.b64) continue;
      const name = String(a.name || 'file');
      const type = String(a.type || 'application/octet-stream');
      body += '--' + bnd + '\r\nContent-Type: ' + type + '; name="' + encWord(name) + '"\r\nContent-Transfer-Encoding: base64\r\nContent-Disposition: attachment; filename="' + encWord(name) + '"\r\n\r\n' + wrap76(String(a.b64).replace(/\s+/g, '')) + '\r\n';
    }
    body += '--' + bnd + '--\r\n';
  }
  // SMTP 투명성: 줄 첫머리 '.' 은 '..' 으로
  const raw = (H.join('\r\n') + '\r\n\r\n' + body).replace(/\r\n\./g, '\r\n..');
  return { raw, id };
}
function escapeHtml(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

// ── SMTP (SSL, AUTH LOGIN) ──────────────────────────────────────────────
async function smtpSend(env, acct, rcpts, raw) {
  const from = acct.user;
  const host = env.SMTP_HOST || 'smtp.worksmobile.com';
  const port = Number(env.SMTP_PORT || 465);
  const secure = String(env.SMTP_SECURE || 'on');   // 'on' = SSL(465) / 'starttls' = 587 / 'off' = 평문(테스트용)
  const sock = connect({ hostname: host, port }, { secureTransport: secure === 'off' ? 'off' : (secure === 'starttls' ? 'starttls' : 'on'), allowHalfOpen: false });
  let s = sock;
  const io = makeIO(s);
  const expect = async (codes, what) => {
    const line = await io.readReply();
    const code = Number(line.slice(0, 3));
    if (!codes.includes(code)) throw new Error((what || 'SMTP') + ' 실패: ' + line.trim().slice(0, 200));
    return line;
  };
  try {
    await expect([220], '접속');
    await io.write('EHLO chjk-scheduler\r\n'); await expect([250], 'EHLO');
    if (secure === 'starttls') {
      await io.write('STARTTLS\r\n'); await expect([220], 'STARTTLS');
      s = sock.startTls(); io.rebind(s);
      await io.write('EHLO chjk-scheduler\r\n'); await expect([250], 'EHLO(TLS)');
    }
    await io.write('AUTH LOGIN\r\n'); await expect([334], 'AUTH');
    await io.write(btoa(acct.user) + '\r\n'); await expect([334], 'AUTH(아이디)');
    await io.write(btoa(acct.pass) + '\r\n'); await expect([235], '로그인 (아이디/외부 앱 비밀번호 확인)');
    await io.write('MAIL FROM:<' + from + '>\r\n'); await expect([250], 'MAIL FROM');
    for (const r of rcpts) { await io.write('RCPT TO:<' + r + '>\r\n'); await expect([250, 251], 'RCPT TO ' + r); }
    await io.write('DATA\r\n'); await expect([354], 'DATA');
    await io.write(raw + '\r\n.\r\n'); await expect([250], '전송');
    await io.write('QUIT\r\n');
    try { await io.readReply(); } catch (e) {}
  } finally {
    try { await s.close(); } catch (e) {}
  }
}
function makeIO(sock) {
  let reader, writer, buf = '';
  const dec = new TextDecoder(), enc = new TextEncoder();
  const bind = (s) => { reader = s.readable.getReader(); writer = s.writable.getWriter(); buf = ''; };
  bind(sock);
  return {
    rebind: bind,
    async write(str) { await writer.write(enc.encode(str)); },
    async readReply() {   // 여러 줄 응답(250-xxx … 250 xxx) 을 마지막 줄까지 읽는다
      for (;;) {
        const nl = buf.indexOf('\r\n');
        if (nl >= 0) {
          const line = buf.slice(0, nl); buf = buf.slice(nl + 2);
          if (/^\d{3}-/.test(line)) continue;
          return line;
        }
        const { value, done } = await reader.read();
        if (done) throw new Error('서버가 연결을 끊었습니다');
        buf += dec.decode(value, { stream: true });
      }
    },
  };
}

// ═══════════════ v3: 대성산업 WMIS (customer.wmis.co.kr) — 주문등록 화면 로직 그대로 ═══════════════
const BASE = 'https://customer.wmis.co.kr';
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36';

function mask(u) { u = String(u || ''); return u.length > 2 ? u.slice(0, 2) + '***' : '***'; }

// ── 세션: 요청마다 새로 로그인 (WMIS 세션이 짧고, 다른 곳 로그인과 엉키지 않게) ──
async function wmisLogin(cred) {
  const jar = {};
  const s = { jar, sess: {} };
  await req(s, '/a09/w/login', { method: 'GET' });                         // JSESSIONID 받기
  const r = await req(s, '/a09/w/login/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json, text/javascript, */*; q=0.01' },
    body: new URLSearchParams({ userid: cred.id, password: cred.pw }).toString(),
  });
  if (r.status === 401) throw new Error('대성 로그인 실패 — 대성 아이디·비밀번호를 확인하세요');
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
