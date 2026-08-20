# -*- coding: utf-8 -*-
# r106: 일정 등록 기능 전면 숨김 (1단계 — 삭제 아님, 화면에서만 제거)
#  - 프로젝트 페이지 툴바의 "프로젝트" 라벨 제거
#  - 탭: 개인 일정(project) → "일정" 이름, 시작 탭/일정 클릭 시 기본으로
#  - 팀원 일정(weekly) 탭 숨김
#  - 달력(personal): 일정 등록 버튼·셀 클릭 등록·개인 일정/배정업무 표시·
#    미완료 N건·미확인 코멘트·출근 점·메모 핀·모바일 오늘 일정·업무 제안 전부 숨김
#    (공지·연차 표시는 유지)

# (old, new, expected_count)
R106_EDITS = [

# 1) 툴바 "프로젝트" 라벨 제거
("""        <span class="inv-flat-label">프로젝트</span>
""", "", 1),

# 2) 탭 이름·기본 탭
("""<button class="sub-tab" data-page="project">개인 일정</button>""",
 """<button class="sub-tab active" data-page="project">일정</button>""", 1),
("""<button class="sub-tab active" data-page="personal">달력</button>""",
 """<button class="sub-tab" data-page="personal">달력</button>""", 1),

# 3) 팀원 일정 탭 숨김 (완전 삭제 아님 — 복원 시 display 제거)
("""<button class="sub-tab" data-page="weekly">""",
 """<button class="sub-tab" data-page="weekly" style="display:none">""", 1),

# 4) 일정 대분류 클릭/로고/시작 → project
("""ts.addEventListener('click', function(){ switchPage('personal'); })""",
 """ts.addEventListener('click', function(){ switchPage('project'); })""", 1),
("""lg.addEventListener('click', function(){ switchPage('personal'); })""",
 """lg.addEventListener('click', function(){ switchPage('project'); })""", 1),
("""  switchPage('personal');   // 기본 탭을 개인일정으로 표시""",
 """  switchPage('project');   // 기본 탭을 일정(구 프로젝트)으로 표시 (r106)""", 1),

# 5) 달력: 일정 등록 버튼 항상 숨김
("""    const entryBtn = document.getElementById('btnEntryAdd');
    if (entryBtn) entryBtn.style.display = hasProfile ? '' : 'none';""",
 """    const entryBtn = document.getElementById('btnEntryAdd');
    if (entryBtn) entryBtn.style.display = 'none';   // r106 일정 등록 숨김""", 1),

# 6) 달력 셀 클릭: 일정 등록 창 열기 제거 (관리자 공지 추가만 유지)
("""        <div ${_viewerRO ? '' : (_calVacOnly ? `onclick="openBroadcastAdd('${dStr}')" title="클릭하여 전 직원 공지 일정 추가/관리"` : `onclick="openEntry('${selId}','${dStr}')" title="클릭하여 일정 추가/수정"`)}""",
 """        <div ${(!_viewerRO && _calVacOnly) ? `onclick="openBroadcastAdd('${dStr}')" title="클릭하여 전 직원 공지 일정 추가/관리"` : ''}""", 1),
("""cursor:${_viewerRO?'default':'pointer'}""",
 """cursor:${(!_viewerRO && _calVacOnly)?'pointer':'default'}""", 1),

# 7) 달력 셀: 개인 일정·배정 업무·예전 일정 데이터 표시 숨김
("""      const dayAssign = _calVacOnly ? [] : assignments.filter(a => a.assigneeId === selId && a.date === dStr);""",
 """      const dayAssign = [];   // r106 일정 숨김""", 1),
("""      const dayPsched = _calVacOnly ? [] : personalSchedules.filter(s => s.memberId === selId && isPschedOnDate(s, dStr)).sort((a,b)=>_schedTimeOrder(a.time)-_schedTimeOrder(b.time));""",
 """      const dayPsched = [];   // r106 일정 숨김""", 1),
("""      const projects = getProjects(en);
      const plans    = getPlans(en);""",
 """      const projects = [], plans = [];   // r106 일정 숨김""", 1),

# 8) 달력 셀: 메모 핀·출근 점·미완료/미확인 표시 숨김
("""      const _memoArr = schedComments[commentKey(selId, dStr)] || [];
      const _hasMemo = _calVacOnly ? false : _memoArr.some(c => c && c.text);""",
 """      const _hasMemo = false;   // r106 일정 메모 숨김""", 1),
("""      if (isTod && !_calVacOnly) {""",
 """      if (false) {   // r106 미완료·미확인 표시 숨김""", 1),
("""              ${(en.status === '출근' || en.status === '정상출근')
                ? `<span style="width:7px;height:7px;border-radius:50%;background:#2f5288"></span>`
                : ''}""",
 """""", 1),

# 9) 모바일 오늘 일정 숨김
("""    var el = document.getElementById('personalTodayMobile'); if(!el) return;""",
 """    var el = document.getElementById('personalTodayMobile'); if(!el) return;
    el.innerHTML=''; return;   // r106 일정 숨김""", 1),

# 10) 업무 제안 버튼 전부 숨김
("""      suggestBtn.style.display = (hasProfile && _canPropose() && myAssigned.length) ? '' : 'none';""",
 """      suggestBtn.style.display = 'none';   // r106 업무 제안 숨김""", 1),
("""        suggestBtnL.style.display = (hasProfile && _canPropose() && myAssignedL.length) ? '' : 'none';""",
 """        suggestBtnL.style.display = 'none';   // r106 업무 제안 숨김""", 1),
("""      roAssignBtn.style.display = (_canPropose() && memberId !== myMemberId) ? '' : 'none';   // 관리자는 프로필(멤버) 없어도 제안 가능""",
 """      roAssignBtn.style.display = 'none';   // r106 업무 제안 숨김""", 1),
]

def apply_r106(s, path):
    for i,(old,new,exp) in enumerate(R106_EDITS):
        n = s.count(old)
        if n != exp: raise SystemExit('R106 FAIL %s edit %d count %d (expect %d)' % (path, i, n, exp))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r106(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r105 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r105 2026-08-20 -->', '<!-- test build r106 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
