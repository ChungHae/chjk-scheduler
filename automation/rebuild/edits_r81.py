# -*- coding: utf-8 -*-
# r81: 프로젝트 목록 표 — 프로젝트명 1/3, 나머지 균등 (재작성본 v3)

OLD = "'<colgroup><col><col style=\"width:110px\"><col style=\"width:120px\"><col style=\"width:120px\"><col style=\"width:80px\"></colgroup>'"
NEW = "'<colgroup><col style=\"width:33.36%\"><col style=\"width:16.66%\"><col style=\"width:16.66%\"><col style=\"width:16.66%\"><col style=\"width:16.66%\"></colgroup>'"

def apply_r81(s, path):
    n = s.count(OLD)
    if n != 1: raise SystemExit('R81 FAIL %s count %d' % (path, n))
    return s.replace(OLD, NEW)

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r81(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r80 2026-08-14 -->') == 1
            s = s.replace('<!-- test build r80 2026-08-14 -->', '<!-- test build r81 2026-08-14 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
