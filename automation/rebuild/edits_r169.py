# -*- coding: utf-8 -*-
# r169: 미배정/제외 입금 목록이 300건에서 잘려 과거 자료가 "사라진 것처럼" 보이던 문제
#
#  사용자 보고(2026-08-31): 신한 엑셀에는 있는 2022년 세화산업사 입금이 앱에 없다.
#  실측 확인:
#   - 업로드한 파일(서울 신한, 11,373행)을 실제 파서 로직 그대로 재현 → 7,359건이 정상 반영되고
#     세화산업사 41건(2022년 9건 포함) 전부 통과. 즉 파일·파서 문제 아님.
#   - 원인은 화면: _fxRenderUnasg 가 목록을 최신순 정렬 후 `slice(0,300)` 으로 그리는데,
#     제목에는 전체 건수를 쓰면서 잘렸다는 안내도, 더 보기도, 검색도 없었다.
#     7천여 건을 한 번에 올리면 2022년 건은 300번째 밖이라 화면에 아예 나오지 않는다.
#     (미배정·보류·제외 세 목록 모두 같은 방식)
#   - 미배정으로 남은 이유는 별개: _fxResolveVendor 가 입금자명 완전일치만 보므로
#     '(주)세화산업사'로 등록된 업체에 '세화산업사'(2022년 표기)는 안 붙는다.
#     이 매칭 규칙은 사용자 결정으로 이번에 건드리지 않는다(지금은 그대로 두기).
#
#  수정(사용자 선택 = "검색창 + 잘림 안내"):
#   (1) 미배정 패널 머리에 검색창(입금자명·날짜·은행·금액). 180ms 디바운스, 다시 그린 뒤 포커스 복원.
#   (2) 검색은 목록 배열 자체를 거른다 — 행 버튼이 _fxUnList[i] / _fxExList[i] 인덱스로 동작하므로
#       "표시만" 거르면 엉뚱한 건에 배정된다. 같은 이유로 제외 목록도 같은 검색어로 함께 거른다.
#   (3) 보류 목록은 거르지 않는다 — [전체 다시 확인](fxUnholdAll)이 _fxHeldList 전체를 푸는 버튼이라
#       걸러 두면 "전체"의 뜻이 달라진다. 대신 잘림 안내만 붙인다.
#   (4) 세 목록 모두 300건을 넘으면 "N건 중 300건만 표시 — 검색으로 좁혀보세요" 를 표시한다.
#   (5) 검색 결과가 0건이어도 패널과 검색창은 남는다(검색어를 지울 수 있어야 하므로).

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R169 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r169(s, path):
    # (1) 상태 + 검색 헬퍼
    s = rep(s,
        "  var _fxUnList=[], _fxExList=[], _fxHeldList=[], _fxShowExcl=false, _fxHeldOpen=false;",
        "  var _fxUnList=[], _fxExList=[], _fxHeldList=[], _fxShowExcl=false, _fxHeldOpen=false;\n"
        "  // r169: 미배정·제외 목록 검색어 (목록이 300건에서 잘려 과거 건이 안 보이던 문제)\n"
        "  var _fxUnQ='', _fxUnQTimer=null;\n"
        "  var _FX_UN_CAP=300;\n"
        "  function _fxUnQMatch(e){\n"
        "    if(!_fxUnQ) return true;\n"
        "    var q=String(_fxUnQ).replace(/[,\\s]/g,'').toLowerCase();\n"
        "    if(!q) return true;\n"
        "    var hay=(String(e.payer||'')+'|'+String(e.date||'')+'|'+String(e.bank||'')+'|'+String(e.amount||''))\n"
        "              .replace(/[,\\s]/g,'').toLowerCase();\n"
        "    return hay.indexOf(q)>=0;\n"
        "  }\n"
        "  window.fxUnQInput = function(v){\n"
        "    if(_fxUnQTimer) clearTimeout(_fxUnQTimer);\n"
        "    _fxUnQTimer=setTimeout(function(){ _fxUnQTimer=null; _fxUnQ=String(v==null?'':v).trim(); _fxRenderUnasg(); }, 180);\n"
        "  };\n"
        "  window.fxUnQClear = function(){\n"
        "    if(_fxUnQTimer){ clearTimeout(_fxUnQTimer); _fxUnQTimer=null; }\n"
        "    _fxUnQ=''; _fxRenderUnasg();\n"
        "  };\n"
        "  function _fxUnCapNote(shown, total){\n"
        "    if(total<=shown) return '';\n"
        "    return '<div style=\"padding:7px 14px;background:#fffbeb;border-bottom:1px solid #f0d9b8;font-size:11.5px;color:#b45309\">'\n"
        "      + '전체 '+_fxFmt(total)+'건 중 '+_fxFmt(shown)+'건만 표시됩니다 &mdash; 위 검색창에 입금자명·날짜·금액을 넣어 좁혀보세요.'\n"
        "      + '</div>';\n"
        "  }",
        1, 'UNQSTATE')

    # (2) 목록 필터 적용 (인덱스가 맞도록 배열 자체를 거른다)
    s = rep(s,
        "    _fxUnList.sort(function(a,b){ return a.date<b.date?1:a.date>b.date?-1:0; });\n"
        "    var TH='padding:8px 10px;background:#fafafa;",
        "    _fxUnList.sort(function(a,b){ return a.date<b.date?1:a.date>b.date?-1:0; });\n"
        "    // r169: 검색 필터. 행 버튼이 _fxUnList[i]/_fxExList[i] 인덱스로 동작하므로 배열 자체를 거른다.\n"
        "    //  보류 목록은 [전체 다시 확인]이 목록 전체를 푸는 버튼이라 거르지 않는다.\n"
        "    var _unAll=_fxUnList.length, _exAll=_fxExList.length;\n"
        "    if(_fxUnQ){\n"
        "      _fxUnList=_fxUnList.filter(_fxUnQMatch);\n"
        "      _fxExList=_fxExList.filter(_fxUnQMatch);\n"
        "    }\n"
        "    var TH='padding:8px 10px;background:#fafafa;",
        1, 'UNQFILTER')

    # (3) 미배정 패널: 검색창 + 잘림 안내 + 결과 0건 처리
    s = rep(s,
        "    if(_fxUnList.length){\n"
        "      fxUnDdHide();\n"
        "      var rows=_fxUnList.slice(0,300).map(function(e,i){",
        "    if(_unAll){\n"
        "      fxUnDdHide();\n"
        "      var rows=_fxUnList.slice(0,_FX_UN_CAP).map(function(e,i){",
        1, 'UNPANEL')

    s = rep(s,
        "        + '<div style=\"padding:10px 14px;border-bottom:1px solid #e3e9f0;font-size:12.5px;font-weight:700;color:#d97706;display:flex;align-items:center;gap:8px;flex-wrap:wrap\">미배정 입금 '+_fxUnList.length+'건'",
        "        + '<div style=\"padding:10px 14px;border-bottom:1px solid #e3e9f0;font-size:12.5px;font-weight:700;color:#d97706;display:flex;align-items:center;gap:8px;flex-wrap:wrap\">미배정 입금 '+_fxFmt(_unAll)+'건'\n"
        "        + (_fxUnQ?'<span style=\"font-weight:400;color:#b45309\">(검색 '+_fxFmt(_fxUnList.length)+'건)</span>':'')\n"
        "        + '<input type=\"text\" id=\"fxUnQ\" class=\"q-flat\" placeholder=\"입금자·날짜·금액 검색…\" autocomplete=\"off\" value=\"'+esc(_fxUnQ)+'\" oninput=\"fxUnQInput(this.value)\" style=\"width:190px;border:1px solid #d6deea !important;background:#fff;font-weight:400\">'\n"
        "        + (_fxUnQ?'<button type=\"button\" class=\"btn\" onclick=\"fxUnQClear()\" style=\"font-size:11px;padding:2px 10px;border:1px solid #d6deea;color:#6b7280;background:#fff;font-weight:400\">검색 지우기</button>':'')",
        1, 'UNHEADER')

    s = rep(s,
        "        + '<div style=\"max-height:420px;overflow:auto\"><table style=\"width:100%;border-collapse:collapse\">'\n"
        "        + '<thead><tr><th style=\"'+TH+'\">사업장</th><th style=\"'+TH+'\">입금일</th><th style=\"'+TH+'\">은행</th><th style=\"'+TH+';text-align:left\">입금자</th><th style=\"'+TH+';text-align:right\">금액</th><th style=\"'+TH+';text-align:left\">거래처 지정</th></tr></thead>'\n"
        "        + '<tbody>'+rows+'</tbody></table></div></div>';",
        "        + _fxUnCapNote(Math.min(_fxUnList.length,_FX_UN_CAP), _fxUnList.length)\n"
        "        + (_fxUnList.length\n"
        "            ? ('<div style=\"max-height:420px;overflow:auto\"><table style=\"width:100%;border-collapse:collapse\">'\n"
        "               + '<thead><tr><th style=\"'+TH+'\">사업장</th><th style=\"'+TH+'\">입금일</th><th style=\"'+TH+'\">은행</th><th style=\"'+TH+';text-align:left\">입금자</th><th style=\"'+TH+';text-align:right\">금액</th><th style=\"'+TH+';text-align:left\">거래처 지정</th></tr></thead>'\n"
        "               + '<tbody>'+rows+'</tbody></table></div>')\n"
        "            : '<div style=\"padding:28px;text-align:center;color:#b6bec9;font-size:12.5px\">검색 결과가 없습니다.</div>')\n"
        "        + '</div>';",
        1, 'UNBODY')

    # (4) 보류 목록: 잘림 안내
    s = rep(s,
        "        var hrows=_fxHeldList.slice(0,300).map(function(e,i){",
        "        var hrows=_fxHeldList.slice(0,_FX_UN_CAP).map(function(e,i){",
        1, 'HELDCAP')
    s = rep(s,
        "        html += '<div style=\"margin-top:6px;background:#fff;border:1px solid #f0d9b8;max-height:300px;overflow:auto\"><table style=\"width:100%;border-collapse:collapse\"><tbody>'+hrows+'</tbody></table></div>';",
        "        html += '<div style=\"margin-top:6px;background:#fff;border:1px solid #f0d9b8\">'\n"
        "          + _fxUnCapNote(Math.min(_fxHeldList.length,_FX_UN_CAP), _fxHeldList.length)\n"
        "          + '<div style=\"max-height:300px;overflow:auto\"><table style=\"width:100%;border-collapse:collapse\"><tbody>'+hrows+'</tbody></table></div></div>';",
        1, 'HELDNOTE')

    # (5) 제외 목록: 검색 반영 + 잘림 안내
    s = rep(s,
        "    if(_fxExList.length){\n"
        "      html += '<div style=\"margin-top:8px;font-size:11.5px;color:#9ca3af\">제외한 입금 '+_fxExList.length+'건 '",
        "    if(_exAll){\n"
        "      html += '<div style=\"margin-top:8px;font-size:11.5px;color:#9ca3af\">제외한 입금 '+_fxFmt(_exAll)+'건 '\n"
        "        + (_fxUnQ?'<span style=\"color:#b45309\">(검색 '+_fxFmt(_fxExList.length)+'건)</span> ':'')",
        1, 'EXHEADER')
    s = rep(s,
        "        var rows2=_fxExList.slice(0,300).map(function(e,i){",
        "        var rows2=_fxExList.slice(0,_FX_UN_CAP).map(function(e,i){",
        1, 'EXCAP')
    s = rep(s,
        "        html += '<div style=\"margin-top:6px;background:#fff;border:1px solid #e3e9f0;max-height:260px;overflow:auto\"><table style=\"width:100%;border-collapse:collapse\"><tbody>'+rows2+'</tbody></table></div>';",
        "        html += '<div style=\"margin-top:6px;background:#fff;border:1px solid #e3e9f0\">'\n"
        "          + _fxUnCapNote(Math.min(_fxExList.length,_FX_UN_CAP), _fxExList.length)\n"
        "          + (_fxExList.length\n"
        "              ? '<div style=\"max-height:260px;overflow:auto\"><table style=\"width:100%;border-collapse:collapse\"><tbody>'+rows2+'</tbody></table></div>'\n"
        "              : '<div style=\"padding:20px;text-align:center;color:#b6bec9;font-size:12px\">검색 결과가 없습니다.</div>')\n"
        "          + '</div>';",
        1, 'EXNOTE')

    # (6) 다시 그린 뒤 검색창 포커스 복원 (디바운스 중 타이핑이 끊기지 않게)
    s = rep(s,
        "    host.innerHTML=html;\n  }\n  // ── r155: 사업자번호 판정 ──",
        "    host.innerHTML=html;\n"
        "    // r169: innerHTML 로 다시 그리면 포커스가 날아가므로 검색 중이면 되돌려 준다.\n"
        "    if(_fxUnQ){\n"
        "      var _qi=document.getElementById('fxUnQ');\n"
        "      if(_qi && document.activeElement!==_qi){\n"
        "        try{ _qi.focus(); _qi.setSelectionRange(_qi.value.length, _qi.value.length); }catch(_e){}\n"
        "      }\n"
        "    }\n  }\n  // ── r155: 사업자번호 판정 ──",
        1, 'FOCUS')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r169(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r168 2026-08-26 -->') == 1
            s = s.replace('<!-- test build r168 2026-08-26 -->', '<!-- test build r169 2026-08-31 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
