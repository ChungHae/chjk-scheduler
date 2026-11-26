#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r286 — 감사 > 저장된 명세표: 묶음 처리 단추 이름을 [선택 인쇄]·[선택 삭제] 로 바꾼다.
사용자 지시(2026-11-26): "고른 것 인쇄, 고른 것 삭제를 선택 인쇄, 선택 삭제로 이름 변경할 것"

사용법:  python3 edits_r286.py <입력 index.html> <출력 index.html> [--test]
"""
import sys

def main():
    if len(sys.argv) < 3:
        print('usage: edits_r286.py <in> <out> [--test]'); return 1
    src, dst = sys.argv[1], sys.argv[2]
    is_test = '--test' in sys.argv[3:]
    with open(src, encoding='utf-8') as f:
        s = f.read()
    n = [0]

    def rep(old, new, cnt, label):
        got = s.count(old)
        assert got == cnt, 'anchor %s: expected %d, found %d' % (label, cnt, got)
        n[0] += 1
        return s.replace(old, new)

    # NEED: r285 묶음 처리 줄이 있어야 한다
    assert "_asBtn('고른 것 인쇄','asLPrintSel()','primary')" in s, 'NEED r285 selection toolbar'

    # ① 단추 이름 두 개
    s = rep("_asBtn('고른 것 인쇄','asLPrintSel()','primary')",
            "_asBtn('선택 인쇄','asLPrintSel()','primary')", 1, 'print-btn')
    s = rep("_asBtn('고른 것 삭제','asLDelSel()','warn')",
            "_asBtn('선택 삭제','asLDelSel()','warn')", 1, 'del-btn')

    # FORBIDDEN: 옛 이름이 남아 있으면 안 된다 (주석은 제외)
    assert "_asBtn('고른 것" not in s, 'FORBIDDEN old button label remains'
    # KEEP: 기능 자체는 그대로
    for k in ['window.asLPrintSel', 'window.asLDelSel', 'asLSelNone()', '_asDocHtmlMany']:
        assert k in s, 'KEEP %s' % k

    if is_test:
        old = '<!-- test build r285 2026-11-26 -->'
        assert s.count(old) == 1, 'test marker r285 not found'
        s = s.replace(old, '<!-- test build r286 2026-11-26 -->')
        n[0] += 1

    with open(dst, 'w', encoding='utf-8') as f:
        f.write(s)
    print('r286 edits applied: %d' % n[0])
    return 0

if __name__ == '__main__':
    sys.exit(main())
