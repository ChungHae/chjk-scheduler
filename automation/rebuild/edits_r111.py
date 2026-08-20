# -*- coding: utf-8 -*-
# r111: 검색 동작 정정 — '프로젝트' 범위로 검색 중일 때는 메모 보드를 아예 숨김.
#       메모는 '전체' 또는 '메모' 범위에서만 표시/검색됨. (r110의 동작 수정)

OLD = """      if(_projSearchQ){
        if((m.vendors||[]).join(' ').toLowerCase().indexOf(_projSearchQ)<0) return false;   // 제목(거래처) 검색
      }"""
NEW = """      if(_projSearchQ){
        if(_projSearchScope==='proj') return false;   // 프로젝트 범위 검색 중엔 메모 전체 숨김
        if((m.vendors||[]).join(' ').toLowerCase().indexOf(_projSearchQ)<0) return false;   // 제목(거래처) 검색
      }"""

def apply_r111(s, path):
    n = s.count(OLD)
    if n != 1: raise SystemExit('R111 FAIL %s count %d' % (path, n))
    return s.replace(OLD, NEW)

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r111(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r110 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r110 2026-08-20 -->', '<!-- test build r111 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
