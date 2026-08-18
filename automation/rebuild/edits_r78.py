# -*- coding: utf-8 -*-
# r78: 팀원 일정 — 상단 목표·주간 이슈 패널 숨김 (재작성본 v3)

OLD = '''  <div class="wk-top-panels" style="display:flex;gap:12px;align-items:stretch;flex-wrap:wrap;margin-bottom:12px">'''
NEW = '''  <div class="wk-top-panels" style="display:none;gap:12px;align-items:stretch;flex-wrap:wrap;margin-bottom:12px">'''

def apply_r78(s, path):
    n = s.count(OLD)
    if n != 1: raise SystemExit('R78 FAIL %s count %d' % (path, n))
    return s.replace(OLD, NEW)

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r78(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r77 2026-08-14 -->') == 1
        s = s.replace('<!-- test build r77 2026-08-14 -->', '<!-- test build r78 2026-08-14 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
