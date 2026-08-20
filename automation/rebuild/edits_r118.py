# -*- coding: utf-8 -*-
# r118: [완전 삭제 2단계] 일정 등록 모달(Entry/ReadOnly) + 개인 일정 목록/빠른추가 +
#       날짜 메모(포스트잇) + 미완료/미확인 모달 + 업무 제안 패널 + 개인 일정 모달 +
#       모바일 오늘 일정 + plans/projects 구형 데이터 렌더 — 전부 코드 제거.
#       유지: 달력, 연차/휴가 모달, 공지(broadcast), 출퇴근 오늘 위젯(+클록 피커),
#             entries/personalSchedules 데이터와 동기화.

import io

def cut(s, start, end, repl, label):
    i1 = s.find(start)
    if i1 < 0 or s.find(start, i1+1) >= 0:
        raise SystemExit('R118 FAIL %s: start marker count %d' % (label, s.count(start)))
    i2 = s.find(end, i1)
    if i2 < 0:
        raise SystemExit('R118 FAIL %s: end marker not found' % label)
    return s[:i1] + repl + s[i2:]

def rep1(s, old, new, label):
    if s.count(old) != 1:
        raise SystemExit('R118 FAIL %s: count %d' % (label, s.count(old)))
    return s.replace(old, new)

def apply_r118(s, path):
    # ── JS ──
    # A. Entry 모달 스택 전체: plans/projects 구형 → 코멘트/포스트잇 → ReadOnly →
    #    Entry 상태/휴가 → openEntry/통합목록/저장/닫기 → RoStatus (renderMemberList 직전까지)
    s = cut(s, '  function getPlans(en) {', '  function renderMemberList() {', '', 'A')
    # B+C. 모바일 오늘 일정 + 개인 일정 목록(빠른추가·드래그·완료 오버레이) 전체
    #      (live에는 모바일 이동(_psMobShift)이 없고 renderPersonalTodayMobile부터 시작)
    bc_start = '  window._psMobShift = function(delta){' if '_psMobShift' in s else '  function renderPersonalTodayMobile(selId){'
    s = cut(s, bc_start, '  window.openBroadcastAdd = function(dStr){', '', 'BC')
    # D. renderPersonalPage 안의 삭제된 함수 호출 제거
    s = rep1(s, '    try{ renderPersonalTodayMobile(selId); }catch(_e){}\n', '', 'D1')
    s = rep1(s, '      renderPersonalListView(selId);\n      renderAssignSuggestPanel(selId);\n', '', 'D2')
    # E+F. renderPersonalPage 끝의 제안 패널 호출 + 제안 패널 함수들 삭제
    s = cut(s, '    renderAssignSuggestPanel(selId);\n  }\n\n  window.toggleAssignSuggestPanel = function() {',
            '  function openPersonalModal(', '  }\n\n  ', 'EF')
    # G. 개인 일정 모달 + 저장/삭제 + 미완료/미확인 모달 전부 (달력 네비 바인딩 직전까지)
    s = cut(s, '  function openPersonalModal(', '  // 팀원 선택 / 월 네비게이션', '', 'G')
    # H. 리스트 추가 핸들러 바인딩 + personalOverlay 동적 생성 (업체별 페이지 직전까지)
    s = cut(s, '  // 보기 모드 토글 + 리스트 추가 핸들러', '  // ─── 업체별 페이지', '', 'H')
    # J1. 오늘 일정 열기(위젯 잔재) — openEntry 삭제됨, 호출부 없음 → 함수 제거
    s = cut(s, '  window.openTodayEntry = function() {', '  // ─── 휴가 기간 신청', '', 'J1')
    # J2. 연차 수정 진입의 openEntry 폴백 → 조용히 종료
    s = rep1(s, "    if(memberId !== myMemberId && !_isAdmin()){ openEntry(memberId, dkStr); return; }",
             "    if(memberId !== myMemberId && !_isAdmin()){ return; }", 'J2a')
    s = rep1(s, "    if(en.status !== '휴가' || !en.vacation){ openEntry(memberId, dkStr); return; }",
             "    if(en.status !== '휴가' || !en.vacation){ return; }", 'J2b')
    # J3. 고아 헬퍼 renderItemGroupsHtml (목록 전용, 호출부 없음)
    s = cut(s, '  // 카테고리 × 업체로 묶어 항목 그룹 HTML 만들기 (헬퍼)', '  window.openBroadcastAdd = function(dStr){', '', 'J3')
    # ── HTML ──
    # I1. 일정 등록 버튼
    i1 = s.find('      <button id="btnEntryAdd"')
    if i1 < 0: raise SystemExit('R118 FAIL I1')
    i2 = s.find('</button>\n', i1)
    s = s[:i1] + s[i2+len('</button>\n'):]
    # I2. 업무 제안 현황 버튼
    i1 = s.find('      <button id="btnAssignSuggest"')
    if i1 < 0: raise SystemExit('R118 FAIL I2')
    i2 = s.find('</button>\n', i1)
    s = s[:i1] + s[i2+len('</button>\n'):]
    # I3. 업무 제안 패널 + 모바일 오늘 일정 div (월간 달력 주석 직전까지)
    s = cut(s, '    <!-- 업무 제안 현황 패널 -->', '    <!-- 월간 달력 (cal 모드 전용) -->', '', 'I3')
    # I4. 업무 리스트(list 모드) 블록 (재무현황 페이지 직전까지 — pagePersonal 닫는 div 복원)
    s = cut(s, '    <!-- 업무 리스트 (list 모드 · 기본) -->', '  <!-- 재무현황 페이지 -->', '  </div>\n\n  ', 'I4')
    # I5. Entry 모달 + ReadOnly 모달 HTML (연차 모달 직전까지)
    s = cut(s, '<!-- ─── Entry Modal', '<div class="overlay" id="vacationModal"', '', 'I5')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        before = len(s)
        s = apply_r118(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r117 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r117 2026-08-20 -->', '<!-- test build r118 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path, 'removed ~%d chars' % (before - len(s)))
