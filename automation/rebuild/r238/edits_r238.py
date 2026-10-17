# -*- coding: utf-8 -*-
# r238 (사용자 요청 2026-10-17): "화성 직원들이 메일을 보낼 때에는 from 주소가 달라야 한다."
#   - 발신 계정 2개: 서울 chjk@chjk.co.kr / 화성 hs-chjk@chjk.co.kr (Worker v2: SMTP_USER_HS / SMTP_PASS_HS).
#   - 보내기 창에 [보내는 계정] 선택칸 — 로그인한 직원의 소속(members[].group)이 '화성'이면 화성 계정이 기본.
#   - 계정을 바꾸면 본문 서명·보낸이 이름도 그 지점 것으로(본문을 손대지 않았을 때만 다시 씀).
#   - 발송 요청에 account:'seoul'|'hs' 를 붙인다. [메일 설정]의 연결 확인은 두 계정 상태를 모두 보여준다.
import io, sys, json

OPS = [
  # ① 초안: 지점을 바깥에서 지정할 수 있게
  ["function _mailQuoteDraft(){",
   "function _mailAcctOf(branch){ return (branch==='화성')?'hs':'seoul'; }   // r238\n  function _mailBranchOf(acct){ return (acct==='hs')?'화성':'서울'; }\n  function _mailQuoteDraft(forceBranch){", 1, "DRAFT_SIG"],
  ["var branch=(_me&&_me.group)?_me.group:'서울'; var SUP=_qSupplierInfo(branch);",
   "var branch=forceBranch||((_me&&_me.group)?_me.group:'서울'); var SUP=_qSupplierInfo(branch);   // r238: 계정 선택에 따라 지점 서명", 1, "DRAFT_BRANCH"],
  ["return { vname:vname, no:no, mgr:mgr, staff:staff, to:_mailClientEmails(vname, mgr), subject:'[충해전기] 견적서 '+no+' — '+vname, body:body, fromName:SUP.corp+' '+staff };",
   "return { vname:vname, no:no, mgr:mgr, staff:staff, to:_mailClientEmails(vname, mgr), subject:'[충해전기] 견적서 '+no+' — '+vname, body:body, fromName:SUP.corp+' '+staff, branch:branch, account:_mailAcctOf(branch), fromMail:SUP.mail };", 1, "DRAFT_RET"],
  # ② 보내기 창: 보낸이 고정 문구 → 계정 선택칸
  ["<span style=\"color:#9ca3af\">보낸이 '+esc(d.fromName)+' &lt;chjk@chjk.co.kr&gt;</span></div>'",
   "<span style=\"color:#374151;display:flex;align-items:center;gap:6px\"><b style=\"color:#14305c\">보내는 계정</b><select id=\"mlAcct\" onchange=\"mlAcctChanged()\" style=\"padding:4px 6px;border:1.5px solid #d6e0ec;border-radius:7px;font-size:12px;font-family:inherit\"><option value=\"seoul\"'+(d.account==='hs'?'':' selected')+'>서울 · chjk@chjk.co.kr</option><option value=\"hs\"'+(d.account==='hs'?' selected':'')+'>화성 · hs-chjk@chjk.co.kr</option></select><span id=\"mlFromName\" style=\"color:#9ca3af\">'+esc(d.fromName)+'</span></span></div>'", 1, "SEND_ACCT"],
  ["    window._mlDraft=d;\n",
   "    window._mlDraft=d;\n    window._mlDraftBody=d.body;\n", 1, "SEND_KEEP"],
  # ③ 계정 바꾸면 서명·보낸이 갱신
  ["  window.qMailSendNow=async function(){",
   "  window.mlAcctChanged=function(){   // r238\n    var sel=document.getElementById('mlAcct'); if(!sel) return;\n    var d=_mailQuoteDraft(_mailBranchOf(sel.value)); window._mlDraft=d;\n    var fn=document.getElementById('mlFromName'); if(fn) fn.textContent=d.fromName;\n    var b=document.getElementById('mlBody'); if(b && b.value===window._mlDraftBody){ b.value=d.body; window._mlDraftBody=d.body; }\n  };\n  window.qMailSendNow=async function(){", 1, "ACCT_CHANGED"],
  # ④ 발송 요청에 account
  ["body:JSON.stringify({to:to, cc:cc, subject:subj, text:body, html:html, fromName:d.fromName, attachments:atts})",
   "body:JSON.stringify({account:((document.getElementById('mlAcct')||{}).value||d.account||'seoul'), to:to, cc:cc, subject:subj, text:body, html:html, fromName:d.fromName, attachments:atts})", 1, "SEND_BODY"],
  # ⑤ 연결 확인: 두 계정 상태
  ["m.innerHTML=j.ok?('<span style=\"color:#15803d\">연결됨 · 발신 계정 '+esc(j.user||'(미설정)')+'</span>')",
   "m.innerHTML=j.ok?('<span style=\"color:#15803d\">연결됨</span> · 서울 '+esc((j.accounts&&j.accounts.seoul)||j.user||'(미설정)')+' · 화성 '+((j.accounts&&j.accounts.hs)?esc(j.accounts.hs):'<span style=\"color:#b45309\">(미설정 — Worker 에 SMTP_USER_HS / SMTP_PASS_HS 추가)</span>'))", 1, "PING_TWO"],
  ["가 chjk@chjk.co.kr 로 보냅니다. Worker 에 넣은",
   "가 서울 chjk@chjk.co.kr / 화성 hs-chjk@chjk.co.kr 계정으로 보냅니다(직원 소속에 따라 자동, 보내기 창에서 바꿀 수 있음). Worker 에 넣은", 1, "CFG_TEXT"],
  ["<!-- test build r237 2026-10-16 -->", "<!-- test build r238 2026-10-17 -->", 1, "MARKER"],
]

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R238 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r238(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        if label == 'MARKER' and not is_test: continue
        s = rep(s, old, new, exp, label)
    return s

def gen_js(out):
    lines = ["// r238 브라우저 적용기 — edits_r238.py 의 OPS. r237 적용본 위에 적용.",
             "function r238Apply(s, isTest){",
             "  function rep(str, old, nw, exp, label){ var n=str.split(old).length-1; if(n!==exp) throw new Error('R238 FAIL '+label+' count '+n+' (expect '+exp+')'); return str.split(old).join(nw); }",
             "  var OPS = " + json.dumps(OPS, ensure_ascii=False) + ";",
             "  for(var i=0;i<OPS.length;i++){ var o=OPS[i]; if(!isTest && o[3]==='MARKER') continue; s = rep(s, o[0], o[1], o[2], o[3]); }",
             "  return s;", "}", "if(typeof module!=='undefined') module.exports = r238Apply;", ""]
    with io.open(out, 'w', encoding='utf-8', newline='') as f: f.write('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv)>2 and sys.argv[1]=='--js': gen_js(sys.argv[2]); print('js written:', sys.argv[2]); sys.exit(0)
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r238(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r238 applied:', path)
