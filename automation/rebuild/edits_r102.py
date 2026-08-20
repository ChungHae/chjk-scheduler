# -*- coding: utf-8 -*-
# r102: 메모 보드 기본 노출을 최대 2줄(10개) → 1줄(5개)로 축소.
#       5개 초과 시 4개 + "+N개 더 보기" 카드. (더 보기/접기 동작은 기존 그대로)

OLD = """    var CAP=10;"""
NEW = """    var CAP=5;"""

def apply_r102(s, path):
    n = s.count(OLD)
    if n != 1: raise SystemExit('R102 FAIL %s count %d' % (path, n))
    return s.replace(OLD, NEW)

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r102(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r101 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r101 2026-08-20 -->', '<!-- test build r102 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
