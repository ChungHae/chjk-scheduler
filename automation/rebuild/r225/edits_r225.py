# -*- coding: utf-8 -*-
# r225 (사용자 요청 2026-10-13): 개인 일정에서 '내 담당 업체' 매출 보기.
#   · 같은 회사 견적을 5회 이상 저장한 사람이 그 회사 담당으로 자동 편입 (여럿이면 가장 많이 쓴 1명, 동률은 최근 작성자).
#   · 관리자는 수동으로 담당을 지정/해제 (수동이 자동보다 우선, "(담당 없음)" 지정은 자동 편입도 막음).
#   · 메모장 도구줄 버튼 → 팝업: 업체별 올해·작년·재작년 매출(매출계산서 공급가, 서울+화성) · 견적 건수 · 합계.
#   · 견적 저장 시 새로 담당이 되면 그 사람 일정에 '담당 업체 편입' 완료 줄.
#   자료: sched_client_owner = { m:{업체명:{who,by,at}} 수동, a:{업체명:{who,at}} 자동 기록 }  (KEYS·백업·복원 배관 포함)
#
# ※ 편집 내용(OPS)은 apply_r225.js 한 곳에만 두고, 이 파일은 그 OPS 를 읽어 적용한다.
#    python3 edits_r225.py <index.html> [<test/index.html>]
#    OPS 규칙: MARKER 는 test 만 · KEYS 는 live 2 / test 3 · CSS_TEST(r224 있을 때) / CSS_LIVE(없을 때) 둘 중 하나만 1.
import io, sys, json, os, re

def load_ops():
    here = os.path.dirname(os.path.abspath(__file__))
    with io.open(os.path.join(here, 'apply_r225.js'), 'r', encoding='utf-8') as f: js = f.read()
    m = re.search(r'var OPS = (\[.*?\]);\n  for\(var i=0', js, re.S)
    if not m: raise SystemExit('apply_r225.js 에서 OPS 를 찾지 못했습니다')
    return json.loads(m.group(1))

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R225 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r225(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    has_r224 = '#cuMineOverlay table' in s
    for old, new, exp, label in load_ops():
        if label == 'MARKER' and not is_test: continue
        if label == 'KEYS' and is_test: exp = 3
        if label == 'CSS_TEST':
            if not has_r224: continue
            exp = 1
        if label == 'CSS_LIVE':
            if has_r224: continue
            exp = 1
        s = rep(s, old, new, exp, label)
    return s

if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r225(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r225 applied:', path)
