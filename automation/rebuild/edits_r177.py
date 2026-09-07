# -*- coding: utf-8 -*-
# r177: 견적목록 붙여넣기 — 모자란 행을 자동으로 늘린다
#
#  사용자 요청: 엑셀에서 100행을 복사해 견적관리에 붙여넣을 때, 미리 행삽입 100개를 하지 않아도
#    Ctrl+V 한 번으로 100행이 그대로 들어가고 등록된 규격은 판매가·구매가가 자동으로 뜨게.
#
#  실측한 현재 동작(하니스로 재현): 견적목록 1행 상태에서 5행을 붙여넣으면 **1행만 들어가고
#    나머지 4행은 아무 안내 없이 사라진다.** 100행이면 99행이 사라진다.
#    원인: _qgPasteText 가 화면에 이미 있는 입력칸에만 쓴다 —
#      var inp=(g[gi]||[])[start.c+ci]; if(!inp) continue;
#    표에 없는 행(gi >= 행수)은 g[gi] 가 undefined 라 그냥 건너뛴다.
#    자동 채우기(_qgFillFromLedger)는 이미 정상이었다 — 들어간 행은 품목·E가·구매가·판매가·납기가
#    제대로 채워졌다. 즉 빠진 것은 '행을 늘리는 일' 하나뿐이다.
#
#  수정: 붙여넣기 직전에 필요한 만큼 빈 행을 만들고 다시 그린 뒤, 그 표를 대상으로 기존 로직을 돌린다.
#    · 행 형태는 [행 삽입](qCartInsertRow)이 만드는 것과 똑같다 — vid/vname 승계, qty 1, manual.
#    · 늘린 뒤 _qcGrid() 를 다시 읽는다(늘리기 전 표에는 새 행이 없다).
#    · 붙여넣기 전체를 실행취소 한 단계로 묶는다(_qPushUndo) — 100행을 되돌릴 방법이 없으면 안 된다.
#      기존 코드에는 이게 아예 없어서 붙여넣기를 취소할 수 없었다.
#    · 거래처를 안 고른 빈 상태에서는 안내하고 멈춘다(행 삽입과 같은 기준).
#    · 조회 전용 계정은 막는다(_guardW).
#    · 한 번에 늘리는 행은 2,000행까지. 넘으면 앞에서부터 2,000행만 넣고 몇 행이 잘렸는지 알린다
#      (조용히 버리지 않는다 — 지금 문제의 본질이 '말 없이 사라지는 것'이었다).

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R177 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r177(s, path):
    s = rep(s,
        "  function _qgPasteText(txt){\n"
        "    var g=_qcGrid(); var b=_qgBounds(); var start = b?{r:b.r0,c:b.c0}:(_qcPos(document.activeElement)||{r:0,c:0});\n"
        "    var rows=String(txt).replace(/\\r/g,'').replace(/\\n+$/,'').split('\\n').map(function(ln){ return ln.split('\\t'); });\n"
        "    _qgSuspend=true; var specRows={};",

        "  var _QPASTE_MAX=2000;   // r177: 한 번에 만들 수 있는 최대 행수\n"
        "  var _qgPasting=false;   // r177: 붙여넣는 동안에는 칸 이동(focusin)으로 실행취소를 쌓지 않는다\n"
        "  function _qgPasteText(txt){\n"
        "    if(!_guardW()) return;\n"
        "    var g=_qcGrid(); var b=_qgBounds(); var start = b?{r:b.r0,c:b.c0}:(_qcPos(document.activeElement)||{r:0,c:0});\n"
        "    var rows=String(txt).replace(/\\r/g,'').replace(/\\n+$/,'').split('\\n').map(function(ln){ return ln.split('\\t'); });\n"
        "    // ── r177: 붙여넣을 만큼 행이 없으면 먼저 늘린다 ──\n"
        "    //  전에는 화면에 있는 행에만 써서 나머지가 말 없이 사라졌다(1행에 100행을 붙이면 99행 소실).\n"
        "    _qPushUndo();   // 붙여넣기 전체를 한 단계로 — 100행을 되돌릴 방법이 있어야 한다\n"
        "    var _cut=0;\n"
        "    if(rows.length > _QPASTE_MAX){ _cut=rows.length-_QPASTE_MAX; rows=rows.slice(0,_QPASTE_MAX); }\n"
        "    var _need = start.r + rows.length;\n"
        "    if(_need > _qCart.length){\n"
        "      var _vendorSel=!!(_qCurId && (typeof quoteVendors!=='undefined'&&quoteVendors) && quoteVendors.find(function(v){return v.id===_qCurId;}));\n"
        "      if(!_vendorSel && !_qCartHasContent()){ showInfoModal('거래처 확인','거래처를 먼저 선택한 뒤 붙여넣어 주세요.'); return; }\n"
        "      _qgPasting=true;\n"
        "      var _vid=_qCart.length?_qCart[0].vid:(_qCurId||'');\n"
        "      var _vn=_qCart.length?_qCart[0].vname:((typeof quoteVendors!=='undefined'&&quoteVendors?(quoteVendors.find(function(v){return v.id===_qCurId;})||{}):{}).name||'');\n"
        "      while(_qCart.length < _need){\n"
        "        _qCart.push({vid:_vid, vname:_vn, spec:'', name:'', e:null, buy:null, small:null, pl:false, sell:null, disc:'', eta:'', qty:1, manual:true});\n"
        "      }\n"
        "      renderQCart();\n"
        "      g=_qcGrid();   // 늘린 표를 다시 읽는다 — 늘리기 전 표에는 새 행이 없다\n"
        "    }\n"
        "    _qgSuspend=true; var specRows={};",
        1, 'GROW')

    # 잘린 행을 알린다 — 조용히 버리지 않는다
    s = rep(s,
        "    try{ _qcsHide(); }catch(e){}\n"
        "    _qCartSave(); renderQCart(); _qgPaint();\n"
        "  }",
        "    try{ _qcsHide(); }catch(e){}\n"
        "    _qgPasting=true;\n"
        "    _qCartSave(); renderQCart(); _qgPaint();\n"
        "    _qgPasting=false;\n"
        "    if(_cut) showInfoModal('붙여넣기','한 번에 넣을 수 있는 행은 '+_QPASTE_MAX+'행까지입니다.\\n'\n"
        "      + '앞에서부터 '+_QPASTE_MAX+'행만 넣었고 '+_cut+'행은 넣지 않았습니다.\\n\\n나머지는 이어서 한 번 더 붙여넣어 주세요.');\n"
        "  }",
        1, 'CUTNOTE')

    #  붙여넣는 도중의 재렌더는 커서를 되돌려 놓는데, 그 focusin 이 실행취소를 한 단계 더 쌓아
    #  Ctrl+Z 가 '빈 행만 늘어난 상태'로 되돌아가 버린다(실측). 붙여넣는 동안은 쌓지 않는다.
    s = rep(s,
        "    if(!(t.classList.contains('qc-in')||t.classList.contains('qc-nego')||t.classList.contains('qc-memo'))) return;\n"
        "    var box=document.getElementById('qCart'); if(box && box.contains(t)) _qPushUndo();",
        "    if(!(t.classList.contains('qc-in')||t.classList.contains('qc-nego')||t.classList.contains('qc-memo'))) return;\n"
        "    if(_qgPasting) return;   // r177: 붙여넣기 중 재렌더의 커서 복귀는 실행취소 단계가 아니다\n"
        "    var box=document.getElementById('qCart'); if(box && box.contains(t)) _qPushUndo();",
        1, 'FOCUSGUARD')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r177(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r176 2026-09-04 -->') == 1
            s = s.replace('<!-- test build r176 2026-09-04 -->', '<!-- test build r177 2026-09-07 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
