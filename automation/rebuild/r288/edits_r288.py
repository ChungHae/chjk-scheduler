#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r288 — 감사 거래명세표: 찍히는 글씨체를 양식 글씨체(바탕)에 맞춘다.

사용자 지시(2026-11-26): "미리보기에서 인쇄영역의 글씨체가 실제와 다름. 일치시킬 것."
  → 지금까지는 고정폭 **바탕체(BatangChe)** 로 찍혀 양식에 인쇄된 **바탕(Batang)** 과 달라 보였다.
    글꼴 차례를 바꿔 바탕을 먼저 쓴다. 칸 좌표·정렬은 그대로다.

사용법:  python3 edits_r288.py <입력 index.html> <출력 index.html> [--test]
"""
import sys

def main():
    if len(sys.argv) < 3:
        print('usage: edits_r288.py <in> <out> [--test]'); return 1
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

    assert 'as-slip{position:relative' in s, 'NEED as-slip css'

    # ① 찍히는 글자: 바탕체(고정폭) → 바탕 (양식에 인쇄된 글꼴과 같게)
    s = rep('font-family:"바탕체",BatangChe,Batang,"바탕",serif;',
            'font-family:Batang,"바탕",BatangChe,"바탕체",serif;', 1, 'slip-font')

    # ② 선으로 그린 양식(그림이 없을 때)도 같은 글꼴로
    s = rep(" font-family=\"BatangChe, Batang, serif\">",
            " font-family=\"Batang, BatangChe, serif\">", 1, 'svg-font')

    assert '"바탕체",BatangChe,Batang' not in s, 'FORBIDDEN old font order remains'
    assert 'font-family:Batang,"바탕"' in s, 'KEEP new font order'

    if is_test:
        old = '<!-- test build r287 2026-11-26 -->'
        assert s.count(old) == 1, 'test marker r287 not found'
        s = s.replace(old, '<!-- test build r288 2026-11-26 -->')
        n[0] += 1

    with open(dst, 'w', encoding='utf-8') as f:
        f.write(s)
    print('r288 edits applied: %d' % n[0])
    return 0

if __name__ == '__main__':
    sys.exit(main())
