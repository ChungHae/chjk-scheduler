# -*- coding: utf-8 -*-
# r120: 프로젝트 숨김 기능 — 메모와 동일한 방식.
#       펼친 패널에 숨김/복원 버튼(등록자만), 툴바에 "숨김 프로젝트 표시" 체크박스,
#       숨긴 프로젝트는 목록에서 제외(체크 시 흐리게+숨김 배지로 표시). p.hidden 은 기존 동기화로 저장.

# (old, new, expected_count)
R120_EDITS = [

# (1) 툴바: 숨김 프로젝트 표시 체크박스 추가
("""<input type="checkbox" onchange="pmToggleHidden(this)" style="width:13px;height:13px;accent-color:#1B3A6B;cursor:pointer">숨김 메모 표시</label>""",
 """<input type="checkbox" onchange="pmToggleHidden(this)" style="width:13px;height:13px;accent-color:#1B3A6B;cursor:pointer">숨김 메모 표시</label>
        <label style="display:inline-flex;align-items:center;gap:5px;font-size:11.5px;color:#6b7280;cursor:pointer;user-select:none;white-space:nowrap;margin-left:10px;flex:0 0 auto"><input type="checkbox" onchange="projToggleHiddenP(this)" style="width:13px;height:13px;accent-color:#1B3A6B;cursor:pointer">숨김 프로젝트 표시</label>""", 1),

# (2) 상태 + 토글/숨김 함수
("""  window.projFilterMember = function(mid){ _projFilterMember = mid||'all'; _projRenderList(); _pmRender(true); };""",
 """  window.projFilterMember = function(mid){ _projFilterMember = mid||'all'; _projRenderList(); _pmRender(true); };
  var _projShowHiddenP = false;
  window.projToggleHiddenP = function(el){ _projShowHiddenP = !!el.checked; _projRenderList(); };
  window.projToggleHide = function(pid){
    var p=projectsList.find(function(x){ return x.id===pid; }); if(!p) return;
    if(!(myMemberId && p.memberId===myMemberId)) return;   // 숨김/복원은 등록자만
    p.hidden = !p.hidden;
    if(p.hidden && _projExpId===pid) _projExpId=null;
    _projSave(); _projRenderList();
  };""", 1),

# (3) 목록 필터: 숨김 제외 (체크 시 표시)
("""      if(_projFilterMember!=='all' && p.memberId!==_projFilterMember) return false;
      if(q && _projSearchScope!=='memo'){""",
 """      if(_projFilterMember!=='all' && p.memberId!==_projFilterMember) return false;
      if(p.hidden && !_projShowHiddenP) return false;   // 숨김 프로젝트 (r120)
      if(q && _projSearchScope!=='memo'){""", 1),

# (4a) 행 흐림 표시
("""var tr='<tr onclick="openProjectView(\\''+p.id+'\\')" style="cursor:pointer;'+(exp?'background:#f4f8fe;':'')+(dim?""",
 """var tr='<tr onclick="openProjectView(\\''+p.id+'\\')" style="cursor:pointer;'+(exp?'background:#f4f8fe;':'')+(p.hidden?'opacity:.55;':'')+(dim?""", 1),

# (4b) 제목 옆 숨김 배지
("""+ '<span style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(exp?(_projDraft.title||'(제목 없음)'):(p.title||'(제목 없음)'))+'</span>'""",
 """+ '<span style="min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+esc(exp?(_projDraft.title||'(제목 없음)'):(p.title||'(제목 없음)'))+'</span>'
          + (p.hidden?'<span style="flex-shrink:0;font-size:10px;font-weight:700;color:#9ca3af;border:1px solid #d1d5db;padding:1px 5px">숨김</span>':'')""", 1),

# (5) 펼친 패널: 숨김/복원 버튼 (프로젝트 삭제 옆)
("""+   '<button type="button" onclick="deleteProject(\\''+p.id+'\\')" style="'+_PJ_BTN+';background:#fff;color:#dc2626;border:1px solid #dc2626">프로젝트 삭제</button>'""",
 """+   '<button type="button" onclick="deleteProject(\\''+p.id+'\\')" style="'+_PJ_BTN+';background:#fff;color:#dc2626;border:1px solid #dc2626">프로젝트 삭제</button>'
        +   '<button type="button" onclick="projToggleHide(\\''+p.id+'\\')" title="'+(p.hidden?'목록에 다시 표시':'목록에서 숨기기 (숨김 프로젝트 표시로 다시 볼 수 있음)')+'" style="'+_PJ_BTN+';background:#fff;color:#5b7ba6;border:1px solid #aac4e6">'+(p.hidden?'복원':'숨김')+'</button>'""", 1),
]

def apply_r120(s, path):
    for i,(old,new,exp) in enumerate(R120_EDITS):
        n = s.count(old)
        if n != exp: raise SystemExit('R120 FAIL %s edit %d count %d (expect %d)' % (path, i, n, exp))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r120(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r119 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r119 2026-08-20 -->', '<!-- test build r120 2026-08-21 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
