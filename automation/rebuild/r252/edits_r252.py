# -*- coding: utf-8 -*-
# r252 (사용자 요청 2026-10-29):
#  ① 유튜브 공지 팝업(r242) 끄기 — `_NOTICES` 를 비움(구조는 남겨 두어 나중에 공지 한 줄로 다시 쓸 수 있음).
#  ③ 바로가기 [ID/PW] 버튼은 본인 비밀번호 재확인 없이 바로 보기(로그인한 직원이면). 수정·삭제는 기존대로 재확인.
#  ② 상단 메뉴 순서: 일정 · 견적 · 업무 사이트(구 '기타', 사용자 10-30 이름 결정) · 매입처 · 재고 · 회계 · 자료실 · 내규
#     하위 탭·페이지 제목 '바로가기' 도 '업무 사이트' 로.
#  ④ 메일 설정 불러오기 실패를 '설정 없음' 으로 착각하던 문제(사용자 11-02 "메일 설정 필요" 창): 실패는 기억하지 않고(_mailCfg 비움) 1회 재시도,
#     그래도 실패면 "메일 설정을 불러오지 못했습니다" 안내. 메일 보내기 창은 열 때마다 새로 읽음(force).
import io, sys, json, re

OPS = [
  ["  <button class=\"page-tab active\" id=\"tabSchedule\">일정</button>\n  <button class=\"page-tab\" data-page=\"rules\">내규</button><!-- r247 -->\n  <button class=\"page-tab\" data-page=\"estimate\">견적</button>\n  <button class=\"page-tab\" id=\"tabAccounting\">회계</button>\n  <button class=\"page-tab\" data-page=\"inventory\">재고</button>\n  <button class=\"page-tab\" data-page=\"purchase\">매입처</button>\n  <button class=\"page-tab\" data-page=\"files\">자료실</button>\n  <button class=\"page-tab\" id=\"tabEtc\">기타</button>",
   "  <button class=\"page-tab active\" id=\"tabSchedule\">일정</button>\n  <button class=\"page-tab\" data-page=\"estimate\">견적</button>\n  <button class=\"page-tab\" id=\"tabEtc\">업무 사이트</button><!-- r252: 구 '기타' -->\n  <button class=\"page-tab\" data-page=\"purchase\">매입처</button>\n  <button class=\"page-tab\" data-page=\"inventory\">재고</button>\n  <button class=\"page-tab\" id=\"tabAccounting\">회계</button>\n  <button class=\"page-tab\" data-page=\"files\">자료실</button>\n  <button class=\"page-tab\" data-page=\"rules\">내규</button><!-- r247 -->", 1, "NAV"],
  ["onclick=\"event.stopPropagation();_linksConfirmMyPw('ID/PW 확인', function(){ _linksShowCredential('${l.id}'); })\"",
   "onclick=\"event.stopPropagation();_linksShowCredential('${l.id}')\"", 1, "CRED_DIRECT"],
  ["입력 시 비밀번호 확인 후 열람 가능한 ID/PW 버튼이 생성됩니다.", "입력하면 목록에 ID/PW 버튼이 생깁니다 (누르면 바로 보임).", 1, "CRED_HINT"],
  ['<button class="sub-tab" data-page="links">바로가기</button>', '<button class="sub-tab" data-page="links">업무 사이트</button>', 1, "SUB_LABEL"],
  ['<span class="inv-flat-label">바로가기</span>', '<span class="inv-flat-label">업무 사이트</span>', 1, "PAGE_LABEL"],
  ["    try{ var r=await _fbFetch(_fbDbUrl+'/'+_AUTH_BASE+'/sched_mail_cfg.json'); _mailCfg=(r&&r.ok?(await r.json()):null)||{}; }catch(_e){ _mailCfg={}; }\n    return _mailCfg;",
   "    for(var _try=0; _try<2; _try++){   // r252: 실패는 '설정 없음' 으로 기억하지 않는다\n      try{ var r=await _fbFetch(_fbDbUrl+'/'+_AUTH_BASE+'/sched_mail_cfg.json'); if(r&&r.ok){ _mailCfg=(await r.json())||{}; return _mailCfg; } }catch(_e){}\n      await new Promise(function(res){ setTimeout(res, 800); });\n    }\n    _mailCfg=null; return { _loadErr:true };", 1, "CFG_LOAD"],
  ["    var cfg=await _mailLoadCfg();\n    if(!cfg.url||!cfg.key){",
   "    var cfg=await _mailLoadCfg(true);   // r252: 열 때마다 새로 읽음\n    if(cfg._loadErr){ showInfoModal('메일 설정 확인 실패','메일 설정을 불러오지 못했습니다 (로그인·네트워크 확인 중).\\n잠시 후 다시 눌러 주세요. 계속되면 새로고침(Ctrl+F5) 후 다시 시도해 주세요.'); return; }\n    if(!cfg.url||!cfg.key){", 1, "CFG_OPEN"],
  ["    var cfg=await _mailLoadCfg(); var d=window._mlDraft||_mailQuoteDraft();",
   "    var cfg=await _mailLoadCfg(); if(cfg._loadErr) cfg=await _mailLoadCfg(true); var d=window._mlDraft||_mailQuoteDraft();   // r252", 1, "CFG_SEND"],
  ["    if(!_isAdmin()){ showInfoModal('권한','메일 설정은 관리자만 할 수 있습니다.'); return; }\n    var cfg=await _mailLoadCfg(true);",
   "    if(!_isAdmin()){ showInfoModal('권한','메일 설정은 관리자만 할 수 있습니다.'); return; }\n    var cfg=await _mailLoadCfg(true);\n    if(cfg._loadErr){ showInfoModal('메일 설정 확인 실패','저장된 메일 설정을 불러오지 못했습니다. 빈 칸으로 저장하면 기존 설정이 지워질 수 있어 창을 열지 않습니다.\\n잠시 후 다시 시도해 주세요.'); return; }   // r252", 1, "CFG_ADMIN"],
]

def _notice_op(s):
    m = re.search(r"  var _NOTICES = \[\n    \{ id:'nt20261020'[^\n]*\n  \];", s)
    if not m: raise SystemExit('R252 FAIL NOTICE')
    return s.replace(m.group(0), "  var _NOTICES = [];   // r252: 10-20 유튜브 공지 종료 (다시 쓰려면 { id, title, yt|url, note } 한 줄 추가 — id 가 새로우면 계정마다 1회)")

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R252 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r252(s, path):
    is_test = '/test/' in path
    for old, new, exp, label in OPS: s = rep(s, old, new, exp, label)
    s = _notice_op(s)
    if is_test: s = rep(s, "<!-- test build r251 2026-10-27 -->", "<!-- test build r252 2026-10-29 -->", 1, "MARKER")
    return s

if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r252(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r252 applied:', path)
