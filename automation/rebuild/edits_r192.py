# -*- coding: utf-8 -*-
# r192: 보류·제외한 입금을 '최근 처리 순'으로 정렬 + 처리 시각 표시
#
#  사용자 요청: "보류한 입금내역과 제외한 입금내역도 거래처 배정입금내역처럼 최근 기준으로
#               정렬되게 해줘. 내가 잘못 누른 것들을 확인하고 다시 되돌리고 싶은데 확인이 힘들어."
#
#  현재 상태(코드 확인):
#   · 보류 목록  : 입금일(e.date) 내림차순.  누른 순서와 무관하다.
#   · 제외 목록  : 정렬이 아예 없다(fxDeposits 들어온 순서 그대로).
#   · 배정 목록  : _fxAsgStamp 가 asgAt(누른 시각)을 남겨 두고 그 시각 기준으로 묶어 보여준다.
#  => 방금 잘못 누른 건을 찾으려면 '입금일'이 아니라 '누른 시각'으로 봐야 한다.
#     배정 목록이 이미 그렇게 동작하므로, 같은 방식을 보류·제외에도 적용한다.
#
#  수정:
#   (A) 누를 때 시각을 남긴다 — 보류 heldAt, 제외 exAt.
#       되돌릴 때(다시 확인·복원)는 표식을 지워, 나중에 다시 누르면 새 시각이 찍히게 한다.
#       ★ 업로드 중 자동 제외(카드정산 규칙)에는 시각을 남기지 않는다. 사용자가 누른 게 아니므로
#         표식이 없어야 손으로 누른 건만 위로 올라온다. 자동 제외 '버튼'은 사용자 행동이라 남긴다.
#   (B) 두 목록을 누른 시각 내림차순으로 정렬. 시각이 없는 옛 자료는 그 뒤에 입금일 순으로 둔다.
#       (기존 자료에는 표식이 없다 — 앞으로 누르는 것부터 맨 위에 쌓인다)
#   (C) 언제 눌렀는지 줄마다 보여준다(방금 / N분 전 / MM-DD HH:mm). 300건 표시 상한이 있어
#       정렬만으로는 "이게 방금 그건가?" 를 확신하기 어렵다.

import io

def rep(s, old, new, exp, label):
    n = s.count(old)
    if n != exp: raise SystemExit('R192 FAIL %s count %d (expect %d)' % (label, n, exp))
    return s.replace(old, new)

def apply_r192(s, path):
    # ── (A) 시각 남기기 ──
    s = rep(s,
        "    var d=_fxUnList[i]; if(!d) return;\n"
        "    d.held=true;\n",
        "    var d=_fxUnList[i]; if(!d) return;\n"
        "    d.held=true; d.heldAt=Date.now();   // r192: 누른 시각 (되돌릴 때 찾기 쉽게)\n",
        1, 'HOLD')

    s = rep(s,
        "    var d=_fxHeldList[i]; if(!d) return;\n"
        "    delete d.held;\n",
        "    var d=_fxHeldList[i]; if(!d) return;\n"
        "    delete d.held; delete d.heldAt;   // r192\n",
        1, 'UNHOLD')

    s = rep(s,
        "    _fxHeldList.forEach(function(e){ delete e.held; });\n",
        "    _fxHeldList.forEach(function(e){ delete e.held; delete e.heldAt; });   // r192\n",
        1, 'UNHOLDALL')

    s = rep(s,
        "    var d=_fxUnList[i]; if(!d) return;\n"
        "    d.excluded=true;\n",
        "    var d=_fxUnList[i]; if(!d) return;\n"
        "    d.excluded=true; d.exAt=Date.now();   // r192\n",
        1, 'EXCL')

    s = rep(s,
        "    var d=_fxHeldList[i]; if(!d) return;\n"
        "    d.excluded=true; delete d.held;\n",
        "    var d=_fxHeldList[i]; if(!d) return;\n"
        "    d.excluded=true; d.exAt=Date.now(); delete d.held; delete d.heldAt;   // r192\n",
        1, 'EXCLHELD')

    s = rep(s,
        "    var d=_fxExList[i]; if(!d) return;\n"
        "    d.excluded=false;\n",
        "    var d=_fxExList[i]; if(!d) return;\n"
        "    d.excluded=false; delete d.exAt;   // r192\n",
        1, 'RESTORE')

    #  자동 제외 '버튼' 은 사용자 행동이므로 시각을 남긴다
    s = rep(s,
        "        targets.forEach(function(e){ e.excluded=true; delete e.held; });\n",
        "        var _now=Date.now();\n"
        "        targets.forEach(function(e){ e.excluded=true; e.exAt=_now; delete e.held; delete e.heldAt; });   // r192\n",
        1, 'AUTOEXCL')

    # ── (B) 정렬 + (C) 시각 표시 도우미 ──
    s = rep(s,
        "  var _fxUnList=[], _fxExList=[], _fxHeldList=[], _fxShowExcl=false, _fxHeldOpen=false;",
        "  var _fxUnList=[], _fxExList=[], _fxHeldList=[], _fxShowExcl=false, _fxHeldOpen=false;\n"
        "  // r192: 보류·제외를 '누른 시각' 내림차순으로. 시각이 없는 옛 자료는 뒤에 입금일 순으로 둔다.\n"
        "  function _fxByActed(key){\n"
        "    return function(a,b){\n"
        "      var ta=(a&&a[key])||0, tb=(b&&b[key])||0;\n"
        "      if(ta!==tb) return tb-ta;                       // 최근에 누른 것이 위\n"
        "      var da=(a&&a.date)||'', db=(b&&b.date)||'';\n"
        "      return da<db?1:da>db?-1:0;                      // 같으면 입금일 최신순\n"
        "    };\n"
        "  }\n"
        "  // r192: 언제 눌렀는지 — 방금 / N분 전 / N시간 전 / MM-DD HH:mm\n"
        "  function _fxActedHtml(ts, label){\n"
        "    if(!ts) return '';\n"
        "    var d=new Date(ts), m=Math.floor((Date.now()-ts)/60000), t;\n"
        "    if(m<1) t='방금';\n"
        "    else if(m<60) t=m+'분 전';\n"
        "    else if(m<24*60) t=Math.floor(m/60)+'시간 전';\n"
        "    else t=('0'+(d.getMonth()+1)).slice(-2)+'-'+('0'+d.getDate()).slice(-2)+' '+('0'+d.getHours()).slice(-2)+':'+('0'+d.getMinutes()).slice(-2);\n"
        "    return '<span title=\"'+label+' '+d.toLocaleString()+'\" style=\"font-size:11px;color:#9ca3af;white-space:nowrap\">'+t+'</span>';\n"
        "  }",
        1, 'HELPERS')

    s = rep(s,
        "    _fxHeldList.sort(function(a,b){ return a.date<b.date?1:a.date>b.date?-1:0; });\n",
        "    _fxHeldList.sort(_fxByActed('heldAt'));   // r192: 최근에 보류한 것이 위\n",
        1, 'SORTHELD')

    s = rep(s,
        "    _fxExList = fxDeposits.filter(function(e){ return e.excluded; });\n",
        "    _fxExList = fxDeposits.filter(function(e){ return e.excluded; });\n"
        "    _fxExList.sort(_fxByActed('exAt'));       // r192: 최근에 제외한 것이 위 (종전에는 정렬이 없었다)\n",
        1, 'SORTEXCL')

    # ── (C) 줄마다 처리 시각 ──
    s = rep(s,
        "            + '<td style=\"'+TD+';text-align:right;font-weight:700\">'+_fxFmt(e.amount)+'</td>'\n"
        "            + '<td style=\"'+TD+'\"><div style=\"display:flex;gap:6px;align-items:center\">'\n"
        "            +   '<button type=\"button\" class=\"btn\" onclick=\"fxUnholdDep('+i+')\"",
        "            + '<td style=\"'+TD+';text-align:right;font-weight:700\">'+_fxFmt(e.amount)+'</td>'\n"
        "            + '<td style=\"'+TD+';text-align:right\">'+_fxActedHtml(e.heldAt,'보류한 시각')+'</td>'   // r192\n"
        "            + '<td style=\"'+TD+'\"><div style=\"display:flex;gap:6px;align-items:center\">'\n"
        "            +   '<button type=\"button\" class=\"btn\" onclick=\"fxUnholdDep('+i+')\"",
        1, 'ROWHELD')

    s = rep(s,
        "            + '<td style=\"'+TD+';text-align:right;color:#9ca3af\">'+_fxFmt(e.amount)+'</td>'\n"
        "            + '<td style=\"'+TD+'\"><button type=\"button\" class=\"btn\" onclick=\"fxRestoreDep('+i+')\"",
        "            + '<td style=\"'+TD+';text-align:right;color:#9ca3af\">'+_fxFmt(e.amount)+'</td>'\n"
        "            + '<td style=\"'+TD+';text-align:right\">'+_fxActedHtml(e.exAt,'제외한 시각')+'</td>'   // r192\n"
        "            + '<td style=\"'+TD+'\"><button type=\"button\" class=\"btn\" onclick=\"fxRestoreDep('+i+')\"",
        1, 'ROWEXCL')
    return s

if __name__ == '__main__':
    for path in ('/mnt/user-data/outputs/index.html', '/mnt/user-data/outputs/testpage/index.html'):
        s = io.open(path, encoding='utf-8').read()
        s = apply_r192(s, path)
        if 'testpage' in path:
            assert s.count('<!-- test build r191 2026-09-17 -->') == 1
            s = s.replace('<!-- test build r191 2026-09-17 -->', '<!-- test build r192 2026-09-17 -->')
        io.open(path, 'w', encoding='utf-8').write(s)
        print('OK', path)
