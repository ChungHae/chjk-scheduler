# -*- coding: utf-8 -*-
# r117: [완전 삭제 1단계] 팀원 일정(주간) + 업무 배정/업무 제안 + 팀 목표/주간 이슈
#       — r106에서 숨김 처리했던 블록의 실제 코드 제거.
#       유지: 연차/휴가, 공지(broadcast), entries(출퇴근·휴가 데이터), 달력, 오늘 위젯.
#       데이터 키/선언(weeklyIssues, teamGoal, assignments 등)은 r119 정리 전까지 유지
#       (동기화는 PATCH 병합이라 서버 데이터도 안전).

import io

def cut(s, start, end, repl, label):
    i1 = s.find(start)
    if i1 < 0 or s.find(start, i1+1) >= 0:
        raise SystemExit('R117 FAIL %s: start marker count != 1' % label)
    i2 = s.find(end, i1)
    if i2 < 0:
        raise SystemExit('R117 FAIL %s: end marker not found after start' % label)
    if s.find(end, i2+1) >= 0 and s.count(end) != 1:
        # end 마커가 여러 개면 start 이후 첫 번째를 쓰는 것 자체는 안전 (그 사이만 삭제)
        pass
    return s[:i1] + repl + s[i2:], (i2 - i1)

def apply_r117(s, path):
    total = 0
    # ── HTML ──
    # H1 팀원 일정 페이지 내용 삭제 (빈 셸 유지 — pageMap 기본값이 pageWeekly)
    s, n = cut(s, '  <div id="pageWeekly" class="page-section">', '  </div><!-- /pageWeekly -->',
               '  <div id="pageWeekly" class="page-section"></div><!-- r117: 팀원 일정 삭제 -->\n  <!-- ', 'H1'); total += n
    # 위 치환으로 기존 END 마커 앞에 주석 열림 추가 → END 마커 라인을 주석으로 무력화
    s = s.replace('  <!-- \n  </div><!-- /pageWeekly -->', '', 1)
    # H2 팀원 일정 탭 버튼 삭제
    i1 = s.find('  <button class="sub-tab" data-page="weekly" style="display:none">')
    if i1 < 0: raise SystemExit('R117 FAIL H2 start')
    i2 = s.find('</button>\n', i1)
    if i2 < 0: raise SystemExit('R117 FAIL H2 end')
    s = s[:i1] + s[i2+len('</button>\n'):]
    # H3 업무 배정 페이지 내용 삭제 (빈 셸 유지)
    s, n = cut(s, '  <div id="pageAssign" class="page-section">', '  <!-- 개인 일정 페이지 -->',
               '  <div id="pageAssign" class="page-section"></div><!-- r117: 업무 배정 삭제 -->\n\n  ', 'H3'); total += n
    # H4 업무 배정 모달 삭제 (Entry Modal 주석 직전까지)
    s, n = cut(s, '<div class="overlay" id="assignOverlay" style="display:none">', '<!-- ─── Entry Modal',
               '', 'H4'); total += n
    # H5 주간 이슈 + 팀 목표 모달 삭제 (issueOverlay부터 외부 script 직전까지)
    s, n = cut(s, '<div class="overlay" id="issueOverlay" style="display:none">', '<script src="https://cdnjs',
               '', 'H5'); total += n
    # ── JS ──
    # J1 주간 이슈 렌더/모달/저장 (선언 weeklyIssues 는 유지)
    s, n = cut(s, '  function renderIssuePanel() {', '  // ─── 업무 배정 페이지', '', 'J1'); total += n
    # J2 업무 배정 페이지/모달/코멘트/바인딩 전체 (applyConfig 직전까지)
    s, n = cut(s, '  // ─── 업무 배정 페이지', '  function applyConfig() {', '', 'J2'); total += n
    # J3 팀 목표 모달 + 배정 연동(renderAssignedTasks/renderEntryAssign/코멘트/토글) 전체
    s, n = cut(s, '  // ─── 팀 목표 ─', '  function defaultMembers() {', '', 'J3'); total += n
    # J4 팀 패널 렌더/높이 맞춤 → 삭제 (HOLIDAYS 이후는 유지)
    s, n = cut(s, '  function renderTeamPanel() {', '  const HOLIDAYS = {', '', 'J4'); total += n
    # J5 주간 셀 렌더 + render() → 빈 스텁 (호출부가 매우 많아 이름 유지)
    s, n = cut(s, '  function weekCellInner(m, d){', '    // ─── Clock Picker',
               '  function render() {}\n\n    // r117: 주간 렌더 삭제 (스텁 유지)\n', 'J5'); total += n
    # J6 주간 네비 바인딩(btnPrev/btnNext/btnToday) — test에는 모바일 이동(_wkMobShift)이 앞에 붙음
    j6start = '  function _wkMobShift(delta){' if '_wkMobShift' in s else "  document.getElementById('btnPrev').addEventListener('click', ()=>{"
    s, n = cut(s, j6start, '  /* ═════════════ 로그인', '', 'J6'); total += n
    # J7 switchPage의 assign 분기: renderAssignPage 삭제됨 → typeof 가드 (도달 불가 경로지만 안전하게)
    old7 = "    if (page === 'assign')    renderAssignPage();"
    if s.count(old7) != 1: raise SystemExit('R117 FAIL J7 count %d' % s.count(old7))
    s = s.replace(old7, "    if (page === 'assign' && typeof renderAssignPage==='function') renderAssignPage();")
    # J8 applyConfig: 삭제된 팀 목표 패널/모달 제목 갱신 줄 제거 (부팅 시 null 에러 방지)
    old8 = """    document.querySelector('#teamPanelGoalBox .team-panel-title').textContent = '' + config.orgName + ' 목표';
    document.querySelector('#teamOverlay h2').textContent = '' + config.orgName + ' 목표';
"""
    if s.count(old8) != 1: raise SystemExit('R117 FAIL J8 count %d' % s.count(old8))
    s = s.replace(old8, '')
    return s, total

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s, total = apply_r117(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r116 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r116 2026-08-20 -->', '<!-- test build r117 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path, 'removed ~%d chars' % total)
