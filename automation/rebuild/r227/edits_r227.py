# -*- coding: utf-8 -*-
# r227 (사용자 요청 2026-10-13, 3건):
#   A) 주간 일정표: 완료 건의 취소선·흐림 제거, ✓ 만 붙여 전부 보이게.
#   B) 신규 영업 응원: '신규 업체명 업무'(kind newbiz) 줄이 진행 중이면 전원 메모장 맨 위 분홍 배너, 완료하면 3일간 초록 축하 배너 (_nbBanner).
#   C) 업무회의 2주 주기: 마지막 회의록 +14일(또는 회의록 없음, 예정 회의 없음)이면 전원 메모장 배너(_mtDueBanner) + 회의 탭 상단 안내(_mtDueHtml).
#      회의 탭 목록은 지난 회의를 접고 [지난 회의 N건 보기](mtTogglePast). 일정에서는 지난 회의의 안건 줄(mtRef)을 숨김(_mmPastMeetingLine).
#
# ※ 편집 내용(OPS)은 apply_r227.js 한 곳에만 두고, 이 파일은 그 OPS 를 읽어 적용한다.
#    python3 edits_r227.py <index.html> [<test/index.html>]      규칙: MARKER 는 test 만. (KEYS 변경 없음)
import io, sys, json, os, re

def load_ops():
    here = os.path.dirname(os.path.abspath(__file__))
    with io.open(os.path.join(here, 'apply_r227.js'), 'r', encoding='utf-8') as f: js = f.read()
    m = re.search(r'var OPS = (\[.*?\]);\n  for\(var i=0', js, re.S)
    if not m: raise SystemExit('apply_r227.js 에서 OPS 를 찾지 못했습니다')
    return json.loads(m.group(1))

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R227 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r227(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in load_ops():
        if label == 'MARKER' and not is_test: continue
        s = rep(s, old, new, exp, label)
    return s

if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s=f.read()
        s = apply_r227(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r227 applied:', path)
