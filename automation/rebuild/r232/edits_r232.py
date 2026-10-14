# -*- coding: utf-8 -*-
# r232 (사용자 요청 2026-10-14): 적재 현황의 날짜를 **0000.00.00 (년.월.일)** 로 통일.
#   r231 은 MM-DD 로 줄이고 올해가 아닐 때만 'YY 를 붙였는데, 섞여 보여 헷갈린다는 지적.
import io, sys

OPS = [
 ["    var thisY=String(today.getFullYear());\n", "", 1, "DROP_Y"],
 ["    function shortD(d){ var y=d.slice(0,4); return (y===thisY?'':(\"'\"+y.slice(2)+\" \"))+d.slice(5).replace('-','-'); }",
  "    function shortD(d){ return String(d||'').replace(/-/g,'.'); }   // r232: 0000.00.00 (년.월.일)",
  1, "FMT"],
 ["'<span title=\"'+esc(r.label)+' · '+biz+' — '+s.d+' · '",
  "'<span title=\"'+esc(r.label)+' · '+biz+' — '+shortD(s.d)+' · '",
  1, "TIP"],
]

MARKER = ["<!-- test build r231 2026-10-14 -->", "<!-- test build r232 2026-10-14 -->"]


def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R232 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)


def apply_r232(s, path):
    is_test = 'testpage' in path or '/test/' in path or path.startswith('test')
    for old, new, exp, label in OPS:
        s = rep(s, old, new, exp, label)
    if is_test:
        s = rep(s, MARKER[0], MARKER[1], 1, 'MARKER')
    if 'thisY' in s[s.index('function _fxUpStat'):s.index('function _fxMetaRefresh')]:
        raise SystemExit('R232 FAIL thisY 잔재')
    return s


if __name__ == '__main__':
    for path in sys.argv[1:]:
        with io.open(path, 'r', encoding='utf-8') as f: s = f.read()
        s = apply_r232(s, path)
        with io.open(path, 'w', encoding='utf-8', newline='') as f: f.write(s)
        print('r232 applied:', path)
