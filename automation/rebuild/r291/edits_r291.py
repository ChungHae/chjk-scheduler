# -*- coding: utf-8 -*-
# r291 — 감사: 끌어다 놓을 때의 강조를 '끌어다 놓는 칸' 안쪽으로만 되돌린다.
#  r290 은 outline 을 inset 그림자로 바꿨지만 여전히 #pageAudit(감사 페이지 전체)에 걸려 있어
#  화면 전체를 둘러싸는 남색 테두리가 떴다. 강조는 #asDrop 한 칸에만 준다.
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

# ① 강조는 #asDrop 에만 — #pageAudit 에 남은 자국도 지운다
rep(
"""  function _asDropOn(on){
    var el=document.getElementById('pageAudit'); if(!el) return;
    // r290: outline 은 상자 바깥에 그려져 테두리를 넘어 보였다 → 안쪽에만 그리는 inset 그림자로
    el.style.outline = ''; el.style.outlineOffset = '';
    el.style.boxShadow = on ? 'inset 0 0 0 3px #1B3A6B' : '';
    var z=document.getElementById('asDrop');
    if(z){ z.style.borderColor = on ? '#1B3A6B' : '#c8d2de'; z.style.background = on ? '#eaf1fb' : '#fafbfc'; }
  }""",
"""  function _asDropOn(on){
    // r291: 강조는 '끌어다 놓는 칸' 안에서만. 페이지 전체(#pageAudit)에 테두리를 두르면
    //       화면을 통째로 감싸는 남색 상자가 떠서 이상하게 보였다.
    var el=document.getElementById('pageAudit');
    if(el){ el.style.outline=''; el.style.outlineOffset=''; el.style.boxShadow=''; }
    var z=document.getElementById('asDrop');
    if(z){
      z.style.borderColor = on ? '#1B3A6B' : '#c8d2de';
      z.style.background  = on ? '#eaf1fb' : '#fafbfc';
      z.style.boxShadow   = on ? 'inset 0 0 0 2px #1B3A6B' : '';
    }
  }""", 1, 'asDropOn-scope')

# ② 글씨체를 '칸' 이 아니라 '글자 종류' 로 가른다 (사용자 지시)
#    숫자·영문 = 수량/품명에 쓰던 고정폭 바탕체 · 한글 = 상호에 쓰던 바탕.
#    한 글꼴 이름(ASmix) 안에서 @font-face 의 unicode-range 로 글자마다 갈라 쓴다.
rep(
"""  // r290: 품목 줄 글꼴 — 바탕(Batang)은 영숫자가 Times 계열이라 한글과 결이 갈린다.
  //        고정폭 바탕체가 처음 쓰던 글꼴이고 표 안에서 더 고르게 보인다.
  var _AS_FAM_ROW = "BatangChe,'바탕체',Batang,'바탕',serif";""",
"""  // r291: 글씨체는 '칸' 이 아니라 '글자 종류' 로 가른다 (사용자 지시).
  //        숫자·영문 = 고정폭 바탕체(수량·품명에 쓰던 것) · 한글 = 바탕(상호에 쓰던 것).
  //        한 글꼴 이름(ASmix) 안에서 unicode-range 로 글자마다 갈라 쓴다 —
  //        둘 다 글자를 모두 갖고 있어서 글꼴 차례(fallback)만으로는 가를 수 없다.
  var _AS_FAM_LAT = "BatangChe,'바탕체'";          // 숫자·영문
  var _AS_FAM_KOR = "Batang,'바탕'";               // 한글
  var _AS_FAM_ROW = _AS_FAM_LAT + "," + _AS_FAM_KOR + ",serif";   // 숫자·영문 먼저
  var _AS_FAM     = "ASmix," + _AS_FAM_KOR + "," + _AS_FAM_LAT + ",serif";
  var _AS_FAM_FACE =
      "@font-face{font-family:ASmix;src:local('BatangChe'),local('바탕체');"
    + "unicode-range:U+0020-024F,U+2000-206F,U+2070-209F,U+20A0-20CF,U+2190-21FF,U+2460-24FF,U+25A0-25FF;}"
    + "@font-face{font-family:ASmix;src:local('Batang'),local('바탕');"
    + "unicode-range:U+1100-11FF,U+2E80-2EFF,U+3000-303F,U+3130-318F,U+3200-32FF,U+4E00-9FFF,"
    + "U+A960-A97F,U+AC00-D7FF,U+F900-FAFF,U+FF00-FFEF;}";""", 1, 'fam-mix')

# ③ 전표 기본 글꼴을 섞은 글꼴로 · @font-face 를 인쇄 문서에 넣는다
rep(
"""    var css='@page{size:A4;margin:0}'
      +'html,body{margin:0;padding:0;background:#fff}'""",
"""    var css='@page{size:A4;margin:0}'
      +_AS_FAM_FACE
      +'html,body{margin:0;padding:0;background:#fff}'""", 1, 'face-css')

rep(
"""font-family:Batang,"바탕",BatangChe,"바탕체",serif;font-size:'+p.fs+'pt""",
"""font-family:'+_AS_FAM+';font-size:'+p.fs+'pt""", 1, 'slip-family')

# ④ 품목 줄의 칸별 글꼴 지정은 더 쓰지 않는다 — 섞은 글꼴이 글자마다 알아서 가른다
rep(
"""      var F = _AS_FAM_ROW;   // r290: 품목 줄은 한글·영숫자 폭이 같은 고정폭 바탕체
      box(p.xNo[0],    a, p.xNo[1],    b, String(start+i+1), {al:'c', fam:F});
      var _nm = (r.name? (r.name+'  ') : '') + r.spec;
      box(p.xName[0],  a, p.xName[1],  b, _nm,
          {al:'l', fam:F, fs:_asShrink(_nm, (p.xName[1]-p.xName[0]) - 2*p.pad, p.fs, p.fsMin)});
      box(p.xQty[0],   a, p.xQty[1],   b, r.qty? _asNum(r.qty):'', {al:'r', fam:F});
      box(p.xPrice[0], a, p.xPrice[1], b, r.price? _asNum(r.price):'', {al:'r', fam:F});
      box(p.xSup[0],   a, p.xSup[1],   b, _asNum(r.supply), {al:'r', fam:F});
      box(p.xTax[0],   a, p.xTax[1],   b, _asNum(r.tax), {al:'r', fam:F});""",
"""      // r291: 칸마다 글꼴을 주지 않는다 — 전표 글꼴(ASmix)이 숫자·영문/한글을 글자마다 가른다
      box(p.xNo[0],    a, p.xNo[1],    b, String(start+i+1), {al:'c'});
      var _nm = (r.name? (r.name+'  ') : '') + r.spec;
      box(p.xName[0],  a, p.xName[1],  b, _nm,
          {al:'l', fs:_asShrink(_nm, (p.xName[1]-p.xName[0]) - 2*p.pad, p.fs, p.fsMin)});
      box(p.xQty[0],   a, p.xQty[1],   b, r.qty? _asNum(r.qty):'', {al:'r'});
      box(p.xPrice[0], a, p.xPrice[1], b, r.price? _asNum(r.price):'', {al:'r'});
      box(p.xSup[0],   a, p.xSup[1],   b, _asNum(r.supply), {al:'r'});
      box(p.xTax[0],   a, p.xTax[1],   b, _asNum(r.tax), {al:'r'});""", 1, 'rows-nofam')

# ⑤ 상호·성명·사업자등록번호 글자를 키운다 — 손잡이 fsHead (기본 11pt)
rep(
"""    fs:10, fsSub:9, fsMin:6.5, pad:1.4,        // 글자 크기(pt) · 작은 칸 · 최소 · 칸 안쪽 여백(mm)""",
"""    fs:10, fsSub:9, fsMin:6.5, pad:1.4,        // 글자 크기(pt) · 작은 칸 · 최소 · 칸 안쪽 여백(mm)
    fsHead:11,                                 // r291: 공급받는자 상호·성명·등록번호 (원본보다 작아 키웠다)""", 1, 'fsHead-default')

rep(
"""  var _AS_KNOBS = ['offX','offY','sclX','sclY','slipX','slipY1','slipY2','rowPad','fs'];""",
"""  var _AS_KNOBS = ['offX','offY','sclX','sclY','slipX','slipY1','slipY2','rowPad','fs','fsHead'];""", 1, 'knobs')

rep(
"""      + fld('rowPad','품목 윗 여백') + fld('fs','글자 크기(pt)',0.5)""",
"""      + fld('rowPad','품목 윗 여백') + fld('fs','글자 크기(pt)',0.5)
      + fld('fsHead','상대방 칸 글자(pt)',0.5)""", 1, 'knob-field')

rep(
"""    fitCell(p.cBiz, head.biz||'', {fs:p.fs});
    fitBox(p.cVname, head.vname||'');
    fitCell(p.cCeo, head.ceo||'');""",
"""    fitCell(p.cBiz, head.biz||'', {fs:p.fsHead});      // r291: 원본보다 작아 키웠다
    fitBox(p.cVname, head.vname||'', {fs:p.fsHead});
    fitCell(p.cCeo, head.ceo||'', {fs:p.fsHead});""", 1, 'head-size')


if IS_TEST:
    import re
    m = re.search(r'<!-- test build r\d+ [\d-]+ -->', s)
    assert m, 'NEED test marker'
    s = s.replace(m.group(0), '<!-- test build r291 2026-11-27 -->')
    n += 1

# 지켜야 할 것
assert "box-sizing:border-box;border:2px dashed #c8d2de" in s, 'KEEP asDrop border-box'
assert s.count("getElementById('pageAudit'); if(!el) return;\n    // r290") == 0, 'FORBIDDEN old r290 block'
assert "el.style.boxShadow = on ?" not in s, 'FORBIDDEN pageAudit highlight'
assert 'font-family:Batang,"바탕"' not in s, 'FORBIDDEN old slip family'
assert s.count('fam:F') == 0, 'FORBIDDEN per-cell fam'
assert '_AS_FAM_FACE' in s and 'unicode-range' in s, 'KEEP font-face'
for _q in ['_AS_FAM_LAT', '_AS_FAM_KOR', '_AS_FAM', '_AS_FAM_ROW']:
    pass

io.open(dst, 'w', encoding='utf-8').write(s)
print('r291 edits applied:', n)
