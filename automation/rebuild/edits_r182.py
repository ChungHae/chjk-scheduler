# -*- coding: utf-8 -*-
# r182 (사용자 요청 2026-09-11): SMC 확인 화면 — 치환 목록은 r182/apply_r182.js 의 OPS 를 읽는다(로더).
#  · 'SMC 사이트 열기' 링크 → http://www.smckorea.net/main/main.jsp (사용자 지정)
#  · 확판가·소물가는 SMC 사이트에서 확인되면 같이 등록 — 확판가 칸에 견적 구매가를 미리 채우지 않고 placeholder 참고값만.
# 결과: live d7e81e80→f2500c4c / test 65b6c0c9→83f39395
import io, sys, os, json, re

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R182 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def load_ops():
    here = os.path.dirname(os.path.abspath(__file__))
    js = io.open(os.path.join(here, 'r182', 'apply_r182.js'), encoding='utf-8').read()
    m = re.search(r'var OPS = (\[.*?\]);\n  for\(', js, re.S)
    return json.loads(m.group(1))

def apply_r182(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in load_ops():
        if not is_test and label == 'MARKER': continue
        s = rep(s, old, new, exp, label)
    return s

if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s = f.read()
        s = apply_r182(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r182 applied:', path)
