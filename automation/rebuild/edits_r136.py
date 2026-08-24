# -*- coding: utf-8 -*-
# r136: [디자인 수정] 미배정 거래처 드롭다운 모서리 각지게.
#  견적 드롭다운 스타일(radius 8px)을 그대로 복사했더니, 항목 hover 하이라이트가
#  둥근 모서리를 따라 잘려 "라운딩되는" 것처럼 보임 — 매입매출 화면의 각진
#  디자인 규칙(border-radius:0)에 맞춰 컨테이너를 각지게 변경.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R136 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r136(s, path):
    s = rep(s, "dd.style.cssText='display:none;position:fixed;width:300px;background:#fff;border:1px solid #d6e4f5;border-radius:8px;box-shadow:0 8px 22px rgba(27,58,107,.15);max-height:260px;overflow:auto;z-index:100060';",
            "dd.style.cssText='display:none;position:fixed;width:300px;background:#fff;border:1px solid #d6e4f5;border-radius:0;box-shadow:0 8px 22px rgba(27,58,107,.15);max-height:260px;overflow:auto;z-index:100060';", 1, 'DD')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r136(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r135 2026-08-24 -->') == 1
            s = s.replace('<!-- test build r135 2026-08-24 -->', '<!-- test build r136 2026-08-24 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
