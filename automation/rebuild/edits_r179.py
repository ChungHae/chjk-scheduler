# -*- coding: utf-8 -*-
# r179: 견적 불러오기 — 날짜를 '기간'으로 검색 + 10개 넘어도 페이지로 전부 보기
#
#  사용자 요청 2가지:
#   ① 지금은 날짜를 하나만 찍어 그 날짜만 검색된다 → 시작일~종료일 기간으로 찾고 싶다.
#   ② 10개까지만 보이고 그 뒤는 볼 방법이 없다 → 페이지를 넘겨 전부 볼 수 있게.
#
#  현재 동작(코드 확인):
#   · 필터는 qLoadDate 한 칸, qq.savedAt(저장 시각)의 YYYYMMDD 와 '완전히 같을 때'만 통과.
#   · 날짜를 안 고르면 최신 10건만 자르고 '최신 10개만 표시됩니다' 안내만 붙었다.
#     → 11번째부터는 날짜나 거래처로 우연히 좁히지 않는 한 볼 방법이 아예 없었다.
#     (날짜를 고르면 상한이 풀려 그날 것은 전부 나왔다 — 상한이 일관되지도 않았다.)
#
#  수정:
#   ① qLoadDate → qLoadFrom ~ qLoadTo 두 칸. 기준 필드는 종전과 같은 savedAt 이다
#      (목록에 찍히는 날짜가 savedAt 이므로, 보이는 값으로 걸러야 예측 가능하다).
#      · 시작일만: 그날부터 이후 전부   · 종료일만: 그날까지 이전 전부
#      · 둘 다: 사이(양끝 포함)         · 거꾸로 넣으면 두 값을 바꿔서 적용한다
#   ② 페이지 나누기(한 쪽 10건). 목록 아래에 '이전 / N M 페이지 · 조건에 맞는 견적 K건 / 다음'.
#      미수현황 페이저(_fxArPagerHtml)와 같은 각진 디자인.
#      · 필터가 바뀌면 1쪽으로 되돌린다(안 그러면 빈 쪽이 보인다).
#      · 삭제 등으로 건수가 줄어 현재 쪽이 사라지면 마지막 쪽으로 당긴다.
#   · '최신 10개만 표시됩니다' 안내는 더 이상 사실이 아니므로 제거한다.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R179 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r179(s, path):
    # (1) 필터 줄: 날짜 한 칸 → 기간 두 칸
    s = rep(s,
        "        +'<input type=\"date\" id=\"qLoadDate\" value=\"\" onchange=\"_qRenderLoadList()\" style=\"'+INP+'\">'\n"
        "        +'<button class=\"btn\" onclick=\"qLoadResetFilters()\" style=\"font-size:12px;padding:6px 10px\">초기화</button>'",
        "        // r179: 날짜 한 칸 → 기간(시작~종료). 한쪽만 넣어도 된다.\n"
        "        +'<span style=\"display:inline-flex;align-items:center;gap:5px\">'\n"
        "          +'<input type=\"date\" id=\"qLoadFrom\" value=\"\" title=\"시작일 (이 날짜부터)\" onchange=\"_qLoadFilterChanged()\" style=\"'+INP+'\">'\n"
        "          +'<span style=\"color:#9ca3af;font-size:12px\">~</span>'\n"
        "          +'<input type=\"date\" id=\"qLoadTo\" value=\"\" title=\"종료일 (이 날짜까지)\" onchange=\"_qLoadFilterChanged()\" style=\"'+INP+'\">'\n"
        "        +'</span>'\n"
        "        +'<button class=\"btn\" onclick=\"qLoadResetFilters()\" style=\"font-size:12px;padding:6px 10px\">초기화</button>'",
        1, 'DATERANGE')

    # 검색어·작성자도 필터가 바뀌면 1쪽으로
    s = rep(s,
        "        +'<input id=\"qLoadSearch\" value=\"'+esc(_defVn)+'\" placeholder=\"거래처 · 이름 · 작성자 · 메모 검색\" oninput=\"_qRenderLoadList()\" style=\"'+INP+';flex:1;min-width:150px\">'\n"
        "        +'<select id=\"qLoadWriter\" onchange=\"_qRenderLoadList()\" style=\"'+INP+'\">'+_wopts2+'</select>'",
        "        +'<input id=\"qLoadSearch\" value=\"'+esc(_defVn)+'\" placeholder=\"거래처 · 이름 · 작성자 · 메모 검색\" oninput=\"_qLoadFilterChanged()\" style=\"'+INP+';flex:1;min-width:150px\">'\n"
        "        +'<select id=\"qLoadWriter\" onchange=\"_qLoadFilterChanged()\" style=\"'+INP+'\">'+_wopts2+'</select>'",
        1, 'FILTERHOOK')

    # 팝업을 열 때는 1쪽부터
    s = rep(s,
        "    ov.style.display='flex';\n"
        "    _qRenderLoadList();\n"
        "  };\n"
        "  window.qLoadResetFilters = function(){   // 필터 모두 비우기 → 전체 표시\n"
        "    var s=document.getElementById('qLoadSearch'); if(s) s.value='';\n"
        "    var w=document.getElementById('qLoadWriter'); if(w) w.value='';\n"
        "    var d=document.getElementById('qLoadDate'); if(d) d.value='';\n"
        "    _qRenderLoadList();\n"
        "  };",
        "    ov.style.display='flex';\n"
        "    _qLoadPage=1;   // r179\n"
        "    _qRenderLoadList();\n"
        "  };\n"
        "  // ── r179: 목록 페이지 ──\n"
        "  var _qLoadPage=1, _QLOAD_PER=10;\n"
        "  window._qLoadFilterChanged = function(){ _qLoadPage=1; _qRenderLoadList(); };   // 필터가 바뀌면 첫 쪽부터\n"
        "  window.qLoadPageDelta = function(d){\n"
        "    _qLoadPage += d; if(_qLoadPage<1) _qLoadPage=1;\n"
        "    _qRenderLoadList();\n"
        "    var box=document.getElementById('qLoadList'); if(box) box.scrollTop=0;\n"
        "  };\n"
        "  window.qLoadResetFilters = function(){   // 필터 모두 비우기 → 전체 표시\n"
        "    var s=document.getElementById('qLoadSearch'); if(s) s.value='';\n"
        "    var w=document.getElementById('qLoadWriter'); if(w) w.value='';\n"
        "    var f=document.getElementById('qLoadFrom'); if(f) f.value='';\n"
        "    var t=document.getElementById('qLoadTo'); if(t) t.value='';\n"
        "    _qLoadPage=1;\n"
        "    _qRenderLoadList();\n"
        "  };",
        1, 'PAGEVARS')

    # (2) 필터 판정: 하루 → 기간
    s = rep(s,
        "    var dv=((document.getElementById('qLoadDate')||{}).value||'');\n"
        "    var dnum=dv?dv.replace(/-/g,''):'';",
        "    // r179: 기간 필터 — 한쪽만 넣어도 되고, 거꾸로 넣으면 바꿔서 적용한다\n"
        "    var _f=((document.getElementById('qLoadFrom')||{}).value||'').replace(/-/g,'');\n"
        "    var _t=((document.getElementById('qLoadTo')||{}).value||'').replace(/-/g,'');\n"
        "    if(_f && _t && _f>_t){ var _sw=_f; _f=_t; _t=_sw; }",
        1, 'RANGEVARS')

    s = rep(s,
        "      if(dnum){ var d=qq.savedAt?new Date(qq.savedAt):null; var ds=d?(d.getFullYear()+String(d.getMonth()+1).padStart(2,'0')+String(d.getDate()).padStart(2,'0')):''; if(ds!==dnum) return false; }\n"
        "      return true;",
        "      if(_f || _t){\n"
        "        var d=qq.savedAt?new Date(qq.savedAt):null;\n"
        "        var ds=d?(d.getFullYear()+String(d.getMonth()+1).padStart(2,'0')+String(d.getDate()).padStart(2,'0')):'';\n"
        "        if(!ds) return false;                 // 저장 시각이 없으면 기간 판정을 할 수 없다\n"
        "        if(_f && ds<_f) return false;\n"
        "        if(_t && ds>_t) return false;\n"
        "      }\n"
        "      return true;",
        1, 'RANGEFILTER')

    # (3) 10개 자르기 → 페이지 나누기
    s = rep(s,
        "    var _moreN='';\n"
        "    if(!dnum && list.length>10){ _moreN='<div style=\"padding:8px 14px;text-align:center;font-size:11px;color:#9ca3af\">최신 10개만 표시됩니다 · 날짜/거래처로 좁혀주세요</div>'; list=list.slice(0,10); }",
        "    // r179: 잘라서 감추지 않고 쪽을 나눈다 — 11번째부터는 볼 방법이 아예 없었다\n"
        "    var _total=list.length;\n"
        "    var _pages=Math.max(1, Math.ceil(_total/_QLOAD_PER));\n"
        "    if(_qLoadPage>_pages) _qLoadPage=_pages;   // 삭제 등으로 줄었으면 마지막 쪽으로\n"
        "    if(_qLoadPage<1) _qLoadPage=1;\n"
        "    list=list.slice((_qLoadPage-1)*_QLOAD_PER, _qLoadPage*_QLOAD_PER);\n"
        "    var _moreN = (_total>_QLOAD_PER)\n"
        "      ? ('<div style=\"display:flex;align-items:center;justify-content:center;gap:10px;padding:10px 14px;border-top:1px solid #eef2f7;background:#fafbfc\">'\n"
        "         + '<button type=\"button\" class=\"btn\" onclick=\"qLoadPageDelta(-1)\"'+(_qLoadPage<=1?' disabled':'')+' style=\"font-size:11.5px;padding:3px 12px;border:1px solid #c8d2de;border-radius:0;background:#fff;color:'+(_qLoadPage<=1?'#c9d0da':'#374151')+';cursor:'+(_qLoadPage<=1?'default':'pointer')+'\">&lsaquo; 이전</button>'\n"
        "         + '<span style=\"font-size:12px;color:#6b7280\">'+_qLoadPage+' / '+_pages+' 페이지 &middot; 조건에 맞는 견적 '+_total+'건</span>'\n"
        "         + '<button type=\"button\" class=\"btn\" onclick=\"qLoadPageDelta(1)\"'+(_qLoadPage>=_pages?' disabled':'')+' style=\"font-size:11.5px;padding:3px 12px;border:1px solid #c8d2de;border-radius:0;background:#fff;color:'+(_qLoadPage>=_pages?'#c9d0da':'#374151')+';cursor:'+(_qLoadPage>=_pages?'default':'pointer')+'\">다음 &rsaquo;</button>'\n"
        "         + '</div>')\n"
        "      : '';",
        1, 'PAGER')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r179(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r178 2026-09-07 -->') == 1
            s = s.replace('<!-- test build r178 2026-09-07 -->', '<!-- test build r179 2026-09-11 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
