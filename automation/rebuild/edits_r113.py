# -*- coding: utf-8 -*-
# r113: 대칭 정리 — '메모' 범위로 검색 중일 때는 프로젝트 목록을 아예 숨김.
#       (r111의 반대 방향: 프로젝트는 '전체' 또는 '프로젝트' 범위에서만 검색/표시)

OLD = """    var q=_projSearchQ;
    list = list.filter(function(p){
      if(p.id===_projExpId) return true;   // 펼쳐서 작업 중인 프로젝트는 항상 표시"""
NEW = """    var q=_projSearchQ;
    if(q && _projSearchScope==='memo'){ _projExpId=null; box.innerHTML=''; return; }   // r113 메모 범위 검색 중엔 프로젝트 목록 숨김
    list = list.filter(function(p){
      if(p.id===_projExpId) return true;   // 펼쳐서 작업 중인 프로젝트는 항상 표시"""

def apply_r113(s, path):
    n = s.count(OLD)
    if n != 1: raise SystemExit('R113 FAIL %s count %d' % (path, n))
    return s.replace(OLD, NEW)

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r113(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r112 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r112 2026-08-20 -->', '<!-- test build r113 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
