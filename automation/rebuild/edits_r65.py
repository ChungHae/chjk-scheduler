# -*- coding: utf-8 -*-
# r65: 업체 표 무한 스크롤 — 처음 200개, 바닥 근처에서 200개씩 추가 로드
R65_EDITS = [
# E1: 상태 + 스크롤 리스너
("""  var _clxQ = '';""",
 """  var _clxQ = '';
  var _clxShown = 200;   // 무한 스크롤: 처음 200개, 바닥 근처에서 200개씩 추가
  window.addEventListener('scroll', function(){
    var pg=document.getElementById('pageClients');
    if(!pg || !pg.classList.contains('active')) return;
    if(_clxExp!==null) return;                             // 펼침/편집 중에는 추가 로드 정지
    if(!document.getElementById('clxMoreNote')) return;    // 더 불러올 항목이 없으면 정지
    var de=document.documentElement;
    if(de.scrollHeight - de.scrollTop - de.clientHeight > 400) return;
    _clxShown += 200;
    _clxRender();
  }, {passive:true});"""),

# E2: 검색 시 200개로 초기화
("""  window.clxSearchInput = function(v){ _clxQ = String(v||'').trim().toLowerCase(); _clxRender(); };""",
 """  window.clxSearchInput = function(v){ _clxQ = String(v||'').trim().toLowerCase(); _clxShown = 200; _clxRender(); };"""),

# E3: 300 고정 캡 → 표시 개수 기반 + 안내 문구
("""    var _capNote='';
    if(list.length>300){
      _capNote='<div style="text-align:center;padding:8px;color:#9ca3af;font-size:11.5px">상위 300개만 표시 중 (전체 '+list.length+'개) · 검색으로 찾아주세요</div>';
      list=list.slice(0,300);
      if(_clxExp && _clxExp!=='' && !list.some(function(c){ return c[0]===_clxExp; })){
        var _exRow=all.filter(function(c){ return c[0]===_clxExp; });
        list=_exRow.concat(list);   // 펼친 업체는 표시 제한과 무관하게 맨 위에 노출
      }
    }""",
 """    var _total=list.length;
    var _capNote='';
    if(_total>_clxShown){
      _capNote='<div id="clxMoreNote" style="text-align:center;padding:10px;color:#9ca3af;font-size:11.5px">전체 '+_total+'개 중 '+_clxShown+'개 표시 &middot; 아래로 스크롤하면 더 불러옵니다</div>';
      list=list.slice(0,_clxShown);
      if(_clxExp && _clxExp!=='' && !list.some(function(c){ return c[0]===_clxExp; })){
        var _exRow=all.filter(function(c){ return c[0]===_clxExp; });
        list=_exRow.concat(list);   // 펼친 업체는 표시 제한과 무관하게 맨 위에 노출
      }
    }"""),

# E4: 페이지 진입 시 초기화
("""    if (page === 'clients'){ _clxExp=null; _clxQ=''; var _cx8=document.getElementById('clxSearch'); if(_cx8) _cx8.value=''; renderClientsPage(); }""",
 """    if (page === 'clients'){ _clxExp=null; _clxQ=''; _clxShown=200; var _cx8=document.getElementById('clxSearch'); if(_cx8) _cx8.value=''; renderClientsPage(); }"""),
]
def apply_r65(s, path):
    for i,(old,new) in enumerate(R65_EDITS):
        n = s.count(old)
        if n != 1: raise SystemExit('R65 FAIL %s edit %d count %d' % (path, i, n))
        s = s.replace(old, new)
    return s
if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r65(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r64 2026-08-13 -->') == 1
            s = s.replace('<!-- test build r64 2026-08-13 -->', '<!-- test build r65 2026-08-13 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
