# -*- coding: utf-8 -*-
# r89: 메모 내용이 전부 완료돼도 거래처명(제목)은 취소선·회색 없이 원래 색 유지 (재작성본 v2)

OLD = """font-size:12.5px;font-weight:700;color:#14305c;'+(allDone?'text-decoration:line-through;color:#9ca3af;':'')+'"""
NEW = """font-size:12.5px;font-weight:700;color:#14305c;"""

def apply_r89(s, path):
    n = s.count(OLD)
    if n != 1: raise SystemExit('R89 FAIL %s count %d' % (path, n))
    return s.replace(OLD, NEW)

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r89(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r88 2026-08-19 -->') == 1
            s = s.replace('<!-- test build r88 2026-08-19 -->', '<!-- test build r89 2026-08-19 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
