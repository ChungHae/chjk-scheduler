# -*- coding: utf-8 -*-
# r179: 메모장 기반 개인 일정 — 서브탭 일정(메모장)·완료(구 일정/프로젝트)·주간·달력·업체 (흰색·전폭 패드) (TEST 우선, 사용자 결정 2026-09-10)
#
#  사용자 요구 요약:
#   · 한 페이지(노란 리갈패드)에 메모만 적는다. 로그인한 사람 이름으로 저장, 메모 본문은 본인만 본다.
#   · 붉은 세로선 왼쪽 여백에 작성 날짜.
#   · 줄 앞에 '-' 또는 '1.' 을 치면 바로 위 메모의 하위 줄로 들어간다(Tab 도 지원).
#   · 줄 맨 앞 키워드로 종류 판별: 미팅/프로젝트/납품/공지/요청(이름). 업체명은 등록 업체 목록과 자동 매칭.
#     '이름 010-…' 줄은 담당자, 명함 사진을 붙이면 담당자 기록.
#   · 세부 옵션은 전부 '완료' 시점의 창에서 정한다 — 일정 저장 / 프로젝트 저장 / 담당자 등록.
#     메모 적은 날 = 프로젝트 시작일, 완료 누른 날 = 종료일.
#   · 완료하면 검은 취소선 + 흐림. 완료 후 24시간 지나면 목록에서 사라진다(자료는 남음, 30일 뒤 정리).
#   · '공지 …' 는 모든 사람 메모장 맨 위에. '요청 이름 …' 은 그 사람 메모장에 뜨고, 피드백·완료가
#     요청한 사람 메모장에도 보인다.
#   · 주간 일정표(주간 탭)에서 사람별로 그 주에 한 일(미팅·납품·프로젝트 완료·휴가)을 다같이 본다.
#   · 달력은 휴가만 (공지 막대 제거).
#
#  자료: sched_memos (memoLines) / sched_memo_cards (memoCards: 명함 dataURL, 640px JPEG 로 줄여 저장)
#   memoLines 항목 = { id, owner(로그인 이름), text, parent(상위 id|null), kind(memo|meeting|project|delivery|
#     notice|request|contact), vendor(매칭 업체명), to(요청 대상), name/phone(담당자), when:{date,time},
#     date(작성일 YYYY-MM-DD), createdAt, done, doneAt, feedback:[{by,text,ts}], card(카드 id), linked:{sched,proj} }
#   등록 지점: 선언 / saveAll / doFbSave 페이로드 / reloadState / KEYS(live 2·test 3) / 백업.
#
#  ★ 다시 그리는 영역(#mmList) 안에 입력칸을 두지 않는다(r171 규칙). 새 줄 입력칸(#mmInput)은 고정,
#    기존 줄 수정은 그 줄에만 input 을 끼워 넣고(_mmEditing) 편집 중엔 재렌더를 건너뛴다.

import io, sys

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R179 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

_D = __import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), 'r179')
def _part(n):
    with io.open(__import__('os').path.join(_D, n + '.txt'), 'r', encoding='utf-8', newline='') as f: return f.read()
CSS = _part('css'); MARKUP_MEMO = _part('markup_memo'); MARKUP_WEEKLY = _part('markup_weekly'); JS = _part('js')

def apply_r179(s, path):
    is_test = 'testpage' in path

    # ── (0) 자료 등록 ──
    s = rep(s, "  let projectsList = load('sched_projects') ?? [];",
        "  let projectsList = load('sched_projects') ?? [];\n"
        "  let memoLines = load('sched_memos') ?? [];        // r179 메모장 줄 [{id,owner,text,parent,kind,vendor,to,name,phone,when,date,createdAt,done,doneAt,feedback,card,linked}]\n"
        "  let memoCards = load('sched_memo_cards') ?? {};   // r179 명함 사진 {cardId: dataURL}", 1, 'DECL')
    s = rep(s, "    save('sched_projects', projectsList);\n    save('sched_client_info', clientInfo);\n",
        "    save('sched_projects', projectsList);\n    save('sched_client_info', clientInfo);\n    save('sched_memos', memoLines);   // r179\n    save('sched_memo_cards', memoCards);\n", 1, 'SAVEALL')
    s = rep(s, "        sched_projects: projectsList,\n",
        "        sched_projects: projectsList,\n        sched_memos: memoLines,   // r179\n        sched_memo_cards: memoCards,\n", 1, 'FBPUT')
    s = rep(s, "    projectsList     = load('sched_projects') ?? [];\n",
        "    projectsList     = load('sched_projects') ?? [];\n    memoLines        = load('sched_memos') ?? [];   // r179\n    memoCards        = load('sched_memo_cards') ?? {};\n", 1, 'RELOAD')
    s = rep(s, "'sched_client_list','sched_projects','sched_client_info','sched_proj_memos'",
        "'sched_client_list','sched_projects','sched_client_info','sched_proj_memos','sched_memos','sched_memo_cards'", 3 if is_test else 2, 'KEYS')
    s = rep(s, "      sched_projects: projectsList, sched_client_info: clientInfo, sched_proj_memos: projMemos,\n",
        "      sched_projects: projectsList, sched_client_info: clientInfo, sched_proj_memos: projMemos,\n      sched_memos: memoLines, sched_memo_cards: memoCards,   // r179\n", 1, 'BACKUP')

    # ── (1) 마크업 ──
    s = rep(s, '  <button class="sub-tab active" data-page="project">일정</button>',
        '  <button class="sub-tab active" data-page="memo">일정</button>\n  <button class="sub-tab" data-page="project">완료</button>\n  <button class="sub-tab" data-page="weekly">주간</button>', 1, 'SUBNAV')
    s = rep(s, '  <div id="pageWeekly" class="page-section"></div><!-- r117: 팀원 일정 삭제 -->', MARKUP_WEEKLY + MARKUP_MEMO, 1, 'MARKUP')

    # ── (2) 페이지 전환 ──
    s = rep(s, "    var _SCHED=['personal','weekly','biz','project','clients'];",
        "    var _SCHED=['personal','weekly','biz','project','clients','memo'];   // r179", 1, 'SCHED')
    s = rep(s, "const pageMap = { weekly:'pageWeekly',", "const pageMap = { memo:'pageMemo', weekly:'pageWeekly',", 1, 'PAGEMAP')
    # live 에는 _wkMobSel 줄(주간 모바일 코드)이 없다 — 분기
    s = rep(s,
        "    if (page === 'weekly') {\n" + ("      _wkMobSel = null;   // 탭 진입 시 항상 오늘부터 (모바일 하루 이동 상태 초기화)\n" if is_test else "") +
        "      weekStart = getMonday(new Date());\n      render();\n      try{ window.scrollTo(0, 0); }catch(e){}\n      setTimeout(_scrollWeeklyToToday, 140);\n    }",
        "    if (page === 'weekly') { _wkStart = getMonday(new Date()); renderWeeklyPage(); }   // r179 주간 일정표\n    if (page === 'memo') { _mmEditing=null; renderMemoPage(true); setTimeout(function(){ try{ var _mi=document.getElementById('mmInput'); if(_mi && window.innerWidth>640) _mi.focus(); }catch(_e){} }, 60); }",
        1, 'HOOK')
    s = rep(s, "      else if(_id==='pageClients' && typeof renderClientsPage==='function') renderClientsPage();",
        "      else if(_id==='pageClients' && typeof renderClientsPage==='function') renderClientsPage();\n      else if(_id==='pageMemo' && typeof renderMemoPage==='function') renderMemoPage();   // r179 (편집 중이면 건너뜀)\n      else if(_id==='pageWeekly' && typeof renderWeeklyPage==='function') renderWeeklyPage();",
        1, 'REFRESH')
    # 시작 탭 = 메모 (일정 탭 버튼·로고·초기 진입 3곳)
    s = rep(s, "switchPage('project');", "switchPage('memo');", 3, 'START')

    # ── (3) 달력은 휴가만 ──
    s = rep(s, "      if (_psShowBcast()) bcastBarsHtml(dStr).forEach(h => _lines.push(h));",
        "      // r179: 달력은 휴가만 (공지 막대 제거)", 1, 'CAL')

    # ── (4) CSS / JS ──
    s = rep(s, "    .page-section { display: none; }", CSS + "    .page-section { display: none; }", 1, 'CSS')
    s = rep(s, "  // ─── 개인 일정 페이지 ──────────────────────────────────", JS + "  // ─── 개인 일정 페이지 ──────────────────────────────────", 1, 'JS')

    if is_test:
        s = rep(s, "<!-- test build r178 2026-09-07 -->", "<!-- test build r179 2026-09-10 -->", 1, 'MARKER')
    return s

if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r179(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r179 applied:', path)
