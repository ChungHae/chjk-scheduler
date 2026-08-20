# -*- coding: utf-8 -*-
# r108: 설정 모달의 "분류 설정" 탭 숨김 (일정 기능 숨김 1단계의 후속 —
#       분류는 할일/일정 카테고리 관리라 더 이상 불필요. 완전 삭제는 2단계에서)

OLD = """      <button class="cfg-tab" data-cfg-tab="categories">분류 설정</button>"""
NEW = """      <button class="cfg-tab" data-cfg-tab="categories" style="display:none">분류 설정</button>"""

def apply_r108(s, path):
    n = s.count(OLD)
    if n != 1: raise SystemExit('R108 FAIL %s count %d' % (path, n))
    return s.replace(OLD, NEW)

if __name__ == '__main__':
    import io
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r108(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r107 2026-08-20 -->') == 1
            s = s.replace('<!-- test build r107 2026-08-20 -->', '<!-- test build r108 2026-08-20 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
