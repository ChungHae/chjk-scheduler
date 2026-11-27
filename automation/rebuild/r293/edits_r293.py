# -*- coding: utf-8 -*-
# r293 — 감사 거래명세표: 총금액 한글+숫자를 '한 세트'로 묶어 빈칸 전체를 폭으로 쓴다 (사용자 지시)
#   "총금액의 한글과 숫자는 항상 같이 움직이는 세트이므로 가로 빈칸 전체를 폭으로 생각하면 됨."
#   cTotKo(47.5~100.0) · cTotNo(102.0~171.0) 두 칸을 cTot(47.5~171.0) 한 칸으로 합치고,
#   한글 바로 뒤 totGap(mm) 만큼 띄워 숫자를 붙인다. 둘은 늘 같은 크기(fsTot 12pt).
import sys, io

src, dst = sys.argv[1], sys.argv[2]
IS_TEST = '--test' in sys.argv
s = io.open(src, encoding='utf-8').read()
n = 0

def rep(old, new, cnt, label):
    global s, n
    got = s.count(old)
    assert got == cnt, 'NEED %s: expected %d, got %d' % (label, cnt, got)
    s = s.replace(old, new)
    n += 1

# ① 칸 하나로 합친다
rep(
"""    cTotKo:[47.50, 43.98,100.00, 52.44],       // 총금액 한글
    cTotNo:[102.00,43.98,171.00, 52.44],       // 총금액 숫자""",
"""    cTot  :[47.50, 43.98,171.00, 52.44],       // r293: 총금액 — 한글+숫자 한 세트, 빈칸 전체가 폭
    totGap:5.0,                                // r293: 한글과 (₩…) 사이 간격(mm)""", 1, 'cell-merge')

# ② 손잡이에 간격 추가
rep(
"""  var _AS_KNOBS = ['offX','offY','sclX','sclY','slipX','slipY1','slipY2','rowPad','fs',
                   'fsHead','fsBiz','fsDate','fsTot'];""",
"""  var _AS_KNOBS = ['offX','offY','sclX','sclY','slipX','slipY1','slipY2','rowPad','fs',
                   'fsHead','fsBiz','fsDate','fsTot','totGap'];""", 1, 'knob-list')

# ③ 그리기 — 한 세트로
rep(
"""      fitCell(p.cTotKo, _asKoAmt(head.total)+'整', {fs:p.fsTot, al:'l'});   // r292: 10 → 12pt
      fitCell(p.cTotNo, '(₩'+_asNum(head.total)+')', {fs:p.fsTot, al:'l'});""",
"""      // r293: 한글과 (₩…) 는 한 세트 — 빈칸 전체(cTot)를 폭으로 보고 둘을 같은 크기로 이어 쓴다
      var _tKo = _asKoAmt(head.total)+'整', _tNo = '(₩'+_asNum(head.total)+')';
      var _tc = p.cTot, _tAvail = (_tc[2]-_tc[0]) - 2*p.pad, _tGap = p.totGap;
      var _tFs = p.fsTot;
      while(_tFs > p.fsMin && (_asTextW(_tKo,_tFs) + _tGap + _asTextW(_tNo,_tFs)) > _tAvail) _tFs -= 0.25;
      var _tKw = _asTextW(_tKo, _tFs), _tNx = _tc[0] + p.pad + _tKw + _tGap;
      box(_tc[0], _tc[1], _tNx, _tc[3], _tKo, {fs:_tFs, al:'l'});      // 한글 — 숫자 자리까지
      box(_tNx, _tc[1], _tc[2], _tc[3], _tNo, {fs:_tFs, al:'l', pad:0});   // 숫자 — 바로 뒤에""", 1, 'draw-set')

# ④ [인쇄 보정] 창에 간격 칸
rep(
"""      + fld('fsDate','년월일(pt)',0.5) + fld('fsTot','총금액 줄(pt)',0.5)""",
"""      + fld('fsDate','년월일(pt)',0.5) + fld('fsTot','총금액 줄(pt)',0.5)
      + fld('totGap','총금액 사이 간격')""", 1, 'cfg-field')

if IS_TEST:
    import re
    m = re.search(r'<!-- test build r\d+ [\d-]+ -->', s)
    assert m, 'NEED test marker'
    s = s.replace(m.group(0), '<!-- test build r293 2026-11-27 -->')
    n += 1

# 지켜야 할 것
assert 'cTotKo' not in s and 'cTotNo' not in s, 'FORBIDDEN old total cells'
assert 'cTot  :[47.50, 43.98,171.00, 52.44]' in s, 'KEEP merged cell'
assert "'totGap'" in s and 'totGap:5.0' in s, 'KEEP gap knob'
assert 'fsHead:10' in s and 'fsBiz:12' in s and 'fsDate:10' in s and 'fsTot:12' in s, 'KEEP r292 sizes'
assert '_AS_FAM_FACE' in s and 'unicode-range' in s, 'KEEP r291 font-face'

io.open(dst, 'w', encoding='utf-8').write(s)
print('r293 edits applied:', n)
