# -*- coding: utf-8 -*-
# r103: (1) 메모 제목(업체명) 글씨를 검정색으로 (표시 + 인라인 수정 입력칸)
#       (2) 프로젝트 검색창에 범위 선택(프로젝트/메모) 추가
#           - 프로젝트: 프로젝트명 + 세부정보 거래처명 + 담당자 이름으로 검색
#           - 메모: 제목(거래처명)으로 검색 (메모 보드 필터)

# (old, new, expected_count)
R103_EDITS = [

# (1a) 접힌 제목 span 색상
("""text-overflow:ellipsis;white-space:nowrap;font-size:12.5px;font-weight:700;color:#14305c;""",
 """text-overflow:ellipsis;white-space:nowrap;font-size:12.5px;font-weight:700;color:#1a1a1a;""", 1),

# (1b) 제목 수정/추가 입력칸 색상 (pm-vend-in, pmVendAddStart, 구형 폼 입력 3곳)
("""font-size:12px;font-weight:700;color:#14305c;font-family:inherit""",
 """font-size:12px;font-weight:700;color:#1a1a1a;font-family:inherit""", 3),

# (2a) 툴바: 검색 범위 select 추가 + placeholder 갱신
("""        <input type="text" id="projSearch" class="q-flat" placeholder="프로젝트명 검색…" autocomplete="off" oninput="projSearchInput(this.value)">""",
 """        <select id="projSearchScope" class="q-flat" onchange="projSearchScopeSet(this.value)" style="width:92px;flex:0 0 auto;background:#fff;color:#1a1a1a;cursor:pointer"><option value="proj">프로젝트</option><option value="memo">메모</option></select>
        <input type="text" id="projSearch" class="q-flat" placeholder="프로젝트명·거래처·담당자 검색…" autocomplete="off" oninput="projSearchInput(this.value)">""", 1),

# (2b) 상태 변수 + 범위 전환 함수
("""  var _projSearchQ = '';""",
 """  var _projSearchQ = '', _projSearchScope = 'proj';""", 1),

("""  window.projSearchInput = function(v){ _projSearchQ = String(v||'').trim().toLowerCase(); _projRenderList(); };""",
 """  window.projSearchInput = function(v){ _projSearchQ = String(v||'').trim().toLowerCase(); _projRenderList(); _pmRender(true); };
  window.projSearchScopeSet = function(v){
    _projSearchScope = (v==='memo')?'memo':'proj';
    var i=document.getElementById('projSearch');
    if(i) i.placeholder = (_projSearchScope==='memo')?'제목·거래처 검색…':'프로젝트명·거래처·담당자 검색…';
    _projRenderList(); _pmRender(true);
  };""", 1),

# (2c) 프로젝트 목록 필터: 프로젝트명 + 세부정보 거래처 + 담당자 이름 (메모 범위일 땐 미적용)
("""      if(q && String(p.title||'').toLowerCase().indexOf(q)<0) return false;""",
 """      if(q && _projSearchScope==='proj'){
        var _hay=String(p.title||'');
        var _dt=p.detail||{};
        (_dt.vendors||[]).forEach(function(v){ _hay+=' '+String(v.name||''); (v.contacts||[]).forEach(function(c){ _hay+=' '+String(c.name||''); }); });
        if(_hay.toLowerCase().indexOf(q)<0) return false;
      }""", 1),

# (2d) 메모 보드 필터: 제목(거래처명) 검색 (프로젝트 범위일 땐 미적용)
("""      if(_projFilterMember!=='all' && m.memberId!==_projFilterMember) return false;   // 직원 필터
      return _pmShowHidden ? true : !m.hidden;""",
 """      if(_projFilterMember!=='all' && m.memberId!==_projFilterMember) return false;   // 직원 필터
      if(_projSearchQ && _projSearchScope==='memo'){
        if((m.vendors||[]).join(' ').toLowerCase().indexOf(_projSearchQ)<0) return false;   // 제목(거래처) 검색
      }
      return _pmShowHidden ? true : !m.hidden;""", 1),
]

def apply_r103(s, path):
    for i,(old,new,exp) in enumerate(R103_EDITS):
        n = s.count(old)
        if n != exp: raise SystemExit('R103 FAIL %s edit %d count %d (expect %d)' % (path, i, n, exp))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r103(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r102 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r102 2026-08-20 -->', '<!-- test build r103 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
