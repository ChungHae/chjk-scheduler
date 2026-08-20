# -*- coding: utf-8 -*-
# r115: 검색어 없이도 범위 선택만으로 보기 전환 —
#       '프로젝트' 선택 = 프로젝트 목록만, '메모' 선택 = 메모 보드만, '전체' = 둘 다.
#       검색어를 입력하면 보이는 쪽 안에서만 필터. (r111/r113의 q 조건 제거)

R115_EDITS = [

# (1) 메모 보드: 프로젝트 범위면 검색어와 무관하게 숨김
("""      if(_projSearchQ){
        if(_projSearchScope==='proj') return false;   // 프로젝트 범위 검색 중엔 메모 전체 숨김
        if((m.vendors||[]).join(' ').toLowerCase().indexOf(_projSearchQ)<0) return false;   // 제목(거래처) 검색
      }""",
 """      if(_projSearchScope==='proj') return false;   // 프로젝트 전용 보기 — 메모 숨김 (r115)
      if(_projSearchQ){
        if((m.vendors||[]).join(' ').toLowerCase().indexOf(_projSearchQ)<0) return false;   // 제목(거래처) 검색
      }""", 1),

# (2) 프로젝트 목록: 메모 범위면 검색어와 무관하게 숨김
("""    if(q && _projSearchScope==='memo'){ _projExpId=null; box.innerHTML=''; return; }   // r113 메모 범위 검색 중엔 프로젝트 목록 숨김""",
 """    if(_projSearchScope==='memo'){ _projExpId=null; box.innerHTML=''; return; }   // r115 메모 전용 보기 — 프로젝트 목록 숨김""", 1),
]

def apply_r115(s, path):
    for i,(old,new,exp) in enumerate(R115_EDITS):
        n = s.count(old)
        if n != exp: raise SystemExit('R115 FAIL %s edit %d count %d (expect %d)' % (path, i, n, exp))
        s = s.replace(old, new)
    return s

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r115(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r114 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r114 2026-08-20 -->', '<!-- test build r115 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
