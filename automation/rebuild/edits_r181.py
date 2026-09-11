# -*- coding: utf-8 -*-
# r181 편집 모듈(저장소용 로더) — 치환 목록은 r181/apply_r181.js 의 OPS(JSON) 를 그대로 읽어 쓴다.
#  (작업공간의 원본 edits_r181.py 와 결과가 같다: live 7d5d8704→d7e81e80, test e4215538→65b6c0c9)
# r181 내용
#  ① 견적 규격 자동완성: Enter 는 '입력한 그대로'. 후보는 ↓/↑ 로 골라 Enter 하거나 마우스 클릭했을 때만 들어간다.
#     (입력한 규격과 완전히 같은 후보가 있으면 그것은 Enter 로 들어간다) 예) SY5120-5LZ-01 → -Q 가 들어가던 문제 해결.
#  ② SMC 가격 확인 대기열(smcQueue, sched_smc_queue, 전원 동기화): 견적 저장 시 '가격표에 없는 규격 + E가' 줄을 모은다.
#     견적 탭 서브탭 'SMC 확인' 에서 금요일 17시 이후 SMC 사이트 가격 확인 → [등록] 하면 SMC 가격표(priceMakers 중 'SMC')에
#     행 추가/갱신(ega, 확판/소물은 extra) → E가가 원장에 연동(기존 오버레이). [제외]=SMC 아님. 메모장 맨 위 배너.
#  등록 지점 6곳: 선언·saveAll·doFbSave·reloadState·KEYS(live 2 / test 3)·전체백업.
# 사용: python3 edits_r181.py index.html test/index.html   (같은 폴더의 r181/apply_r181.js 필요)
import io, sys, os, json, re

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R181 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def load_ops():
    here = os.path.dirname(os.path.abspath(__file__))
    js = io.open(os.path.join(here, 'r181', 'apply_r181.js'), encoding='utf-8').read()
    m = re.search(r'var OPS = (\[.*?\]);\n  for\(', js, re.S)
    return json.loads(m.group(1))

def apply_r181(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in load_ops():
        if not is_test:
            if label == 'MARKER': continue
            if label == 'KEYS': exp = 2
        s = rep(s, old, new, exp, label)
    return s

if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s = f.read()
        s = apply_r181(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r181 applied:', path)
