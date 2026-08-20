# -*- coding: utf-8 -*-
# r110: (1) 프로젝트 세부정보 업체명 검색에서 엔터 → 최상단 검색 업체 등록
#       (2) 검색 범위가 '프로젝트'여도 메모 보드가 같은 검색어로 필터되도록
#           (해당 없는 메모는 숨김 — 이제 검색어가 있으면 모든 범위에서 메모 필터)

# (old, new, expected_count)
R110_EDITS = [

# (1a) 입력칸에 keydown 연결
("""onfocus="pjdVendorSearch(this)" onblur="pjdVendorBlur()\"""",
 """onfocus="pjdVendorSearch(this)" onkeydown="pjdVendorKey(event,this)" onblur="pjdVendorBlur()\"""", 1),

# (1b) 엔터 → 최상단 검색 결과 등록
("""  window.pjdVendorBlur=function(){ setTimeout(function(){ var b=document.getElementById('pjdVendorSug'); if(b) b.style.display='none'; },150); };""",
 """  window.pjdVendorBlur=function(){ setTimeout(function(){ var b=document.getElementById('pjdVendorSug'); if(b) b.style.display='none'; },150); };
  window.pjdVendorKey=function(ev, el){
    if(ev.key!=='Enter') return;
    ev.preventDefault();
    var box=document.getElementById('pjdVendorSug');
    var first=(box && box.style.display!=='none') ? box.querySelector('[data-nm]') : null;
    if(first){ pjdVendorAdd(first.dataset.nm); return; }
    var q=String(el.value||'').trim().toLowerCase(); if(!q) return;
    try{ ensureClientList(); }catch(_e){}
    var hit=allClients().find(function(c){ return String(c[0]).toLowerCase().indexOf(q)>=0 && !_pjD.vendors.some(function(v){ return v.name===c[0]; }); });
    if(hit) pjdVendorAdd(hit[0]);
  };""", 1),

# (2) 검색어가 있으면 범위와 무관하게 메모 보드도 필터
("""      if(_projSearchQ && _projSearchScope!=='proj'){""",
 """      if(_projSearchQ){""", 1),
]

def apply_r110(s, path):
    for i,(old,new,exp) in enumerate(R110_EDITS):
        n = s.count(old)
        if n != exp: raise SystemExit('R110 FAIL %s edit %d count %d (expect %d)' % (path, i, n, exp))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r110(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r109 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r109 2026-08-20 -->', '<!-- test build r110 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
