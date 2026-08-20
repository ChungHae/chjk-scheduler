# -*- coding: utf-8 -*-
# r105: (1) 검색 범위에 "전체" 추가 (프로젝트+메모 동시 검색, 기본값=전체)
#       (2) 메모 보드: 메모 5개 전부 표시 + "더 보기/접기"를 그리드 아래 가로 바로 이동

# (old, new, expected_count)
R105_EDITS = [

# (1a) 범위 select에 전체 옵션 (기본 선택)
("""<option value="proj">프로젝트</option><option value="memo">메모</option></select>""",
 """<option value="all">전체</option><option value="proj">프로젝트</option><option value="memo">메모</option></select>""", 1),

# (1b) 기본 placeholder
("""placeholder="프로젝트명·거래처·담당자 검색…" autocomplete="off" oninput="projSearchInput(this.value)">""",
 """placeholder="프로젝트·메모 검색…" autocomplete="off" oninput="projSearchInput(this.value)">""", 1),

# (1c) 기본 범위 = 전체
("""  var _projSearchQ = '', _projSearchScope = 'proj';""",
 """  var _projSearchQ = '', _projSearchScope = 'all';""", 1),

# (1d) 범위 전환 함수 3단계
("""  window.projSearchScopeSet = function(v){
    _projSearchScope = (v==='memo')?'memo':'proj';
    var i=document.getElementById('projSearch');
    if(i) i.placeholder = (_projSearchScope==='memo')?'제목·거래처 검색…':'프로젝트명·거래처·담당자 검색…';
    _projRenderList(); _pmRender(true);
  };""",
 """  window.projSearchScopeSet = function(v){
    _projSearchScope = (v==='memo'||v==='proj')?v:'all';
    var i=document.getElementById('projSearch');
    if(i) i.placeholder = (_projSearchScope==='memo')?'제목·거래처 검색…':((_projSearchScope==='proj')?'프로젝트명·거래처·담당자 검색…':'프로젝트·메모 검색…');
    _projRenderList(); _pmRender(true);
  };""", 1),

# (1e) 프로젝트 목록: 메모 전용 범위가 아니면 검색 적용
("""      if(q && _projSearchScope==='proj'){""",
 """      if(q && _projSearchScope!=='memo'){""", 1),

# (1f) 메모 보드: 프로젝트 전용 범위가 아니면 검색 적용
("""      if(_projSearchQ && _projSearchScope==='memo'){""",
 """      if(_projSearchQ && _projSearchScope!=='proj'){""", 1),

# (2a) 5개 전부 표시 (기존: 4개+더보기 카드)
("""    if(!_pmShowAll && list.length>CAP){ shown=list.slice(0,CAP-1); more=list.length-(CAP-1); }""",
 """    if(!_pmShowAll && list.length>CAP){ shown=list.slice(0,CAP); more=list.length-CAP; }""", 1),

# (2b) 더 보기/접기: 그리드 카드 → 그리드 아래 가로 바
("""    if(more>0){
      cards += '<div onclick="pmToggleAll()" style="aspect-ratio:1/1;background:#fbfcfe;border:1px dashed #aab8ca;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:12.5px;font-weight:700;color:#5b7ba6" onmouseover="this.style.background=\\'#f4f8fe\\'" onmouseout="this.style.background=\\'#fbfcfe\\'">&#65291;'+more+'개 더 보기</div>';
    } else if(_pmShowAll && list.length>CAP){
      cards += '<div onclick="pmToggleAll()" style="aspect-ratio:1/1;background:#fbfcfe;border:1px dashed #aab8ca;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:12.5px;font-weight:700;color:#5b7ba6" onmouseover="this.style.background=\\'#f4f8fe\\'" onmouseout="this.style.background=\\'#fbfcfe\\'">접기</div>';
    }
    var formCard='';
    if(_pmForm && !_pmEditId){ formCard=_pmFormCardHtml(null); }
    box.innerHTML = (cards||formCard)
      ? ('<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px">'+formCard+cards+'</div>')
      : '';""",
 """    var moreBar='';
    if(more>0){
      moreBar = '<div onclick="pmToggleAll()" style="margin-top:8px;padding:7px 0;text-align:center;background:#fbfcfe;border:1px dashed #aab8ca;cursor:pointer;font-size:12.5px;font-weight:700;color:#5b7ba6" onmouseover="this.style.background=\\'#f4f8fe\\'" onmouseout="this.style.background=\\'#fbfcfe\\'">&#65291;'+more+'개 더 보기</div>';
    } else if(_pmShowAll && list.length>CAP){
      moreBar = '<div onclick="pmToggleAll()" style="margin-top:8px;padding:7px 0;text-align:center;background:#fbfcfe;border:1px dashed #aab8ca;cursor:pointer;font-size:12.5px;font-weight:700;color:#5b7ba6" onmouseover="this.style.background=\\'#f4f8fe\\'" onmouseout="this.style.background=\\'#fbfcfe\\'">접기</div>';
    }
    var formCard='';
    if(_pmForm && !_pmEditId){ formCard=_pmFormCardHtml(null); }
    box.innerHTML = (cards||formCard)
      ? ('<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px">'+formCard+cards+'</div>'+moreBar)
      : '';""", 1),
]

def apply_r105(s, path):
    for i,(old,new,exp) in enumerate(R105_EDITS):
        n = s.count(old)
        if n != exp: raise SystemExit('R105 FAIL %s edit %d count %d (expect %d)' % (path, i, n, exp))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r105(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r104 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r104 2026-08-20 -->', '<!-- test build r105 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
