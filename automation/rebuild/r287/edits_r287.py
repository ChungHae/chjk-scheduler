#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r287 — 감사 거래명세표: 글자를 양식의 '칸' 기준으로 앉힌다.

사용자 지시(2026-11-26)
  · 인쇄한 결과에 맞춘 좌표를 버리고, 실제 표 안에 반듯하게 들어가도록 다시 잡을 것
  · 선에 걸치는 것들(번호·년월일 등) 정리
  · 품명·규격은 표 윗선에서 아주 살짝 띄울 것
  · 공급받는자 주소는 두 줄일 때 그에 맞춰 정렬하고, 넘칠 것 같으면 글자를 줄일 것. 상호도 같음
  · 미리보기 양식 그림은 A4 한 장 전체에 깔 것

사용법:  python3 edits_r287.py <입력 index.html> <출력 index.html> [--test]
"""
import sys

N = [0]

def main():
    if len(sys.argv) < 3:
        print('usage: edits_r287.py <in> <out> [--test]'); return 1
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

    def repblock(start, end, new, label):
        """start 로 시작해 end 로 끝나는 구간을 통째로 바꾼다"""
        nonlocal s
        a = s.find(start)
        assert a >= 0, 'block start %s' % label
        b = s.find(end, a)
        assert b >= 0, 'block end %s' % label
        assert s.find(start, a+1) < 0, 'block start %s not unique' % label
        N[0] += 1
        s = s[:a] + new + s[b+len(end):]

    # NEED
    for k in ['var _AS_POS0 = {', 'function _asSlipHtml(', 'function _asDocHtml(',
              'function _asDocHtmlMany(', 'function _asWrapDoc(', '_asFormSvg(']:
        assert k in s, 'NEED %s' % k

    # ── ① 좌표표: 점이 아니라 '칸'으로 ────────────────────────────
    POS = """  var _AS_POS0 = {
    offX:-0.7, offY:0,                         // 프린터 보정(전체 이동) · r283 실측
    sclX:0.9924, sclY:0.9950,                  // r283: 프린터 배율 보정 (1 = 그대로)
    slipX:26.2, slipY1:12.1, slipY2:150.4, slipW:171, slipH:127,
    fs:10, fsSub:9, fsMin:6.5, pad:1.4,        // 글자 크기(pt) · 작은 칸 · 최소 · 칸 안쪽 여백(mm)
    // ── 아래는 빈 양식(300dpi 실측)의 칸 좌표 [왼쪽, 위, 오른쪽, 아래] mm ──
    cNo   :[26.5 , 12.90, 62.00, 18.45],       // 거래명세서 번호
    cYear :[137.0, 12.90,147.90, 18.45],
    cMon  :[150.87,12.90,156.46, 18.45],
    cDay  :[158.92,12.90,164.84, 18.45],
    cBiz  :[100.60,18.50,171.49, 26.98],       // 공급받는자 등록번호
    cVname:[100.60,26.98,135.58, 35.48],       // 공급받는자 상호
    cCeo  :[141.89,26.98,171.49, 35.48],       // 공급받는자 성명
    cAddr :[100.60,35.48,171.49, 43.98],       // 공급받는자 주소 (두 줄까지)
    addrLead:3.5,                              // 주소 두 줄일 때 줄 간격 mm
    cTotKo:[47.50, 43.98,100.00, 52.44],       // 총금액 한글
    cTotNo:[102.00,43.98,171.00, 52.44],       // 총금액 숫자
    rowTop:60.94, rowBot:110.09, rowPad:1.0, rowPadB:0.5,   // 품목표 안쪽
    xNo   :[0.54 , 8.08], xName:[8.08 , 97.04], xQty:[97.04,107.62],
    xPrice:[107.62,128.80], xSup:[128.80,151.05], xTax:[151.05,171.49],
    sumTop:110.09, sumBot:118.42,              // '계' 줄
    cMemo :[1.20 ,118.90, 46.00,126.50]        // 비고 (테두리 아래 빈 자리)
  };
"""
    repblock('  var _AS_POS0 = {', '  };\n', POS, 'POS0')

    rep("var _AS_KNOBS = ['offX','offY','sclX','sclY','slipX','slipY1','slipY2','rowY','fs'];",
        "var _AS_KNOBS = ['offX','offY','sclX','sclY','slipX','slipY1','slipY2','rowPad','fs'];",
        1, 'KNOBS')

    rep("  var _AS_PITCH = 3.5417;                      // 품목 줄 간격 mm (10pt)",
        "  function _asPitch(p){ return ((p.rowBot-p.rowPadB) - (p.rowTop+p.rowPad)) / _AS_ROWS; }",
        1, 'PITCH')

    # ── ② 전표 그리기: 칸 안에 세로 가운데 · 가로 정렬 ──────────────
    SLIP = """  // r287: 글자를 '칸' 안에 앉힌다 — 세로는 가운데, 가로는 칸 성격대로.
  //        글자 폭은 바탕체 기준으로 셈한다(한글 1자 = 글자크기, 영숫자 = 절반).
  function _asTextW(t, fs){
    t = String(t==null?'':t); var w = 0;
    for(var i=0;i<t.length;i++) w += (t.charCodeAt(i)>0x2000 ? 1 : 0.5);
    return w * fs * 0.3528;
  }
  function _asShrink(t, avail, fs, lo){
    lo = lo || 6.5;
    while(fs > lo && _asTextW(t, fs) > avail) fs -= 0.25;
    return fs;
  }
  // 한 줄로 안 되면 낱말 기준으로 길이가 비슷하게 두 줄로 쪼갠다
  function _asTwoLines(t, avail, fs){
    t = String(t==null?'':t).trim();
    if(!t || _asTextW(t, fs) <= avail) return [t];
    var w = t.split(/\\s+/), best = null, bd = 1e9;
    for(var i=1;i<w.length;i++){
      var a = w.slice(0,i).join(' '), b = w.slice(i).join(' ');
      var dd = Math.abs(_asTextW(a,fs) - _asTextW(b,fs));
      if(dd < bd){ bd = dd; best = [a,b]; }
    }
    if(!best){ var h = Math.ceil(t.length/2); best = [t.slice(0,h), t.slice(h)]; }
    return best;
  }
  function _asSlipHtml(d, page, pages, head, grid){
    var p = P(), o = [];
    // 미리보기(양식 위)는 프린터 보정을 빼고 원래 좌표 그대로 보여 준다
    if(grid === 'form') p = Object.assign({}, p, {offX:0, offY:0, sclX:1, sclY:1});
    var SX = (p.sclX||1), SY = (p.sclY||1);
    function box(x1, y1, x2, y2, txt, opt){
      opt = opt || {};
      var fs = opt.fs || p.fs, al = opt.al || 'l', pad = (opt.pad==null? p.pad : opt.pad);
      var px = x1*SX + p.offX, py = y1*SY + p.offY;
      var w = (x2-x1)*SX, h = (y2-y1)*SY;
      var st = 'position:absolute;white-space:pre;overflow:hidden;'
        + 'left:'+px+'mm;top:'+py+'mm;width:'+w+'mm;height:'+h+'mm;'
        + 'line-height:'+h+'mm;font-size:'+fs+'pt;'
        + 'text-align:'+(al==='r'?'right':(al==='c'?'center':'left'))+';'
        + (al==='c' ? '' : (al==='r' ? 'padding-right:'+pad+'mm;' : 'padding-left:'+pad+'mm;'))
        + 'box-sizing:border-box;';
      o.push('<div class="as-f" style="'+st+'">'+esc(txt==null?'':String(txt))+'</div>');
    }
    function cell(c, txt, opt){ box(c[0], c[1], c[2], c[3], txt, opt); }
    // 칸을 넘치면 글자를 줄여서 넣는다
    function fitCell(c, txt, opt){
      opt = opt || {};
      var fs = _asShrink(txt, (c[2]-c[0]) - 2*p.pad, opt.fs || p.fsSub, p.fsMin);
      cell(c, txt, {fs:fs, al:opt.al || 'c'});
    }
    // 머리
    cell(p.cNo, d.no==null?'':String(d.no), {al:'l'});
    var dt = (d.date||'').split('-');
    if(dt.length===3){
      cell(p.cYear, dt[0], {fs:p.fsSub, al:'r'});
      cell(p.cMon, String(+dt[1]), {fs:p.fsSub, al:'c'});
      cell(p.cDay, String(+dt[2]), {fs:p.fsSub, al:'c'});
    }
    fitCell(p.cBiz, head.biz||'', {fs:p.fs});
    fitCell(p.cVname, head.vname||'');
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
    }
    // 총금액 — 첫 장에만
    if(page===0){
      fitCell(p.cTotKo, _asKoAmt(head.total)+'整', {fs:p.fs, al:'l'});
      fitCell(p.cTotNo, '(₩'+_asNum(head.total)+')', {fs:p.fs, al:'l'});
    }
    // 품목 — 표 안쪽을 13줄로 고르게 나눈다 (윗선에서 rowPad 만큼 띄운다)
    var pitch = _asPitch(p), top = p.rowTop + p.rowPad;
    var start = page*_AS_ROWS, part = d.rows.slice(start, start+_AS_ROWS);
    part.forEach(function(r,i){
      var a = top + i*pitch, b = a + pitch;
      box(p.xNo[0],    a, p.xNo[1],    b, String(start+i+1), {al:'c'});
      var _nm = (r.name? (r.name+'  ') : '') + r.spec;
      box(p.xName[0],  a, p.xName[1],  b, _nm,
          {al:'l', fs:_asShrink(_nm, (p.xName[1]-p.xName[0]) - 2*p.pad, p.fs, p.fsMin)});
      box(p.xQty[0],   a, p.xQty[1],   b, r.qty? _asNum(r.qty):'', {al:'r'});
      box(p.xPrice[0], a, p.xPrice[1], b, r.price? _asNum(r.price):'', {al:'r'});
      box(p.xSup[0],   a, p.xSup[1],   b, _asNum(r.supply), {al:'r'});
      box(p.xTax[0],   a, p.xTax[1],   b, _asNum(r.tax), {al:'r'});
    });
    // 이하 여백 — 마지막 장이 13줄을 채우지 않았을 때만
    if(page===pages-1 && part.length < _AS_ROWS){
      var ea = top + part.length*pitch;
      box(p.xName[0], ea, p.xName[1], ea+pitch, '- 이 하 여 백 -', {al:'c'});
    }
    // 계 — 마지막 장에만
    if(page===pages-1){
      box(p.xSup[0], p.sumTop, p.xSup[1], p.sumBot, _asNum(head.supply), {al:'r'});
      box(p.xTax[0], p.sumTop, p.xTax[1], p.sumBot, _asNum(head.tax), {al:'r'});
    }
    if(d.memo) cell(p.cMemo, d.memo, {fs:p.fsSub, al:'l'});
    var _form = (grid==='form' && !_asFormImg) ? _asFormSvg(p) : '';
    return '<div class="as-slip'+(grid===true?' as-grid':'')+'">'+_form+o.join('')+'</div>';
  }
"""
    repblock('  function _asSlipHtml(d, page, pages, head, grid){',
             '\n  // 칸 너비(mm)에 맞춰 줄바꿈', SLIP + '  // 칸 너비(mm)에 맞춰 줄바꿈', 'SLIP')

    # ── ③ 양식 그림은 A4 한 장 전체에 깐다 ─────────────────────────
    PAGE_OLD = ("        pagesHtml.push('<div class=\"as-page\">'\n"
                "          + '<div class=\"as-pos\" style=\"top:'+p.slipY1+'mm\">'+_asSlipHtml(d,pg,pages,head,grid)+'</div>'\n"
                "          + '<div class=\"as-pos\" style=\"top:'+p.slipY2+'mm\">'+_asSlipHtml(d,pg,pages,head,grid)+'</div>'\n"
                "          + '</div>');")
    PAGE_NEW = ("        pagesHtml.push('<div class=\"as-page\">' + _asPageForm(grid)\n"
                "          + '<div class=\"as-pos\" style=\"top:'+p.slipY1+'mm\">'+_asSlipHtml(d,pg,pages,head,grid)+'</div>'\n"
                "          + '<div class=\"as-pos\" style=\"top:'+p.slipY2+'mm\">'+_asSlipHtml(d,pg,pages,head,grid)+'</div>'\n"
                "          + '</div>');")
    rep(PAGE_OLD, PAGE_NEW, 2, 'page-form')

    rep("  function _asWrapDoc(pagesHtml, p){",
        "  // r287: 등록된 양식 그림은 전표마다가 아니라 A4 한 장 전체에 깐다\n"
        "  function _asPageForm(grid){\n"
        "    if(grid !== 'form' || !_asFormImg) return '';\n"
        "    return '<img class=\"as-pageform\" src=\"'+esc(_asFormImg)+'\" alt=\"\">';\n"
        "  }\n"
        "  function _asWrapDoc(pagesHtml, p){", 1, 'pageform-fn')

    rep("      +'img.as-form{object-fit:fill}'",
        "      +'img.as-form{object-fit:fill}'\n"
        "      +'.as-pageform{position:absolute;left:0;top:0;width:210mm;height:297mm;object-fit:fill;pointer-events:none;z-index:0}'",
        1, 'pageform-css')

    # ── ④ [인쇄 보정] 창의 '품목 첫 줄' → '품목 윗 여백' ─────────────
    rep("      + fld('rowY','품목 첫 줄') + fld('fs','글자 크기(pt)',0.5)",
        "      + fld('rowPad','품목 윗 여백') + fld('fs','글자 크기(pt)',0.5)", 1, 'calib-field')

    # FORBIDDEN / KEEP
    assert 'p.rowY' not in s, 'FORBIDDEN p.rowY remains'
    assert '_AS_PITCH' not in s, 'FORBIDDEN _AS_PITCH remains'
    for k in ['_asPageForm', '_asTwoLines', '_asShrink', 'as-pageform', 'rowPad']:
        assert k in s, 'KEEP %s' % k

    if is_test:
        old = '<!-- test build r286 2026-11-26 -->'
        assert s.count(old) == 1, 'test marker r286 not found'
        s = s.replace(old, '<!-- test build r287 2026-11-26 -->')
        N[0] += 1

    with open(dst, 'w', encoding='utf-8') as f:
        f.write(s)
    print('r287 edits applied: %d' % N[0])
    return 0

if __name__ == '__main__':
    sys.exit(main())
