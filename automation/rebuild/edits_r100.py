# -*- coding: utf-8 -*-
# r100: 메모 보드도 직원 필터(projMemberFilter) 적용 — 전체=모두의 메모, 특정 직원 선택 시 그 직원 메모만.
#       (열람은 전원 가능 그대로; 작성 중인 초안/업체수정 중 카드는 필터와 무관하게 항상 표시)

R100_EDITS = [

# (1) 직원 필터 변경 시 메모 보드도 강제 재렌더
("""  window.projFilterMember = function(mid){ _projFilterMember = mid||'all'; _projRenderList(); };""",
 """  window.projFilterMember = function(mid){ _projFilterMember = mid||'all'; _projRenderList(); _pmRender(true); };"""),

# (2) 메모 목록에 작성자 필터 적용
("""    var list=projMemos.filter(function(m){ return _pmShowHidden ? true : !m.hidden; });""",
 """    var list=projMemos.filter(function(m){
      if(m.id===_pmDraftId || m.id===_pmVendEditFor) return true;   // 작성/수정 중 카드는 항상 표시
      if(_projFilterMember!=='all' && m.memberId!==_projFilterMember) return false;   // 직원 필터
      return _pmShowHidden ? true : !m.hidden;
    });"""),
]

def apply_r100(s, path):
    for i,(old,new) in enumerate(R100_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R100 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r100(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r99 2026-08-19 -->') == 1
            s = s.replace('<!-- test build r99 2026-08-19 -->', '<!-- test build r100 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
