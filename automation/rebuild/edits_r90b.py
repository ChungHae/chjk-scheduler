# -*- coding: utf-8 -*-
# r90b: 카드 제목 업체 연결 문자 수정 — esc()가 &middot;를 문자 그대로 노출하던 버그. (재작성본 v2)

OLD = """esc(m.vendors.join(' &middot; '))"""
NEW = """esc(m.vendors.join(' · '))"""

def apply_r90b(s, path):
    n = s.count(OLD)
    if n != 1: raise SystemExit('R90B FAIL %s count %d' % (path, n))
    return s.replace(OLD, NEW)

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r90b(s, path)
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
