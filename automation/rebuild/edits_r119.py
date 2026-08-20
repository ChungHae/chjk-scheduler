# -*- coding: utf-8 -*-
# r119: [완전 삭제 3단계·최종] 업체별 일정 페이지 + 분류 설정 + 달력의 일정 잔재 코드 제거.
#       데이터 선언·동기화 키(sched_assignments/comments/categories/issues/team_goal 등)는
#       기존 데이터 보호와 구버전 탭 호환을 위해 유지 (PATCH 병합 저장이라 안전).

import io

def cut(s, start, end, repl, label):
    i1 = s.find(start)
    if i1 < 0 or s.find(start, i1+1) >= 0:
        raise SystemExit('R119 FAIL %s: start count %d' % (label, s.count(start)))
    i2 = s.find(end, i1)
    if i2 < 0:
        raise SystemExit('R119 FAIL %s: end not found' % label)
    return s[:i1] + repl + s[i2:]

def rep1(s, old, new, label):
    if s.count(old) != 1:
        raise SystemExit('R119 FAIL %s: count %d' % (label, s.count(old)))
    return s.replace(old, new)

def apply_r119(s, path):
    # ── 달력(renderPersonalPage) 안의 일정 잔재 ──
    # P1. list 모드 분기 통째 제거
    s = cut(s, "    if (personalViewMode === 'list' && !_calVacOnly) {", '    // 월간 달력 그리드 (cal 모드)', '', 'P1')
    # P2. 죽은 선언(dayAssign/dayPsched/projects/plans/vacStr) 제거
    s = rep1(s, """      const vacStr  = en.status === '휴가' && en.vacation ? en.vacation.type : '';

      // 배정 업무
      const dayAssign = [];   // r106 일정 숨김
      // 개인 일정 항목
      const dayPsched = [];   // r106 일정 숨김
      // 하위 호환 (예전 데이터)
      const projects = [], plans = [];   // r106 일정 숨김
""", '', 'P2')
    # P3. if(false) 죽은 블록 제거 (_hasMemo/_ovdHtml/_unreadHtml 빈 선언은 유지 — 템플릿에서 참조)
    s = cut(s, '      if (false) {   // r106 미완료·미확인 표시 숨김', '      let inner = `', '', 'P3')
    # P4. 죽은 일정/배정 렌더 루프 제거
    s = cut(s, '      // 할일 / 일정 항목\n      dayPsched.forEach(s => {', '      // 줄 수 제한', '', 'P4')
    # P5. 달력 끝 업무 제안 버튼 갱신 블록 제거 (함수 닫는 중괄호 복원)
    s = cut(s, '    // ── 업무 제안 현황 버튼 업데이트 ─', '    // 팀원 선택 / 월 네비게이션', '  }\n\n', 'P5')
    # ── 업체별 일정 페이지 ──
    # B1. 검색/이름 수집 JS + 검색 모달 바인딩 (주간 이슈 선언 직전까지)
    s = cut(s, '  function getAllBizNames() {', '  // ─── 주간 이슈', '', 'B1')
    # B2. renderBizPage + 기록 삭제/이름 변경/병합
    s = cut(s, '  function renderBizPage() {', '  function parseExcelDate(excelDate) {', '', 'B2')
    # B3. switchPage 의 biz 진입 분기
    s = rep1(s, """    if (page === 'biz'){
      var _bt=document.getElementById('bizFilterInput'); if(_bt) _bt.value='';
      var _bm=document.getElementById('bizFilterMember'); if(_bm) _bm.value='';
      var _bs=document.getElementById('bizFilterStatus'); if(_bs) _bs.value='';
      renderBizPage();
    }
""", '', 'B3')
    # B4. _refreshActiveView 의 biz 분기
    s = rep1(s, "      else if(_id==='pageBiz' && typeof renderBizPage==='function') renderBizPage();\n", '', 'B4')
    # B5. HTML: pageBiz 내용 삭제 (빈 셸 유지)
    s = cut(s, '  <div id="pageBiz" class="page-section">', '  <!-- 업무 배정 페이지 -->',
            '  <div id="pageBiz" class="page-section"></div><!-- r119: 업체별 일정 삭제 -->\n\n  ', 'B5')
    # B6. 업체별 일정 탭 버튼 삭제
    i1 = s.find('  <button class="sub-tab" data-page="biz" style="display:none">')
    if i1 < 0: raise SystemExit('R119 FAIL B6')
    i2 = s.find('\n', i1)
    s = s[:i1] + s[i2+1:]
    # B7. 업체별 검색 모달 HTML 삭제
    s = cut(s, '<div class="overlay" id="bizSearchOverlay" style="display:none">', '<!-- ─── 내 프로필 Modal', '', 'B7')
    # ── 분류 설정 ──
    # C1. 설정 모달의 분류 설정 패널 HTML
    s = cut(s, '    <!-- 패널: 분류 설정 -->', '    <div class="cfg-tab-panel" id="cfgPanelFirebase">', '', 'C1')
    # C2. 분류 설정 탭 버튼
    s = rep1(s, '      <button class="cfg-tab" data-cfg-tab="categories" style="display:none">분류 설정</button>\n', '', 'C2')
    # C3. 분류 편집 JS (cfgCatDraft ~ cfgCatClose 바인딩)
    s = cut(s, '  let cfgCatDraft = []; // 편집 중 임시 목록', '  function defaultMembers() {', '', 'C3')
    # C4. 설정 모달 열 때 분류 목록 렌더 호출 제거
    s = rep1(s, '    renderCfgCatList();\n', '', 'C4')
    # C5. CAT 색상 프록시/헬퍼 제거 (schedCategories 선언은 데이터 호환용 유지)
    s = rep1(s, """  // 헬퍼: 이름으로 카테고리 조회
  function catByName(name) { return schedCategories.find(c => c.name === name) || { color:'#9ca3af', bg:'#f9fafb', icon:'📌' }; }
  const CAT_COLOR = new Proxy({}, { get: (_, n) => catByName(n).color });
  const CAT_BG    = new Proxy({}, { get: (_, n) => catByName(n).bg });
  const CAT_ICON  = new Proxy({}, { get: (_, n) => catByName(n).icon });
""", '', 'C5')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        before = len(s)
        s = apply_r119(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r118 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r118 2026-08-20 -->', '<!-- test build r119 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path, 'removed ~%d chars' % (before - len(s)))
