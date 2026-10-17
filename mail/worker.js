// 충해전기 사내전산 — 메일 발송 Worker (Cloudflare Workers)  v2 (2026-10-17: 서울·화성 발신 계정 2개)
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
// GET /ping → { ok:true, user:"ch***@chjk.co.kr", accounts:{ seoul:"ch***@…", hs:"hs***@…"|null } }

import { connect } from 'cloudflare:sockets';

export default {
  async fetch(request, env) {
    const origin = env.ALLOW_ORIGIN || 'https://chunghae.github.io';
    const cors = {
      'Access-Control-Allow-Origin': origin,
      'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, X-Mail-Key',
      'Access-Control-Max-Age': '86400',
    };
    const json = (obj, status) => new Response(JSON.stringify(obj), { status: status || 200, headers: Object.assign({ 'Content-Type': 'application/json; charset=utf-8' }, cors) });
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    const url = new URL(request.url);
    const ACC = {
      seoul: { user: env.SMTP_USER, pass: env.SMTP_PASS, label: '서울' },
      hs:    { user: env.SMTP_USER_HS, pass: env.SMTP_PASS_HS, label: '화성' },
    };
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
