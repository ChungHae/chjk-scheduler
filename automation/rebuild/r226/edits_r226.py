# -*- coding: utf-8 -*-
# r226 (사용자 요청 2026-10-13, 3건):
#   A) SMC 확인: 확판가 칸의 '견적 ○○' 안내(placeholder) 제거 → 별도 '견적가' 열(견적 때 넣은 구매가, 읽기 전용).
#   B) 메모장 맨 위 '내 담당 업체 N곳 · 올해/작년 매출' 카드 → 클릭하면 r225 팝업(coOpenMine). 메모 진입 시 매출 자료 예열(_coWarmForMemo).
#   C) 업체별 소물류 구매가 기준(확판가 hp / 소물가 sm): sched_client_pbase { 업체명:{base,by,at} } (배관 6곳).
#      SMC 잠금 줄에 적용(_qpbApplyRow: 소물가 기준이면 구매가=소물가, 원래 확판가는 c.hp 보관 → 원장 flush 는 확판가),
#      첫 견적에서 소물가 있는 잠금 줄이 담기면 선택 팝업(qpbChoose) 자동, 견적번호 옆 배지(_qpbBadge) 클릭으로 변경.
#
# ※ 편집 내용(OPS)은 apply_r226.js 한 곳에만 두고, 이 파일은 그 OPS 를 읽어 적용한다.
#    python3 edits_r226.py <index.html> [<test/index.html>]      규칙: MARKER 는 test 만 · KEYS 는 live 2 / test 3.
import io, sys, json, os, re

def load_ops():
    here = os.path.dirname(os.path.abspath(__file__))
    with io.open(os.path.join(here, 'apply_r226.js'), 'r', encoding='utf-8') as f: js = f.read()
    m = re.search(r'var OPS = (\[.*?\]);\n  for\(var i=0', js, re.S)
    if not m: raise SystemExit('apply_r226.js 에서 OPS 를 찾지 못했습니다')
    return json.loads(m.group(1))

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R226 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r226(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in load_ops():
        if label == 'MARKER' and not is_test: continue
        if label == 'KEYS' and is_test: exp = 3
        s = rep(s, old, new, exp, label)
    return s

if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r226(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r226 applied:', path)
