// r179 브라우저 적용기 — 저장소의 r178 원본 blob + r179 부품을 받아 모듈과 같은 치환을 수행한다.
// (edits_r179.py 의 apply_r179 를 JS 로 옮긴 것. 결과 git blob sha 가 기대값과 같을 때만 사용한다.)
function r179Apply(s, isTest, P){
  function rep(str, old, nw, exp, label){
    var n=str.split(old).length-1;
    if(n!==exp) throw new Error('R179 FAIL '+label+' count '+n+' (expect '+exp+')');
    return str.split(old).join(nw);
  }
  s = rep(s, "  let projectsList = load('sched_projects') ?? [];",
    "  let projectsList = load('sched_projects') ?? [];\n  let memoLines = load('sched_memos') ?? [];        // r179 메모장 줄 [{id,owner,text,parent,kind,vendor,to,name,phone,when,date,createdAt,done,doneAt,feedback,card,linked}]\n  let memoCards = load('sched_memo_cards') ?? {};   // r179 명함 사진 {cardId: dataURL}", 1, 'DECL');
  s = rep(s, "    save('sched_projects', projectsList);\n    save('sched_client_info', clientInfo);\n",
    "    save('sched_projects', projectsList);\n    save('sched_client_info', clientInfo);\n    save('sched_memos', memoLines);   // r179\n    save('sched_memo_cards', memoCards);\n", 1, 'SAVEALL');
  s = rep(s, "        sched_projects: projectsList,\n",
    "        sched_projects: projectsList,\n        sched_memos: memoLines,   // r179\n        sched_memo_cards: memoCards,\n", 1, 'FBPUT');
  s = rep(s, "    projectsList     = load('sched_projects') ?? [];\n",
    "    projectsList     = load('sched_projects') ?? [];\n    memoLines        = load('sched_memos') ?? [];   // r179\n    memoCards        = load('sched_memo_cards') ?? {};\n", 1, 'RELOAD');
  s = rep(s, "'sched_client_list','sched_projects','sched_client_info','sched_proj_memos'",
    "'sched_client_list','sched_projects','sched_client_info','sched_proj_memos','sched_memos','sched_memo_cards'", isTest?3:2, 'KEYS');
  s = rep(s, "      sched_projects: projectsList, sched_client_info: clientInfo, sched_proj_memos: projMemos,\n",
    "      sched_projects: projectsList, sched_client_info: clientInfo, sched_proj_memos: projMemos,\n      sched_memos: memoLines, sched_memo_cards: memoCards,   // r179\n", 1, 'BACKUP');
  s = rep(s, '  <button class="sub-tab active" data-page="project">일정</button>',
    '  <button class="sub-tab active" data-page="memo">일정</button>\n  <button class="sub-tab" data-page="project">완료</button>\n  <button class="sub-tab" data-page="weekly">주간</button>', 1, 'SUBNAV');
  s = rep(s, '  <div id="pageWeekly" class="page-section"></div><!-- r117: 팀원 일정 삭제 -->', P.markup_weekly + P.markup_memo, 1, 'MARKUP');
  s = rep(s, "    var _SCHED=['personal','weekly','biz','project','clients'];",
    "    var _SCHED=['personal','weekly','biz','project','clients','memo'];   // r179", 1, 'SCHED');
  s = rep(s, "const pageMap = { weekly:'pageWeekly',", "const pageMap = { memo:'pageMemo', weekly:'pageWeekly',", 1, 'PAGEMAP');
  s = rep(s,
    "    if (page === 'weekly') {\n" + (isTest ? "      _wkMobSel = null;   // 탭 진입 시 항상 오늘부터 (모바일 하루 이동 상태 초기화)\n" : "") +
    "      weekStart = getMonday(new Date());\n      render();\n      try{ window.scrollTo(0, 0); }catch(e){}\n      setTimeout(_scrollWeeklyToToday, 140);\n    }",
    "    if (page === 'weekly') { _wkStart = getMonday(new Date()); renderWeeklyPage(); }   // r179 주간 일정표\n    if (page === 'memo') { _mmEditing=null; renderMemoPage(true); setTimeout(function(){ try{ var _mi=document.getElementById('mmInput'); if(_mi && window.innerWidth>640) _mi.focus(); }catch(_e){} }, 60); }",
    1, 'HOOK');
  s = rep(s, "      else if(_id==='pageClients' && typeof renderClientsPage==='function') renderClientsPage();",
    "      else if(_id==='pageClients' && typeof renderClientsPage==='function') renderClientsPage();\n      else if(_id==='pageMemo' && typeof renderMemoPage==='function') renderMemoPage();   // r179 (편집 중이면 건너뜀)\n      else if(_id==='pageWeekly' && typeof renderWeeklyPage==='function') renderWeeklyPage();",
    1, 'REFRESH');
  s = rep(s, "switchPage('project');", "switchPage('memo');", 3, 'START');
  s = rep(s, "      if (_psShowBcast()) bcastBarsHtml(dStr).forEach(h => _lines.push(h));",
    "      // r179: 달력은 휴가만 (공지 막대 제거)", 1, 'CAL');
  s = rep(s, "    .page-section { display: none; }", P.css + "    .page-section { display: none; }", 1, 'CSS');
  s = rep(s, "  // ─── 개인 일정 페이지 ──────────────────────────────────", P.js + "  // ─── 개인 일정 페이지 ──────────────────────────────────", 1, 'JS');
  if(isTest) s = rep(s, "<!-- test build r178 2026-09-07 -->", "<!-- test build r179 2026-09-10 -->", 1, 'MARKER');
  return s;
}
if(typeof module!=='undefined') module.exports = r179Apply;
