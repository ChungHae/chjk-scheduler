# -*- coding: utf-8 -*-
# r292 — 감사 거래명세표: 칸마다 인쇄 글자 크기를 따로 정한다 (사용자 지시)
#   상호·성명 10pt · 사업자등록번호 12pt · 년월일 10pt · 총금액 줄 12pt
#   r291 이 하나로 묶어 두었던 fsHead(11pt) 를 넷으로 나눈다. 모두 [인쇄 보정]에서 고칠 수 있다.
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

# ① 손잡이 넷으로 나눈다
rep(
"""    fsHead:11,                                 // r291: 공급받는자 상호·성명·등록번호 (원본보다 작아 키웠다)""",
"""    fsHead:10, fsBiz:12, fsDate:10, fsTot:12,  // r292: 상호·성명 / 사업자등록번호 / 년월일 / 총금액 줄""", 1, 'knob-defaults')

rep(
"""  var _AS_KNOBS = ['offX','offY','sclX','sclY','slipX','slipY1','slipY2','rowPad','fs','fsHead'];""",
"""  var _AS_KNOBS = ['offX','offY','sclX','sclY','slipX','slipY1','slipY2','rowPad','fs',
                   'fsHead','fsBiz','fsDate','fsTot'];""", 1, 'knob-list')

# ② 년월일
rep(
"""      cell(p.cYear, dt[0], {fs:p.fsSub, al:'r'});
      cell(p.cMon, String(+dt[1]), {fs:p.fsSub, al:'c'});
      cell(p.cDay, String(+dt[2]), {fs:p.fsSub, al:'c'});""",
"""      cell(p.cYear, dt[0], {fs:p.fsDate, al:'r'});          // r292: 9 → 10pt
      cell(p.cMon, String(+dt[1]), {fs:p.fsDate, al:'c'});
      cell(p.cDay, String(+dt[2]), {fs:p.fsDate, al:'c'});""", 1, 'date-size')

# ③ 사업자등록번호 · 상호 · 성명
rep(
"""    fitCell(p.cBiz, head.biz||'', {fs:p.fsHead});      // r291: 원본보다 작아 키웠다
    fitBox(p.cVname, head.vname||'', {fs:p.fsHead});
    fitCell(p.cCeo, head.ceo||'', {fs:p.fsHead});""",
"""    fitCell(p.cBiz, head.biz||'', {fs:p.fsBiz});       // r292: 등록번호 12pt
    fitBox(p.cVname, head.vname||'', {fs:p.fsHead});   //        상호·성명 10pt
    fitCell(p.cCeo, head.ceo||'', {fs:p.fsHead});""", 1, 'biz-head-size')

# ④ 총금액 줄
rep(
"""      fitCell(p.cTotKo, _asKoAmt(head.total)+'整', {fs:p.fs, al:'l'});
      fitCell(p.cTotNo, '(₩'+_asNum(head.total)+')', {fs:p.fs, al:'l'});""",
"""      fitCell(p.cTotKo, _asKoAmt(head.total)+'整', {fs:p.fsTot, al:'l'});   // r292: 10 → 12pt
      fitCell(p.cTotNo, '(₩'+_asNum(head.total)+')', {fs:p.fsTot, al:'l'});""", 1, 'total-size')

# ⑤ [인쇄 보정] 창
rep(
"""      + fld('fsHead','상대방 칸 글자(pt)',0.5)""",
"""      + fld('fsHead','상호·성명(pt)',0.5) + fld('fsBiz','사업자등록번호(pt)',0.5)
      + fld('fsDate','년월일(pt)',0.5) + fld('fsTot','총금액 줄(pt)',0.5)""", 1, 'cfg-fields')

if IS_TEST:
    import re
    m = re.search(r'<!-- test build r\d+ [\d-]+ -->', s)
    assert m, 'NEED test marker'
    s = s.replace(m.group(0), '<!-- test build r292 2026-11-27 -->')
    n += 1

# 지켜야 할 것
assert 'fsHead:10' in s and 'fsBiz:12' in s and 'fsDate:10' in s and 'fsTot:12' in s, 'KEEP new defaults'
assert "{fs:p.fsSub, al:'r'}" not in s, 'FORBIDDEN old date size'
assert "{fs:p.fs, al:'l'});" not in s, 'FORBIDDEN old total size'
assert s.count("fld('fsHead'") == 1 and s.count("fld('fsTot'") == 1, 'KEEP cfg fields'
assert '_AS_FAM_FACE' in s and 'unicode-range' in s, 'KEEP r291 font-face'
assert "'fsTot'" in s, 'KEEP knob list'

io.open(dst, 'w', encoding='utf-8').write(s)
print('r292 edits applied:', n)
