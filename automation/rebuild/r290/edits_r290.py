#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r290 — 품목 줄(번호·품명 및 규격·수량·단가·공급가액·세액)만 처음 글씨체(바탕체)로 되돌린다.

사용자 지시(2026-11-27): "-이하여백- 은 그대로 진행하면 되는데, 번호, 품명 및 규격, 수량,
  단가, 공급가액, 세액 부분은 처음 설정한 글씨체가 맞는 것 같음. 아마도 한글과 영어,
  숫자가 글씨체가 다른 듯 함."
  → 바탕(Batang)은 한글은 명조인데 영숫자가 Times 계열이라 한 줄 안에서 결이 갈린다.
    품목 줄은 한글·영숫자 폭이 같은 고정폭 **바탕체(BatangChe)** 가 맞다.
    나머지(머리칸·총금액·이하여백·비고 등)는 r288 그대로 바탕을 쓴다.

사용법:  python3 edits_r290.py <입력 index.html> <출력 index.html> [--test]
"""
import sys

N = [0]

def main():
    if len(sys.argv) < 3:
        print('usage: edits_r290.py <in> <out> [--test]'); return 1
    src, dst = sys.argv[1], sys.argv[2]
    is_test = '--test' in sys.argv[3:]
    with open(src, encoding='utf-8') as f:
        s = f.read()

    def rep(old, new, cnt, label):
        nonlocal s
        got = s.count(old)
        assert got == cnt, 'anchor %s: expected %d, found %d' % (label, cnt, got)
        N[0] += 1
        s = s.replace(old, new)

    assert 'function _asSlipHtml(' in s, 'NEED _asSlipHtml'
    assert 'part.forEach(function(r,i){' in s, 'NEED item rows'

    # ① box() 가 글꼴을 따로 받을 수 있게
    rep("""      var fs = opt.fs || p.fs, al = opt.al || 'l', pad = (opt.pad==null? p.pad : opt.pad);""",
        """      var fs = opt.fs || p.fs, al = opt.al || 'l', pad = (opt.pad==null? p.pad : opt.pad);
      var fam = opt.fam || '';                                  // r290: 칸마다 글꼴을 달리 쓸 수 있게""",
        1, 'box-fam-var')

    rep("""        + 'line-height:'+h+'mm;font-size:'+fs+'pt;'""",
        """        + 'line-height:'+h+'mm;font-size:'+fs+'pt;'
        + (fam ? ('font-family:'+fam+';') : '')""", 1, 'box-fam-css')

    # ② 품목 줄만 고정폭 바탕체로
    OLD_ROWS = """    part.forEach(function(r,i){
      var a = top + i*pitch, b = a + pitch;
      box(p.xNo[0],    a, p.xNo[1],    b, String(start+i+1), {al:'c'});
      var _nm = (r.name? (r.name+'  ') : '') + r.spec;
      box(p.xName[0],  a, p.xName[1],  b, _nm,
          {al:'l', fs:_asShrink(_nm, (p.xName[1]-p.xName[0]) - 2*p.pad, p.fs, p.fsMin)});
      box(p.xQty[0],   a, p.xQty[1],   b, r.qty? _asNum(r.qty):'', {al:'r'});
      box(p.xPrice[0], a, p.xPrice[1], b, r.price? _asNum(r.price):'', {al:'r'});
      box(p.xSup[0],   a, p.xSup[1],   b, _asNum(r.supply), {al:'r'});
      box(p.xTax[0],   a, p.xTax[1],   b, _asNum(r.tax), {al:'r'});
    });"""
    NEW_ROWS = """    part.forEach(function(r,i){
      var a = top + i*pitch, b = a + pitch;
      var F = _AS_FAM_ROW;   // r290: 품목 줄은 한글·영숫자 폭이 같은 고정폭 바탕체
      box(p.xNo[0],    a, p.xNo[1],    b, String(start+i+1), {al:'c', fam:F});
      var _nm = (r.name? (r.name+'  ') : '') + r.spec;
      box(p.xName[0],  a, p.xName[1],  b, _nm,
          {al:'l', fam:F, fs:_asShrink(_nm, (p.xName[1]-p.xName[0]) - 2*p.pad, p.fs, p.fsMin)});
      box(p.xQty[0],   a, p.xQty[1],   b, r.qty? _asNum(r.qty):'', {al:'r', fam:F});
      box(p.xPrice[0], a, p.xPrice[1], b, r.price? _asNum(r.price):'', {al:'r', fam:F});
      box(p.xSup[0],   a, p.xSup[1],   b, _asNum(r.supply), {al:'r', fam:F});
      box(p.xTax[0],   a, p.xTax[1],   b, _asNum(r.tax), {al:'r', fam:F});
    });"""
    rep(OLD_ROWS, NEW_ROWS, 1, 'item-rows')

    # ③ 품목 줄 글꼴 상수
    rep("  function _asSlipHtml(d, page, pages, head, grid){",
        "  // r290: 품목 줄 글꼴 — 바탕(Batang)은 영숫자가 Times 계열이라 한글과 결이 갈린다.\n"
        "  //        고정폭 바탕체가 처음 쓰던 글꼴이고 표 안에서 더 고르게 보인다.\n"
        "  var _AS_FAM_ROW = \"BatangChe,'바탕체',Batang,'바탕',serif\";\n"
        "  function _asSlipHtml(d, page, pages, head, grid){", 1, 'fam-const')

    # ④ 쪽 이동 줄에서 'n / N' 표시를 뺀다 (사용자 지시 11-27)
    rep("""        + _asBtn('끝','asLGo('+(pages-1)+')')
        + '<span style="margin-left:6px;color:#6b7280">'+(_asLPage+1)+' / '+pages+'</span>'
        + '</div>';""",
        """        + _asBtn('끝','asLGo('+(pages-1)+')')
        + '</div>';""", 1, 'pager-count')
    assert "'+(_asLPage+1)+' / '+pages+'" not in s, 'FORBIDDEN page count text remains'

    # ⑤ [선택 삭제] 팝업: 세부 내역을 빼고 한 줄로 (사용자 지시 11-27)
    rep("""    var head=recs.slice(0,6).map(function(v){ return '  · '+(v.date||'')+' 번호 '+(v.no||'')+' · '+(v.vname||''); }).join('\\n');
    showConfirmModal('거래명세표 '+recs.length+'건 삭제',
      head + (recs.length>6?('\\n  … 모두 '+recs.length+'건'):'') + '\\n\\n고른 거래명세표를 모두 지웁니다. 되돌릴 수 없습니다.',""",
        """    showConfirmModal('거래명세표 '+recs.length+'건 삭제',
      '총 '+recs.length+'건의 거래명세표를 삭제합니다. 되돌릴 수 없습니다.',""", 1, 'del-text')
    assert '고른 거래명세표를 모두 지웁니다' not in s, 'FORBIDDEN old delete text remains'

    # ⑥ 상호·주소: 한 줄 → 두 줄 → 그래도 넘치면 글자 줄이기 (사용자 지시 11-27)
    OLD_HEAD = """    fitCell(p.cVname, head.vname||'');
    fitCell(p.cCeo, head.ceo||'');
    // 주소 — 한 줄이면 한 줄, 아니면 두 줄을 칸 가운데에 맞춰 넣는다
    var ac = p.cAddr, aAvail = (ac[2]-ac[0]) - 2*p.pad;
    var aLines = _asTwoLines(head.addr||'', aAvail, p.fsSub);
    if(aLines.length <= 1){
      fitCell(ac, aLines[0]||'');
    }else{
      var afs = p.fsSub;
      while(afs > p.fsMin && Math.max(_asTextW(aLines[0],afs), _asTextW(aLines[1],afs)) > aAvail) afs -= 0.25;
      var mid = (ac[1]+ac[3])/2, L = p.addrLead;
      box(ac[0], mid-L, ac[2], mid, aLines[0], {fs:afs, al:'c'});
      box(ac[0], mid, ac[2], mid+L, aLines[1], {fs:afs, al:'c'});
    }"""
    NEW_HEAD = """    fitBox(p.cVname, head.vname||'');
    fitCell(p.cCeo, head.ceo||'');
    fitBox(p.cAddr, head.addr||'');"""
    rep(OLD_HEAD, NEW_HEAD, 1, 'head-fields')

    # fitBox: 원래 크기 한 줄 → 원래 크기 두 줄 → 그래도 넘치면 축소
    rep("""    // 칸을 넘치면 글자를 줄여서 넣는다
    function fitCell(c, txt, opt){""",
        """    // r290: 상호·주소는 ① 그대로 한 줄 → ② 두 줄 → ③ 그래도 넘치면 글자를 줄인다
    function fitBox(c, txt, opt){
      opt = opt || {};
      var base = opt.fs || p.fsSub, avail = (c[2]-c[0]) - 2*p.pad;
      txt = String(txt==null? '' : txt);
      if(!txt) return;
      if(_asTextW(txt, base) <= avail){ cell(c, txt, {fs:base, al:'c'}); return; }   // ① 한 줄 그대로
      var ls = _asTwoLines(txt, avail, base);
      if(ls.length < 2){ cell(c, txt, {fs:_asShrink(txt, avail, base, p.fsMin), al:'c'}); return; }
      var fs = base;                                                                  // ② 두 줄
      while(fs > p.fsMin && Math.max(_asTextW(ls[0],fs), _asTextW(ls[1],fs)) > avail) fs -= 0.25;  // ③ 그래도 넘치면
      var mid = (c[1]+c[3])/2, L = (opt.lead || p.addrLead);
      box(c[0], mid-L, c[2], mid, ls[0], {fs:fs, al:'c'});
      box(c[0], mid, c[2], mid+L, ls[1], {fs:fs, al:'c'});
    }
    // 칸을 넘치면 글자를 줄여서 넣는다
    function fitCell(c, txt, opt){""", 1, 'fitbox')
    assert 'fitBox(p.cVname' in s and 'fitBox(p.cAddr' in s, 'KEEP fitBox calls'

    for k in ['_AS_FAM_ROW', "fam:F", "opt.fam"]:
        assert k in s, 'KEEP %s' % k
    # 이하여백·총금액·머리칸은 글꼴을 주지 않는다 (바탕 그대로)
    assert s.count("'- 이 하 여 백 -', {al:'c'})") == 1, 'FORBIDDEN 이하여백 font changed'

    if is_test:
        old = '<!-- test build r289 2026-11-27 -->'
        assert s.count(old) == 1, 'test marker r289 not found'
        s = s.replace(old, '<!-- test build r290 2026-11-27 -->')
        N[0] += 1

    with open(dst, 'w', encoding='utf-8') as f:
        f.write(s)
    print('r290 edits applied: %d' % N[0])
    return 0

if __name__ == '__main__':
    sys.exit(main())
